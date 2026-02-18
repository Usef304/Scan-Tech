"""
URL Security Scanner Module
"""
import re
import ssl
import socket
import urllib.parse
from datetime import datetime
import requests
from urllib3.exceptions import InsecureRequestWarning
import warnings

# Suppress SSL warnings
warnings.filterwarnings('ignore', category=InsecureRequestWarning)

# Import custom modules
from security.url_analyzer import analyze_url_structure
from security.threat_check import check_url_threats
from security.reputation import check_url_reputation

def scan_url(url):
    """
    Comprehensive URL security scan
    
    Args:
        url (str): URL to scan
    
    Returns:
        dict: Scan results
    """
    results = {
        'url': url,
        'security_score': 100,  # Start with perfect score
        'threats': [],
        'warnings': [],
        'recommendations': [],
        'details': {},
        'timestamp': datetime.now().isoformat(),
        'is_safe': True
    }
    
    try:
        # Step 1: URL Structure Analysis
        structure_analysis = analyze_url_structure(url)
        results['details']['structure'] = structure_analysis
        
        # Adjust score based on structure analysis
        if not structure_analysis['has_https']:
            results['security_score'] -= 20
            results['warnings'].append('Website does not use HTTPS')
            results['recommendations'].append('Use HTTPS for secure communication')
        
        if structure_analysis['is_ip_address']:
            results['security_score'] -= 10
            results['warnings'].append('URL uses IP address instead of domain name')
        
        if structure_analysis['has_suspicious_keywords']:
            results['security_score'] -= 15
            results['warnings'].append('URL contains suspicious keywords')
            results['recommendations'].append('Be cautious with this URL')
        
        # Step 2: Check URL Shorteners
        if structure_analysis['is_url_shortener']:
            results['security_score'] -= 10
            results['warnings'].append('URL is shortened - original destination is hidden')
            results['recommendations'].append('Consider using a URL expander service')
        
        # Step 3: SSL/TLS Check
        ssl_info = check_ssl_certificate(url)
        results['details']['ssl'] = ssl_info
        
        if ssl_info['has_ssl']:
            if ssl_info['days_until_expiry'] < 30:
                results['security_score'] -= 10
                results['warnings'].append(f"SSL certificate expires soon ({ssl_info['days_until_expiry']} days)")
        else:
            results['security_score'] -= 25
            results['threats'].append('No SSL certificate detected')
            results['recommendations'].append('Do not enter sensitive information on this site')
        
        # Step 4: Check Threat Intelligence
        threat_check = check_url_threats(url)
        results['details']['threat_intelligence'] = threat_check
        
        # Process threat results
        for source, result in threat_check.items():
            if result.get('malicious', False):
                results['security_score'] -= 30
                results['threats'].append(f"{source} marks this as malicious")
                results['is_safe'] = False
        
        # Step 5: Check Reputation
        reputation_check = check_url_reputation(url)
        results['details']['reputation'] = reputation_check
        
        if reputation_check.get('domain_age_days', 0) < 30:
            results['security_score'] -= 10
            results['warnings'].append('Domain is very new (less than 30 days)')
        
        if reputation_check.get('risk_score', 0) > 70:
            results['security_score'] -= 20
            results['warnings'].append('Domain has high risk score')
        
        # Step 6: Headers Analysis
        headers_info = analyze_headers(url)
        results['details']['headers'] = headers_info
        
        # Check security headers
        security_headers = headers_info.get('security_headers', {})
        missing_headers = []
        
        if not security_headers.get('strict_transport_security'):
            missing_headers.append('Strict-Transport-Security')
        
        if not security_headers.get('x_frame_options'):
            missing_headers.append('X-Frame-Options')
        
        if not security_headers.get('x_content_type_options'):
            missing_headers.append('X-Content-Type-Options')
        
        if missing_headers:
            results['security_score'] -= 5
            results['warnings'].append(f'Missing security headers: {", ".join(missing_headers)}')
            results['recommendations'].append('Implement missing security headers')
        
        # Step 7: Content Analysis (limited)
        content_info = analyze_content(url)
        results['details']['content'] = content_info
        
        if content_info.get('has_suspicious_patterns', False):
            results['security_score'] -= 10
            results['warnings'].append('Page contains suspicious patterns')
        
        # Step 8: Redirect Analysis
        redirect_info = check_redirects(url)
        results['details']['redirects'] = redirect_info
        
        if redirect_info['redirect_count'] > 2:
            results['security_score'] -= 5
            results['warnings'].append(f'Multiple redirects detected ({redirect_info["redirect_count"]})')
        
        # Step 9: Final Score Calculation
        # Ensure score is within 0-100 range
        results['security_score'] = max(0, min(100, results['security_score']))
        
        # Determine risk level
        if results['security_score'] >= 80:
            results['risk_level'] = 'Low'
        elif results['security_score'] >= 60:
            results['risk_level'] = 'Medium'
        elif results['security_score'] >= 40:
            results['risk_level'] = 'High'
        else:
            results['risk_level'] = 'Critical'
        
        # Add timestamp
        results['scan_completed'] = datetime.now().isoformat()
        
        # Remove duplicate warnings/threats
        results['threats'] = list(set(results['threats']))
        results['warnings'] = list(set(results['warnings']))
        results['recommendations'] = list(set(results['recommendations']))
        
        return results
        
    except Exception as e:
        return {
            'url': url,
            'security_score': 0,
            'error': f'Scan failed: {str(e)}',
            'threats': ['Scan error occurred'],
            'warnings': [],
            'recommendations': ['Try again later'],
            'is_safe': False,
            'risk_level': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }

