# Doodly-Style AI Whiteboard Animation Generator

This project generates whiteboard animation videos from scripts using AI for script, image, and audio generation, and Manim/MoviePy for animation.

## Features
- Generate educational whiteboard videos from a script or topic
- Uses GPT-4o mini for script, DALL-E for images, ElevenLabs for TTS
- SVG vectorization and Manim-based animation
- FastAPI API and CLI interface

## Installation

### 1. System Dependencies
Install the following system packages (names for Debian/Ubuntu):
```
sudo apt-get update && sudo apt-get install -y ffmpeg potrace imagemagick libcairo2 libcairo2-dev pkg-config libpango1.0-0 libpangocairo-1.0-0 libglib2.0-0 libpixman-1-0 libgirepository1.0-dev python3-gi cmake build-essential
```

### 2. Python Dependencies
Install Python packages:
```
pip install -r requirements.txt
```

## Usage

### Run FastAPI Server
```
uvicorn main:app --reload
```

### Run CLI
```
python cli.py
```

### Main API Endpoints
- `POST /generate-image` — Generate a sketch image from a prompt
- `POST /animate-svg` — Animate an SVG (from a PNG) for a given duration
- `POST /concatenate-videos` — Concatenate a list of video files
- `POST /batch-animate-and-merge` — Batch process images to SVG animations and merge
- `POST /generate-script-video` — Full pipeline: script → images/audio → SVG animation → merged video
- `GET /list-svg-videos` — List all SVG animation videos

## Modal Deployment
- See `modal_app.py` for a Modal deployment example
- All system and Python dependencies must be included in the Modal image
- Set your OpenAI and ElevenLabs API keys as Modal secrets
- Deploy with:
  ```
  modal deploy modal_app.py
  ```

## Notes
- Outputs and intermediate files are stored in the `outputs/` and `apiOutputs/` directories
- For production, consider using S3 or persistent storage for outputs

## License
MIT 