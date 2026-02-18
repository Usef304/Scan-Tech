"""
Configuration settings for the QR Security Scanner
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # API Keys
    GOOGLE_SAFE_BROWSING_API_KEY = os.getenv('AIzaSyCZRemhcADeT-PyqXWRwrTO1jZ1O_OjPnY', '')
    VIRUSTOTAL_API_KEY = os.getenv('0e66cc9b0bb4cf2766f52f41c3c86b6d34c63a171ade77d3f4f3daa20f1116bf', '')
    PHISHTANK_API_KEY = os.getenv('PHISHTANK_API_KEY', '')
    ABUSEIPDB_API_KEY = os.getenv('4a682ba1ebcf402eb880a9031fe283dd59d59de43d78f74154433eb92e52c8a73d36f3971a95aa94', '')
    
    # API URLs
    GOOGLE_SAFE_BROWSING_URL = 'https://safebrowsing.googleapis.com/v4/threatMatches:find'
    VIRUSTOTAL_URL = 'https://www.virustotal.com/api/v3/urls'
    PHISHTANK_URL = 'http://checkurl.phishtank.com/checkurl/'
    ABUSEIPDB_URL = 'https://api.abuseipdb.com/api/v2/check'
    
    # Timeouts
    REQUEST_TIMEOUT = 10  # seconds
    
    # File upload settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'gif'}
    UPLOAD_FOLDER = 'uploads'
    
    # Database
    DATABASE_PATH = 'scans.db'
    
    # Security thresholds
    SAFE_SCORE_THRESHOLD = 70
    WARNING_SCORE_THRESHOLD = 40
    
    # Domain age threshold (days)
    NEW_DOMAIN_THRESHOLD = 30
    
    # Suspicious keywords
    SUSPICIOUS_KEYWORDS = [
        'login', 'signin', 'verify', 'account', 'banking',
        'paypal', 'password', 'secure', 'update', 'confirm',
        'admin', 'php', 'wp-', 'jquery', 'free', 'win',
        'prize', 'reward', 'urgent', 'immediate'
    ]
    
    # URL shortener services
    URL_SHORTENERS = [
        'bit.ly', 'tinyurl.com', 'goo.gl', 'ow.ly', 'is.gd',
        'buff.ly', 'adf.ly', 'shorte.st', 'cutt.ly', 'shorturl.at',
        'tiny.cc', 'bit.do', 'rebrand.ly', 'bl.ink', 'clickmeter.com'
    ]


    print("GOOGLE_SAFE_BROWSING_API_KEY:", repr(os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')))
    print("VIRUSTOTAL_API_KEY:", repr(os.getenv('VIRUSTOTAL_API_KEY')))
    print("ABUSEIPDB_API_KEY:", repr(os.getenv('ABUSEIPDB_API_KEY')))