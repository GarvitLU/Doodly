import openai
import os
import re
from typing import List

class ScriptService:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def generate_script(self, topic: str, style: str = "educational") -> str:
        """
        Generate a detailed, step-by-step educational script for a whiteboard animation video about the topic.
        """
        try:
            system_prompt = f"""
You are an expert data structures and algorithms (DSA) educator. 
Write a clear, step-by-step, educational script for a whiteboard animation video about the topic: "{topic}".

Requirements:
- Do NOT include a generic introduction or conclusion.
- Each sentence should explain a specific concept, property, or operation about arrays in DSA.
- Each sentence should be self-contained, visualizable, and suitable for a single whiteboard sketch.
- Use simple, direct language.
- Cover: what arrays are, how they work, how to access elements, indexing, memory layout, common operations (insert, delete, traverse), and real-world examples.
- Do NOT mention "in this video" or "we will learn".
- Number each step or concept if possible.

Return only the script text, no additional formatting or explanations.
"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create a detailed, step-by-step script about: {topic}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            script = response.choices[0].message.content.strip()
            print("\n[ScriptService] Generated script for topic:", topic)
            print("[ScriptService] Script:\n", script)
            return script
            
        except Exception as e:
            print(f"Error generating script: {str(e)}")
            # Fallback script
            return f"1. An array is a collection of elements stored in contiguous memory locations.\n2. Each element in an array can be accessed using its index, starting from zero.\n3. Arrays allow fast access to any element using its index.\n4. Inserting an element at a specific position may require shifting other elements.\n5. Deleting an element also involves shifting elements to fill the gap.\n6. Traversing an array means visiting each element one by one.\n7. Arrays are used to store lists of data, such as student scores or daily temperatures.\n8. The size of an array is fixed at the time of creation."
    
    def split_script_into_sentences(self, script: str) -> List[str]:
        """
        Split the script into individual sentences for image generation
        """
        # Split by common sentence endings, but be careful with abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', script)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 5:  # Filter out very short fragments
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def create_image_prompt(self, sentence: str) -> str:
        """
        Create an optimized prompt for image generation from a sentence
        """
        # Remove common words that don't add visual value
        visual_words = sentence.lower()
        
        # Add whiteboard sketch style keywords
        prompt = f"whiteboard sketch style illustration of {visual_words}, hand-drawn, educational, clean, simple, no text, only visual elements"
        
        return prompt 