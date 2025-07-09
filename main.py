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

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html") as f:
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