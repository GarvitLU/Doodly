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

            # --- Label/heading logic ---
            # Detect if this is a diagram or label-worthy image
            diagram_keywords = ["diagram", "flowchart", "process", "structure", "cycle", "chart", "graph", "map", "step", "labeled"]
            is_diagram = any(kw in sentence.lower() for kw in diagram_keywords)
            
            # Use a temp file to store which frames get labels for this job_id
            label_file = f"outputs/.label_indices_{job_id}.txt"
            if os.path.exists(label_file):
                with open(label_file, "r") as f:
                    label_indices = [int(x) for x in f.read().strip().split(",") if x.strip()]
            else:
                # If not present, randomly select 1-2 indices (besides diagrams)
                num_labels = min(2, max(1, random.randint(1, 2)))
                # Only select from non-diagram frames
                # We'll select after the first call, so for now, just pick 1-2 random indices
                label_indices = random.sample(range(10), num_labels)  # fallback, will be overwritten below
                # We'll update this below after we know total frames
            
            # If this is the first frame, and label_file doesn't exist, create it with correct indices
            if frame_index == 0 and not os.path.exists(label_file):
                # Try to get total frames from environment (if set by caller), else fallback to 10
                total_frames = int(os.environ.get("TOTAL_FRAMES", "10"))
                # Find all diagram frames (simulate for now, as we don't have all sentences here)
                # We'll just pick 1-2 random indices for now
                num_labels = min(2, max(1, random.randint(1, 2)))
                label_indices = random.sample(range(total_frames), num_labels)
                with open(label_file, "w") as f:
                    f.write(",".join(str(x) for x in label_indices))
            
            # Should this frame get a label?
            add_label = (frame_index == 0) or is_diagram or (frame_index in label_indices)

            # --- Prompt construction ---
            # Detect if the sentence involves people
            people_keywords = [
                "person", "people", "man", "woman", "boy", "girl", "teacher", "student", "child", "children", "adult", "woman", "men", "women", "kid", "kids", "human", "face", "worker", "employee", "boss", "manager", "team", "group", "crowd", "audience", "speaker", "presenter", "doctor", "nurse", "patient", "customer", "client", "user", "friend", "family", "parent", "father", "mother", "son", "daughter", "brother", "sister"
            ]
            involves_people = any(kw in sentence.lower() for kw in people_keywords)

            if involves_people:
                people_detail_instruction = (
                    " in a clean, detailed, hand-drawn whiteboard sketch style, cartoon style. "
                    "Show the full body, with clear facial features, expressive faces, detailed clothing, and realistic body posture. "
                    "Minimal, black lines on white background. No color, no shading. Professional whiteboard animation style."
                )
            else:
                people_detail_instruction = ""

            cartoon_face_instruction = " with cartoon-style faces (not realistic, but friendly and expressive)" if involves_people else ""
            full_body_instruction = " Show the full body of the person, including face, body, and figure, in a hand-drawn cartoon style." if involves_people else ""

            if add_label:
                # Use a minimal heading/label
                heading = sentence[:40].strip().rstrip('.!?')
                label = heading.split(":")[-1].strip() if ":" in heading else heading
                prompt = (
                    f"A clean, hand-drawn whiteboard sketch of: {sentence}{cartoon_face_instruction}{full_body_instruction}{people_detail_instruction}. "
                    f"Add a minimal heading or label at the very top margin, outside the main drawing area, in a small font: '{label}'. "
                    f"Ensure the main illustration is centered and does not overlap with the text. "
                    f"Minimal, black lines, white background."
                )
            else:
                base_prompt = self._create_sketch_prompt(sentence)
                # Insert cartoon face, full body, and detail instructions before the style requirements if needed
                if involves_people:
                    # Try to insert after the first line (the concept description)
                    lines = base_prompt.split("\n")
                    if len(lines) > 1:
                        lines[0] = lines[0] + cartoon_face_instruction + full_body_instruction + people_detail_instruction
                        prompt = "\n".join(lines)
                    else:
                        prompt = base_prompt + cartoon_face_instruction + full_body_instruction + people_detail_instruction
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
    
    def _create_sketch_prompt(self, sentence: str) -> str:
        """
        Create an optimized prompt for whiteboard sketch style images
        """
        # Clean the sentence for better image generation
        clean_sentence = sentence.strip().rstrip('.!?')
        
        # Create a comprehensive prompt for whiteboard sketch style
        prompt = f"""Create a whiteboard sketch illustration of: {clean_sentence}

Style requirements:
- Hand-drawn whiteboard sketch style
- Clean, simple, educational illustration
- Use only black lines on white background
- No text, words, or letters in the image
- Minimalist and clear visual representation
- Professional educational diagram style
- Focus on the main concept or idea
- Use simple shapes and lines like a real whiteboard drawing
- Whiteboard or chalkboard background
- Sketchy, hand-drawn appearance

The illustration should clearly represent the concept described in the sentence without any text overlay."""

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