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

            # Intelligent analysis of script content
            involves_people = self._analyze_script_content(sentence)
            print(f"[IdeogramImageService] Script analysis - involves_people: {involves_people}")

            # Determine orientation for prompt optimization
            is_portrait = size == "1024x1024" or size == "1024x1536"
            is_landscape = size == "1536x1024"

            # Generate the enhanced prompt
            prompt = self._create_enhanced_sketch_prompt(sentence, involves_people, is_portrait, is_landscape)
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

    def _analyze_script_content(self, sentence: str) -> bool:
        """
        Intelligently analyze script content to determine if people/characters are actually needed.
        Focuses on context rather than just keyword matching.
        """
        sentence_lower = sentence.lower().strip()
        
        # Programming/technical concepts that should NOT have people
        programming_keywords = [
            "array", "list", "dictionary", "set", "tuple", "stack", "queue", "tree", "graph", "hash", "sort", "search",
            "algorithm", "function", "method", "class", "object", "variable", "loop", "condition", "recursion", "iteration",
            "insert", "delete", "update", "access", "traverse", "merge", "split", "filter", "map", "reduce", "index",
            "pointer", "reference", "memory", "data structure", "data type", "syntax", "compiler", "interpreter", "debug",
            "exception", "error handling", "validation", "parsing", "tokenization", "optimization", "complexity", "big o",
            "binary", "hexadecimal", "decimal", "floating point", "integer", "string", "boolean", "null", "undefined"
        ]
        
        # Educational/process concepts that should focus on content
        educational_keywords = [
            "process", "step", "procedure", "workflow", "system", "architecture", "design", "pattern", "framework",
            "library", "module", "package", "dependency", "interface", "api", "database", "schema", "query", "sql",
            "network", "protocol", "http", "tcp", "udp", "socket", "server", "client", "request", "response", "json",
            "xml", "html", "css", "javascript", "python", "java", "c++", "c#", "php", "ruby", "go", "rust", "swift",
            "react", "angular", "vue", "node", "express", "django", "flask", "spring", "dotnet", "docker", "kubernetes",
            "git", "version control", "branch", "merge", "commit", "push", "pull", "repository", "deployment", "ci/cd"
        ]
        
        # Check if sentence is about programming/technical concepts
        has_programming_content = any(keyword in sentence_lower for keyword in programming_keywords)
        has_educational_content = any(keyword in sentence_lower for keyword in educational_keywords)
        
        # People-related keywords that might actually need human figures
        people_action_keywords = [
            "you need to", "you should", "you can", "you will", "you must", "you have to",
            "the user", "the developer", "the programmer", "the student", "the teacher",
            "someone", "anyone", "everyone", "nobody", "somebody", "anybody", "everybody"
        ]
        
        # Check if sentence actually involves people doing actions
        has_people_actions = any(keyword in sentence_lower for keyword in people_action_keywords)
        
        # Decision logic:
        # 1. If it's clearly about programming/technical concepts -> NO people (focus on content)
        # 2. If it's about educational processes -> NO people (focus on diagrams)
        # 3. If it mentions people doing specific actions -> MAYBE include 1 small figure
        # 4. Otherwise -> NO people (default to content focus)
        
        if has_programming_content or has_educational_content:
            print(f"[IdeogramImageService] Technical/educational content detected - focusing on concepts")
            return False
        elif has_people_actions:
            print(f"[IdeogramImageService] People actions detected - may include 1 small figure")
            return True
        else:
            print(f"[IdeogramImageService] Default content - focusing on concepts")
            return False

    def _map_size_to_aspect_ratio(self, size: str) -> str:
        """
        Map image size to Ideogram aspect ratio format
        """
        size_map = {
            "1024x1024": "ASPECT_1_1",      # Square (Portrait)
            "1536x1024": "ASPECT_3_2",      # Landscape
            "1024x1536": "ASPECT_2_3",      # Portrait (tall)
            "1024x1024": "ASPECT_1_1"       # Square (Portrait) - duplicate removed
        }
        
        aspect_ratio = size_map.get(size, "ASPECT_1_1")
        print(f"[IdeogramImageService] Size: {size} -> Aspect Ratio: {aspect_ratio}")
        
        # Log orientation info
        if size == "1024x1024":
            print(f"[IdeogramImageService] Using PORTRAIT orientation (1:1 square)")
        elif size == "1536x1024":
            print(f"[IdeogramImageService] Using LANDSCAPE orientation (3:2)")
        elif size == "1024x1536":
            print(f"[IdeogramImageService] Using PORTRAIT orientation (2:3 tall)")
        else:
            print(f"[IdeogramImageService] Using default SQUARE orientation (1:1)")
            
        return aspect_ratio

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

    def _create_enhanced_sketch_prompt(self, sentence: str, involves_people: bool, is_portrait: bool = False, is_landscape: bool = False) -> str:
        """
        Create an optimized prompt for whiteboard sketch style images with focus on educational content.
        Now orientation-aware for better layout.
        """
        clean_sentence = sentence.strip().rstrip('.!?')
        
        # Orientation-specific layout guidance
        if is_portrait:
            layout_guidance = "Use vertical layout with content stacked from top to bottom. Center the main concept prominently."
        elif is_landscape:
            layout_guidance = "Use horizontal layout with content spread across the width. Place main concept in the center with supporting elements on sides."
        else:
            layout_guidance = "Use balanced layout with content centered in the frame."
        
        # Example: "Arrays are collections of data" -> focus on array diagrams, not people
        # Example: "When you insert an element" -> focus on insertion process, not faces
        
        if involves_people:
            prompt = f'''A detailed, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Requirements:
- Focus 80% on the main concept, process, or topic being explained
- Include only 1 small, simple human figure (stick figure style, no detailed faces) to show interaction/learning
- Show clear diagrams, charts, flowcharts, or visual representations of the concept
- Add minimal, handwritten-style text: only 1-2 key labels or terms (NO heading or title)
- Clean, bold black lines on a pure white background (no color)
- Professional, educational composition
- Emphasize the educational content over human elements
- Use simple, clear visual metaphors to explain the concept
- If explaining programming concepts, show code structures, data flow, or algorithms
- If explaining processes, show step-by-step diagrams or flowcharts
- Make the concept the hero of the illustration
- Layout: {layout_guidance}'''
        else:
            prompt = f'''A detailed, hand-drawn whiteboard sketch illustration of: {clean_sentence}

Requirements:
- Focus entirely on the concept, object, process, or system being explained
- Include relevant diagrams, flowcharts, data structures, or visual representations
- Add minimal, handwritten-style text: only 1-2 key labels or terms (NO heading or title)
- Clean, bold black lines on a pure white background (no color)
- Professional, educational composition
- Use clear visual metaphors and examples
- If explaining programming concepts, show code structures, data flow, or algorithms
- If explaining processes, show step-by-step diagrams or flowcharts
- Make the concept easy to understand visually
- NO human figures or faces unless explicitly mentioned in the concept
- Layout: {layout_guidance}'''
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