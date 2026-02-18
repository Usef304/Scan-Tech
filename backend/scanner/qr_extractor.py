"""
QR Code Extractor Module
"""
import os
import json
from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol

def extract_qr_from_image(image_path):
    """
    Extract QR code content from image file
    
    Args:
        image_path (str): Path to the image file
    
    Returns:
        dict: Extraction result with success flag and content
    """
    try:
        # Check if file exists
        if not os.path.exists(image_path):
            return {
                'success': False,
                'error': 'File not found',
                'content': None
            }
        
        # Open image with PIL
        img = Image.open(image_path)
        
        # Decode QR codes
        decoded_objects = decode(img, symbols=[ZBarSymbol.QRCODE])
        
        if decoded_objects:
            content = decoded_objects[0].data.decode('utf-8')
            return {
                'success': True,
                'content': content,
                'type': 'qr_code',
                'format': 'PIL',
                'count': len(decoded_objects)
            }
        else:
            # Try to enhance image if no QR found
            try:
                # Convert to grayscale and increase contrast
                img_gray = img.convert('L')
                decoded_objects = decode(img_gray, symbols=[ZBarSymbol.QRCODE])
                
                if decoded_objects:
                    content = decoded_objects[0].data.decode('utf-8')
                    return {
                        'success': True,
                        'content': content,
                        'type': 'qr_code',
                        'format': 'PIL_enhanced',
                        'count': len(decoded_objects)
                    }
            except:
                pass
            
            return {
                'success': False,
                'error': 'No QR code found in image',
                'content': None,
                'type': 'none'
            }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Extraction error: {str(e)}',
            'content': None
        }

def extract_qr_from_camera_frame(frame):
    """
    Extract QR code from camera frame (stub function - uses frontend jsQR instead)
    
    Args:
        frame: Camera frame (not used in backend)
    
    Returns:
        dict: Extraction result
    """
    # This function is a stub - actual camera scanning is done in frontend with jsQR
    return {
        'success': False,
        'error': 'Camera scanning is handled in frontend using jsQR',
        'content': None
    }

def validate_content(content):
    """
    Validate extracted content and determine type
    
    Args:
        content (str): Extracted content
    
    Returns:
        dict: Validation result
    """
    if not content:
        return {
            'valid': False,
            'type': 'empty',
            'message': 'Empty content'
        }
    
    # Check if it's a URL
    if content.startswith(('http://', 'https://', 'www.')):
        return {
            'valid': True,
            'type': 'url',
            'message': 'URL detected'
        }
    
    # Check if it's text
    if len(content) < 1000:  # Arbitrary limit for text
        return {
            'valid': True,
            'type': 'text',
            'message': 'Text content detected'
        }
    
    # Check if it's JSON
    if content.strip().startswith('{') or content.strip().startswith('['):
        try:
            json.loads(content)
            return {
                'valid': True,
                'type': 'json',
                'message': 'JSON content detected'
            }
        except:
            pass
    
    # Default to text
    return {
        'valid': True,
        'type': 'unknown',
        'message': 'Unknown content type'
    }

def scan_image_file(file_path):
    """
    Convenience function to scan QR from image file
    
    Args:
        file_path (str): Path to image file
    
    Returns:
        str: Extracted content or None
    """
    result = extract_qr_from_image(file_path)
    if result['success']:
        return result['content']
    return None