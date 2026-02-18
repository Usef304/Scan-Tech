"""
QR Code Security Scanner - Main Application
"""
import os
from dotenv import load_dotenv
load_dotenv()
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename




# Import custom modules
from scanner.qr_extractor import extract_qr_from_image
from scanner.url_scanner import scan_url
from database.db_handler import (
    init_db, save_scan_result, get_scan_result, 
    get_recent_scans, get_stats
)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
app.config['REPORT_FOLDER'] = 'reports'

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['REPORT_FOLDER'], exist_ok=True)

# Initialize database
init_db()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Render home page"""
    stats = get_stats()
    recent_scans = get_recent_scans(limit=5)
    return render_template('index.html', stats=stats, recent_scans=recent_scans)

@app.route('/scan')
def scan_page():
    """Render QR scan page"""
    return render_template('scan.html')

@app.route('/manual')
def manual_page():
    """Render manual URL entry page"""
    return render_template('manual.html')

@app.route('/report/<scan_id>')
def report_page(scan_id):
    """Render report page"""
    result = get_scan_result(scan_id)
    if not result:
        return render_template('error.html', error="Report not found"), 404
    return render_template('report.html', report=result)

@app.route('/api/scan_qr', methods=['POST'])
def api_scan_qr():
    """API endpoint to scan QR code from image"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file
        if not allowed_file(file.filename):
            return jsonify({
                'success': False, 
                'error': 'File type not allowed. Allowed types: PNG, JPG, JPEG, BMP, GIF'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract QR code content
        result = extract_qr_from_image(filepath)
        
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to extract QR code')
            }), 400
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Save initial result
        initial_data = {
            'scan_id': scan_id,
            'content': result['content'],
            'content_type': result.get('type', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'source': 'qr_upload'
        }
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'content': result['content'],
            'type': result.get('type', 'text'),
            'message': 'QR code scanned successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/check_url', methods=['POST'])
def api_check_url():
    """API endpoint to check URL security"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        url = data['url'].strip()
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        
        # Scan the URL
        scan_result = scan_url(url)
        
        # Save to database
        db_result = {
            'scan_id': scan_id,
            'url': url,
            'result': scan_result,
            'timestamp': datetime.now().isoformat(),
            'source': 'manual_entry'
        }
        save_scan_result(db_result)
        
        return jsonify({
            'success': True,
            'scan_id': scan_id,
            'url': url,
            'result': scan_result,
            'message': 'URL scanned successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/report/<scan_id>', methods=['GET'])
def api_get_report(scan_id):
    """API endpoint to get scan report"""
    result = get_scan_result(scan_id)
    
    if not result:
        return jsonify({'success': False, 'error': 'Report not found'}), 404
    
    return jsonify({
        'success': True,
        'report': result
    })

@app.route('/api/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'QR Security Scanner',
        'version': '1.0.0'
    })

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get statistics"""
    stats = get_stats()
    recent_scans = get_recent_scans(limit=10)
    
    return jsonify({
        'success': True,
        'stats': stats,
        'recent_scans': recent_scans
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    print("=" * 50)
    print("QR Code Security Scanner")
    print("=" * 50)
    print(f"Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)