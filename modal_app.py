import modal
import os
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import asyncio

# Create Modal app
app = modal.App("sketch-animation")

# Define the Modal image with all dependencies
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
        "libpango1.0-dev",
        "libpangocairo-1.0-0", 
        "libglib2.0-0", 
        "libglib2.0-dev",
        "libpixman-1-0", 
        "libgirepository1.0-dev", 
        "python3-gi", 
        "cmake", 
        "build-essential",
        "libffi-dev",
        "libssl-dev",
        "wget",
        "curl",
        "git",
        "gobject-introspection"
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
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "jinja2==3.1.2",
        "manim",
        "svgpathtools",
        "numpy",
        "opencv-python",
        "svgwrite",
        "whisper-openai"
    ])
    .add_local_file("main.py", "/app/main.py")
    .add_local_file("doodly_pipeline.py", "/app/doodly_pipeline.py")
    .add_local_file("cli.py", "/app/cli.py")
    .add_local_dir("services", "/app/services")
    .add_local_dir("templates", "/app/templates")
    .workdir("/app")
    .env({"PYTHONPATH": "/app"})
)

# Create a volume for persistent storage
volume = modal.Volume.from_name("sketch-animation-storage", create_if_missing=True)

# Pydantic models for API requests
class GenImageRequest(BaseModel):
    prompt: str

class AnimateSVGRequest(BaseModel):
    image_url: str
    duration: float

class ConcatVideosRequest(BaseModel):
    video_urls: List[str]

class BatchAnimateAndMergeRequest(BaseModel):
    items: List[dict]  # Each item: {image_url: str, duration: float}

class ScriptVideoRequest(BaseModel):
    script: str
    image_quality: str = "medium"  # low, medium, high
    voice_id: str = "pNInz6obpgDQGcFmaJgB"  # Default Adam voice
    video_type: str = "landscape"  # landscape, portrait
    animation_duration: Optional[float] = None  # Optional: duration for each image animation

