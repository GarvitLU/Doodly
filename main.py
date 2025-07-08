from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import os
from dotenv import load_dotenv
from services.video_generator import VideoGenerator
from services.script_service import ScriptService
from services.audio_service import AudioService
from services.image_service import ImageService
import uuid
import asyncio

load_dotenv()

app = FastAPI(
    title="Whiteboard Animation Video Generator",
    description="AI-powered whiteboard sketch video generation system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
script_service = ScriptService()
audio_service = AudioService()
image_service = ImageService()
video_generator = VideoGenerator()

# Setup templates
templates = Jinja2Templates(directory="templates")

class VideoRequest(BaseModel):
    topic: str
    style: str = "educational"
    duration_per_frame: float = 3.0
    include_background_music: bool = False
    include_hand_animation: bool = False

class VideoResponse(BaseModel):
    job_id: str
    status: str
    message: str

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-video", response_model=VideoResponse)
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Generate a whiteboard animation video from a topic"""
    try:
        job_id = str(uuid.uuid4())
        
        # Add the video generation task to background tasks
        background_tasks.add_task(
            process_video_generation,
            job_id,
            request.topic,
            request.style,
            request.duration_per_frame,
            request.include_background_music,
            request.include_hand_animation
        )
        
        return VideoResponse(
            job_id=job_id,
            status="processing",
            message="Video generation started. Use the job_id to check status."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video-status/{job_id}")
async def get_video_status(job_id: str):
    """Get the status of a video generation job"""
    try:
        # Check if video file exists
        video_path = f"outputs/video_{job_id}.mp4"
        if os.path.exists(video_path):
            return {
                "job_id": job_id,
                "status": "completed",
                "video_url": f"/download-video/{job_id}"
            }
        else:
            return {
                "job_id": job_id,
                "status": "processing",
                "message": "Video is still being generated"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download-video/{job_id}")
async def download_video(job_id: str):
    """Download the generated video"""
    try:
        video_path = f"outputs/video_{job_id}.mp4"
        if os.path.exists(video_path):
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename=f"whiteboard_video_{job_id}.mp4"
            )
        else:
            raise HTTPException(status_code=404, detail="Video not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_video_generation(
    job_id: str,
    topic: str,
    style: str,
    duration_per_frame: float,
    include_background_music: bool,
    include_hand_animation: bool
):
    """Background task to generate the video"""
    try:
        print(f"Starting video generation for job {job_id}")
        
        # Step 1: Generate script
        print("Generating script...")
        script = script_service.generate_script(topic, style)
        
        # Step 2: Generate audio
        print("Generating audio...")
        print(f"[AudioService] Using voice ID: {audio_service.default_voice}")
        audio_path = await audio_service.generate_audio(script, job_id)
        
        # Step 3: Generate images for each sentence
        print("Generating images...")
        sentences = script_service.split_script_into_sentences(script)
        image_paths = []
        
        for i, sentence in enumerate(sentences):
            image_path = image_service.generate_sketch_image(sentence, job_id, i)
            image_paths.append(image_path)
        
        # Step 4: Generate video
        print("Generating video...")
        video_path = await video_generator.create_video(
            audio_path=audio_path,
            image_paths=image_paths,
            job_id=job_id,
            duration_per_frame=duration_per_frame,
            include_background_music=include_background_music,
            include_hand_animation=include_hand_animation
        )
        
        print(f"Video generation completed for job {job_id}")
        
    except Exception as e:
        print(f"Error in video generation for job {job_id}: {str(e)}")

if __name__ == "__main__":
    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 