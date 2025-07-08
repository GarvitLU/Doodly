# Whiteboard Animation Video Generator

An AI-powered Python tool that automatically creates sketch-style whiteboard animation videos from topics or scripts using OpenAI GPT-4, ElevenLabs Text-to-Speech, and DALL-E image generation.

## 🎬 Features

- **AI Script Generation**: Uses GPT-4 to expand topics into educational scripts
- **Text-to-Speech**: Converts scripts to natural voiceovers using ElevenLabs
- **AI Image Generation**: Creates whiteboard sketch-style illustrations using DALL-E
- **Video Compilation**: Combines audio and images into professional videos using MoviePy
- **Multiple Styles**: Support for educational, technical, business, and creative styles
- **CLI & API**: Use as command-line tool or web API
- **Background Processing**: Asynchronous video generation with job tracking

## 🛠 Tech Stack

- **Python 3.8+**
- **FastAPI** - Web API framework
- **OpenAI GPT-4** - Script generation
- **ElevenLabs** - Text-to-speech
- **DALL-E 2 (gpt-image-1)** - Image generation
- **MoviePy** - Video editing and compilation
- **Pillow** - Image processing

## 📋 Prerequisites

- Python 3.8 or higher
- OpenAI API key
- ElevenLabs API key
- FFmpeg (for video processing)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd whiteboard-animation-generator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg** (required for video processing)
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```
   
   **Windows:**
   Download from [FFmpeg official website](https://ffmpeg.org/download.html)

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
   ```

## 🎯 Usage

### Command Line Interface

Generate a video from a topic:
```bash
python cli.py "How photosynthesis works"
```

With custom options:
```bash
python cli.py "Machine learning basics" \
  --style technical \
  --duration 4.0 \
  --background-music \
  --hand-animation \
  --output my_video
```

List available voices:
```bash
python cli.py --list-voices
```

### Web API

1. **Start the server**
   ```bash
   python main.py
   ```

2. **Generate a video**
   ```bash
   curl -X POST "http://localhost:8000/generate-video" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "How photosynthesis works",
       "style": "educational",
       "duration_per_frame": 3.0,
       "include_background_music": false,
       "include_hand_animation": false
     }'
   ```

3. **Check video status**
   ```bash
   curl "http://localhost:8000/video-status/{job_id}"
   ```

4. **Download the video**
   ```bash
   curl "http://localhost:8000/download-video/{job_id}" --output video.mp4
   ```

## 📚 API Documentation

### Endpoints

#### `POST /generate-video`
Generate a whiteboard animation video.

**Request Body:**
```json
{
  "topic": "string",
  "style": "educational|technical|business|creative",
  "duration_per_frame": 3.0,
  "include_background_music": false,
  "include_hand_animation": false
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "processing",
  "message": "Video generation started. Use the job_id to check status."
}
```

#### `GET /video-status/{job_id}`
Check the status of a video generation job.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "completed|processing",
  "video_url": "/download-video/{job_id}"
}
```

#### `GET /download-video/{job_id}`
Download the generated video file.

## 🎨 Customization

### Video Styles

- **educational**: Academic, classroom-style explanations
- **technical**: Professional, technical documentation style
- **business**: Corporate, presentation style
- **creative**: Artistic, storytelling style

### Voice Options

List available voices and their IDs:
```bash
python cli.py --list-voices
```

Change default voice in `.env`:
```env
DEFAULT_VOICE=pNInz6obpgDQGcFmaJgB  # Adam voice
```

### Image Generation

The system automatically creates whiteboard sketch-style images for each sentence in the script using DALL-E 2 (gpt-image-1). Images are generated with prompts optimized for educational illustrations and whiteboard sketch style.

### Video Effects

- **Ken Burns Effect**: Subtle zoom and pan animations
- **Fade Transitions**: Smooth transitions between images
- **Background Music**: Optional royalty-free background music
- **Hand Animation**: Optional animated hand overlay (placeholder)

## 📁 Project Structure

```
whiteboard-animation-generator/
├── main.py                 # FastAPI application
├── cli.py                  # Command-line interface
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
├── README.md              # This file
├── services/              # Core services
│   ├── __init__.py
│   ├── script_service.py  # GPT-4 script generation
│   ├── audio_service.py   # ElevenLabs TTS
│   ├── image_service.py   # DALL-E image generation
│   └── video_generator.py # MoviePy video compilation
└── outputs/               # Generated files
    ├── audio_*.mp3        # Generated audio files
    ├── image_*.png        # Generated images
    └── video_*.mp4        # Final videos
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | Required |
| `DEFAULT_VIDEO_WIDTH` | Video width in pixels | 1920 |
| `DEFAULT_VIDEO_HEIGHT` | Video height in pixels | 1080 |
| `DEFAULT_FPS` | Video frame rate | 30 |
| `DEFAULT_DURATION_PER_FRAME` | Seconds per image | 3.0 |
| `DEFAULT_VOICE` | ElevenLabs voice ID | pNInz6obpgDQGcFmaJgB (Adam) |
| `DEFAULT_AUDIO_MODEL` | ElevenLabs model | eleven_monolingual_v1 |

### Video Settings

- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 FPS
- **Format**: MP4 (H.264)
- **Audio**: AAC codec

## 🚀 Deployment

### Local Development
```bash
python main.py
```

### Production Deployment

1. **Using Docker** (recommended):
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   RUN apt-get update && apt-get install -y ffmpeg
   
   EXPOSE 8000
   CMD ["python", "main.py"]
   ```

2. **Using Gunicorn**:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

## 🐛 Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Install FFmpeg: `brew install ffmpeg` (macOS) or `sudo apt install ffmpeg` (Ubuntu)

2. **API key errors**
   - Verify your API keys are correctly set in `.env`
   - Check API key permissions and quotas

3. **Memory issues**
   - Reduce video resolution in `.env`
   - Process fewer images simultaneously

4. **Video generation fails**
   - Check available disk space
   - Verify all dependencies are installed
   - Check API rate limits

### Debug Mode

Enable debug logging:
```env
DEBUG=True
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review API documentation

## 🎯 Roadmap

- [ ] YouTube upload automation
- [ ] Subtitle generation
- [ ] Multiple language support
- [ ] Custom hand animation assets
- [ ] Background music library
- [ ] Video templates
- [ ] Batch processing
- [ ] Web interface 