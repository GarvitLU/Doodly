# 🚀 Quick Start Guide

Get your whiteboard animation video generator up and running in minutes!

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- ElevenLabs API key

## 🎯 One-Command Setup

```bash
# Run the deployment script
./deploy.sh
```

This script will:
- ✅ Check Python and FFmpeg installation
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up configuration files
- ✅ Guide you through API key setup

## 🔑 Get Your API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Create a new API key
4. Add it to your `.env` file

### ElevenLabs API Key
1. Go to [ElevenLabs](https://elevenlabs.io/speech-synthesis)
2. Sign up for a free account
3. Go to your profile settings
4. Copy your API key
5. Add it to your `.env` file

## 🎬 Generate Your First Video

### Option 1: Web Interface (Recommended)
```bash
# Start the server
python main.py

# Open your browser to:
# http://localhost:8000
```

### Option 2: Command Line
```bash
# Generate a simple video
python cli.py "How photosynthesis works"

# Generate with custom options
python cli.py "Machine learning basics" --style technical --duration 4.0
```

### Option 3: API
```bash
# Start the server
python main.py

# In another terminal, generate video
curl -X POST "http://localhost:8000/generate-video" \
  -H "Content-Type: application/json" \
  -d '{"topic": "How photosynthesis works"}'
```

## 🧪 Test the System

```bash
# Run the test script
python test_generation.py
```

## 📁 Project Structure

```
whiteboard-animation-generator/
├── main.py                 # 🚀 Start here - FastAPI server
├── cli.py                  # 💻 Command line interface
├── test_generation.py      # 🧪 Test script
├── deploy.sh              # ⚡ One-command setup
├── requirements.txt       # 📦 Python dependencies
├── env.example           # 🔧 Configuration template
├── services/             # 🔧 Core services
│   ├── script_service.py  # 📝 GPT-4 script generation
│   ├── audio_service.py   # 🎵 ElevenLabs TTS
│   ├── image_service.py   # 🖼️ DALL-E 2 image generation
│   └── video_generator.py # 🎬 MoviePy video compilation
├── templates/            # 🌐 Web interface
│   └── index.html        # 📱 User interface
└── outputs/              # 📁 Generated files
    ├── audio_*.mp3       # 🎵 Generated audio
    ├── image_*.png       # 🖼️ Generated images
    └── video_*.mp4       # 🎬 Final videos
```

## 🎨 Video Styles

- **educational**: Academic, classroom-style explanations
- **technical**: Professional, technical documentation
- **business**: Corporate, presentation style
- **creative**: Artistic, storytelling approach

## ⚙️ Configuration

Edit `.env` file to customize:

```env
# Video settings
DEFAULT_VIDEO_WIDTH=1920
DEFAULT_VIDEO_HEIGHT=1080
DEFAULT_FPS=30
DEFAULT_DURATION_PER_FRAME=3.0

# Audio settings
DEFAULT_VOICE=pNInz6obpgDQGcFmaJgB  # Adam voice
DEFAULT_AUDIO_MODEL=eleven_monolingual_v1
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker
docker-compose up --build

# Or build manually
docker build -t whiteboard-generator .
docker run -p 8000:8000 whiteboard-generator
```

## 🆘 Troubleshooting

### Common Issues

1. **"FFmpeg not found"**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu
   sudo apt install ffmpeg
   ```

2. **"API key errors"**
   - Check your `.env` file
   - Verify API keys are correct
   - Check API quotas

3. **"Video generation fails"**
   - Ensure enough disk space
   - Check all dependencies installed
   - Run test script: `python test_generation.py`

### Get Help

- 📖 Read the full [README.md](README.md)
- 🧪 Run tests: `python test_generation.py`
- 🔍 Check logs in terminal output
- 📧 Create an issue on GitHub

## 🎯 Next Steps

1. ✅ Generate your first video
2. 🎨 Experiment with different styles
3. 🔧 Customize voice and settings
4. 🚀 Deploy to production
5. 📈 Scale for multiple users

## 💡 Pro Tips

- Start with simple topics for testing
- Use educational style for best results
- Keep topics under 2-3 minutes for optimal quality
- Monitor API usage to avoid rate limits
- Use Docker for consistent deployment

---

**Happy video generating! 🎬✨** 