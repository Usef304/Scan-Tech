"""
Reputation and Risk Assessment Module
"""
import re
import socket
from datetime import datetime
import whois
import requests
from config import Config

def check_url_reputation(url):
    """
    Check URL reputation and calculate risk score
    
    Args:
        url (str): URL to check
    
    Returns:
        dict: Reputation analysis
    """
    import urllib.parse
    
    parsed = urllib.parse.urlparse(url)
    domain = parsed.netloc.split(':')[0]
    
    results = {
        'domain': domain,
        'risk_score': 0,
        'risk_factors': [],
        'reputation_indicators': {},
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Factor 1: Domain Age
        domain_age = get_domain_age(domain)
        results['domain_age_days'] = domain_age
        
        if domain_age:
            if domain_age < 30:
                results['risk_score'] += 30
                results['risk_factors'].append('Very new domain (< 30 days)')
            elif domain_age < 365:
                results['risk_score'] += 15
                results['risk_factors'].append('New domain (< 1 year)')
        
        # Factor 2: TLD Analysis
        tld_risk = analyze_tld(domain)
        results['tld_analysis'] = tld_risk
        
        if tld_risk.get('is_high_risk_tld', False):
            results['risk_score'] += 20
            results['risk_factors'].append('High-risk TLD')
        
        # Factor 3: Subdomain Count
        subdomain_count = domain.count('.')
        results['subdomain_count'] = subdomain_count
        
        if subdomain_count > 2:
            results['risk_score'] += 10
            results['risk_factors'].append('Multiple subdomains')
        
        # Factor 4: Domain Length
        domain_length = len(domain.split('.')[0])
        results['domain_length'] = domain_length
        
        if domain_length > 20:
            results['risk_score'] += 5
            results['risk_factors'].append('Long domain name')
        elif domain_length < 3:
            results['risk_score'] += 10
            results['risk_factors'].append('Very short domain name')
        
        # Factor 5: Character Analysis
        char_analysis = analyze_characters(domain)
        results['character_analysis'] = char_analysis
        
        if char_analysis.get('has_hyphens', False):
            results['risk_score'] += 5
            results['risk_factors'].append('Domain contains hyphens')
        
        if char_analysis.get('has_numbers', False):
            results['risk_score'] += 5
            results['risk_factors'].append('Domain contains numbers')
        
        # Factor 6: Popularity Check (simplified)
        try:
            # Try to resolve domain
            socket.gethostbyname(domain)
            results['dns_resolution'] = True
        except:
            results['dns_resolution'] = False
            results['risk_score'] += 25
            results['risk_factors'].append('DNS resolution failed')
        
        # Factor 7: Alexa Rank (simulated)
        alexa_rank = simulate_alexa_check(domain)
        results['alexa_rank'] = alexa_rank
        
        if alexa_rank == 'Not in top 1M':
            results['risk_score'] += 10
            results['risk_factors'].append('Low popularity domain')
        
        # Factor 8: SSL Certificate (basic check)
        has_ssl = check_ssl_basic(domain)
        results['has_ssl'] = has_ssl
        
        if not has_ssl:
            results['risk_score'] += 15
            results['risk_factors'].append('No SSL certificate')
        
        # Calculate final risk score (0-100)
        results['risk_score'] = min(100, results['risk_score'])
        
        # Determine risk level
        if results['risk_score'] >= 70:
            results['risk_level'] = 'High'
        elif results['risk_score'] >= 40:
            results['risk_level'] = 'Medium'
        else:
            results['risk_level'] = 'Low'
        
        # Get WHOIS information
        try:
            whois_info = whois.whois(domain)
            results['whois'] = {
                'registrar': whois_info.registrar,
                'creation_date': str(whois_info.creation_date),
                'expiration_date': str(whois_info.expiration_date),
                'name_servers': whois_info.name_servers,
                'org': whois_info.org
            }
        except:
            results['whois'] = {'error': 'Could not retrieve WHOIS data'}
        
        return results
        
    except Exception as e:
        return {
            'error': str(e),
            'risk_score': 50,
            'risk_level': 'Unknown'
        }

def get_domain_age(domain):
    """Get domain age in days"""
    try:
        w = whois.whois(domain)
        creation_date = w.creation_date
        
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
        
        if creation_date:
            delta = datetime.now() - creation_date
            return delta.days
        return None
    except:
        return None

def analyze_tld(domain):
    """Analyze Top-Level Domain for risk"""
    tld = domain.split('.')[-1].lower()
    
    # Lists of TLDs by risk (simplified)
    high_risk_tlds = {'tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'club', 'online'}
    medium_risk_tlds = {'info', 'biz', 'click', 'link', 'pro', 'work', 'site'}
    
    is_high_risk = tld in high_risk_tlds
    is_medium_risk = tld in medium_risk_tlds
    
    risk_score = 0
    if is_high_risk:
        risk_score = 20
    elif is_medium_risk:
        risk_score = 10
    
    return {
        'tld': tld,
        'is_high_risk_tld': is_high_risk,
        'is_medium_risk_tld': is_medium_risk,
        'tld_risk_score': risk_score
    }

def analyze_characters(text):
    """Analyze character patterns in domain"""
    # Remove TLD
    name = text.split('.')[0]
    
    return {
        'length': len(name),
        'has_hyphens': '-' in name,
        'has_numbers': bool(re.search(r'\d', name)),
        'has_special_chars': bool(re.search(r'[^a-zA-Z0-9-]', name)),
        'vowel_count': len(re.findall(r'[aeiouAEIOU]', name)),
        'consonant_count': len(re.findall(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]', name)),
        'digit_count': len(re.findall(r'\d', name))
    }

def simulate_alexa_check(domain):
    """Simulate Alexa rank check"""
    # In a real implementation, you would use Alexa API
    # This is a simplified simulation
    popular_domains = {
        'google.com': 'Top 10',
        'youtube.com': 'Top 10',
        'facebook.com': 'Top 10',
        'twitter.com': 'Top 10',
        'instagram.com': 'Top 10',
        'linkedin.com': 'Top 100',
        'github.com': 'Top 100',
        'wikipedia.org': 'Top 10'
    }
    
    return popular_domains.get(domain, 'Not in top 1M')

def check_ssl_basic(domain):
    """Basic SSL check"""
    try:
        import ssl
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                return True
    except:
        return False

def calculate_reputation_score(url):
    """Calculate overall reputation score (0-100)"""
    reputation_data = check_url_reputation(url)
    risk_score = reputation_data.get('risk_score', 50)
    
    # Convert risk score to reputation score
    reputation_score = max(0, 100 - risk_score)
    
    reputation_data['reputation_score'] = reputation_score
    
    # Add grade
    if reputation_score >= 80:
        reputation_data['grade'] = 'A'
    elif reputation_score >= 60:
        reputation_data['grade'] = 'B'
    elif reputation_score >= 40:
        reputation_data['grade'] = 'C'
    elif reputation_score >= 20:
        reputation_data['grade'] = 'D'
    else:
        reputation_data['grade'] = 'F'
    
    return reputation_data