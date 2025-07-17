from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
from services.ideogram_image_service import IdeogramImageService
import subprocess
from doodly_pipeline import png_to_svg, animate_svg, concatenate_videos
import glob
from services.script_service import ScriptService
from services.audio_service import AudioService
from services.video_generator import VideoGenerator
import asyncio
from services.s3_service import S3Service

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
    animation_duration: float = None  # Optional: duration for each image animation

print('DEBUG: OPENAI_API_KEY:', os.getenv('OPENAI_API_KEY'))
print('DEBUG: IDEOGRAM_API_KEY:', os.getenv('IDEOGRAM_API_KEY'))

@app.post("/generate-image")
async def generate_image(req: GenImageRequest):
    job_id = str(uuid.uuid4())
    image_service = IdeogramImageService()
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
    Generate a complete video from script with customizable parameters and per-sentence audio sync.
    Upload the final video to S3 and return only the S3 URL.
    """
    try:
        job_id = str(uuid.uuid4())
        print(f"🎬 Starting script-based video generation for job: {job_id}")
        
        # Initialize services
        script_service = ScriptService()
        audio_service = AudioService()
        image_service = IdeogramImageService()
        video_generator = VideoGenerator(video_type=req.video_type)  # Initialize with correct orientation
        s3_service = S3Service()
        
        # Set custom voice ID
        audio_service.set_voice(req.voice_id)
        
        # Set image quality and size based on video type
        if req.video_type == "landscape":
            image_size = "1536x1024"
        else:  # portrait
            image_size = "1024x1536"  # Tall portrait (1024x1536)
        
        print(f"🎬 Video type: {req.video_type.upper()}")
        print(f"📐 Image size: {image_size}")
        print(f"🎥 Video dimensions: {video_generator.output_width}x{video_generator.output_height}")
        
        # Step 1: Split script into sentences
        print("🖼️ Step 1: Splitting script into sentences...")
        sentences = script_service.split_script_into_sentences(req.script)
        print(f"📊 Found {len(sentences)} sentences to illustrate")
        
        # Step 2: Generate audio for each sentence and get durations
        print("🎵 Step 2: Generating audio per sentence...")
        audio_segments = await audio_service.generate_audio_per_sentence(sentences, job_id)
        print(f"✅ Audio segments generated: {len(audio_segments)}")
        
        # Step 3: Generate images for each sentence
        print("🖼️ Step 3: Generating images...")
        image_paths = []
        for i, seg in enumerate(audio_segments):
            print(f"   🎨 Generating image {i+1}/{len(audio_segments)}: {seg['sentence'][:50]}...")
            image_path = image_service.generate_sketch_image_with_quality(
                seg['sentence'], job_id, i, req.image_quality, image_size
            )
            image_paths.append(image_path)
        print(f"✅ All images generated ({len(image_paths)} images)")
        
        # Step 4: Convert images to SVGs and animate them with per-sentence duration
        print("🎬 Step 4: Converting to SVGs and animating with per-sentence duration...")
        from doodly_pipeline import png_to_svg, animate_svg, concatenate_videos
        import requests
        svg_video_paths = []
        
        def download_image_if_needed(image_path, job_id, index):
            """Download image from S3 URL if needed, return local path"""
            if image_path.startswith('http'):
                # Download from S3 URL
                response = requests.get(image_path)
                if response.status_code == 200:
                    local_path = f"outputs/image_{job_id}_{index}_local.png"
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    return local_path
                else:
                    raise Exception(f"Failed to download image from {image_path}")
            else:
                # Already a local path
                return image_path
        
        for i, (image_path, seg) in enumerate(zip(image_paths, audio_segments)):
            # Download image locally if it's an S3 URL
            local_image_path = download_image_if_needed(image_path, job_id, i)
            
            svg_path = png_to_svg(local_image_path)
            out_name = f"svg_anim_{job_id}_{i}.mp4"
            
            # Use the exact audio duration for perfect synchronization
            # If animation_duration is provided, use it; otherwise use the actual audio duration
            duration = req.animation_duration if req.animation_duration is not None else seg['duration']
            
            # Ensure minimum duration for smooth animation
            if duration < 1.0:
                duration = 1.0
            
            print(f"   🎬 Animating frame {i+1}: {duration:.2f}s duration")
            video_path = animate_svg(svg_path, duration, out_name)
            new_video_path = os.path.join(API_OUTPUTS_DIR, out_name)
            os.rename(video_path, new_video_path)
            svg_video_paths.append(new_video_path)
            
            # Cleanup SVG, PBM, and temporary local image files
            try:
                if os.path.exists(svg_path):
                    os.remove(svg_path)
                pbm_path = svg_path.replace('.svg', '.pbm')
                if os.path.exists(pbm_path):
                    os.remove(pbm_path)
                # Clean up temporary local image if it was downloaded
                if local_image_path != image_path and os.path.exists(local_image_path):
                    os.remove(local_image_path)
            except Exception as e:
                print(f"Warning: Could not delete temporary files: {e}")
        
        # Step 5: Concatenate all SVG videos
        print("🎬 Step 5: Concatenating videos...")
        final_video_path = os.path.join(MERGED_VIDEO_DIR, f"script_video_{job_id}.mp4")
        concatenate_videos(svg_video_paths, final_video_path, video_type=req.video_type)
        
        # Cleanup: Delete individual SVG video files
        print("🧹 Cleaning up individual SVG video files...")
        for video_path in svg_video_paths:
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    print(f"   Deleted: {video_path}")
            except Exception as e:
                print(f"Warning: Could not delete {video_path}: {e}")
        
        # Step 6: Concatenate all audio segments
        print("🎵 Step 6: Concatenating audio segments...")
        from moviepy.editor import AudioFileClip, concatenate_audioclips, VideoFileClip
        audio_clips = [AudioFileClip(seg['audio_path']) for seg in audio_segments]
        final_audio = concatenate_audioclips(audio_clips)
        final_audio_path = os.path.join("outputs", f"final_audio_{job_id}.mp3")
        final_audio.write_audiofile(final_audio_path)
        for clip in audio_clips:
            clip.close()
        
        # Cleanup: Delete individual audio segments
        print("🧹 Cleaning up individual audio segments...")
        for seg in audio_segments:
            try:
                if os.path.exists(seg['audio_path']):
                    os.remove(seg['audio_path'])
                    print(f"   Deleted: {seg['audio_path']}")
            except Exception as e:
                print(f"Warning: Could not delete {seg['audio_path']}: {e}")
        
        # Step 7: Add audio to final video
        print("🎵 Step 7: Adding audio to final video...")
        video_clip = VideoFileClip(final_video_path)
        final_video = video_clip.set_audio(AudioFileClip(final_audio_path))
        final_output_path = os.path.join(MERGED_VIDEO_DIR, f"final_script_video_{job_id}.mp4")
        final_video.write_videofile(
            final_output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=False,
            logger=None,
            fps=24
        )
        video_clip.close()
        final_video.close()
        
        # Cleanup: Delete intermediate files
        print("🧹 Cleaning up intermediate files...")
        try:
            if os.path.exists(final_video_path):
                os.remove(final_video_path)
                print(f"   Deleted intermediate video: {final_video_path}")
            if os.path.exists(final_audio_path):
                os.remove(final_audio_path)
                print(f"   Deleted intermediate audio: {final_audio_path}")
        except Exception as e:
            print(f"Warning: Could not delete intermediate files: {e}")
        
        # Step 8: Upload final video to S3
        s3_url = s3_service.upload_video(final_output_path, job_id, "final")
        if os.path.exists(final_output_path):
            os.remove(final_output_path)
        
        print(f"🎉 Script video generation completed! S3 URL: {s3_url}")
        return {
            "final_video_url": s3_url
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