def check_ssl_certificate(url):
    """Check SSL certificate details"""
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.netloc
        
        # Remove port if present
        if ':' in hostname:
            hostname = hostname.split(':')[0]
        
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                
                # Parse certificate dates
                not_after = cert['notAfter']
                not_before = cert['notBefore']
                
                # Convert to datetime
                from datetime import datetime
                expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                issue_date = datetime.strptime(not_before, '%b %d %H:%M:%S %Y %Z')
                
                # Calculate days until expiry
                days_until_expiry = (expiry_date - datetime.now()).days
                
                return {
                    'has_ssl': True,
                    'issuer': dict(x[0] for x in cert['issuer']),
                    'subject': dict(x[0] for x in cert['subject']),
                    'issued': issue_date.isoformat(),
                    'expires': expiry_date.isoformat(),
                    'days_until_expiry': days_until_expiry,
                    'is_valid': days_until_expiry > 0
                }
    except Exception as e:
        return {
            'has_ssl': False,
            'error': str(e)
        }

def analyze_headers(url):
    """Analyze HTTP headers for security features"""
    try:
        response = requests.get(url, timeout=10, verify=False, allow_redirects=False)
        headers = response.headers
        
        security_headers = {
            'strict_transport_security': 'Strict-Transport-Security' in headers,
            'x_frame_options': 'X-Frame-Options' in headers,
            'x_content_type_options': 'X-Content-Type-Options' in headers,
            'x_xss_protection': 'X-XSS-Protection' in headers,
            'content_security_policy': 'Content-Security-Policy' in headers,
            'referrer_policy': 'Referrer-Policy' in headers
        }
        
        return {
            'status_code': response.status_code,
            'server': headers.get('Server', 'Unknown'),
            'content_type': headers.get('Content-Type', 'Unknown'),
            'security_headers': security_headers,
            'all_headers': dict(headers)
        }
    except Exception as e:
        return {
            'error': str(e),
            'security_headers': {}
        }

def analyze_content(url):
    """Limited content analysis (no JS execution)"""
    try:
        response = requests.get(url, timeout=10, verify=False)
        content = response.text.lower()
        
        suspicious_patterns = []
        
        # Check for common phishing patterns
        patterns = {
            'login_form': ['<form', 'password', 'type="password"'],
            'suspicious_scripts': ['eval(', 'document.write', 'innerhtml'],
            'hidden_elements': ['style="display:none"', 'visibility:hidden'],
            'fake_ssl': ['secure', 'verified', 'protected']
        }
        
        for pattern_name, keywords in patterns.items():
            if all(keyword in content for keyword in keywords[:2]):
                suspicious_patterns.append(pattern_name)
        
        return {
            'content_length': len(content),
            'has_login_form': 'password' in content and '<form' in content,
            'has_suspicious_patterns': len(suspicious_patterns) > 0,
            'suspicious_patterns_found': suspicious_patterns,
            'estimated_risk': 'High' if len(suspicious_patterns) > 2 else 'Medium' if suspicious_patterns else 'Low'
        }
    except Exception as e:
        return {
            'error': str(e),
            'has_suspicious_patterns': False
        }

def check_redirects(url):
    """Check for URL redirects"""
    try:
        response = requests.get(url, timeout=10, verify=False, allow_redirects=True)
        history = response.history
        
        redirect_chain = []
        for resp in history:
            redirect_chain.append({
                'url': resp.url,
                'status_code': resp.status_code,
                'headers': dict(resp.headers)
            })
        
        return {
            'redirect_count': len(history),
            'final_url': response.url,
            'redirect_chain': redirect_chain,
            'has_redirects': len(history) > 0
        }
    except Exception as e:
        return {
            'error': str(e),
            'redirect_count': 0,
            'has_redirects': False
        }