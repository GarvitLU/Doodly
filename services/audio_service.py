import os
import asyncio
from elevenlabs import generate, save, set_api_key, voices
import aiofiles
import whisper

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
            outputs_dir = os.getenv("OUTPUTS_DIR", "outputs")
            audio_path = f"{outputs_dir}/audio_{job_id}.mp3"
            save(audio, audio_path)
            
            print(f"Audio generated and saved to {audio_path}")
            
            # DEBUG: Verify file was created
            if not os.path.exists(audio_path):
                print(f"ERROR: Audio file was not created: {audio_path}")
                raise Exception("Audio generation failed, file not created.")
            else:
                print(f"DEBUG: Audio file verified to exist: {audio_path}")
            
            return audio_path
            
        except Exception as e:
            print(f"Error generating audio: {str(e)}")
            # Create a fallback audio file or raise the error
            raise Exception(f"Failed to generate audio: {str(e)}")
    
    async def generate_audio_per_sentence(self, sentences: list, job_id: str) -> list:
        """
        Generate audio for each sentence and return a list of dicts with 'audio_path' and 'duration' for each.
        """
        from moviepy.editor import AudioFileClip
        audio_segments = []
        for i, sentence in enumerate(sentences):
            audio = generate(
                text=sentence,
                voice=self.default_voice,
                model=self.default_model
            )
            outputs_dir = os.getenv("OUTPUTS_DIR", "outputs")
            audio_path = f"{outputs_dir}/audio_{job_id}_{i}.mp3"
            save(audio, audio_path)
            
            # DEBUG: Verify file was created
            if not os.path.exists(audio_path):
                print(f"ERROR: Audio file was not created: {audio_path}")
                raise Exception(f"Audio generation failed for sentence {i}, file not created.")
            else:
                print(f"DEBUG: Audio file verified to exist: {audio_path}")
            
            # Get duration
            duration = AudioFileClip(audio_path).duration
            audio_segments.append({
                'audio_path': audio_path,
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