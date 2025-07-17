import modal
import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# Create Modal app
app = modal.App("sketch-animation-s3")

# Define a simplified Modal image with S3 support
image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install([
        "ffmpeg", 
        "potrace", 
        "imagemagick", 
        "libcairo2", 
        "libcairo2-dev", 
        "pkg-config", 
        "libpango1.0-0", 
        "libpangocairo-1.0-0", 
        "libpango1.0-dev",  # Added for pangocairo
        "libglib2.0-0", 
        "libpixman-1-0", 
        "python3-gi", 
        "build-essential",
        "libffi-dev",
        "libssl-dev",
        "wget",
        "curl",
        "git"
    ])
    .pip_install([
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "openai>=1.10.0",
        "elevenlabs==0.2.26",
        "moviepy==1.0.3",
        "Pillow==10.1.0",
        "python-dotenv==1.0.0",
        "requests==2.31.0",
        "pydantic==2.5.0",
        "aiofiles==23.2.1",
        "jinja2==3.1.2",
        "numpy",
        "opencv-python",
        "svgwrite",
        "boto3",
        "whisper-openai",
        "manim",
        "svgpathtools"
    ])
    .workdir("/app")
    .env({"PYTHONPATH": "/app"})
    .add_local_file("services/s3_service.py", "/app/services/s3_service.py")
    .add_local_file("services/script_service.py", "/app/services/script_service.py")
    .add_local_file("services/image_service_s3.py", "/app/services/image_service_s3.py") 
    .add_local_file("services/audio_service_s3.py", "/app/services/audio_service_s3.py")
    .add_local_file("services/__init__.py", "/app/services/__init__.py")
    .add_local_file("doodly_pipeline.py", "/app/doodly_pipeline.py")
    .add_local_file("templates/index.html", "/app/templates/index.html")
    .add_local_file("templates/scriptapi.html", "/app/templates/scriptapi.html")
)

# Pydantic models
class GenImageRequest(BaseModel):
    prompt: str

class ScriptVideoRequest(BaseModel):
    script: str
    image_quality: str = "medium"
    voice_id: str = "pNInz6obpgDQGcFmaJgB"
    video_type: str = "landscape"

