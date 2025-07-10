#!/usr/bin/env python3
"""
Test script for the new script-based video generation API
"""

import requests
import json
import time

def test_script_api():
    """Test the script-based video generation API"""
    
    # API endpoint
    url = "http://localhost:8000/generate-script-video"
    
    # Test data
    test_data = {
        "script": "An array is a collection of elements stored in contiguous memory locations. Each element in an array can be accessed using its index, starting from zero. Arrays allow fast access to any element using its index.",
        "image_quality": "low",  # Use low quality for faster testing
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam voice
        "video_type": "landscape"  # Landscape orientation
    }
    
    print("🧪 Testing Script-Based Video Generation API")
    print("=" * 50)
    print(f"📝 Script: {test_data['script'][:50]}...")
    print(f"🎨 Image Quality: {test_data['image_quality']}")
    print(f"🎤 Voice ID: {test_data['voice_id']}")
    print(f"📐 Video Type: {test_data['video_type']}")
    print()
    
    try:
        print("🚀 Sending request to API...")
        response = requests.post(url, json=test_data, timeout=300)  # 5 minute timeout
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API Response received successfully!")
            print()
            print("📊 Response Details:")
            print(f"   Job ID: {result.get('job_id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            print(f"   Sentences Count: {result.get('sentences_count', 'N/A')}")
            print(f"   Images Count: {result.get('images_count', 'N/A')}")
            print(f"   Final Video URL: {result.get('final_video_url', 'N/A')}")
            
            if result.get('final_video_url'):
                print(f"\n🎬 Video generated successfully!")
                print(f"📥 Download URL: http://localhost:8000{result['final_video_url']}")
            else:
                print("\n⚠️  No video URL in response")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (5 minutes)")
        print("This is normal for video generation as it takes time to process")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - make sure the server is running on localhost:8000")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def test_frontend_endpoints():
    """Test if the frontend endpoints are accessible"""
    
    endpoints = [
        ("/", "Main Interface"),
        ("/scriptapi", "Script API Interface")
    ]
    
    print("\n🌐 Testing Frontend Endpoints")
    print("=" * 30)
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {name}: Accessible")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Error - {str(e)}")

if __name__ == "__main__":
    print("🎬 Script-Based Video Generator API Test")
    print("=" * 40)
    
    # Test frontend endpoints first
    test_frontend_endpoints()
    
    # Test the API
    test_script_api()
    
    print("\n✨ Test completed!")
    print("\n📋 Next steps:")
    print("1. Open http://localhost:8000/scriptapi in your browser")
    print("2. Enter a script and customize settings")
    print("3. Click 'Generate Video' to test the full workflow") 