# Create FastAPI app instance
def create_fastapi_app():
    """Create and configure the FastAPI application"""
    import sys
    sys.path.append("/app")
    
    web_app = FastAPI(title="Sketch Animation API")
    
    # Set up directories
    os.makedirs("/data/apiOutputs", exist_ok=True)
    os.makedirs("/data/apiOutputs/video", exist_ok=True)
    os.makedirs("/data/outputs", exist_ok=True)
    
    # Set environment variables
    os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "")
    os.environ["ELEVENLABS_API_KEY"] = os.environ.get("ELEVENLABS_API_KEY", "")
    
    # Mount static files
    web_app.mount("/apiOutputs", StaticFiles(directory="/data/apiOutputs"), name="apiOutputs")
    
    @web_app.post("/generate-image")
    async def generate_image(req: GenImageRequest):
        """Generate a sketch image from a prompt"""
        try:
            from services.ideogram_image_service import IdeogramImageService
            
            job_id = str(uuid.uuid4())
            image_service = IdeogramImageService()
            
            image_path = image_service.generate_sketch_image(req.prompt, job_id, 0)
            # Move image to apiOutputs in volume
            new_image_path = f"/data/apiOutputs/{os.path.basename(image_path)}"
            os.rename(image_path, new_image_path)
            
            # Commit volume changes
            volume.commit()
            
            return {"image_url": f"/apiOutputs/{os.path.basename(new_image_path)}"}
        except Exception as e:
            return {"error": str(e)}

    @web_app.post("/animate-svg")
    async def animate_svg_endpoint(req: AnimateSVGRequest):
        """Animate an SVG from an image"""
        try:
            from doodly_pipeline import png_to_svg, animate_svg
            
            image_path = req.image_url.lstrip("/")
            if not image_path.startswith("/data/apiOutputs"):
                image_path = f"/data/apiOutputs/{os.path.basename(image_path)}"
            
            svg_path = png_to_svg(image_path)
            out_name = f"svg_anim_{uuid.uuid4()}.mp4"
            video_path = animate_svg(svg_path, req.duration, out_name)
            
            # Move files to volume
            new_svg_path = f"/data/apiOutputs/{os.path.basename(svg_path)}"
            new_video_path = f"/data/apiOutputs/{out_name}"
            os.rename(svg_path, new_svg_path)
            os.rename(video_path, new_video_path)
            
            # Cleanup
            pbm_path = new_svg_path.replace('.svg', '.pbm')
            for cleanup_file in [new_svg_path, pbm_path]:
                if os.path.exists(cleanup_file):
                    os.remove(cleanup_file)
            
            volume.commit()
            
            return {
                "svg_url": f"/apiOutputs/{os.path.basename(new_svg_path)}", 
                "video_url": f"/apiOutputs/{out_name}"
            }
        except Exception as e:
            return {"error": str(e)}

    @web_app.post("/generate-script-video")
    async def generate_script_video(req: ScriptVideoRequest):
        """Generate a complete video from script"""
        try:
            from services.script_service import ScriptService
            from services.audio_service import AudioService
            from services.ideogram_image_service import IdeogramImageService
            from doodly_pipeline import png_to_svg, animate_svg, concatenate_videos
            from moviepy.editor import AudioFileClip, concatenate_audioclips, VideoFileClip
            
            job_id = str(uuid.uuid4())
            
            # Initialize services
            script_service = ScriptService()
            audio_service = AudioService()
            image_service = IdeogramImageService()
            
            # Set custom voice ID
            audio_service.set_voice(req.voice_id)
            
            # Set image quality and size based on video type
            if req.video_type == "landscape":
                image_size = "1536x1024"
            else:  # portrait
                image_size = "1024x1024"
            
            # Step 1: Split script into sentences
            sentences = script_service.split_script_into_sentences(req.script)
            
            # Step 2: Generate audio for each sentence
            audio_segments = []
            for i, sentence in enumerate(sentences):
                audio = await audio_service.generate_audio_per_sentence([sentence], f"{job_id}_{i}")
                audio_segments.extend(audio)
            
            # Step 3: Generate images for each sentence
            image_paths = []
            for i, seg in enumerate(audio_segments):
                image_path = image_service.generate_sketch_image_with_quality(
                    seg['sentence'], job_id, i, req.image_quality, image_size
                )
                image_paths.append(image_path)
            
            # Step 4: Convert images to SVGs and animate them
            svg_video_paths = []
            for i, (image_path, seg) in enumerate(zip(image_paths, audio_segments)):
                svg_path = png_to_svg(image_path)
                out_name = f"svg_anim_{job_id}_{i}.mp4"
                duration = req.animation_duration if req.animation_duration is not None else seg['duration']
                video_path = animate_svg(svg_path, duration, out_name)
                
                new_video_path = f"/data/apiOutputs/{out_name}"
                os.rename(video_path, new_video_path)
                svg_video_paths.append(new_video_path)
                
                # Cleanup
                for cleanup_file in [svg_path, svg_path.replace('.svg', '.pbm')]:
                    if os.path.exists(cleanup_file):
                        os.remove(cleanup_file)
            
            # Step 5: Concatenate all SVG videos
            final_video_path = f"/data/apiOutputs/video/script_video_{job_id}.mp4"
            concatenate_videos(svg_video_paths, final_video_path)
            
            # Step 6: Concatenate all audio segments
            audio_clips = [AudioFileClip(seg['audio_path']) for seg in audio_segments]
            final_audio = concatenate_audioclips(audio_clips)
            final_audio_path = f"/data/outputs/final_audio_{job_id}.mp3"
            final_audio.write_audiofile(final_audio_path)
            
            # Step 7: Add audio to final video
            video_clip = VideoFileClip(final_video_path)
            final_video = video_clip.set_audio(AudioFileClip(final_audio_path))
            final_output_path = f"/data/apiOutputs/video/final_script_video_{job_id}.mp4"
            final_video.write_videofile(
                final_output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Cleanup
            video_clip.close()
            final_video.close()
            for clip in audio_clips:
                clip.close()
            final_audio.close()
            
            # Remove intermediate files
            for video_path in svg_video_paths:
                if os.path.exists(video_path):
                    os.remove(video_path)
            
            for seg in audio_segments:
                if os.path.exists(seg['audio_path']):
                    os.remove(seg['audio_path'])
            
            # Commit volume changes
            volume.commit()
            
            return {
                "final_video_url": f"/apiOutputs/video/final_script_video_{job_id}.mp4"
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

    @web_app.post("/concatenate-videos")
    async def concatenate_videos_endpoint(req: ConcatVideosRequest):
        """Concatenate multiple videos"""
        try:
            from doodly_pipeline import concatenate_videos
            
            video_paths = [f"/data/{v.lstrip('/')}" for v in req.video_urls]
            output_path = f"/data/apiOutputs/video/final_video_{uuid.uuid4()}.mp4"
            
            concatenate_videos(video_paths, output_path)
            volume.commit()
            
            return {"final_video_url": f"/apiOutputs/video/{os.path.basename(output_path)}"}
        except Exception as e:
            return {"error": str(e)}

    @web_app.get("/list-svg-videos")
    async def list_svg_videos():
        """List all SVG animation videos"""
        try:
            import glob
            video_files = glob.glob("/data/apiOutputs/svg_anim_*.mp4")
            video_urls = [f"/apiOutputs/{os.path.basename(f)}" for f in video_files]
            
            return {"video_urls": video_urls}
        except Exception as e:
            return {"error": str(e)}

    return web_app

# Deploy the FastAPI app using Modal's ASGI support
@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=[
        modal.Secret.from_name("openai-api-key"),
        modal.Secret.from_name("ELEVENLABS_API_KEY")
    ],
    timeout=3600,  # 1 hour timeout
    memory=8192,   # 8GB memory
    cpu=4.0,       # 4 CPU cores
    allow_concurrent_inputs=10
)
@modal.asgi_app()
def fastapi_app():
    """Create and return the FastAPI application"""
    return create_fastapi_app()

# Local development entry point
if __name__ == "__main__":
    import uvicorn
    fastapi_app = create_fastapi_app()
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000) 