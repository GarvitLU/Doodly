from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
from services.image_service import ImageService
import subprocess
from doodly_pipeline import png_to_svg, animate_svg, concatenate_videos
from dotenv import load_dotenv
import glob
from services.script_service import ScriptService
from services.audio_service import AudioService
from services.video_generator import VideoGenerator
import asyncio

API_OUTPUTS_DIR = 'apiOutputs'
MERGED_VIDEO_DIR = os.path.join(API_OUTPUTS_DIR, 'video')
os.makedirs(API_OUTPUTS_DIR, exist_ok=True)
os.makedirs(MERGED_VIDEO_DIR, exist_ok=True)

app = FastAPI(title="Animated SVG Generator")
app.mount("/apiOutputs", StaticFiles(directory=API_OUTPUTS_DIR), name="apiOutputs")

class GenImageRequest(BaseModel):
    prompt: str

class AnimateSVGRequest(BaseModel):
    image_url: str
    duration: float

class ConcatVideosRequest(BaseModel):
    video_urls: list

class BatchAnimateAndMergeRequest(BaseModel):
    items: list  # Each item: {image_url: str, duration: float}

class ScriptVideoRequest(BaseModel):
    script: str
    image_quality: str = "medium"  # low, medium, high
    voice_id: str = "pNInz6obpgDQGcFmaJgB"  # Default Adam voice
    video_type: str = "landscape"  # landscape, portrait

load_dotenv()
print('DEBUG: OPENAI_API_KEY:', os.getenv('OPENAI_API_KEY'))

@app.post("/generate-image")
async def generate_image(req: GenImageRequest):
    job_id = str(uuid.uuid4())
    image_service = ImageService()
    image_path = image_service.generate_sketch_image(req.prompt, job_id, 0)
    # Move image to apiOutputs
    new_image_path = os.path.join(API_OUTPUTS_DIR, os.path.basename(image_path))
    os.rename(image_path, new_image_path)
    return {"image_url": f"/apiOutputs/{os.path.basename(new_image_path)}"}

@app.post("/animate-svg")
async def animate_svg_api(req: AnimateSVGRequest):
    image_path = req.image_url.lstrip("/")
    if not image_path.startswith(API_OUTPUTS_DIR):
        image_path = os.path.join(API_OUTPUTS_DIR, os.path.basename(image_path))
    svg_path = png_to_svg(image_path)
    out_name = f"svg_anim_{uuid.uuid4()}.mp4"
    video_path = animate_svg(svg_path, req.duration, out_name)
    new_svg_path = os.path.join(API_OUTPUTS_DIR, os.path.basename(svg_path))
    os.rename(svg_path, new_svg_path)
    new_video_path = os.path.join(API_OUTPUTS_DIR, out_name)
    os.rename(video_path, new_video_path)
    # Cleanup: delete SVG and PBM
    pbm_path = new_svg_path.replace('.svg', '.pbm')
    try:
        if os.path.exists(new_svg_path):
            os.remove(new_svg_path)
        if os.path.exists(pbm_path):
            os.remove(pbm_path)
    except Exception as e:
        print(f"Warning: Could not delete SVG/PBM: {e}")
    return {"svg_url": f"/apiOutputs/{os.path.basename(new_svg_path)}", "video_url": f"/apiOutputs/{os.path.basename(new_video_path)}"}

@app.post("/concatenate-videos")
async def concatenate_videos_api(req: ConcatVideosRequest):
    video_paths = [v.lstrip("/") for v in req.video_urls]
    output_path = os.path.join(MERGED_VIDEO_DIR, f"final_video_{uuid.uuid4()}.mp4")
    concatenate_videos(video_paths, output_path)
    return {"final_video_url": f"/apiOutputs/video/{os.path.basename(output_path)}"}

@app.post("/batch-animate-and-merge")
async def batch_animate_and_merge(req: BatchAnimateAndMergeRequest):
    svg_urls = []
    video_urls = []
    for item in req.items:
        image_path = item['image_url'].lstrip("/")
        if not image_path.startswith(API_OUTPUTS_DIR):
            image_path = os.path.join(API_OUTPUTS_DIR, os.path.basename(image_path))
        duration = item['duration']
        svg_path = png_to_svg(image_path)
        new_svg_path = os.path.join(API_OUTPUTS_DIR, os.path.basename(svg_path))
        os.rename(svg_path, new_svg_path)
        svg_urls.append(f"/apiOutputs/{os.path.basename(new_svg_path)}")
        out_name = f"svg_anim_{uuid.uuid4()}.mp4"
        video_path = animate_svg(new_svg_path, duration, out_name)
        new_video_path = os.path.join(API_OUTPUTS_DIR, out_name)
        os.rename(video_path, new_video_path)
        video_urls.append(f"/apiOutputs/{os.path.basename(new_video_path)}")
        # Cleanup: delete SVG and PBM
        pbm_path = new_svg_path.replace('.svg', '.pbm')
        try:
            if os.path.exists(new_svg_path):
                os.remove(new_svg_path)
            if os.path.exists(pbm_path):
                os.remove(pbm_path)
        except Exception as e:
            print(f"Warning: Could not delete SVG/PBM: {e}")
    # Merge all videos
    video_paths = [v.lstrip("/") for v in video_urls]
    output_path = os.path.join(MERGED_VIDEO_DIR, f"final_video_{uuid.uuid4()}.mp4")
    concatenate_videos(video_paths, output_path)
    return {
        "svg_urls": svg_urls,
        "video_urls": video_urls,
        "final_video_url": f"/apiOutputs/video/{os.path.basename(output_path)}"
    }

