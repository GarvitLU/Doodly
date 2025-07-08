import os
import asyncio
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx import resize
import numpy as np
from PIL import Image
import math

class VideoGenerator:
    def __init__(self):
        self.output_width = 1920
        self.output_height = 1080
        self.fps = 30
    
    async def create_video(
        self,
        audio_path: str,
        image_paths: list,
        job_id: str,
        duration_per_frame: float = 3.0,
        include_background_music: bool = False,
        include_hand_animation: bool = False
    ) -> str:
        """
        Create a whiteboard animation video from audio and images
        """
        try:
            print(f"Creating video for job {job_id}")
            
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            
            # Calculate timing for each image
            num_images = len(image_paths)
            if num_images == 0:
                raise Exception("No images provided for video generation")
            
            # Calculate frame duration based on audio length
            frame_duration = total_duration / num_images
            
            # Create video clips from images
            video_clips = []
            
            for i, image_path in enumerate(image_paths):
                if os.path.exists(image_path):
                    # Create image clip with calculated duration
                    image_clip = ImageClip(image_path, duration=frame_duration)
                    
                    # Resize image to fit video dimensions
                    image_clip = image_clip.resize((self.output_width, self.output_height))
                    
                    # Add fade in/out effects
                    image_clip = image_clip.fadein(0.5).fadeout(0.5)
                    
                    # Add Ken Burns effect (optional)
                    if include_hand_animation:
                        image_clip = self._add_ken_burns_effect(image_clip)
                    
                    video_clips.append(image_clip)
                else:
                    print(f"Warning: Image file not found: {image_path}")
            
            if not video_clips:
                raise Exception("No valid video clips created")
            
            # Concatenate all video clips
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Add audio
            final_video = final_video.set_audio(audio_clip)
            
            # Add background music if requested
            if include_background_music:
                final_video = await self._add_background_music(final_video, total_duration)
            
            # Add hand animation overlay if requested
            if include_hand_animation:
                final_video = await self._add_hand_animation(final_video, total_duration)
            
            # Set video properties
            final_video = final_video.set_fps(self.fps)
            
            # Export video
            output_path = f"outputs/video_{job_id}.mp4"
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Clean up
            audio_clip.close()
            final_video.close()
            for clip in video_clips:
                clip.close()
            
            print(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error creating video: {str(e)}")
            raise Exception(f"Failed to create video: {str(e)}")
    
    def _add_ken_burns_effect(self, clip):
        """
        Add Ken Burns effect (slow zoom/pan) to the clip
        """
        def ken_burns(get_frame, t):
            frame = get_frame(t)
            # Ensure frame is a numpy array
            if not isinstance(frame, np.ndarray):
                frame = np.array(frame)
            print(f"[KenBurns] Frame type: {type(frame)}, shape: {getattr(frame, 'shape', None)}")
            if len(frame.shape) == 2:
                h, w = frame.shape
            elif len(frame.shape) == 3:
                h, w = frame.shape[:2]
            else:
                raise Exception(f"Unexpected frame shape: {frame.shape}")
            
            # Calculate zoom factor (subtle zoom from 1.0 to 1.1)
            zoom_factor = 1.0 + (0.1 * t / clip.duration)
            
            # Calculate pan (subtle movement)
            pan_x = int(50 * math.sin(t * 0.5))
            pan_y = int(30 * math.cos(t * 0.3))
            
            new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
            
            # Resize frame
            resized_frame = resize.resize(frame, (new_w, new_h))
            
            # Crop to original size with pan
            start_x = max(0, (new_w - w) // 2 + pan_x)
            start_y = max(0, (new_h - h) // 2 + pan_y)
            end_x = min(new_w, start_x + w)
            end_y = min(new_h, start_y + h)
            
            return resized_frame[start_y:end_y, start_x:end_x]
        
        return clip.fl(ken_burns)
    
    async def _add_background_music(self, video_clip, duration):
        """
        Add background music to the video
        """
        try:
            # You can add royalty-free background music here
            # For now, we'll return the original clip
            # In a real implementation, you'd load an actual music file
            
            # In practice, you would do something like:
            # background_music = AudioFileClip("assets/background_music.mp3")
            # background_music = background_music.loop(duration=duration)
            # background_music = background_music.volumex(0.3)  # Lower volume
            # final_audio = CompositeAudioClip([video_clip.audio, background_music])
            # video_clip = video_clip.set_audio(final_audio)
            
            return video_clip
            
        except Exception as e:
            print(f"Warning: Could not add background music: {str(e)}")
            return video_clip
    
    async def _add_hand_animation(self, video_clip, duration):
        """
        Add animated hand overlay to simulate drawing
        """
        try:
            # This is a placeholder for hand animation
            # In a real implementation, you would:
            # 1. Load a hand GIF or video
            # 2. Create a clip from it
            # 3. Composite it over the main video
            
            # For now, we'll return the original clip
            # In practice, you would do something like:
            # hand_clip = VideoFileClip("assets/hand_animation.gif")
            # hand_clip = hand_clip.loop(duration=duration)
            # hand_clip = hand_clip.resize((200, 200))  # Resize hand
            # hand_clip = hand_clip.set_position(('right', 'bottom'))
            # final_video = CompositeVideoClip([video_clip, hand_clip])
            
            return video_clip
            
        except Exception as e:
            print(f"Warning: Could not add hand animation: {str(e)}")
            return video_clip
    
    def create_simple_video(self, image_paths: list, job_id: str, duration_per_frame: float = 3.0) -> str:
        """
        Create a simple video without audio (for testing)
        """
        try:
            video_clips = []
            
            for image_path in image_paths:
                if os.path.exists(image_path):
                    clip = ImageClip(image_path, duration=duration_per_frame)
                    clip = clip.resize((self.output_width, self.output_height))
                    video_clips.append(clip)
            
            if not video_clips:
                raise Exception("No valid video clips created")
            
            final_video = concatenate_videoclips(video_clips, method="compose")
            final_video = final_video.set_fps(self.fps)
            
            output_path = f"outputs/simple_video_{job_id}.mp4"
            final_video.write_videofile(
                output_path,
                codec='libx264',
                verbose=False,
                logger=None
            )
            
            # Clean up
            final_video.close()
            for clip in video_clips:
                clip.close()
            
            return output_path
            
        except Exception as e:
            print(f"Error creating simple video: {str(e)}")
            raise Exception(f"Failed to create simple video: {str(e)}") 