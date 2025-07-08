import os
import asyncio
from elevenlabs import generate, save, set_api_key, voices
import aiofiles

class AudioService:
    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
        set_api_key(api_key)
        
        # Use the voice ID from .env if provided, otherwise fallback to Adam
        self.default_voice = os.getenv("DEFAULT_VOICE") or "pNInz6obpgDQGcFmaJgB"
        self.default_model = os.getenv("DEFAULT_AUDIO_MODEL", "eleven_monolingual_v1")
    
    async def generate_audio(self, script: str, job_id: str) -> str:
        """
        Generate audio from script using ElevenLabs API
        """
        try:
            print(f"Generating audio for job {job_id}")
            print(f"[AudioService] Using voice ID: {self.default_voice}")
            
            # Generate audio using ElevenLabs
            audio = generate(
                text=script,
                voice=self.default_voice,
                model=self.default_model
            )
            
            # Save audio file
            audio_path = f"outputs/audio_{job_id}.mp3"
            save(audio, audio_path)
            
            print(f"Audio generated and saved to {audio_path}")
            return audio_path
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            # Create a fallback audio file or raise the error
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    async def get_available_voices(self):
        """
        Get list of available voices from ElevenLabs
        """
        try:
            available_voices = voices()
            voice_list = []
            for voice in available_voices:
                voice_list.append({
                    "id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, 'category', 'Unknown')
                })
            return voice_list
        except Exception as e:
            print(f"Error getting voices: {str(e)}")
            # Default fallback voices with IDs
            return [
                {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "category": "Default"},
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "category": "Default"},
                {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "category": "Default"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "category": "Default"}
            ]
    
    def set_voice(self, voice_id: str):
        """
        Set the voice ID to use for audio generation
        """
        self.default_voice = voice_id
    
    def set_model(self, model_name: str):
        """
        Set the model to use for audio generation
        """
        self.default_model = model_name 