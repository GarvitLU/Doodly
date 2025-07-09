import openai
import os
import base64
import aiofiles
from PIL import Image
import io
import random

class ImageService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.image_model = os.getenv("DEFAULT_IMAGE_MODEL", "gpt-image-1")
    
    def generate_sketch_image(self, sentence: str, job_id: str, frame_index: int) -> str:
        """
        Generate a whiteboard sketch-style image from a sentence using DALL-E
        Automatically adds minimal text (heading/label) to diagrams or 1-2 random images per job.
        """
        try:
            print(f"[ImageService] Job ID: {job_id} | Generating image for frame {frame_index}: {sentence[:50]}...")

            # Detect if the sentence involves people
            people_keywords = [
                "person", "people", "man", "woman", "boy", "girl", "teacher", "student", "child", "children", "adult", "woman", "men", "women", "kid", "kids", "human", "face", "worker", "employee", "boss", "manager", "team", "group", "crowd", "audience", "speaker", "presenter", "doctor", "nurse", "patient", "customer", "client", "user", "friend", "family", "parent", "father", "mother", "son", "daughter", "brother", "sister"
            ]
            involves_people = any(kw in sentence.lower() for kw in people_keywords)

            # Generate the base prompt without any text elements
            base_prompt = self._create_sketch_prompt(sentence)
            
            if involves_people:
                people_detail_instruction = (
                    " Show full body with clear facial features, expressive cartoon-style faces, "
                    "detailed clothing, and realistic body posture. Clean, hand-drawn style with "
                    "friendly and approachable character design."
                )
                prompt = base_prompt + people_detail_instruction
            else:
                prompt = base_prompt

            print(f"[ImageService] Image prompt: {prompt}")
            
            # Generate image using DALL-E 2 (gpt-image-1)
            response = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size="1536x1024",
                quality="medium",
                n=1,
            )
            print(f"[ImageService] DALL-E API raw response for frame {frame_index}: {response}")

            # Check for errors or missing data
            if not hasattr(response, 'data') or not response.data:
                print(f"[ImageService] ERROR: No image data returned. Full response: {response}")
                if hasattr(response, 'error'):
                    print(f"[ImageService] OpenAI API error: {response.error}")
                raise Exception(f"OpenAI API did not return valid image data. See logs for details.")

            image_data_obj = response.data[0]
            image_url = getattr(image_data_obj, 'url', None)
            b64_json = getattr(image_data_obj, 'b64_json', None)

            image_path = f"outputs/image_{job_id}_{frame_index}.png"

            if image_url:
                print(f"[ImageService] Image URL for frame {frame_index}: {image_url}")
                try:
                    self._download_and_save_image(image_url, image_path)
                    print(f"[ImageService] Image saved to {image_path}")
                except Exception as download_err:
                    print(f"[ImageService] Error downloading image for frame {frame_index}: {download_err}")
                    raise Exception(f"Failed to download image: {download_err}")
                return image_path
            elif b64_json:
                print(f"[ImageService] Received base64 image data for frame {frame_index}")
                try:
                    # Do NOT print the base64 string
                    image_data = base64.b64decode(b64_json)
                    image = Image.open(io.BytesIO(image_data))
                    image.save(image_path, "PNG")
                    print(f"[ImageService] Image saved to {image_path} from base64 data")
                except Exception as b64_err:
                    print(f"[ImageService] Error decoding base64 image for frame {frame_index}: {b64_err}")
                    raise Exception(f"Failed to decode base64 image: {b64_err}")
                return image_path
            else:
                print(f"[ImageService] ERROR: No image URL or base64 data returned. Full response: {response}")
                raise Exception(f"OpenAI API did not return a valid image URL or base64 image data. See logs for details.")
            
        except Exception as e:
            print(f"[ImageService] Error generating image for frame {frame_index}: {str(e)}")
            # Create a fallback image or raise the error
            raise Exception(f"Failed to generate image: {str(e)}")
    
    def generate_sketch_image_with_quality(self, sentence: str, job_id: str, frame_index: int, quality: str = "medium", size: str = "1536x1024") -> str:
        """
        Generate a whiteboard sketch-style image with customizable quality and size
        """
        try:
            print(f"[ImageService] Job ID: {job_id} | Generating image for frame {frame_index}: {sentence[:50]}...")
            print(f"[ImageService] Quality: {quality}, Size: {size}")

            # Detect if the sentence involves people
            people_keywords = [
                "person", "people", "man", "woman", "boy", "girl", "teacher", "student", "child", "children", "adult", "woman", "men", "women", "kid", "kids", "human", "face", "worker", "employee", "boss", "manager", "team", "group", "crowd", "audience", "speaker", "presenter", "doctor", "nurse", "patient", "customer", "client", "user", "friend", "family", "parent", "father", "mother", "son", "daughter", "brother", "sister"
            ]
            involves_people = any(kw in sentence.lower() for kw in people_keywords)

            # Generate the base prompt without any text elements
            base_prompt = self._create_sketch_prompt(sentence)
            
            if involves_people:
                people_detail_instruction = (
                    " Show full body with clear facial features, expressive cartoon-style faces, "
                    "detailed clothing, and realistic body posture. Clean, hand-drawn style with "
                    "friendly and approachable character design."
                )
                prompt = base_prompt + people_detail_instruction
            else:
                prompt = base_prompt

            print(f"[ImageService] Image prompt: {prompt}")
            
            # Generate image using DALL-E with custom quality and size
            response = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )
            print(f"[ImageService] DALL-E API raw response for frame {frame_index}: {response}")

            # Check for errors or missing data
            if not hasattr(response, 'data') or not response.data:
                print(f"[ImageService] ERROR: No image data returned. Full response: {response}")
                if hasattr(response, 'error'):
                    print(f"[ImageService] OpenAI API error: {response.error}")
                raise Exception(f"OpenAI API did not return valid image data. See logs for details.")

            image_data_obj = response.data[0]
            image_url = getattr(image_data_obj, 'url', None)
            b64_json = getattr(image_data_obj, 'b64_json', None)

            image_path = f"outputs/image_{job_id}_{frame_index}.png"

            if image_url:
                print(f"[ImageService] Image URL for frame {frame_index}: {image_url}")
                try:
                    self._download_and_save_image(image_url, image_path)
                    print(f"[ImageService] Image saved to {image_path}")
                except Exception as download_err:
                    print(f"[ImageService] Error downloading image for frame {frame_index}: {download_err}")
                    raise Exception(f"Failed to download image: {download_err}")
                return image_path
            elif b64_json:
                print(f"[ImageService] Received base64 image data for frame {frame_index}")
                try:
                    # Do NOT print the base64 string
                    image_data = base64.b64decode(b64_json)
                    image = Image.open(io.BytesIO(image_data))
                    image.save(image_path, "PNG")
                    print(f"[ImageService] Image saved to {image_path} from base64 data")
                except Exception as b64_err:
                    print(f"[ImageService] Error decoding base64 image for frame {frame_index}: {b64_err}")
                    raise Exception(f"Failed to decode base64 image: {b64_err}")
                return image_path
            else:
                print(f"[ImageService] ERROR: No image URL or base64 data returned. Full response: {response}")
                raise Exception(f"OpenAI API did not return a valid image URL or base64 image data. See logs for details.")
            
        except Exception as e:
            print(f"[ImageService] Error generating image for frame {frame_index}: {str(e)}")
            # Create a fallback image or raise the error
            raise Exception(f"Failed to generate image: {str(e)}")
    
    def _create_sketch_prompt(self, sentence: str) -> str:
        """
        Create an optimized prompt for whiteboard sketch style images
        """
        # Clean the sentence for better image generation
        clean_sentence = sentence.strip().rstrip('.!?')
        
        # Create a comprehensive prompt for whiteboard sketch style
        prompt = f"""A clean, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Style requirements:
- Professional whiteboard sketch style, as if drawn by hand with a black marker
- Single, bold, clean outlines only - no double lines, no shading, no fills
- Pure black lines on clean white background
- Simple, clear, educational illustration style
- Minimalist design focusing on essential visual elements
- No text, words, letters, numbers, or labels anywhere in the image
- No speech bubbles, captions, or written content
- Vector-style illustration suitable for line art conversion
- Clean geometric shapes and smooth curves
- Professional educational diagram quality
- Avoid complex textures or detailed shading
- Focus on clear, recognizable shapes and forms
- Draw only one person, with one left and one right hand, in a natural pose
- Do not draw extra hands, fingers, or repeated body parts
- No duplicate limbs, no extra fingers, no repeated objects"""

        return prompt
    
    def _download_and_save_image(self, image_url: str, save_path: str):
        """
        Download image from URL and save to local path
        """
        try:
            import requests
            response = requests.get(image_url)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                image.save(save_path, "PNG")
                print(f"[ImageService] Image successfully downloaded and saved to {save_path}")
            else:
                print(f"[ImageService] Failed to download image: HTTP {response.status_code}")
                raise Exception(f"Failed to download image: HTTP {response.status_code}")
        except Exception as e:
            print(f"[ImageService] Exception during image download: {e}")
            raise
    
    async def resize_image(self, image_path: str, target_size: tuple = (1024, 1024)) -> str:
        """
        Resize image to target size while maintaining aspect ratio
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize image
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Save resized image
                resized_path = image_path.replace('.png', '_resized.png')
                img.save(resized_path, "PNG")
                
                return resized_path
                
        except Exception as e:
            print(f"Error resizing image: {str(e)}")
            return image_path  # Return original path if resize fails 