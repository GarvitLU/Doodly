#!/bin/bash

# Modal Deployment Script for Sketch Animation
# This script automates the deployment process to Modal Labs

set -e

echo "🚀 Starting Modal deployment for Sketch Animation..."

# Check if Modal CLI is installed
if ! command -v modal &> /dev/null; then
    echo "❌ Modal CLI is not installed. Please install it first:"
    echo "   pip install modal"
    exit 1
fi

# Check if user is authenticated
if ! modal token check &> /dev/null; then
    echo "❌ You are not authenticated with Modal. Please run:"
    echo "   modal token new"
    exit 1
fi

echo "✅ Modal CLI is installed and authenticated"

# Check for required environment variables
if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "❌ OPENAI_API_KEY environment variable is not set"
    echo "Please set your OpenAI API key:"
    echo "   export OPENAI_API_KEY=your_key_here"
    exit 1
fi

if [[ -z "$ELEVENLABS_API_KEY" ]]; then
    echo "❌ ELEVENLABS_API_KEY environment variable is not set"
    echo "Please set your ElevenLabs API key:"
    echo "   export ELEVENLABS_API_KEY=your_key_here"
    exit 1
fi

echo "✅ API keys found in environment variables"

# Create Modal secrets
echo "🔐 Creating Modal secrets..."

# Create OpenAI API key secret
if modal secret create openai-api-key OPENAI_API_KEY="$OPENAI_API_KEY" 2>/dev/null; then
    echo "✅ OpenAI API key secret created successfully"
else
    echo "ℹ️  OpenAI API key secret already exists (updating...)"
    modal secret create openai-api-key OPENAI_API_KEY="$OPENAI_API_KEY" --force
fi

# Create ElevenLabs API key secret
if modal secret create elevenlabs-api-key ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" 2>/dev/null; then
    echo "✅ ElevenLabs API key secret created successfully"
else
    echo "ℹ️  ElevenLabs API key secret already exists (updating...)"
    modal secret create elevenlabs-api-key ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY" --force
fi

# Verify secrets were created
echo "🔍 Verifying secrets..."
if modal secret list | grep -q "openai-api-key" && modal secret list | grep -q "elevenlabs-api-key"; then
    echo "✅ Both secrets verified successfully"
else
    echo "❌ Failed to verify secrets"
    exit 1
fi

# Deploy the application
echo "🚀 Deploying application to Modal..."
if modal deploy modal_app.py; then
    echo "✅ Application deployed successfully!"
else
    echo "❌ Deployment failed"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "Your application is now running on Modal Labs."
echo "Check the deployment URL in the output above."
echo ""
echo "📚 Next steps:"
echo "1. Test your deployment with the provided URL"
echo "2. Monitor logs with: modal logs sketch-animation"
echo "3. Check usage stats with: modal stats sketch-animation"
echo ""
echo "🔧 Common endpoints:"
echo "- GET  /              - Main web interface"
echo "- GET  /scriptapi     - Script API interface"
echo "- POST /generate-script-video - Generate video from script"
echo "- POST /generate-image - Generate single image"
echo ""
echo "📖 For more information, see MODAL_DEPLOYMENT.md" 