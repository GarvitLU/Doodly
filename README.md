# AI Whiteboard Animation Generator

A powerful tool that generates educational whiteboard animation videos from scripts using AI for content generation, Ideogram AI for images, ElevenLabs for text-to-speech, and Manim for smooth animations.

## 🎯 Features

- **Script-to-Video Pipeline**: Convert educational scripts into professional whiteboard animations
- **AI-Powered Content**: Intelligent script analysis and content-focused image generation
- **Multiple Image Providers**: Support for both Ideogram AI and OpenAI DALL-E
- **Orientation Support**: Generate videos in Landscape (1536x1024) or Portrait (1024x1024) formats
- **Smart Timing**: Automatic audio-animation synchronization
- **Content-First Approach**: 80% focus on educational content, 20% on visual elements
- **Multiple Voices**: Choose from various ElevenLabs voices
- **Quality Options**: Low, Medium, and High quality settings
- **S3 Integration**: Cloud storage support for generated content
- **FastAPI API**: RESTful API with web interface
- **CLI Interface**: Command-line tool for batch processing

## 🚀 Quick Start

### 1. System Dependencies

**macOS:**
```bash
brew install ffmpeg potrace imagemagick cairo pango glib pixman gobject-introspection cmake
```

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y ffmpeg potrace imagemagick libcairo2 libcairo2-dev pkg-config libpango1.0-0 libpango1.0-dev libpangocairo-1.0-0 libglib2.0-0 libglib2.0-dev libpixman-1-0 libgirepository1.0-dev python3-gi cmake build-essential libffi-dev libssl-dev
```

### 2. Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file with your API keys:
```env
# Required for Ideogram AI (recommended)
IDEOGRAM_API_KEY=your_ideogram_api_key_here

# Alternative: OpenAI DALL-E
OPENAI_API_KEY=your_openai_api_key_here

# Required for Text-to-Speech
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Optional: AWS S3 (for cloud storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your_bucket_name
```

### 4. Start the Server
```bash
python3 main.py
```

### 5. Access the Web Interface
Open your browser and go to: **http://localhost:8000/scriptapi**

## 📋 API Endpoints

### Main Endpoints

- `POST /generate-script-video` — Full pipeline: script → images/audio → animation → video
- `POST /generate-image` — Generate a single sketch image from a prompt
- `POST /animate-svg` — Animate an SVG for a given duration
- `POST /concatenate-videos` — Concatenate multiple video files
- `GET /list-svg-videos` — List all generated SVG animation videos

### Script Video Generation

**Endpoint:** `POST /generate-script-video`

**Request Body:**
```json
{
  "script": "Arrays are collections of data stored in contiguous memory locations. Each element can be accessed using its index, starting from zero. Arrays allow fast access to any element using its index.",
  "image_quality": "medium",  // "low", "medium", "high"
  "voice_id": "pNInz6obpgDQGcFmaJgB",  // ElevenLabs voice ID
  "video_type": "landscape",  // "landscape" or "portrait"
  "animation_duration": 2.5   // Optional: custom duration per frame
}
```

**Response:**
```json
{
  "final_video_url": "https://your-s3-bucket.s3.region.amazonaws.com/videos/job_id/final_video.mp4"
}
```

## 🎨 Configuration Options

### Image Quality
| Quality | Speed | Cost | Best For |
|---------|-------|------|----------|
| Low | Fastest | Lowest | Testing, quick previews |
| Medium | Balanced | Moderate | Most use cases |
| High | Slowest | Highest | Professional content |

### Video Orientations
| Type | Resolution | Aspect Ratio | Use Case |
|------|------------|--------------|----------|
| Landscape | 1536x1024 | 3:2 | Traditional videos, presentations |
| Portrait | 1024x1024 | 1:1 | Social media, mobile viewing |

### Available Voices
| Voice ID | Name | Description |
|----------|------|-------------|
| `pNInz6obpgDQGcFmaJgB` | Adam | Professional Male |
| `21m00Tcm4TlvDq8ikWAM` | Rachel | Professional Female |
| `AZnzlk1XvdvUeBnXmlld` | Domi | Casual Female |
| `EXAVITQu4vr4xnSDxMaL` | Bella | Friendly Female |

## 🔧 How It Works

### 1. Script Processing
- Intelligent sentence splitting
- Content analysis for optimal image generation
- Programming/educational concept detection

### 2. Audio Generation
- ElevenLabs text-to-speech conversion
- Per-sentence audio generation
- Duration calculation for perfect sync

### 3. Image Generation
- **Ideogram AI** (recommended): High-quality, cost-effective images
- **OpenAI DALL-E**: Alternative option
- Content-focused prompts (80% concept, 20% visual elements)
- Orientation-aware layout optimization

### 4. Animation Pipeline
- PNG to SVG conversion using ImageMagick + Potrace
- Manim-based drawing animations
- Audio-synchronized timing
- Smooth transitions and effects

### 5. Video Compilation
- Frame-by-frame audio synchronization
- Professional video output
- S3 cloud storage integration

## 🎯 Content Intelligence

The system intelligently analyzes scripts to optimize content:

### Programming Concepts
- Arrays, algorithms, data structures
- Code flow diagrams and visualizations
- **No human figures** - focuses entirely on concepts

### Educational Processes
- Step-by-step workflows
- System architectures
- Process diagrams and flowcharts

### People-Related Content
- Only includes human figures when actually needed
- Stick figure style, no detailed faces
- Minimal visual distraction

## 📁 Project Structure

```
sketchAnimation/
├── main.py                    # FastAPI server
├── cli.py                     # Command-line interface
├── doodly_pipeline.py         # SVG animation pipeline
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables
├── services/
│   ├── ideogram_image_service_s3.py  # Ideogram AI integration
│   ├── image_service.py              # OpenAI DALL-E integration
│   ├── audio_service_s3.py           # ElevenLabs TTS with S3
│   ├── script_service.py             # Script processing
│   ├── video_generator.py            # Video compilation
│   └── s3_service.py                 # Cloud storage
├── templates/
│   ├── scriptapi.html        # Web interface
│   └── index.html            # Basic interface
├── outputs/                  # Generated content
├── apiOutputs/               # API outputs
└── media/                    # Manim outputs
```

## 🚀 Deployment Options

### Local Development
```bash
python3 main.py
```

### Modal Cloud Deployment
```bash
# Deploy to Modal
modal deploy modal_app.py

# Or with S3 integration
modal deploy modal_app_s3.py
```

### Docker Deployment
```bash
docker-compose up -d
```

## 🧪 Testing

### Test the API
```bash
python3 test_script_api.py
```

### CLI Testing
```bash
python3 cli.py "How arrays work in programming"
```

## 🐛 Troubleshooting

### Common Issues

1. **Python Command Not Found**
   ```bash
   # Use python3 instead of python
   python3 main.py
   ```

2. **ImageMagick Issues**
   ```bash
   # macOS
   brew install imagemagick
   
   # Ubuntu
   sudo apt-get install imagemagick
   ```

3. **Manim Installation**
   ```bash
   pip install manim
   ```

4. **API Key Errors**
   - Verify all API keys in `.env` file
   - Check API key permissions and credits

### Performance Tips

- Use "Low" quality for testing
- Keep scripts concise (3-8 sentences work best)
- Landscape orientation processes faster than portrait
- Use S3 for production deployments

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub