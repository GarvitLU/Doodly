import openai
import os
import base64
from PIL import Image
import io
import random
from .s3_service import S3Service

class ImageService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.image_model = os.getenv("DEFAULT_IMAGE_MODEL", "gpt-image-1")
        # Initialize S3 service
        try:
            self.s3_service = S3Service()
            self.use_s3 = True
            print("[ImageService] S3 storage enabled")
        except Exception as e:
            print(f"[ImageService] S3 not available, using local storage: {e}")
            self.use_s3 = False
    
    def generate_sketch_image(self, sentence: str, job_id: str, frame_index: int) -> str:
        """
        Generate a whiteboard sketch-style image focused on humans, emotional faces, and script-based context.
        Returns S3 URL if S3 is available, otherwise local file path.
        """
        try:
            print(f"[ImageService] Job ID: {job_id} | Generating image for frame {frame_index}: {sentence[:50]}...")

            # Detect if the sentence involves people
            people_keywords = [
                "person", "people", "man", "woman", "boy", "girl", "teacher", "student", "child", "children", "adult", 
                "men", "women", "kid", "kids", "human", "face", "worker", "employee", "boss", "manager", "team", "group", 
                "crowd", "audience", "speaker", "presenter", "doctor", "nurse", "patient", "customer", "client", "user", 
                "friend", "family", "parent", "father", "mother", "son", "daughter", "brother", "sister"
            ]
            involves_people = any(kw in sentence.lower() for kw in people_keywords)

            # Generate the enhanced prompt
            prompt = self._create_enhanced_sketch_prompt(sentence, involves_people)
            print(f"[ImageService] Image prompt: {prompt}")

            # Generate image using DALL-E
            response = self.client.images.generate(
                model=self.image_model,
                prompt=prompt,
                size="1536x1024",
                quality="medium",
                n=1,
            )
            print(f"[ImageService] DALL-E API raw response for frame {frame_index}: {response}")

            if not hasattr(response, 'data') or not response.data:
                print(f"[ImageService] ERROR: No image data returned. Full response: {response}")
                if hasattr(response, 'error'):
                    print(f"[ImageService] OpenAI API error: {response.error}")
                raise Exception(f"OpenAI API did not return valid image data. See logs for details.")

            image_data_obj = response.data[0]
            image_url = getattr(image_data_obj, 'url', None)
            b64_json = getattr(image_data_obj, 'b64_json', None)

            # Create temporary local path
            temp_image_path = f"outputs/image_{job_id}_{frame_index}.png"
            os.makedirs("outputs", exist_ok=True)

            if image_url:
                self._download_and_save_image(image_url, temp_image_path)
                print(f"[ImageService] Image saved to {temp_image_path}")
            elif b64_json:
                image_data = base64.b64decode(b64_json)
                image = Image.open(io.BytesIO(image_data))
                image.save(temp_image_path, "PNG")
                print(f"[ImageService] Image saved to {temp_image_path} from base64 data")
            else:
                raise Exception("OpenAI API did not return a valid image URL or base64 image data.")
            
            # Upload to S3 if available
            if self.use_s3:
                try:
                    s3_url = self.s3_service.upload_image(temp_image_path, job_id, frame_index)
                    print(f"[ImageService] Image uploaded to S3: {s3_url}")
                    # Clean up local file
                    os.remove(temp_image_path)
                    return s3_url
                except Exception as e:
                    print(f"[ImageService] Failed to upload to S3, keeping local file: {e}")
                    return temp_image_path
            else:
                return temp_image_path
                
        except Exception as e:
            print(f"[ImageService] Error generating image for frame {frame_index}: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    def generate_sketch_image_with_quality(self, sentence: str, job_id: str, frame_index: int, quality: str = "medium", size: str = "1536x1024") -> str:
        """
        Generate a whiteboard sketch-style image with customizable quality and size.
        Returns S3 URL if S3 is available, otherwise local file path.
        """
        try:
            print(f"[ImageService] Job ID: {job_id} | Generating image for frame {frame_index}: {sentence[:50]}...")
            print(f"[ImageService] Quality: {quality}, Size: {size}")

            # Detect if the sentence involves people
            people_keywords = [
                "person", "people", "man", "woman", "boy", "girl", "teacher", "student", "child", "children", "adult", 
                "men", "women", "kid", "kids", "human", "face", "worker", "employee", "boss", "manager", "team", "group", 
                "crowd", "audience", "speaker", "presenter", "doctor", "nurse", "patient", "customer", "client", "user", 
                "friend", "family", "parent", "father", "mother", "son", "daughter", "brother", "sister"
            ]
            involves_people = any(kw in sentence.lower() for kw in people_keywords)

            # Generate the enhanced prompt
            prompt = self._create_enhanced_sketch_prompt(sentence, involves_people)
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

            if not hasattr(response, 'data') or not response.data:
                print(f"[ImageService] ERROR: No image data returned. Full response: {response}")
                if hasattr(response, 'error'):
                    print(f"[ImageService] OpenAI API error: {response.error}")
                raise Exception(f"OpenAI API did not return valid image data. See logs for details.")

            image_data_obj = response.data[0]
            image_url = getattr(image_data_obj, 'url', None)
            b64_json = getattr(image_data_obj, 'b64_json', None)

            # Create temporary local path
            temp_image_path = f"outputs/image_{job_id}_{frame_index}.png"
            os.makedirs("outputs", exist_ok=True)

            if image_url:
                self._download_and_save_image(image_url, temp_image_path)
                print(f"[ImageService] Image saved to {temp_image_path}")
            elif b64_json:
                image_data = base64.b64decode(b64_json)
                image = Image.open(io.BytesIO(image_data))
                image.save(temp_image_path, "PNG")
                print(f"[ImageService] Image saved to {temp_image_path} from base64 data")
            else:
                raise Exception("OpenAI API did not return a valid image URL or base64 image data.")
            
            # Upload to S3 if available
            if self.use_s3:
                try:
                    s3_url = self.s3_service.upload_image(temp_image_path, job_id, frame_index)
                    print(f"[ImageService] Image uploaded to S3: {s3_url}")
                    # Clean up local file
                    os.remove(temp_image_path)
                    return s3_url
                except Exception as e:
                    print(f"[ImageService] Failed to upload to S3, keeping local file: {e}")
                    return temp_image_path
            else:
                return temp_image_path
                
        except Exception as e:
            print(f"[ImageService] Error generating image for frame {frame_index}: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    def _create_enhanced_sketch_prompt(self, sentence: str, involves_people: bool) -> str:
        """
        Create an optimized prompt for whiteboard sketch style images with a focus on humans, emotions, and context.
        """
        clean_sentence = sentence.strip().rstrip('.!?')
        if involves_people:
            prompt = f'''A detailed, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Requirements:
- Multiple animated human faces, each with a unique, strong emotional expression (e.g., joy, surprise, curiosity, empathy)
- Faces should be highly expressive, with clear, exaggerated features (eyes, eyebrows, mouth)
- Include diverse people: vary age, ethnicity, hairstyle, and accessories
- Show people interacting with each other and with relevant objects from the script
- Scene should include subtle background elements for context (e.g., classroom, office, outdoor setting)
- Add minimal, handwritten-style text: only 1-2 labels or captions to clarify the scene (NO heading or title)
- Clean, bold black lines on a pure white background (no color)
- Professional, educational, and engaging composition
- Avoid clutter: focus on clarity and emotional impact'''
        else:
            prompt = f'''A detailed, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Requirements:
- Include relevant objects or actions from the script
- Add minimal, handwritten-style text: only 1-2 labels or captions to clarify the scene (NO heading or title)
- Clean, bold black lines on a pure white background (no color)
- Professional, educational, and engaging composition
- Avoid clutter: focus on clarity and visual storytelling'''
        return prompt

    def _download_and_save_image(self, image_url: str, save_path: str):
        """
        Download image from URL and save to local path
        """
        import requests
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image.save(save_path, "PNG")
        else:
            raise Exception(f"Failed to download image: HTTP {response.status_code}") 