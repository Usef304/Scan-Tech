"""
Threat Intelligence Checking Module
"""
import os
import requests
import json
import urllib.parse
import socket
from datetime import datetime

# API URLs (can stay here)
GOOGLE_SAFE_BROWSING_URL = 'https://safebrowsing.googleapis.com/v4/threatMatches:find'
VIRUSTOTAL_URL = 'https://www.virustotal.com/api/v3/urls'
PHISHTANK_URL = 'http://checkurl.phishtank.com/checkurl/'
ABUSEIPDB_URL = 'https://api.abuseipdb.com/api/v2/check'

REQUEST_TIMEOUT = 10  # seconds

def check_google_safe_browsing(url):
    """Check URL against Google Safe Browsing API"""
    api_key = os.getenv('GOOGLE_SAFE_BROWSING_API_KEY')
    if not api_key:
        return {
            'enabled': False,
            'error': 'API key not configured',
            'malicious': False
        }
    
    try:
        api_url = f"{GOOGLE_SAFE_BROWSING_URL}?key={api_key}"
        payload = {
            "client": {"clientId": "qr-security-scanner", "clientVersion": "1.0.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}]
            }
        }
        headers = {'Content-Type': 'application/json'}
        response = requests.post(api_url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            has_matches = 'matches' in result and len(result['matches']) > 0
            if has_matches:
                threats = [match['threatType'] for match in result['matches']]
                return {
                    'enabled': True,
                    'malicious': True,
                    'threats': threats,
                    'match_count': len(result['matches']),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'enabled': True,
                    'malicious': False,
                    'threats': [],
                    'match_count': 0,
                    'timestamp': datetime.now().isoformat()
                }
        else:
            return {
                'enabled': True,
                'error': f'API error: {response.status_code}',
                'malicious': False,
                'response_code': response.status_code
            }
    except Exception as e:
        return {
            'enabled': True,
            'error': str(e),
            'malicious': False
        }

def check_virustotal(url):
    """Check URL against VirusTotal API"""
    api_key = os.getenv('VIRUSTOTAL_API_KEY')
    if not api_key:
        return {
            'enabled': False,
            'error': 'API key not configured',
            'malicious': False
        }
    
    try:
        headers = {'x-apikey': api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
        # Submit URL
        submit_response = requests.post(VIRUSTOTAL_URL, headers=headers, data={'url': url}, timeout=REQUEST_TIMEOUT)
        if submit_response.status_code == 200:
            result = submit_response.json()
            if 'data' in result and 'id' in result['data']:
                analysis_id = result['data']['id']
                analysis_url = f"{VIRUSTOTAL_URL}/{analysis_id}"
                analysis_response = requests.get(analysis_url, headers=headers, timeout=REQUEST_TIMEOUT)
                if analysis_response.status_code == 200:
                    analysis_result = analysis_response.json()
                    if 'data' in analysis_result and 'attributes' in analysis_result['data']:
                        stats = analysis_result['data']['attributes'].get('stats', {})
                        malicious_count = stats.get('malicious', 0)
                        suspicious_count = stats.get('suspicious', 0)
                        is_malicious = malicious_count > 0
                        total_engines = stats.get('harmless', 0) + stats.get('malicious', 0) + \
                                       stats.get('suspicious', 0) + stats.get('undetected', 0)
                        return {
                            'enabled': True,
                            'malicious': is_malicious,
                            'malicious_count': malicious_count,
                            'suspicious_count': suspicious_count,
                            'total_engines': total_engines,
                            'stats': stats,
                            'timestamp': datetime.now().isoformat()
                        }
        return {
            'enabled': True,
            'error': 'Could not retrieve analysis results',
            'malicious': False
        }
    except Exception as e:
        return {
            'enabled': True,
            'error': str(e),
            'malicious': False
        }

def check_phishtank(url):
    """Check URL against PhishTank API"""
    api_key = os.getenv('PHISHTANK_API_KEY')
    if not api_key:
        return {
            'enabled': False,
            'error': 'API key not configured',
            'malicious': False
        }
    
    try:
        data = {'url': url, 'format': 'json', 'app_key': api_key}
        response = requests.post(PHISHTANK_URL, data=data, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            if 'results' in result:
                phish_info = result['results']
                is_phish = phish_info.get('in_database', False)
                return {
                    'enabled': True,
                    'malicious': is_phish,
                    'in_database': is_phish,
                    'verified': phish_info.get('verified', False),
                    'verified_at': phish_info.get('verified_at'),
                    'timestamp': datetime.now().isoformat()
                }
        return {
            'enabled': True,
            'error': 'Could not retrieve results',
            'malicious': False
        }
    except Exception as e:
        return {
            'enabled': True,
            'error': str(e),
            'malicious': False
        }

def check_abuseipdb(ip_address):
    """Check IP address against AbuseIPDB"""
    api_key = os.getenv('ABUSEIPDB_API_KEY')
    if not api_key:
        return {
            'enabled': False,
            'error': 'API key not configured',
            'malicious': False
        }
    
    try:
        headers = {'Key': api_key, 'Accept': 'application/json'}
        params = {'ipAddress': ip_address, 'maxAgeInDays': 90}
        response = requests.get(ABUSEIPDB_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            result = response.json()
            if 'data' in result:
                data = result['data']
                abuse_score = data.get('abuseConfidenceScore', 0)
                is_malicious = abuse_score > 50
                return {
                    'enabled': True,
                    'malicious': is_malicious,
                    'abuse_score': abuse_score,
                    'total_reports': data.get('totalReports', 0),
                    'country': data.get('countryCode'),
                    'isp': data.get('isp'),
                    'usage_type': data.get('usageType'),
                    'last_reported': data.get('lastReportedAt'),
                    'timestamp': datetime.now().isoformat()
                }
        return {
            'enabled': True,
            'error': 'Could not retrieve results',
            'malicious': False
        }
    except Exception as e:
        return {
            'enabled': True,
            'error': str(e),
            'malicious': False
        }

def check_url_threats(url):
    """Comprehensive threat check using all available services"""
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.split(':')[0]

    results = {
        'google_safe_browsing': check_google_safe_browsing(url),
        'virustotal': check_virustotal(url),
        'phishtank': check_phishtank(url)
    }

    # Try to get IP for AbuseIPDB check
    try:
        ip_address = socket.gethostbyname(domain)
        results['abuseipdb'] = check_abuseipdb(ip_address)
    except:
        results['abuseipdb'] = {
            'enabled': False,
            'error': 'Could not resolve IP address',
            'malicious': False
        }

    # Calculate overall malicious status
    malicious_sources = []
    for source, result in results.items():
        if result.get('enabled', False) and result.get('malicious', False):
            malicious_sources.append(source)

    results['overall'] = {
        'is_malicious': len(malicious_sources) > 0,
        'malicious_sources': malicious_sources,
        'malicious_count': len(malicious_sources),
        'total_checks': len(results),
        'timestamp': datetime.now().isoformat()
    }

    return results