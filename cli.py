#!/usr/bin/env python3
"""
Command Line Interface for Whiteboard Animation Video Generator
"""

import asyncio
import argparse
import os
import sys
from dotenv import load_dotenv
from services.script_service import ScriptService
from services.audio_service import AudioService
from services.image_service import ImageService
from services.video_generator import VideoGenerator
import uuid

load_dotenv()

class WhiteboardVideoCLI:
    def __init__(self):
        self.script_service = ScriptService()
        self.audio_service = AudioService()
        self.image_service = ImageService()
        self.video_generator = VideoGenerator()
    
    async def generate_video(
        self,
        topic: str,
        style: str = "educational",
        duration_per_frame: float = 3.0,
        include_background_music: bool = False,
        include_hand_animation: bool = False,
        output_name: str = None
    ):
        """
        Generate a whiteboard animation video from command line
        """
        try:
            job_id = output_name or str(uuid.uuid4())
            
            print(f"🎬 Starting whiteboard video generation for: {topic}")
            print(f"📁 Job ID: {job_id}")
            print(f"🎨 Style: {style}")
            
            # Step 1: Generate script
            print("\n📝 Step 1: Generating script...")
            script = await self.script_service.generate_script(topic, style)
            print(f"✅ Script generated ({len(script)} characters)")
            print(f"📄 Script preview: {script[:100]}...")
            
            # Step 2: Generate audio
            print("\n🎵 Step 2: Generating audio...")
            audio_path = await self.audio_service.generate_audio(script, job_id)
            print(f"✅ Audio generated: {audio_path}")
            
            # Step 3: Generate images for each sentence
            print("\n🖼️  Step 3: Generating images...")
            sentences = self.script_service.split_script_into_sentences(script)
            print(f"📊 Found {len(sentences)} sentences to illustrate")
            
            image_paths = []
            for i, sentence in enumerate(sentences):
                print(f"   🎨 Generating image {i+1}/{len(sentences)}: {sentence[:50]}...")
                image_path = await self.image_service.generate_sketch_image(sentence, job_id, i)
                image_paths.append(image_path)
            
            print(f"✅ All images generated ({len(image_paths)} images)")
            
            # Step 4: Generate video
            print("\n🎬 Step 4: Creating video...")
            video_path = await self.video_generator.create_video(
                audio_path=audio_path,
                image_paths=image_paths,
                job_id=job_id,
                duration_per_frame=duration_per_frame,
                include_background_music=include_background_music,
                include_hand_animation=include_hand_animation
            )
            
            print(f"\n🎉 Video generation completed!")
            print(f"📁 Output file: {video_path}")
            print(f"📊 Video details:")
            print(f"   - Topic: {topic}")
            print(f"   - Style: {style}")
            print(f"   - Images: {len(image_paths)}")
            print(f"   - Background music: {'Yes' if include_background_music else 'No'}")
            print(f"   - Hand animation: {'Yes' if include_hand_animation else 'No'}")
            
            return video_path
            
        except Exception as e:
            print(f"\n❌ Error during video generation: {str(e)}")
            return None
    
    async def list_voices(self):
        """
        List available ElevenLabs voices
        """
        try:
            voices = await self.audio_service.get_available_voices()
            print("🎤 Available ElevenLabs voices:")
            print("   ID                                    | Name    | Category")
            print("   " + "-" * 70)
            for voice in voices:
                print(f"   {voice['id']:<36} | {voice['name']:<7} | {voice['category']}")
            print("\n💡 To use a specific voice, set DEFAULT_VOICE in your .env file:")
            print("   DEFAULT_VOICE=voice_id_here")
        except Exception as e:
            print(f"❌ Error listing voices: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="Whiteboard Animation Video Generator CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py "How photosynthesis works"
  python cli.py "Machine learning basics" --style "technical" --duration 4.0
  python cli.py "The water cycle" --background-music --hand-animation
  python cli.py --list-voices
        """
    )
    
    parser.add_argument(
        "topic",
        nargs="?",
        help="Topic or script for the whiteboard video"
    )
    
    parser.add_argument(
        "--style",
        default="educational",
        choices=["educational", "technical", "business", "creative"],
        help="Style of the video (default: educational)"
    )
    
    parser.add_argument(
        "--duration",
        type=float,
        default=3.0,
        help="Duration per frame in seconds (default: 3.0)"
    )
    
    parser.add_argument(
        "--background-music",
        action="store_true",
        help="Include background music in the video"
    )
    
    parser.add_argument(
        "--hand-animation",
        action="store_true",
        help="Include hand animation overlay"
    )
    
    parser.add_argument(
        "--output",
        help="Custom output filename (without extension)"
    )
    
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available ElevenLabs voices"
    )
    
    args = parser.parse_args()
    
    # Check if required environment variables are set
    required_vars = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file or environment.")
        sys.exit(1)
    
    # Create outputs directory if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    
    cli = WhiteboardVideoCLI()
    
    if args.list_voices:
        asyncio.run(cli.list_voices())
    elif args.topic:
        asyncio.run(cli.generate_video(
            topic=args.topic,
            style=args.style,
            duration_per_frame=args.duration,
            include_background_music=args.background_music,
            include_hand_animation=args.hand_animation,
            output_name=args.output
        ))
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 