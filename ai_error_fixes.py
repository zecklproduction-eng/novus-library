"""
AI Error Fixes for LiteLLM Issues
This module provides error handling and fallbacks for AI functionality
"""

import os
import traceback
import logging
from functools import wraps
from flask import jsonify, current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_ai_call(fallback_response=None, log_errors=True):
    """
    Decorator to safely handle AI API calls with fallbacks
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"AI function {func.__name__} failed: {str(e)}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Return fallback response if provided
                if fallback_response is not None:
                    return fallback_response
                
                # Default error response
                return {
                    'error': 'AI service temporarily unavailable',
                    'status': 'error',
                    'details': str(e) if current_app.debug else 'Service temporarily down'
                }
        return wrapper
    return decorator

def check_ai_service_status():
    """
    Check if AI services are properly configured
    """
    openai_key = os.environ.get('OPENAI_API_KEY')
    use_openai = os.environ.get('USE_OPENAI', '0') in ('1', 'true', 'True')
    
    status = {
        'openai_configured': bool(openai_key),
        'openai_enabled': use_openai,
        'ai_available': bool(openai_key and use_openai)
    }
    
    return status

def get_ai_fallback_message():
    """
    Get a user-friendly fallback message for AI features
    """
    return "AI summary generation is temporarily unavailable. Please try again later."

def create_safe_ai_response(summary_text=None, **kwargs):
    """
    Create a standardized AI response with error handling
    """
    response = {
        'status': 'success',
        'cached': kwargs.get('cached', False),
        'model': kwargs.get('model', 'unknown')
    }
    
    if summary_text:
        response['summary'] = summary_text
    else:
        response['summary'] = get_ai_fallback_message()
    
    if 'cached_at' in kwargs:
        response['cached_at'] = kwargs['cached_at']
    
    if 'error' in kwargs:
        response['error'] = kwargs['error']
        response['status'] = 'error'
    
    return response

# Configuration for different AI services
AI_SERVICE_CONFIG = {
    'openai': {
        'enabled': lambda: os.environ.get('USE_OPENAI', '0') in ('1', 'true', 'True'),
        'api_key': lambda: os.environ.get('OPENAI_API_KEY'),
        'model': lambda: os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
        'timeout': 10
    },
    'fallback_models': {
        'primary': 'gpt-3.5-turbo',
        'backup': 'gpt-3.5-turbo'  # Same model as fallback for now
    }
}

def validate_ai_request(data, required_fields=None):
    """
    Validate AI request data
    """
    if not data:
        return False, "No data provided"
    
    if required_fields:
        missing = [field for field in required_fields if field not in data or not data.get(field)]
        if missing:
            return False, f"Missing required fields: {', '.join(missing)}"
    
    return True, "Valid"

def handle_ai_service_error(error, service_name='OpenAI'):
    """
    Handle different types of AI service errors
    """
    error_str = str(error).lower()
    
    # Check for specific error types
    if 'rate limit' in error_str or '429' in error_str:
        return {
            'error': 'Rate limit exceeded',
            'retry_after': 'Please wait a moment before trying again'
        }
    elif 'invalid api key' in error_str or '401' in error_str:
        return {
            'error': 'Invalid API configuration',
            'retry_after': 'Please check API key configuration'
        }
    elif 'bad request' in error_str or '400' in error_str:
        return {
            'error': 'Invalid request format',
            'retry_after': 'Please check your request parameters'
        }
    elif 'timeout' in error_str or '503' in error_str:
        return {
            'error': 'Service temporarily unavailable',
            'retry_after': 'Please try again in a few moments'
        }
    else:
        return {
            'error': f'{service_name} service error',
            'retry_after': 'Please try again later'
        }

# Monkey patch for better error handling in existing AI functions
def patch_ai_functions():
    """
    Apply error handling patches to existing AI functions
    """
    try:
        from image_summary_ai import ImageSummaryAI
        
        # Store original methods
        original_init = ImageSummaryAI.__init__
        original_summarize_manga = ImageSummaryAI.summarize_manga_page
        original_summarize_cover = ImageSummaryAI.summarize_book_cover
        original_extract_text = ImageSummaryAI.extract_text_from_image
        
        # Enhanced __init__ with better error handling
        def enhanced_init(self, api_key=None):
            try:
                original_init(self, api_key)
                self.error_count = 0
                self.last_error = None
            except Exception as e:
                logger.error(f"Failed to initialize ImageSummaryAI: {e}")
                self.api_key = None
                self.model = 'fallback'
                self.error_count = 1
                self.last_error = str(e)
        
        # Enhanced methods with error handling
        def enhanced_summarize_manga(self, image_path, max_sentences=5):
            try:
                result = original_summarize_manga(self, image_path, max_sentences)
                self.error_count = 0
                return result
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                logger.error(f"ImageSummaryAI.summarize_manga_page failed: {e}")
                raise
        
        def enhanced_summarize_cover(self, image_path):
            try:
                result = original_summarize_cover(self, image_path)
                self.error_count = 0
                return result
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                logger.error(f"ImageSummaryAI.summarize_book_cover failed: {e}")
                raise
        
        def enhanced_extract_text(self, image_path):
            try:
                result = original_extract_text(self, image_path)
                self.error_count = 0
                return result
            except Exception as e:
                self.error_count += 1
                self.last_error = str(e)
                logger.error(f"ImageSummaryAI.extract_text_from_image failed: {e}")
                raise
        
        # Apply patches
        ImageSummaryAI.__init__ = enhanced_init
        ImageSummaryAI.summarize_manga_page = enhanced_summarize_manga
        ImageSummaryAI.summarize_book_cover = enhanced_summarize_cover
        ImageSummaryAI.extract_text_from_image = enhanced_extract_text
        
        logger.info("Successfully patched ImageSummaryAI with error handling")
        
    except ImportError:
        logger.warning("ImageSummaryAI not found, skipping patches")
    except Exception as e:
        logger.error(f"Failed to patch AI functions: {e}")

if __name__ == "__main__":
    # Test the error handling
    print("AI Error Fixes Module")
    print("===================")
    print(f"Service Status: {check_ai_service_status()}")
    print(f"Fallback Message: {get_ai_fallback_message()}")
    
    # Test patching
    patch_ai_functions()
    print("Error handling patches applied")