def create_fastapi_app():
    """Create and configure the FastAPI application with S3 storage"""
    import sys
    sys.path.append("/app")
    
    web_app = FastAPI(title="Sketch Animation API - S3 Storage")
    
    # Set up temporary directories for processing
    os.makedirs("/tmp/outputs", exist_ok=True)
    os.makedirs("/tmp/apiOutputs", exist_ok=True)
    os.makedirs("/tmp/apiOutputs/video", exist_ok=True)
    
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
    os.environ["ELEVENLABS_API_KEY"] = os.environ.get("ELEVENLABS_API_KEY", "")
    
    @web_app.post("/generate-image")
    async def generate_image(req: GenImageRequest):
        """Generate a sketch image from a prompt and store in S3"""
        try:
            from services.image_service_s3 import ImageService
            
            job_id = str(uuid.uuid4())
            image_service = ImageService()
            
            # Generate image (will be stored in S3)
            image_url = image_service.generate_sketch_image(req.prompt, job_id, 0)
            
            return {"image_url": image_url}
        except Exception as e:
            return {"error": str(e)}

    @web_app.post("/generate-s3-video")
    async def generate_s3_video(req: ScriptVideoRequest):
        """Generate a complete video from script with S3 storage"""
        try:
            from services.script_service import ScriptService
            from services.audio_service_s3 import AudioService
            from services.ideogram_image_service_s3 import IdeogramImageService
            from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, concatenate_audioclips, VideoFileClip
            import requests
            import tempfile
            import os
            
            job_id = str(uuid.uuid4())
            
            # Initialize services
            script_service = ScriptService()
            audio_service = AudioService()
            image_service = IdeogramImageService()
            
            # Set custom voice ID
            audio_service.set_voice(req.voice_id)
            
            # Set image size based on video type
            if req.video_type == "landscape":
                image_size = "1536x1024"
            else:
                image_size = "1024x1024"
            
            # Step 1: Split script into sentences
            sentences = script_service.split_script_into_sentences(req.script)
            
            # Step 2: Generate audio for each sentence
            audio_segments = []
            for i, sentence in enumerate(sentences):
                audio = await audio_service.generate_audio_per_sentence([sentence], f"{job_id}_{i}", req.voice_id)
                audio_segments.extend(audio)
            
            # Step 3: Generate images for each sentence
            image_urls = []
            for i, seg in enumerate(audio_segments):
                image_url = image_service.generate_sketch_image_with_quality(
                    seg['sentence'], job_id, i, req.image_quality, image_size
                )
                image_urls.append(image_url)
            
            # Step 4: Download images and convert to SVG animations
            from doodly_pipeline import png_to_svg, animate_svg, concatenate_videos
            svg_video_paths = []
            temp_files = []

            for i, (image_url, seg) in enumerate(zip(image_urls, audio_segments)):
                # Download image from S3 URL to temp file
                if image_url.startswith('http'):
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        temp_image_path = f"/tmp/outputs/temp_image_{job_id}_{i}.png"
                        with open(temp_image_path, 'wb') as f:
                            f.write(response.content)
                        temp_files.append(temp_image_path)
                    else:
                        raise Exception(f"Failed to download image from {image_url}")
                else:
                    temp_image_path = image_url

                # Convert PNG to SVG
                svg_path = png_to_svg(temp_image_path)
                temp_files.append(svg_path)

                # Animate SVG with per-sentence duration
                out_name = f"svg_anim_{job_id}_{i}.mp4"
                video_path = animate_svg(svg_path, seg['duration'], out_name)
                svg_video_paths.append(video_path)

                # Cleanup SVG and PBM files
                try:
                    pbm_path = svg_path.replace('.svg', '.pbm')
                    if os.path.exists(svg_path):
                        os.remove(svg_path)
                    if os.path.exists(pbm_path):
                        os.remove(pbm_path)
                except Exception as e:
                    print(f"Warning: Could not delete SVG/PBM: {e}")

            # Step 5: Concatenate SVG video clips
            temp_video_path = f"/tmp/outputs/final_script_video_{job_id}.mp4"
            concatenate_videos(svg_video_paths, temp_video_path)
            
            # Step 6: Download and concatenate audio segments
            audio_clips = []
            for seg in audio_segments:
                if seg['audio_path'].startswith('http'):
                    # Download audio from S3 URL
                    response = requests.get(seg['audio_path'])
                    if response.status_code == 200:
                        temp_audio_path = f"/tmp/outputs/temp_audio_{job_id}_{len(audio_clips)}.mp3"
                        with open(temp_audio_path, 'wb') as f:
                            f.write(response.content)
                        temp_files.append(temp_audio_path)
                        audio_clip = AudioFileClip(temp_audio_path)
                    else:
                        raise Exception(f"Failed to download audio from {seg['audio_path']}")
                else:
                    audio_clip = AudioFileClip(seg['audio_path'])
                audio_clips.append(audio_clip)
            
            final_audio = concatenate_audioclips(audio_clips)
            
            # Step 7: Add audio to video
            final_video = VideoFileClip(temp_video_path)
            final_video = final_video.set_audio(final_audio)

            # Step 8: Export final video with audio
            final_video_path = f"/tmp/outputs/final_video_with_audio_{job_id}.mp4"
            final_video.write_videofile(
                final_video_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None,
                fps=24
            )

            # Step 9: Upload final video to S3
            from services.s3_service import S3Service
            s3_service = S3Service()
            final_video_url = s3_service.upload_video(final_video_path, job_id, "final")

            # Cleanup
            final_video.close()
            final_audio.close()
            for clip in audio_clips:
                clip.close()

            # Remove temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            for video_path in svg_video_paths:
                if os.path.exists(video_path):
                    os.remove(video_path)
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if os.path.exists(final_video_path):
                os.remove(final_video_path)
            
            return {
                "job_id": job_id,
                "status": "completed",
                "script": req.script,
                "video_type": req.video_type,
                "sentences_count": len(sentences),
                "images_count": len(image_urls),
                "final_video_url": final_video_url
            }
            
        except Exception as e:
            return {"error": str(e)}

    @web_app.post("/generate-script-video")
    async def generate_script_video(req: ScriptVideoRequest):
        """Generate a full SVG-animated video (one per sentence), upload all outputs to S3, and return only the S3 video URL."""
        try:
            from services.script_service import ScriptService
            from services.audio_service_s3 import AudioService
            from services.ideogram_image_service_s3 import IdeogramImageService
            from services.s3_service import S3Service
            from doodly_pipeline import png_to_svg, animate_svg, concatenate_videos
            from moviepy.editor import AudioFileClip, concatenate_audioclips, VideoFileClip
            import requests
            import os
            import uuid

            job_id = str(uuid.uuid4())
            script_service = ScriptService()
            audio_service = AudioService()
            image_service = IdeogramImageService()
            s3_service = S3Service()

            # Set image size based on video type
            if req.video_type == "landscape":
                image_size = "1536x1024"
            else:
                image_size = "1024x1024"

            # Step 1: Split script into sentences
            sentences = script_service.split_script_into_sentences(req.script)

            # Step 2: Generate audio for each sentence (already async)
            audio_segments = await audio_service.generate_audio_per_sentence(sentences, job_id, req.voice_id)

            # Step 3: Generate images for each sentence in parallel
            import asyncio
            image_tasks = [
                asyncio.to_thread(
                    image_service.generate_sketch_image_with_quality,
                    seg['sentence'], job_id, i, req.image_quality, image_size
                )
                for i, seg in enumerate(audio_segments)
            ]
            image_urls = await asyncio.gather(*image_tasks)

            # Step 4: Download images, convert to SVG, animate SVG
            svg_paths = []
            svg_video_paths = []
            temp_files = []
            durations = []
            for i, (image_url, seg) in enumerate(zip(image_urls, audio_segments)):
                # Download image from S3 URL to temp file
                if image_url.startswith('http'):
                    response = requests.get(image_url)
                    if response.status_code == 200:
                        temp_image_path = f"/tmp/outputs/temp_image_{job_id}_{i}.png"
                        with open(temp_image_path, 'wb') as f:
                            f.write(response.content)
                        temp_files.append(temp_image_path)
                    else:
                        raise Exception(f"Failed to download image from {image_url}")
                else:
                    temp_image_path = image_url

                # Convert PNG to SVG
                svg_path = png_to_svg(temp_image_path)
                svg_paths.append(svg_path)
                temp_files.append(svg_path)

                # Animate SVG with per-sentence duration
                out_name = f"svg_anim_{job_id}_{i}.mp4"
                duration = seg['duration']
                video_path = animate_svg(svg_path, duration, out_name)
                svg_video_paths.append(video_path)
                durations.append(duration)

            # Step 5: Concatenate SVG video clips
            temp_video_path = f"/tmp/outputs/final_script_video_{job_id}.mp4"
            concatenate_videos(svg_video_paths, temp_video_path)

            # Step 6: Download and concatenate audio segments
            audio_clips = []
            for seg in audio_segments:
                if seg['audio_path'].startswith('http'):
                    # Download audio from S3 URL
                    response = requests.get(seg['audio_path'])
                    if response.status_code == 200:
                        temp_audio_path = f"/tmp/outputs/temp_audio_{job_id}_{len(audio_clips)}.mp3"
                        with open(temp_audio_path, 'wb') as f:
                            f.write(response.content)
                        temp_files.append(temp_audio_path)
                        audio_clip = AudioFileClip(temp_audio_path)
                    else:
                        raise Exception(f"Failed to download audio from {seg['audio_path']}")
                else:
                    audio_clip = AudioFileClip(seg['audio_path'])
                audio_clips.append(audio_clip)

            final_audio = concatenate_audioclips(audio_clips)

            # Step 7: Add audio to video
            final_video = VideoFileClip(temp_video_path)
            final_video = final_video.set_audio(final_audio)

            # Step 8: Export final video with audio
            final_video_path = f"/tmp/outputs/final_video_with_audio_{job_id}.mp4"
            final_video.write_videofile(
                final_video_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None,
                fps=24
            )

            # Step 9: Upload all outputs to S3
            s3_video_url = s3_service.upload_video(final_video_path, job_id, "final_svg_video")

            # Cleanup
            final_video.close()
            final_audio.close()
            for clip in audio_clips:
                clip.close()

            # Cleanup temp files
            for path in temp_files + svg_video_paths + [temp_video_path, final_video_path]:
                if os.path.exists(path):
                    os.remove(path)

            print(f"Returning S3 video URL: {s3_video_url}")  # Debug print before return

            return {
                "final_video_url": s3_video_url
            }
        except Exception as e:
            return {"error": str(e)}

    @web_app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the main HTML page"""
        try:
            with open("/app/templates/index.html", "r") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        except Exception as e:
            return HTMLResponse(content=f"<h1>Error loading page: {str(e)}</h1>")

    @web_app.get("/scriptapi", response_class=HTMLResponse)
    async def script_api():
        """Serve the script API HTML page"""
        try:
            with open("/app/templates/scriptapi.html", "r") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        except Exception as e:
            return HTMLResponse(content=f"<h1>Error loading script API page: {str(e)}</h1>")

    @web_app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "message": "Sketch Animation API with S3 storage is running"}

    @web_app.post("/test-response")
    async def test_response():
        """Test endpoint to verify response handling"""
        return {
            "job_id": "test-123",
            "status": "completed",
            "script": "Test script",
            "video_type": "landscape",
            "sentences_count": 1,
            "images_count": 1,
            "final_video_url": "https://lisa-research.s3.ap-south-1.amazonaws.com/test/video.mp4"
        }

    @web_app.get("/list-job-files/{job_id}")
    async def list_job_files(job_id: str):
        """List all files associated with a specific job in S3"""
        try:
            from services.s3_service import S3Service
            s3_service = S3Service()
            files = s3_service.get_job_files(job_id)
            return {
                "job_id": job_id,
                "files": files
            }
        except Exception as e:
            return {"error": str(e)}

    return web_app

# Deploy the FastAPI app using Modal's ASGI support
@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("openai-api-key"),
        modal.Secret.from_name("ELEVENLABS_API_KEY"),
        modal.Secret.from_name("aws-s3-credentials")
    ],
    timeout=3600,
    memory=16384,   # 16GB RAM
    cpu=8.0,        # 8 CPUs
    allow_concurrent_inputs=10  # 10 concurrent jobs
)
@modal.asgi_app()
def fastapi_app():
    """Create and return the FastAPI application with S3 storage"""
    return create_fastapi_app()

if __name__ == "__main__":
    import uvicorn
    fastapi_app = create_fastapi_app()
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000) 