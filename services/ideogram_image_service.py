import os
import base64
from PIL import Image
import io
import requests
import time
from .s3_service import S3Service

class IdeogramImageService:
    def __init__(self):
        self.api_key = os.getenv("IDEOGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("IDEOGRAM_API_KEY environment variable is required")
        
        self.base_url = "https://api.ideogram.ai"
        
        # Initialize S3 service
        try:
            self.s3_service = S3Service()
            self.use_s3 = True
            print("[IdeogramImageService] S3 storage enabled")
        except Exception as e:
            print(f"[IdeogramImageService] S3 not available, using local storage: {e}")
            self.use_s3 = False
    
    def generate_sketch_image(self, sentence: str, job_id: str, frame_index: int) -> str:
        """
        Generate a whiteboard sketch-style image using Ideogram API.
        Returns S3 URL if S3 is available, otherwise local file path.
        """
        return self.generate_sketch_image_with_quality(sentence, job_id, frame_index, "standard", "1024x1024")
    
    def generate_sketch_image_with_quality(self, sentence: str, job_id: str, frame_index: int, quality: str = "standard", size: str = "1024x1024") -> str:
        """
        Generate a whiteboard sketch-style image with customizable quality and size using Ideogram API.
        Returns S3 URL if S3 is available, otherwise local file path.
        """
        try:
            print(f"[IdeogramImageService] Job ID: {job_id} | Generating image for frame {frame_index}: {sentence[:50]}...")
            print(f"[IdeogramImageService] Quality: {quality}, Size: {size}")

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
            print(f"[IdeogramImageService] Image prompt: {prompt}")

            # Map size to aspect ratio
            aspect_ratio = self._map_size_to_aspect_ratio(size)
            
            # Create image generation request
            image_url = self._create_image_generation(prompt, aspect_ratio)
            print(f"[IdeogramImageService] Generation completed, image URL: {image_url}")

            # Create temporary local path
            temp_image_path = f"outputs/image_{job_id}_{frame_index}.png"
            os.makedirs("outputs", exist_ok=True)

            # Download and save the image
            self._download_and_save_image(image_url, temp_image_path)
            print(f"[IdeogramImageService] Image saved to {temp_image_path}")
            
            # Upload to S3 if available
            if self.use_s3:
                try:
                    s3_url = self.s3_service.upload_image(temp_image_path, job_id, frame_index)
                    print(f"[IdeogramImageService] Image uploaded to S3: {s3_url}")
                    # Clean up local file
                    os.remove(temp_image_path)
                    return s3_url
                except Exception as e:
                    print(f"[IdeogramImageService] Failed to upload to S3, keeping local file: {e}")
                    return temp_image_path
            else:
                return temp_image_path
                
        except Exception as e:
            print(f"[IdeogramImageService] Error generating image for frame {frame_index}: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    def _map_size_to_aspect_ratio(self, size: str) -> str:
        """
        Map image size to Ideogram aspect ratio format
        """
        size_map = {
            "1024x1024": "ASPECT_1_1",
            "1536x1024": "ASPECT_3_2", 
            "1024x1536": "ASPECT_2_3",
            "1024x1024": "ASPECT_1_1"
        }
        return size_map.get(size, "ASPECT_1_1")

    def _create_image_generation(self, prompt: str, aspect_ratio: str) -> str:
        """
        Create an image generation request with Ideogram API
        """
        headers = {
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "image_request": {
                "prompt": prompt,
                "model": "V_2",
                "aspect_ratio": aspect_ratio,
                "magic_prompt_option": "AUTO",
                "seed": 0,
                "negative_prompt": "",
                "style_type": "AUTO"
            }
        }
        
        print(f"[IdeogramImageService] Making API request to: {self.base_url}/generate")
        print(f"[IdeogramImageService] Payload: {payload}")
        
        response = requests.post(
            f"{self.base_url}/generate",
            headers=headers,
            json=payload
        )
        
        print(f"[IdeogramImageService] Response status: {response.status_code}")
        print(f"[IdeogramImageService] Response text: {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Ideogram API error: {response.status_code} - {response.text}")
        
        data = response.json()
        
        # Extract image URL from response
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]["url"]
        else:
            raise Exception("No image URL found in Ideogram API response")

    def _create_enhanced_sketch_prompt(self, sentence: str, involves_people: bool) -> str:
        """
        Create an optimized prompt for whiteboard sketch style images with focus on educational content.
        """
        clean_sentence = sentence.strip().rstrip('.!?')
        
        if involves_people:
            prompt = f'''A detailed, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Requirements:
- Focus 70% on the main concept/topic being explained
- Include 1-2 small, simple human figures (not faces) to show interaction/learning
- Show clear diagrams, charts, or visual representations of the concept
- Add minimal, handwritten-style text: only 1-2 key labels or terms (NO heading or title)
- Clean, bold black lines on a pure white background (no color)
- Professional, educational composition
- Emphasize the educational content over human elements
- Use simple, clear visual metaphors to explain the concept'''
        else:
            prompt = f'''A detailed, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Requirements:
- Focus entirely on the concept, object, or process being explained
- Include relevant diagrams, flowcharts, or visual representations
- Add minimal, handwritten-style text: only 1-2 key labels or terms (NO heading or title)
- Clean, bold black lines on a pure white background (no color)
- Professional, educational composition
- Use clear visual metaphors and examples
- Make the concept easy to understand visually'''
        return prompt

    def _download_and_save_image(self, image_url: str, save_path: str):
        """
        Download image from URL and save to local path
        """
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image.save(save_path, "PNG")
        else:
            raise Exception(f"Failed to download image: HTTP {response.status_code}") 