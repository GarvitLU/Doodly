import os
import asyncio
from elevenlabs import generate, save, set_api_key, voices
import aiofiles
import whisper
from .s3_service import S3Service

class AudioService:
    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is required")
        set_api_key(api_key)
        
        # Use the voice ID from .env if provided, otherwise fallback to Adam
        self.default_voice = os.getenv("DEFAULT_VOICE") or "pNInz6obpgDQGcFmaJgB"
        self.default_model = os.getenv("DEFAULT_AUDIO_MODEL", "eleven_monolingual_v1")
        
        # Initialize S3 service
        try:
            self.s3_service = S3Service()
            self.use_s3 = True
            print("[AudioService] S3 storage enabled")
        except Exception as e:
            print(f"[AudioService] S3 not available, using local storage: {e}")
            self.use_s3 = False
    
    async def generate_audio(self, script: str, job_id: str, voice_id: str = None) -> str:
        """
        Generate audio from script using ElevenLabs API.
        Returns S3 URL if S3 is available, otherwise local file path.
        """
        try:
            actual_voice = voice_id if voice_id else "ftDdhfYtmfGP0tFlBYA1"
            print(f"Generating audio for job {job_id}")
            print(f"[AudioService] Using voice ID: {actual_voice}")  # Debug print
            
            # Generate audio using ElevenLabs
            audio = generate(
                text=script,
                voice=actual_voice,
                model=self.default_model
            )
            
            # Save audio file locally first
            audio_path = f"outputs/audio_{job_id}.mp3"
            os.makedirs("outputs", exist_ok=True)
            save(audio, audio_path)
            
            print(f"Audio generated and saved to {audio_path}")
            
            # Upload to S3 if available
            if self.use_s3:
                try:
                    s3_url = self.s3_service.upload_audio(audio_path, job_id, 0)
                    print(f"[AudioService] Audio uploaded to S3: {s3_url}")
                    # Clean up local file
                    os.remove(audio_path)
                    return s3_url
                except Exception as e:
                    print(f"[AudioService] Failed to upload to S3, keeping local file: {e}")
                    return audio_path
            else:
                return audio_path
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            # Create a fallback audio file or raise the error
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    async def generate_audio_per_sentence(self, sentences: list, job_id: str, voice_id: str = None) -> list:
        """
        Generate audio for each sentence and return a list of dicts with 'audio_path' and 'duration' for each.
        Returns S3 URLs if S3 is available, otherwise local file paths.
        """
        from moviepy.editor import AudioFileClip
        audio_segments = []
        actual_voice = voice_id if voice_id else "ftDdhfYtmfGP0tFlBYA1"
        print(f"[AudioService] Actually using voice: {actual_voice}")  # Debug print
        for i, sentence in enumerate(sentences):
            audio = generate(
                text=sentence,
                voice=actual_voice,
                model=self.default_model
            )
            
            # Save audio file locally first
            audio_path = f"outputs/audio_{job_id}_{i}.mp3"
            os.makedirs("outputs", exist_ok=True)
            save(audio, audio_path)
            
            # Get duration
            duration = AudioFileClip(audio_path).duration
            
            # Upload to S3 if available
            final_audio_path = audio_path
            if self.use_s3:
                try:
                    s3_url = self.s3_service.upload_audio(audio_path, job_id, i)
                    print(f"[AudioService] Audio segment {i} uploaded to S3: {s3_url}")
                    # Clean up local file
                    os.remove(audio_path)
                    final_audio_path = s3_url
                except Exception as e:
                    print(f"[AudioService] Failed to upload audio segment {i} to S3, keeping local file: {e}")
            
            audio_segments.append({
                'audio_path': final_audio_path,
                'duration': duration,
                'sentence': sentence
            })
        
        return audio_segments
    
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

    def transcribe_audio(self, audio_path: str, model_size: str = "base") -> list:
        """
        Transcribe audio and return a list of words with their start/end timestamps using Whisper.
        """
        model = whisper.load_model(model_size)
        result = model.transcribe(audio_path, word_timestamps=True, verbose=False)
        words = []
        for segment in result["segments"]:
            for word in segment["words"]:
                words.append({
                    "word": word["word"],
                    "start": word["start"],
                    "end": word["end"]
                })
        return words 