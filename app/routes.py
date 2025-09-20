from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.utils import decode_qr, analyze_url_with_virustotal, calculate_safety_score, validate_image
from app.forms import QRUploadForm, QRDataForm
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/scan')
def scan():
    # Create form instances for the scan page
    upload_form = QRUploadForm()
    data_form = QRDataForm()
    return render_template('scan.html', upload_form=upload_form, data_form=data_form)

@bp.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

def analyze_url(url):
    """Shared function for URL analysis"""
    # Call VirusTotal directly (no caching for now)
    result, error = analyze_url_with_virustotal(url)
    
    if error:
        return None, error
        
    if result and 'data' in result and 'attributes' in result['data']:
        return result, None
    else:
        return None, "Unexpected response format from security service"

# ... keep the rest of the routes exactly the same ...
@bp.route('/analyze', methods=['POST'])
def analyze_qr():
    form = QRUploadForm()
    
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
        return redirect(url_for('main.scan'))
    
    try:
        file = form.file.data
        image_data = file.read()
        
        # Validate the file is actually an image
        is_valid, error_msg = validate_image(file)
        if not is_valid:
            flash(error_msg, 'error')
            return redirect(url_for('main.scan'))
        
        url = decode_qr(image_data)
        
        if not url:
            flash('Could not decode QR code. Please ensure it is a valid QR code image.', 'error')
            return redirect(url_for('main.scan'))
        
        result, error = analyze_url_with_virustotal(url)
        
        if error:
            flash(f'Error analyzing URL: {error}', 'error')
            return redirect(url_for('main.scan'))
        
        if not result or 'data' not in result or 'attributes' not in result['data']:
            flash('Unexpected response format from security service.', 'error')
            return redirect(url_for('main.scan'))
        
        attributes = result['data']['attributes']
        stats = attributes.get('last_analysis_stats', {})
        
        safety_score, verdict = calculate_safety_score(stats)
        
        return render_template('result.html', 
                              url=url, 
                              safety_score=safety_score, 
                              verdict=verdict,
                              stats=stats)
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.scan'))

@bp.route('/analyze-qr-data', methods=['POST'])
def analyze_qr_data():
    form = QRDataForm()
    
    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'error')
        return redirect(url_for('main.scan'))
    
    qr_data = form.qr_data.data
    
    try:
        if qr_data.startswith(('http://', 'https://')):
            result, error = analyze_url_with_virustotal(qr_data)
            
            if error:
                flash(f'Error analyzing URL: {error}', 'error')
                return redirect(url_for('main.scan'))
            
            if not result or 'data' not in result or 'attributes' not in result['data']:
                flash('Unexpected response format from security service.', 'error')
                return redirect(url_for('main.scan'))
            
            attributes = result['data']['attributes']
            stats = attributes.get('last_analysis_stats', {})
            
            safety_score, verdict = calculate_safety_score(stats)
            
            return render_template('result.html', 
                                  url=qr_data, 
                                  safety_score=safety_score, 
                                  verdict=verdict,
                                  stats=stats)
        else:
            # For non-URL QR codes, show basic info
            return render_template('result.html', 
                                  url=qr_data, 
                                  safety_score=100, 
                                  verdict="Safe",
                                  stats={'malicious': 0, 'suspicious': 0, 'harmless': 1, 'undetected': 0})
            
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('main.scan'))