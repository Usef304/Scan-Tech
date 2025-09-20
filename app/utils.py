import base64
from io import BytesIO
import requests
import os
import logging
from PIL import Image
import time

# Configure logging
logger = logging.getLogger(__name__)

try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False
    try:
        import cv2
        import numpy as np
        CV2_AVAILABLE = True
    except ImportError:
        CV2_AVAILABLE = False
        logger.warning("No QR decoding libraries available")

def validate_image(file_stream):
    """Validate that the uploaded file is actually an image using PIL"""
    try:
        # Check file signature using PIL
        file_stream.seek(0)
        file_start = file_stream.read(1024)
        file_stream.seek(0)
        
        # Try to open and verify the image with PIL
        try:
            image = Image.open(BytesIO(file_start))
            image.verify()  # This verifies the image integrity
            return True, None
        except Exception as pil_error:
            # Check common image file signatures as fallback
            image_signatures = {
                b'\xFF\xD8\xFF': 'jpg/jpeg',
                b'\x89PNG\r\n\x1a\n': 'png',
                b'GIF87a': 'gif',
                b'GIF89a': 'gif',
                b'BM': 'bmp',
                b'II*\x00': 'tiff',
                b'MM\x00*': 'tiff',
                b'RIFF': 'webp'
            }
            
            for signature, format_name in image_signatures.items():
                if file_start.startswith(signature):
                    return True, None
            
            return False, f"File is not a valid image: {str(pil_error)}"
            
    except Exception as e:
        logger.error(f"Error validating image: {e}")
        return False, "Error validating image"

def resize_image(image_data, max_size=(800, 600)):
    """Resize image to improve QR decoding performance"""
    try:
        image = Image.open(BytesIO(image_data))
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        # Preserve original format if possible, otherwise use PNG
        image_format = image.format if image.format else 'PNG'
        image.save(output, format=image_format)
        return output.getvalue()
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image_data  # Return original if resize fails

def decode_qr(image_data):
    try:
        # Resize image first for better performance
        image_data = resize_image(image_data)
        
        if PYZBAR_AVAILABLE:
            image = Image.open(BytesIO(image_data))
            decoded_objects = decode(image)
            if decoded_objects:
                return decoded_objects[0].data.decode('utf-8')
        elif CV2_AVAILABLE:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            data, vertices_array, binary_qrcode = detector.detectAndDecode(img)
            if vertices_array is not None:
                return data
        return None
    except Exception as e:
        logger.error(f"Error decoding QR: {e}")
        return None

def analyze_url_with_virustotal(url):
    api_key = os.environ.get('VT_API_KEY')
    
    # Return error if no API key
    if not api_key or api_key == "your_virustotal_api_key_here":
        logger.error("VirusTotal API key not configured")
        return None, "VirusTotal API key not configured. Please add your API key to the .env file."
    
    try:
        # First, try to get existing analysis results
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')
        headers = {"x-apikey": api_key}
        
        response = requests.get(
            f'https://www.virustotal.com/api/v3/urls/{url_id}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 404:
            # URL not found, submit it for analysis
            return submit_url_for_analysis(url, api_key)
        else:
            logger.error(f"VirusTotal API error: {response.status_code}")
            return None, f"VirusTotal API error: {response.status_code}"
            
    except requests.RequestException as e:
        logger.error(f"VirusTotal API request failed: {e}")
        return None, f"VirusTotal API request failed: {str(e)}"

def submit_url_for_analysis(url, api_key):
    """Submit a URL for analysis and wait for results"""
    try:
        headers = {"x-apikey": api_key}
        
        # Submit URL for analysis
        submit_response = requests.post(
            'https://www.virustotal.com/api/v3/urls',
            headers=headers,
            data={'url': url},
            timeout=30
        )
        
        if submit_response.status_code == 200:
            # URL was submitted successfully, get the analysis ID
            analysis_id = submit_response.json()['data']['id']
            
            # Wait for analysis to complete (polling with timeout)
            return wait_for_analysis_results(analysis_id, api_key, url)
        else:
            logger.error(f"Failed to submit URL: {submit_response.status_code}")
            return None, f"Failed to submit URL to VirusTotal: {submit_response.status_code}"
            
    except requests.RequestException as e:
        logger.error(f"URL submission failed: {e}")
        return None, f"URL submission failed: {str(e)}"

def wait_for_analysis_results(analysis_id, api_key, original_url, max_attempts=5, delay=3):
    """Wait for VirusTotal analysis results with polling"""
    headers = {"x-apikey": api_key}
    
    for attempt in range(max_attempts):
        try:
            time.sleep(delay)  # Wait before checking
            
            result_response = requests.get(
                f'https://www.virustotal.com/api/v3/analyses/{analysis_id}',
                headers=headers,
                timeout=30
            )
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                status = result_data['data']['attributes']['status']
                
                if status == 'completed':
                    return result_data, None
                elif status == 'queued':
                    continue  # Still processing
                else:
                    return None, f"Analysis failed with status: {status}"
            
        except requests.RequestException as e:
            logger.error(f"Analysis polling failed: {e}")
            # If polling fails, try to get results by URL ID as fallback
            return get_results_by_url_id(original_url, api_key)
    
    # If we reach here, analysis timed out
    return get_results_by_url_id(original_url, api_key)

def get_results_by_url_id(url, api_key):
    """Get results using URL ID (fallback method)"""
    try:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')
        headers = {"x-apikey": api_key}
        
        response = requests.get(
            f'https://www.virustotal.com/api/v3/urls/{url_id}',
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, "URL analysis timed out and could not retrieve results"
            
    except requests.RequestException as e:
        logger.error(f"Fallback URL lookup failed: {e}")
        return None, "Could not retrieve analysis results after multiple attempts"

def calculate_safety_score(stats):
    """Calculate safety score based on VirusTotal analysis results"""
    # Ensure all stats have values
    malicious = stats.get('malicious', 0) or 0
    suspicious = stats.get('suspicious', 0) or 0
    harmless = stats.get('harmless', 0) or 0
    undetected = stats.get('undetected', 0) or 0
    
    total = malicious + suspicious + harmless + undetected
    
    if total == 0:
        return 0, "No data"
    
    # Calculate actual safety percentage based on results
    if malicious > 0:
        # URL has malicious reports - score based on threat severity
        threat_ratio = (malicious + (suspicious * 0.5)) / total
        safety_percentage = max(0, 100 - (threat_ratio * 100))
        
        if malicious > 5:
            return round(safety_percentage, 1), "Dangerous"
        elif malicious > 2:
            return round(safety_percentage, 1), "Unsafe"
        else:
            return round(safety_percentage, 1), "Risky"
            
    elif suspicious > 0:
        # URL has suspicious reports but no malicious
        suspicion_ratio = suspicious / total
        safety_percentage = max(0, 100 - (suspicion_ratio * 50))  # Less severe than malicious
        
        if suspicious > 3:
            return round(safety_percentage, 1), "Suspicious"
        else:
            return round(safety_percentage, 1), "Caution"
            
    else:
        # No threats found - score based on confidence
        confidence_ratio = harmless / total
        safety_percentage = confidence_ratio * 100
        
        if safety_percentage >= 95:
            return round(safety_percentage, 1), "Very Safe"
        elif safety_percentage >= 80:
            return round(safety_percentage, 1), "Safe"
        elif safety_percentage >= 60:
            return round(safety_percentage, 1), "Mostly Safe"
        else:
            return round(safety_percentage, 1), "Low Confidence"