@app.post("/generate-script-video")
async def generate_script_video(req: ScriptVideoRequest):
    """
    Generate a complete video from script with customizable parameters
    """
    try:
        job_id = str(uuid.uuid4())
        print(f"🎬 Starting script-based video generation for job: {job_id}")
        
        # Initialize services
        script_service = ScriptService()
        audio_service = AudioService()
        image_service = ImageService()
        video_generator = VideoGenerator()
        
        # Set custom voice ID
        audio_service.set_voice(req.voice_id)
        
        # Set image quality and size based on video type
        if req.video_type == "landscape":
            image_size = "1536x1024"
            video_generator.output_width = 1536
            video_generator.output_height = 1024
        else:  # portrait
            image_size = "1024x1024"
            video_generator.output_width = 1024
            video_generator.output_height = 1024
        
        # Step 1: Generate audio from script
        print("🎵 Step 1: Generating audio...")
        audio_path = await audio_service.generate_audio(req.script, job_id)
        print(f"✅ Audio generated: {audio_path}")
        
        # Step 2: Split script into sentences and generate images
        print("🖼️ Step 2: Generating images...")
        sentences = script_service.split_script_into_sentences(req.script)
        print(f"📊 Found {len(sentences)} sentences to illustrate")
        
        image_paths = []
        for i, sentence in enumerate(sentences):
            print(f"   🎨 Generating image {i+1}/{len(sentences)}: {sentence[:50]}...")
            # Generate image with custom quality
            image_path = image_service.generate_sketch_image_with_quality(
                sentence, job_id, i, req.image_quality, image_size
            )
            image_paths.append(image_path)
        
        print(f"✅ All images generated ({len(image_paths)} images)")
        
        # Step 3: Convert images to SVGs and animate them
        print("🎬 Step 3: Converting to SVGs and animating...")
        svg_video_paths = []
        for i, image_path in enumerate(image_paths):
            # Convert PNG to SVG
            svg_path = png_to_svg(image_path)
            
            # Animate SVG
            out_name = f"svg_anim_{job_id}_{i}.mp4"
            video_path = animate_svg(svg_path, 3.0, out_name)  # 3 seconds per frame
            
            # Move to apiOutputs
            new_video_path = os.path.join(API_OUTPUTS_DIR, out_name)
            os.rename(video_path, new_video_path)
            svg_video_paths.append(new_video_path)
            
            # Cleanup SVG and PBM files
            try:
                if os.path.exists(svg_path):
                    os.remove(svg_path)
                pbm_path = svg_path.replace('.svg', '.pbm')
                if os.path.exists(pbm_path):
                    os.remove(pbm_path)
            except Exception as e:
                print(f"Warning: Could not delete SVG/PBM: {e}")
        
        # Step 4: Concatenate all SVG videos
        print("🎬 Step 4: Concatenating videos...")
        final_video_path = os.path.join(MERGED_VIDEO_DIR, f"script_video_{job_id}.mp4")
        concatenate_videos(svg_video_paths, final_video_path)
        
        # Step 5: Add audio to final video
        print("🎵 Step 5: Adding audio to final video...")
        from moviepy.editor import VideoFileClip, AudioFileClip
        video_clip = VideoFileClip(final_video_path)
        audio_clip = AudioFileClip(audio_path)
        
        # Match video duration to audio duration
        if video_clip.duration < audio_clip.duration:
            # Loop video if it's shorter than audio
            loops_needed = int(audio_clip.duration / video_clip.duration) + 1
            video_clip = video_clip.loop(loops_needed)
        
        # Trim video to match audio duration
        final_video = video_clip.subclip(0, audio_clip.duration)
        final_video = final_video.set_audio(audio_clip)
        
        # Save final video with audio
        final_output_path = os.path.join(MERGED_VIDEO_DIR, f"final_script_video_{job_id}.mp4")
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
        audio_clip.close()
        final_video.close()
        
        print(f"🎉 Script video generation completed!")
        return {
            "job_id": job_id,
            "status": "completed",
            "script": req.script,
            "image_quality": req.image_quality,
            "voice_id": req.voice_id,
            "video_type": req.video_type,
            "sentences_count": len(sentences),
            "images_count": len(image_paths),
            "final_video_url": f"/apiOutputs/video/{os.path.basename(final_output_path)}",
            "audio_path": audio_path
        }
        
    except Exception as e:
        print(f"❌ Error during script video generation: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html") as f:
        return f.read()

@app.get("/scriptapi", response_class=HTMLResponse)
async def script_api():
    with open("templates/scriptapi.html") as f:
        return f.read()

@app.get("/list-svg-videos")
async def list_svg_videos():
    # Find all svg_anim_*.mp4 in apiOutputs/ (not in apiOutputs/video/)
    pattern = os.path.join(API_OUTPUTS_DIR, "svg_anim_*.mp4")
    video_files = glob.glob(pattern)
    # Sort by creation time (oldest first)
    video_files.sort(key=lambda x: os.path.getctime(x))
    # Return as URLs
    urls = [f"/apiOutputs/{os.path.basename(f)}" for f in video_files]
    return {"video_urls": urls}

if __name__ == "__main__":
    import uvicorn
    os.makedirs("outputs", exist_ok=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 