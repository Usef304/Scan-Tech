"""
URL Structure Analyzer
"""
import re
import urllib.parse
import ipaddress
from datetime import datetime
import whois
import validators
from config import Config

def analyze_url_structure(url):
    """
    Analyze URL structure for suspicious patterns
    
    Args:
        url (str): URL to analyze
    
    Returns:
        dict: Analysis results
    """
    try:
        parsed = urllib.parse.urlparse(url)
        
        # Basic components
        scheme = parsed.scheme
        netloc = parsed.netloc
        path = parsed.path
        query = parsed.query
        fragment = parsed.fragment
        
        # Check if it's an IP address
        is_ip = False
        ip_type = None
        try:
            ipaddress.ip_address(netloc.split(':')[0])
            is_ip = True
            ip_type = 'IPv4'
        except:
            try:
                ipaddress.IPv6Address(netloc.split(':')[0])
                is_ip = True
                ip_type = 'IPv6'
            except:
                pass
        
        # Check for suspicious keywords in URL
        suspicious_keywords = []
        url_lower = url.lower()
        
        for keyword in Config.SUSPICIOUS_KEYWORDS:
            if keyword.lower() in url_lower:
                suspicious_keywords.append(keyword)
        
        # Check for URL shorteners
        is_shortener = False
        shortener_service = None
        
        for shortener in Config.URL_SHORTENERS:
            if shortener in netloc:
                is_shortener = True
                shortener_service = shortener
                break
        
        # Check URL length
        url_length = len(url)
        is_long_url = url_length > 100
        
        # Check for special characters
        special_chars = re.findall(r'[^\w\s./:-]', url)
        has_special_chars = len(special_chars) > 5
        
        # Check for hex encoding
        hex_patterns = re.findall(r'%[0-9a-fA-F]{2}', url)
        has_hex_encoding = len(hex_patterns) > 3
        
        # Check port
        port = None
        if ':' in netloc:
            port_part = netloc.split(':')[-1]
            if port_part.isdigit():
                port = int(port_part)
        
        # Validate URL format
        is_valid_url = validators.url(url)
        
        return {
            'scheme': scheme,
            'netloc': netloc,
            'path': path,
            'query': query,
            'fragment': fragment,
            'is_ip_address': is_ip,
            'ip_type': ip_type,
            'has_https': scheme == 'https',
            'has_suspicious_keywords': len(suspicious_keywords) > 0,
            'suspicious_keywords_found': suspicious_keywords,
            'is_url_shortener': is_shortener,
            'shortener_service': shortener_service,
            'url_length': url_length,
            'is_long_url': is_long_url,
            'has_special_chars': has_special_chars,
            'special_chars_count': len(special_chars),
            'has_hex_encoding': has_hex_encoding,
            'hex_patterns_count': len(hex_patterns),
            'port': port,
            'is_valid_url': is_valid_url,
            'domain': netloc.split(':')[0] if not is_ip else netloc
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'is_valid_url': False
        }

def get_domain_info(domain):
    """
    Get WHOIS information for domain
    
    Args:
        domain (str): Domain name
    
    Returns:
        dict: WHOIS information
    """
    try:
        w = whois.whois(domain)
        
        # Parse dates
        creation_date = w.creation_date
        expiration_date = w.expiration_date
        updated_date = w.updated_date
        
        # Handle multiple dates
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        if isinstance(expiration_date, list):
            expiration_date = expiration_date[0]
        if isinstance(updated_date, list):
            updated_date = updated_date[0]
        
        # Calculate domain age
        domain_age_days = None
        if creation_date:
            delta = datetime.now() - creation_date
            domain_age_days = delta.days
        
        return {
            'domain_name': w.domain_name,
            'registrar': w.registrar,
            'creation_date': creation_date.isoformat() if creation_date else None,
            'expiration_date': expiration_date.isoformat() if expiration_date else None,
            'updated_date': updated_date.isoformat() if updated_date else None,
            'name_servers': w.name_servers,
            'status': w.status,
            'emails': w.emails,
            'org': w.org,
            'country': w.country,
            'city': w.city,
            'domain_age_days': domain_age_days,
            'is_registered': True
        }
    except Exception as e:
        return {
            'error': str(e),
            'is_registered': False,
            'domain_age_days': None
        }

def parse_query_params(query_string):
    """
    Parse and analyze query parameters
    
    Args:
        query_string (str): Query string
    
    Returns:
        dict: Query parameters analysis
    """
    try:
        params = urllib.parse.parse_qs(query_string)
        
        suspicious_params = []
        for key, values in params.items():
            key_lower = key.lower()
            
            # Check for suspicious parameter names
            suspicious_keywords = ['token', 'auth', 'key', 'password', 'secret']
            for keyword in suspicious_keywords:
                if keyword in key_lower:
                    suspicious_params.append({
                        'parameter': key,
                        'reason': f'Contains suspicious keyword: {keyword}',
                        'values': values
                    })
                    break
        
        return {
            'parameter_count': len(params),
            'parameters': params,
            'has_suspicious_params': len(suspicious_params) > 0,
            'suspicious_parameters': suspicious_params
        }
    except Exception as e:
        return {
            'error': str(e),
            'parameter_count': 0,
            'has_suspicious_params': False
        }