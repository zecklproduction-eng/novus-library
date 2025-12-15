"""
Image-to-Summary AI Module
Uses GPT-4 Vision to read images and generate summaries for manga pages and book covers
"""

import os
import base64
import requests
import json
from pathlib import Path

OPENAI_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4-turbo')

class ImageSummaryAI:
    """Handle image reading and summary generation using GPT-4 Vision"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or OPENAI_KEY
        self.model = OPENAI_MODEL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def encode_image_to_base64(self, image_path):
        """Convert image file to base64"""
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to encode image: {e}")
    
    def get_image_media_type(self, image_path):
        """Determine media type from file extension"""
        ext = Path(image_path).suffix.lower()
        media_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return media_types.get(ext, 'image/jpeg')
    
    def summarize_manga_page(self, image_path, max_sentences=5):
        """
        Summarize a manga page image
        Extracts story content and key events
        """
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            base64_image = self.encode_image_to_base64(image_path)
            media_type = self.get_image_media_type(image_path)
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:{media_type};base64,{base64_image}'
                                }
                            },
                            {
                                'type': 'text',
                                'text': f"""Analyze this manga page and provide a concise summary in {max_sentences} sentences or less. 
                                Focus on:
                                1. Main events happening
                                2. Character interactions
                                3. Plot progression
                                Keep it brief and clear."""
                            }
                        ]
                    }
                ],
                'max_tokens': 300
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content'].strip()
            return None
            
        except Exception as e:
            raise Exception(f"Failed to summarize manga page: {e}")
    
    def summarize_book_cover(self, image_path):
        """
        Analyze a book cover image
        Extracts title, author, genre hints from cover design
        """
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            base64_image = self.encode_image_to_base64(image_path)
            media_type = self.get_image_media_type(image_path)
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:{media_type};base64,{base64_image}'
                                }
                            },
                            {
                                'type': 'text',
                                'text': """Analyze this book/manga cover and provide:
                                1. Visible title or main text
                                2. Main visual elements and themes
                                3. Apparent genre based on design
                                4. Brief description of what the cover conveys
                                Keep it concise (3-4 sentences)."""
                            }
                        ]
                    }
                ],
                'max_tokens': 250
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content'].strip()
            return None
            
        except Exception as e:
            raise Exception(f"Failed to summarize book cover: {e}")
    
    def extract_text_from_image(self, image_path):
        """
        Extract all visible text from an image
        Useful for manga dialogue and text boxes
        """
        if not os.path.exists(image_path):
            raise Exception(f"Image not found: {image_path}")
        
        if not self.api_key:
            raise Exception("OpenAI API key not configured")
        
        try:
            base64_image = self.encode_image_to_base64(image_path)
            media_type = self.get_image_media_type(image_path)
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:{media_type};base64,{base64_image}'
                                }
                            },
                            {
                                'type': 'text',
                                'text': """Extract ALL visible text from this image in order.
                                Include dialogue, captions, and text boxes.
                                Preserve the reading order as much as possible.
                                Format as a clean list."""
                            }
                        ]
                    }
                ],
                'max_tokens': 1000
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content'].strip()
            return None
            
        except Exception as e:
            raise Exception(f"Failed to extract text from image: {e}")


# Test the module
if __name__ == "__main__":
    ai = ImageSummaryAI()
    print("✓ ImageSummaryAI module loaded successfully")
    print(f"  Model: {ai.model}")
    print(f"  API Key configured: {'Yes' if ai.api_key else 'No'}")
