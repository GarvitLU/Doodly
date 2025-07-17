import os
import asyncio
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
from moviepy.video.fx import resize
import numpy as np
from PIL import Image
import math

class VideoGenerator:
    def __init__(self, video_type: str = "landscape"):
        """
        Initialize video generator with orientation support
        video_type: "landscape" or "portrait"
        """
        self.video_type = video_type
        
        # Set dimensions based on orientation
        if video_type == "portrait":
            self.output_width = 1024
            self.output_height = 1536  # Tall portrait (1024x1536)
            print(f"[VideoGenerator] Initialized for PORTRAIT format: {self.output_width}x{self.output_height}")
        else:  # landscape
            self.output_width = 1536
            self.output_height = 1024
            print(f"[VideoGenerator] Initialized for LANDSCAPE format: {self.output_width}x{self.output_height}")
        
        self.fps = 30
    
    async def create_video(
        self,
        audio_path: str,
        image_paths: list,
        job_id: str,
        duration_per_frame: float = 3.0,
        include_background_music: bool = False,
        include_hand_animation: bool = False,
        video_type: str = None
    ) -> str:
        """
        Create a whiteboard animation video from audio and images
        """
        try:
            # Update video type if provided
            if video_type:
                self.video_type = video_type
                if video_type == "portrait":
                    self.output_width = 1024
                    self.output_height = 1536  # Tall portrait (1024x1536)
                else:  # landscape
                    self.output_width = 1536
                    self.output_height = 1024
                print(f"[VideoGenerator] Updated to {video_type.upper()} format: {self.output_width}x{self.output_height}")
            
            print(f"Creating {self.video_type} video for job {job_id}")
            print(f"Video dimensions: {self.output_width}x{self.output_height}")
            
            # Load audio
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            
            # Calculate timing for each image
            num_images = len(image_paths)
            if num_images == 0:
                raise Exception("No images provided for video generation")
            
            # Calculate frame duration based on audio length for better sync
            frame_duration = total_duration / num_images
            print(f"Audio duration: {total_duration:.2f}s, Images: {num_images}, Frame duration: {frame_duration:.2f}s")
            
            # Create video clips from images
            video_clips = []
            
            for i, image_path in enumerate(image_paths):
                if os.path.exists(image_path):
                    # Create image clip with calculated duration
                    image_clip = ImageClip(image_path, duration=frame_duration)
                    
                    # Properly resize image to fit video dimensions while maintaining aspect ratio
                    image_clip = self._resize_with_padding(image_clip, self.output_width, self.output_height)
                    
                    # Add subtle fade in/out effects (shorter for smoother transitions)
                    image_clip = image_clip.fadein(0.3).fadeout(0.3)
                    
                    # Add Ken Burns effect (optional)
                    if include_hand_animation:
                        image_clip = self._add_ken_burns_effect(image_clip)
                    
                    video_clips.append(image_clip)
                    print(f"Added frame {i+1}/{num_images} with duration {frame_duration:.2f}s")
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
            
            # Export video with orientation-specific filename
            orientation_suffix = "_portrait" if self.video_type == "portrait" else "_landscape"
            output_path = f"outputs/video_{job_id}{orientation_suffix}.mp4"
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
            
            print(f"{self.video_type.capitalize()} video created successfully: {output_path}")
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

    def _resize_with_padding(self, clip, target_width, target_height):
        """
        Resize image clip to target dimensions while maintaining aspect ratio using padding
        """
        # Get original dimensions
        original_width = clip.w
        original_height = clip.h
        
        # Calculate aspect ratios
        target_ratio = target_width / target_height
        original_ratio = original_width / original_height
        
        print(f"[VideoGenerator] Original: {original_width}x{original_height} ({original_ratio:.2f})")
        print(f"[VideoGenerator] Target: {target_width}x{target_height} ({target_ratio:.2f})")
        
        if original_ratio > target_ratio:
            # Original is wider than target - fit to width, pad height
            new_width = target_width
            new_height = int(target_width / original_ratio)
            pad_top = (target_height - new_height) // 2
            pad_bottom = target_height - new_height - pad_top
            
            print(f"[VideoGenerator] Fitting to width: {new_width}x{new_height}, padding: {pad_top}+{pad_bottom}")
            
            # Resize to fit width
            resized_clip = clip.resize(width=new_width)
            
            # Create padded clip
            def add_padding(get_frame, t):
                frame = get_frame(t)
                # Create white background
                padded_frame = np.full((target_height, target_width, 3), 255, dtype=np.uint8)
                # Place the resized frame in the center
                padded_frame[pad_top:pad_top+new_height, :] = frame
                return padded_frame
            
            return resized_clip.fl(add_padding)
            
        else:
            # Original is taller than target - fit to height, pad width
            new_width = int(target_height * original_ratio)
            new_height = target_height
            pad_left = (target_width - new_width) // 2
            pad_right = target_width - new_width - pad_left
            
            print(f"[VideoGenerator] Fitting to height: {new_width}x{new_height}, padding: {pad_left}+{pad_right}")
            
            # Resize to fit height
            resized_clip = clip.resize(height=new_height)
            
            # Create padded clip
            def add_padding(get_frame, t):
                frame = get_frame(t)
                # Create white background
                padded_frame = np.full((target_height, target_width, 3), 255, dtype=np.uint8)
                # Place the resized frame in the center
                padded_frame[:, pad_left:pad_left+new_width] = frame
                return padded_frame
            
            return resized_clip.fl(add_padding) 