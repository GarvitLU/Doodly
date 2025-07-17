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
app = modal.App("sketch-animation-simple")

# Define a simplified Modal image without Manim
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
        "svgwrite"
    ])
    .workdir("/app")
    .env({"PYTHONPATH": "/app"})
    .add_local_file("services/script_service.py", "/app/services/script_service.py")
    .add_local_file("services/image_service.py", "/app/services/image_service.py") 
    .add_local_file("services/audio_service.py", "/app/services/audio_service.py")
    .add_local_file("services/__init__.py", "/app/services/__init__.py")
    .add_local_file("templates/index.html", "/app/templates/index.html")
    .add_local_file("templates/scriptapi.html", "/app/templates/scriptapi.html")
)

# Create a volume for persistent storage
volume = modal.Volume.from_name("sketch-animation-storage", create_if_missing=True)

# Pydantic models
class GenImageRequest(BaseModel):
    prompt: str

class ScriptVideoRequest(BaseModel):
    script: str
    image_quality: str = "medium"
    voice_id: str = "pNInz6obpgDQGcFmaJgB"
    video_type: str = "landscape"

def create_fastapi_app():
    """Create and configure the FastAPI application"""
    import sys
    sys.path.append("/app")
    
    web_app = FastAPI(title="Sketch Animation API - Simple")
    
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

    @web_app.post("/generate-simple-video")
    async def generate_simple_video(req: ScriptVideoRequest):
        """Generate a simple slideshow video from script (without SVG animation)"""
        try:
            from services.script_service import ScriptService
            from services.audio_service import AudioService
            from services.ideogram_image_service import IdeogramImageService
            from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
            
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
                audio = await audio_service.generate_audio_per_sentence([sentence], f"{job_id}_{i}")
                audio_segments.extend(audio)
            
            # Step 3: Generate images for each sentence
            image_paths = []
            for i, seg in enumerate(audio_segments):
                image_path = image_service.generate_sketch_image_with_quality(
                    seg['sentence'], job_id, i, req.image_quality, image_size
                )
                image_paths.append(image_path)
            
            # Step 4: Create simple slideshow video
            video_clips = []
            for i, (image_path, seg) in enumerate(zip(image_paths, audio_segments)):
                # Create image clip with duration matching audio
                clip = ImageClip(image_path, duration=seg['duration'])
                if req.video_type == "landscape":
                    clip = clip.resize((1536, 1024))
                else:
                    clip = clip.resize((1024, 1024))
                video_clips.append(clip)
            
            # Step 5: Concatenate video clips
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Step 6: Concatenate audio segments
            audio_clips = [AudioFileClip(seg['audio_path']) for seg in audio_segments]
            from moviepy.editor import concatenate_audioclips
            final_audio = concatenate_audioclips(audio_clips)
            
            # Step 7: Add audio to video
            final_video = final_video.set_audio(final_audio)
            
            # Step 8: Export final video
            final_output_path = f"/data/apiOutputs/video/simple_video_{job_id}.mp4"
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
            final_video.close()
            final_audio.close()
            for clip in video_clips:
                clip.close()
            for clip in audio_clips:
                clip.close()
            
            # Remove intermediate files
            for seg in audio_segments:
                if os.path.exists(seg['audio_path']):
                    os.remove(seg['audio_path'])
            
            # Commit volume changes
            volume.commit()
            
            return {
                "job_id": job_id,
                "status": "completed",
                "script": req.script,
                "video_type": req.video_type,
                "sentences_count": len(sentences),
                "images_count": len(image_paths),
                "final_video_url": f"/apiOutputs/video/simple_video_{job_id}.mp4"
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
        return {"status": "healthy", "message": "Sketch Animation API is running"}

    return web_app

# Deploy the FastAPI app using Modal's ASGI support
@app.function(
    image=image,
    volumes={"/data": volume},
    secrets=[
        modal.Secret.from_name("openai-api-key"),
        modal.Secret.from_name("ELEVENLABS_API_KEY")
    ],
    timeout=3600,
    memory=4096,
    cpu=2.0,
    allow_concurrent_inputs=5
)
@modal.asgi_app()
def fastapi_app():
    """Create and return the FastAPI application"""
    return create_fastapi_app()

if __name__ == "__main__":
    import uvicorn
    fastapi_app = create_fastapi_app()
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000) 