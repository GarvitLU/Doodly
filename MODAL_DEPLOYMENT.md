# Modal Deployment Guide for Sketch Animation

This guide will help you deploy your sketch animation project to Modal Labs.

## Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Modal CLI**: Install the Modal CLI tool
3. **API Keys**: OpenAI API key and ElevenLabs API key

## Installation

### 1. Install Modal CLI

```bash
pip install modal
```

### 2. Setup Modal Authentication

```bash
modal token new
```

Follow the prompts to authenticate with your Modal account.

## Configuration

### 1. Create Modal Secrets

You need to create two secrets in Modal for your API keys:

#### OpenAI API Key
```bash
modal secret create openai-api-key OPENAI_API_KEY=your_openai_api_key_here
```

#### ElevenLabs API Key
```bash
modal secret create elevenlabs-api-key ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 2. Verify Secrets

```bash
modal secret list
```

You should see both `openai-api-key` and `elevenlabs-api-key` in the list.

## Deployment

### 1. Deploy the Application

```bash
modal deploy modal_app.py
```

This will:
- Build the Docker image with all dependencies
- Upload your source code
- Create the Modal volume for persistent storage
- Deploy all the API endpoints

### 2. Get the Deployment URL

After deployment, Modal will provide you with a URL like:
```
https://your-username--sketch-animation-root.modal.run
```

## API Endpoints

Once deployed, your application will have the following endpoints:

### Web Interface
- `GET /` - Main web interface
- `GET /scriptapi` - Script API interface

### API Endpoints
- `POST /generate-image` - Generate a sketch image
- `POST /animate-svg` - Animate an SVG from an image
- `POST /generate-script-video` - Generate complete video from script
- `POST /concatenate-videos` - Concatenate multiple videos
- `GET /list-svg-videos` - List all SVG animation videos
- `GET /apiOutputs/{file_path}` - Serve generated files

## Usage Examples

### 1. Generate a Script Video

```bash
curl -X POST "https://your-deployment-url/generate-script-video" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "An array is a collection of elements. Each element has an index. Arrays allow fast access to elements.",
    "image_quality": "medium",
    "voice_id": "pNInz6obpgDQGcFmaJgB",
    "video_type": "landscape"
  }'
```

### 2. Generate a Single Image

```bash
curl -X POST "https://your-deployment-url/generate-image" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A whiteboard sketch of an array data structure"
  }'
```

## Configuration Options

### Image Quality
- `"low"` - Fast generation, lower quality (512x512)
- `"medium"` - Balanced quality and speed (1024x1024 or 1536x1024)
- `"high"` - Best quality, slower generation (1536x1024)

### Video Types
- `"landscape"` - 1536x1024 resolution
- `"portrait"` - 1024x1024 resolution

### Voice Options
- `"pNInz6obpgDQGcFmaJgB"` - Adam (Professional Male)
- `"21m00Tcm4TlvDq8ikWAM"` - Rachel (Professional Female)
- `"AZnzlk1XvdvUeBnXmlld"` - Domi (Casual Female)
- `"EXAVITQu4vr4xnSDxMaL"` - Bella (Friendly Female)

## System Resources

The deployment is configured with:
- **CPU**: 2-4 cores depending on the endpoint
- **Memory**: 4-8GB depending on the endpoint
- **Timeout**: 1 hour for video generation
- **Storage**: Persistent volume for outputs

## Monitoring and Logs

### View Logs
```bash
modal logs sketch-animation
```

### Monitor Function Usage
```bash
modal stats sketch-animation
```

## Troubleshooting

### Common Issues

1. **Secret Not Found**
   - Verify secrets are created: `modal secret list`
   - Check secret names match exactly: `openai-api-key` and `elevenlabs-api-key`

2. **API Key Errors**
   - Verify your OpenAI API key has sufficient credits
   - Check ElevenLabs API key is valid and has available characters

3. **Memory Issues**
   - Video generation is memory-intensive
   - Consider using lower image quality for testing

4. **Timeout Issues**
   - Large scripts may take longer to process
   - Consider breaking long scripts into smaller segments

### Debug Mode

To enable debug logging, modify the Modal function decorators to include:
```python
@app.function(
    # ... existing parameters ...
    environment={"DEBUG": "1"}
)
```

## Cost Optimization

1. **Use appropriate image quality**:
   - Use "low" for testing
   - Use "medium" for most production content
   - Use "high" only when necessary

2. **Monitor API usage**:
   - OpenAI charges per image generated
   - ElevenLabs charges per character spoken

3. **Clean up old files**:
   - The volume persists files between runs
   - Consider implementing cleanup logic for old outputs

## Scaling

Modal automatically scales based on demand:
- Functions spin up when requests come in
- Resources are allocated dynamically
- No need to manage infrastructure

## Security

- API keys are securely stored in Modal secrets
- No secrets are exposed in logs or code
- HTTPS is enforced for all endpoints

## Support

For issues:
1. Check Modal logs: `modal logs sketch-animation`
2. Verify API key quotas and limits
3. Check system dependencies in the Docker image
4. Review Modal documentation at [modal.com/docs](https://modal.com/docs)

## Local Development

You can still run the application locally:

```bash
# Set environment variables
export OPENAI_API_KEY=your_key_here
export ELEVENLABS_API_KEY=your_key_here

# Run locally
python main.py
```

## Updating the Deployment

To update your deployment:

1. Make changes to your code
2. Run the deploy command again:
   ```bash
   modal deploy modal_app.py
   ```

Modal will automatically update the deployment with your changes. 