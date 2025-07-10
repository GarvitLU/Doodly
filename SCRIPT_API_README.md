# Script-Based Video Generation API

A new API endpoint and frontend interface for generating whiteboard animation videos directly from scripts with customizable parameters.

## 🎯 Overview

The Script API allows you to create educational whiteboard animation videos by providing:
- **Script content** - Your educational text
- **Image quality** - Low, Medium, or High quality DALL-E images
- **Voice selection** - Choose from multiple ElevenLabs voices
- **Video orientation** - Landscape (1536x1024) or Portrait (1024x1024)

## 🚀 Quick Start

### 1. Start the Server
```bash
python3 main.py
```

### 2. Access the Interface
Open your browser and go to: **http://localhost:8000/scriptapi**

### 3. Generate a Video
1. Enter your script in the text area
2. Choose your preferred settings
3. Click "Generate Video"
4. Wait for processing (2-5 minutes)
5. Download your video

## 📋 API Endpoint

### POST `/generate-script-video`

**Request Body:**
```json
{
  "script": "Your educational script here. Each sentence will become a separate image.",
  "image_quality": "medium",  // "low", "medium", "high"
  "voice_id": "pNInz6obpgDQGcFmaJgB",  // ElevenLabs voice ID
  "video_type": "landscape",  // "landscape" or "portrait"
  "animation_duration": 2.5  // (optional) duration in seconds for each image animation
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "script": "Your original script",
  "image_quality": "medium",
  "voice_id": "pNInz6obpgDQGcFmaJgB",
  "video_type": "landscape",
  "sentences_count": 5,
  "images_count": 5,
  "final_video_url": "/apiOutputs/video/final_script_video_uuid.mp4",
  "audio_path": "outputs/audio_uuid.mp3"
}
```

## 🎨 Available Voices

| Voice ID | Name | Description |
|----------|------|-------------|
| `pNInz6obpgDQGcFmaJgB` | Adam | Professional Male |
| `21m00Tcm4TlvDq8ikWAM` | Rachel | Professional Female |
| `AZnzlk1XvdvUeBnXmlld` | Domi | Casual Female |
| `EXAVITQu4vr4xnSDxMaL` | Bella | Friendly Female |

## 📐 Video Orientations

| Type | Resolution | Aspect Ratio | Use Case |
|------|------------|--------------|----------|
| Landscape | 1536x1024 | 3:2 | Traditional videos, presentations |
| Portrait | 1024x1024 | 1:1 | Social media, mobile viewing |

## 🎨 Image Quality Options

| Quality | Speed | Cost | Best For |
|---------|-------|------|----------|
| Low | Fastest | Lowest | Testing, quick previews |
| Medium | Balanced | Moderate | Most use cases |
| High | Slowest | Highest | Professional content |

## 🔧 How It Works

1. **Script Processing**: Your script is split into individual sentences
2. **Audio Generation**: ElevenLabs converts the script to natural speech
3. **Image Generation**: DALL-E creates sketch-style images for each sentence
4. **SVG Conversion**: Images are converted to vector graphics using ImageMagick + Potrace
5. **Animation**: Manim animates the SVG drawing process
6. **Video Compilation**: All animations are merged with synchronized audio

## 📝 Example Usage

### Using the Web Interface
1. Go to http://localhost:8000/scriptapi
2. Enter your script:
   ```
   An array is a collection of elements stored in contiguous memory locations. 
   Each element in an array can be accessed using its index, starting from zero. 
   Arrays allow fast access to any element using its index.
   ```
3. Select "Medium" quality, "Landscape" orientation, and "Adam" voice
4. Click "Generate Video"
5. Wait for processing and download your video

### Using the API Directly
```python
import requests

url = "http://localhost:8000/generate-script-video"
data = {
    "script": "Your educational script here.",
    "image_quality": "medium",
    "voice_id": "pNInz6obpgDQGcFmaJgB",
    "video_type": "landscape"
}

response = requests.post(url, json=data)
result = response.json()
print(f"Video URL: http://localhost:8000{result['final_video_url']}")
```

## 🧪 Testing

Run the test script to verify everything works:
```bash
python3 test_script_api.py
```

## 📁 File Structure

```
├── main.py                    # Main FastAPI server
├── templates/
│   └── scriptapi.html        # Script API frontend
├── services/
│   ├── image_service.py      # DALL-E image generation
│   ├── audio_service.py      # ElevenLabs TTS
│   ├── script_service.py     # Script processing
│   └── video_generator.py    # Video compilation
├── doodly_pipeline.py        # SVG animation pipeline
├── test_script_api.py        # API test script
└── apiOutputs/               # Generated videos and images
    └── video/                # Final video files
```

## ⚠️ Requirements

- **Python 3.8+**
- **OpenAI API Key** (for DALL-E image generation)
- **ElevenLabs API Key** (for text-to-speech)
- **FFmpeg** (for video processing)
- **ImageMagick** (for PNG to SVG conversion)
- **Potrace** (for vectorization)

## 🔧 Environment Variables

Create a `.env` file with:
```env
OPENAI_API_KEY=your_openai_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
DEFAULT_VOICE=pNInz6obpgDQGcFmaJgB
DEFAULT_IMAGE_MODEL=gpt-image-1
```

## 🎬 Output

The API generates:
- **Individual images** for each sentence (saved in `outputs/`)
- **Audio file** from the script (saved in `outputs/`)
- **Animated SVG videos** for each image (saved in `apiOutputs/`)
- **Final compiled video** with audio (saved in `apiOutputs/video/`)

## 🚀 Performance Tips

- Use "Low" quality for testing and development
- Use "Medium" quality for most production content
- Use "High" quality only for premium content
- Keep scripts concise (3-8 sentences work best)
- Landscape orientation is faster to process than portrait

## 🐛 Troubleshooting

### Common Issues

1. **Server not starting**: Check if port 8000 is available
2. **API key errors**: Verify your OpenAI and ElevenLabs API keys
3. **Video generation fails**: Ensure FFmpeg is installed
4. **SVG conversion fails**: Check ImageMagick and Potrace installation

### Error Messages

- `"OpenAI API did not return valid image data"`: Check your OpenAI API key and quota
- `"Failed to generate audio"`: Check your ElevenLabs API key
- `"No valid video clips created"`: Check if images were generated successfully

## 📞 Support

For issues or questions:
1. Check the console output for detailed error messages
2. Verify all dependencies are installed
3. Test with the provided test script
4. Check API key validity and quotas 