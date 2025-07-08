#!/bin/bash

# Whiteboard Animation Video Generator Deployment Script

echo "🎬 Whiteboard Animation Video Generator - Deployment Script"
echo "=========================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python version $python_version is too old. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python $python_version detected"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg is not installed. Installing FFmpeg..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo "❌ Homebrew is not installed. Please install FFmpeg manually."
            echo "Visit: https://ffmpeg.org/download.html"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command -v yum &> /dev/null; then
            sudo yum install -y ffmpeg
        else
            echo "❌ Package manager not found. Please install FFmpeg manually."
            exit 1
        fi
    else
        echo "❌ Unsupported operating system. Please install FFmpeg manually."
        exit 1
    fi
fi

echo "✅ FFmpeg detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create outputs directory
echo "📁 Creating outputs directory..."
mkdir -p outputs

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "📝 Please edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY"
    echo "   - ELEVENLABS_API_KEY"
    echo ""
    echo "You can get these keys from:"
    echo "   - OpenAI: https://platform.openai.com/api-keys"
    echo "   - ElevenLabs: https://elevenlabs.io/speech-synthesis"
    echo ""
    read -p "Press Enter after you've added your API keys..."
fi

# Check if API keys are set
if ! grep -q "your_openai_api_key_here" .env; then
    echo "✅ API keys appear to be configured"
else
    echo "⚠️  Please make sure to add your API keys to the .env file"
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "🚀 To start the application:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Start the server: python main.py"
echo "   3. Open browser: http://localhost:8000"
echo ""
echo "📖 For more information, see README.md"
echo ""
echo "🧪 To test the system: python test_generation.py" 