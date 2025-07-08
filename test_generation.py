#!/usr/bin/env python3
"""
Test script for whiteboard animation video generator
"""

import asyncio
import os
from dotenv import load_dotenv
from services.script_service import ScriptService
from services.audio_service import AudioService
from services.image_service import ImageService
from services.video_generator import VideoGenerator

load_dotenv()

async def test_video_generation():
    """
    Test the complete video generation pipeline
    """
    print("🧪 Testing Whiteboard Animation Video Generator")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your .env file")
        return False
    
    try:
        # Initialize services
        script_service = ScriptService()
        audio_service = AudioService()
        image_service = ImageService()
        video_generator = VideoGenerator()
        
        # Test topic
        topic = "How plants make food through photosynthesis"
        job_id = "test_generation"
        
        print(f"📝 Testing script generation for: {topic}")
        
        # Step 1: Generate script
        script = await script_service.generate_script(topic, "educational")
        print(f"✅ Script generated: {len(script)} characters")
        print(f"📄 Script preview: {script[:100]}...")
        
        # Step 2: Split into sentences
        sentences = script_service.split_script_into_sentences(script)
        print(f"📊 Found {len(sentences)} sentences")
        
        # Step 3: Generate audio (test with first sentence only to save time)
        print(f"🎵 Testing audio generation...")
        test_script = sentences[0] if sentences else "This is a test sentence for audio generation."
        audio_path = await audio_service.generate_audio(test_script, job_id)
        print(f"✅ Audio generated: {audio_path}")
        
        # Step 4: Generate one test image
        print(f"🖼️  Testing image generation...")
        test_sentence = sentences[0] if sentences else "A simple test illustration"
        image_path = await image_service.generate_sketch_image(test_sentence, job_id, 0)
        print(f"✅ Image generated: {image_path}")
        
        # Step 5: Test simple video creation
        print(f"🎬 Testing video generation...")
        video_path = video_generator.create_simple_video([image_path], job_id, 3.0)
        print(f"✅ Video generated: {video_path}")
        
        print("\n🎉 All tests passed! The system is working correctly.")
        print(f"📁 Generated files:")
        print(f"   - Audio: {audio_path}")
        print(f"   - Image: {image_path}")
        print(f"   - Video: {video_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def test_services_individually():
    """
    Test each service individually
    """
    print("\n🔧 Testing Individual Services")
    print("=" * 30)
    
    # Test script service
    try:
        script_service = ScriptService()
        script = await script_service.generate_script("Test topic", "educational")
        print("✅ Script service: Working")
    except Exception as e:
        print(f"❌ Script service: Failed - {str(e)}")
    
    # Test audio service
    try:
        audio_service = AudioService()
        print("✅ Audio service: Initialized")
    except Exception as e:
        print(f"❌ Audio service: Failed - {str(e)}")
    
    # Test image service
    try:
        image_service = ImageService()
        print("✅ Image service: Initialized")
    except Exception as e:
        print(f"❌ Image service: Failed - {str(e)}")
    
    # Test video generator
    try:
        video_generator = VideoGenerator()
        print("✅ Video generator: Initialized")
    except Exception as e:
        print(f"❌ Video generator: Failed - {str(e)}")

def main():
    """
    Run all tests
    """
    print("🚀 Starting Whiteboard Animation Video Generator Tests")
    print("=" * 60)
    
    # Create outputs directory
    os.makedirs("outputs", exist_ok=True)
    
    # Run tests
    asyncio.run(test_services_individually())
    success = asyncio.run(test_video_generation())
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("You can now use the CLI or API to generate videos.")
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")

if __name__ == "__main__":
    main() 