"""
Image-to-Summary AI Module
Uses Google Gemini 1.5 Flash to read images and generate summaries for manga pages and book covers.
Now Powered by Gemini API via REST.
"""

import os
import base64
import requests
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use Gemini API Key
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_MODEL = 'gemini-3-flash-preview'  # Standard multimodal model

class ImageSummaryAI:
    """Handle image reading and summary generation using Google Gemini API"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or GEMINI_KEY
        self.model = GEMINI_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        self.error_count = 0
        self.last_error = None
        
        if not self.api_key:
            logger.warning("No Gemini API key found")
    
    def encode_image_to_base64(self, image_path):
        """Convert image file to base64"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to encode image: {e}")
    
    def get_image_mime_type(self, image_path):
        """Determine mime type from file extension"""
        ext = Path(image_path).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    def _call_gemini(self, contents):
        """Helper to call Gemini API"""
        if not self.api_key:
            raise Exception("Gemini API key not configured")
            
        url = f"{self.base_url}?key={self.api_key}"
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.4,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 4096,
                "stopSequences": []
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Gemini API Error {response.status_code}: {response.text}")
            response.raise_for_status()
            
        return response.json()

    def summarize_manga_page(self, image_path, max_sentences=5):
        """Summarize a manga page image"""
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        
        try:
            base64_img = self.encode_image_to_base64(image_path)
            mime_type = self.get_image_mime_type(image_path)
            
            prompt = f"""Analyze this manga page and provide a concise summary in {max_sentences} sentences or less. 
            Focus on: 1. Main events happening, 2. Character interactions, 3. Plot progression. Keep it brief."""
            
            contents = [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_img
                        }
                    }
                ]
            }]
            
            result = self._call_gemini(contents)
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to summarize manga page: {e}")
            raise Exception(f"Failed to summarize manga page: {e}")

    def summarize_book_cover(self, image_path):
        """Analyze a book cover image"""
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        
        try:
            base64_img = self.encode_image_to_base64(image_path)
            mime_type = self.get_image_mime_type(image_path)
            
            prompt = """Analyze this book/manga cover and provide:
            1. Visible title or main text
            2. Main visual elements and themes
            3. Apparent genre based on design
            4. Brief description of what the cover conveys
            Keep it concise (3-4 sentences)."""
            
            contents = [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_img
                        }
                    }
                ]
            }]
            
            result = self._call_gemini(contents)
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to summarize cover: {e}")
            raise Exception(f"Failed to summarize cover: {e}")

    def extract_text_from_image(self, image_path):
        """Extract all visible text from an image"""
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        
        try:
            base64_img = self.encode_image_to_base64(image_path)
            mime_type = self.get_image_mime_type(image_path)
            
            prompt = """Extract ALL visible text from this image in order.
            Include dialogue, captions, and text boxes.
            Preserve the reading order as much as possible.
            Format as a clean list."""
            
            contents = [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64_img
                        }
                    }
                ]
            }]
            
            result = self._call_gemini(contents)
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Failed to extract text: {e}")
            raise Exception(f"Failed to extract text: {e}")

    def chat_with_context(self, user_message, context_text=""):
        """Chat with the AI using provided context"""
        try:
            system_prompt = f"""You are a helpful manga reading assistant. 
            Context about the current reading session:
            {context_text}
            
            Answer the user's questions based on this context or general knowledge about anime/manga.
            Keep answers concise and spoiler-free unless asked."""
            
            contents = [{
                "parts": [
                    {"text": system_prompt + "\n\nUser Question: " + user_message}
                ]
            }]
            
            result = self._call_gemini(contents)
            return result['candidates'][0]['content']['parts'][0]['text'].strip()
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise Exception(f"Chat failed: {e}")

if __name__ == "__main__":
    ai = ImageSummaryAI()
    print("✓ ImageSummaryAI module loaded (GEMINI EDITION)")
    print(f"  Model: {ai.model}")
    print(f"  API Key configured: {'Yes' if ai.api_key else 'No'}")
