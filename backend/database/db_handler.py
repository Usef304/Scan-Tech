"""
Database Handler for SQLite
"""
import sqlite3
import json
from datetime import datetime
from config import Config

def init_db():
    """Initialize database with required tables"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        # Create scans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT UNIQUE NOT NULL,
                url TEXT NOT NULL,
                result TEXT NOT NULL,
                security_score INTEGER,
                risk_level TEXT,
                source TEXT,
                timestamp TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create threats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS threats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT NOT NULL,
                threat_type TEXT NOT NULL,
                description TEXT,
                severity TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans (scan_id)
            )
        ''')
        
        # Create statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_scans INTEGER DEFAULT 0,
                safe_scans INTEGER DEFAULT 0,
                malicious_scans INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Initialize statistics if empty
        cursor.execute('SELECT COUNT(*) FROM statistics')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO statistics (total_scans, safe_scans, malicious_scans) VALUES (0, 0, 0)')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully")
        
    except Exception as e:
        print(f"Database initialization error: {e}")

def save_scan_result(scan_data):
    """Save scan result to database"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        scan_id = scan_data.get('scan_id')
        url = scan_data.get('url', '')
        result = json.dumps(scan_data.get('result', {}))
        security_score = scan_data.get('result', {}).get('security_score', 0)
        risk_level = scan_data.get('result', {}).get('risk_level', 'Unknown')
        source = scan_data.get('source', 'unknown')
        timestamp = scan_data.get('timestamp', datetime.now().isoformat())
        
        # Insert scan
        cursor.execute('''
            INSERT INTO scans (scan_id, url, result, security_score, risk_level, source, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (scan_id, url, result, security_score, risk_level, source, timestamp))
        
        # Update statistics
        is_safe = scan_data.get('result', {}).get('is_safe', True)
        cursor.execute('''
            UPDATE statistics 
            SET total_scans = total_scans + 1,
                safe_scans = safe_scans + ?,
                malicious_scans = malicious_scans + ?,
                last_updated = CURRENT_TIMESTAMP
        ''', (1 if is_safe else 0, 0 if is_safe else 1))
        
        # Save threats if any
        threats = scan_data.get('result', {}).get('threats', [])
        for threat in threats:
            cursor.execute('''
                INSERT INTO threats (scan_id, threat_type, description, severity)
                VALUES (?, ?, ?, ?)
            ''', (scan_id, 'general', threat, 'high'))
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error saving scan result: {e}")
        return False

def get_scan_result(scan_id):
    """Retrieve scan result by scan_id"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM scans WHERE scan_id = ?', (scan_id,))
        row = cursor.fetchone()
        
        if row:
            result = {
                'scan_id': row['scan_id'],
                'url': row['url'],
                'result': json.loads(row['result']),
                'security_score': row['security_score'],
                'risk_level': row['risk_level'],
                'source': row['source'],
                'timestamp': row['timestamp'],
                'created_at': row['created_at']
            }
            
            # Get threats
            cursor.execute('SELECT * FROM threats WHERE scan_id = ?', (scan_id,))
            threats = cursor.fetchall()
            result['threats'] = [dict(threat) for threat in threats]
            
            conn.close()
            return result
        
        conn.close()
        return None
        
    except Exception as e:
        print(f"Error retrieving scan result: {e}")
        return None

def get_recent_scans(limit=10):
    """Get recent scans"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT scan_id, url, security_score, risk_level, timestamp
            FROM scans
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        scans = [dict(row) for row in rows]
        
        conn.close()
        return scans
        
    except Exception as e:
        print(f"Error getting recent scans: {e}")
        return []

def get_stats():
    """Get overall statistics"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM statistics')
        row = cursor.fetchone()
        
        if row:
            stats = {
                'total_scans': row[1],
                'safe_scans': row[2],
                'malicious_scans': row[3],
                'last_updated': row[4]
            }
            
            # Calculate percentages
            if stats['total_scans'] > 0:
                stats['safe_percentage'] = round((stats['safe_scans'] / stats['total_scans']) * 100, 2)
                stats['malicious_percentage'] = round((stats['malicious_scans'] / stats['total_scans']) * 100, 2)
            else:
                stats['safe_percentage'] = 0
                stats['malicious_percentage'] = 0
            
            conn.close()
            return stats
        
        conn.close()
        return {}
        
    except Exception as e:
        print(f"Error getting statistics: {e}")
        return {}

def search_scans(query, limit=20):
    """Search scans by URL"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT scan_id, url, security_score, risk_level, timestamp
            FROM scans
            WHERE url LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{query}%', limit))
        
        rows = cursor.fetchall()
        scans = [dict(row) for row in rows]
        
        conn.close()
        return scans
        
    except Exception as e:
        print(f"Error searching scans: {e}")
        return []

def delete_old_scans(days=30):
    """Delete scans older than specified days"""
    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM threats 
            WHERE scan_id IN (
                SELECT scan_id FROM scans 
                WHERE date(created_at) < date('now', '-? days')
            )
        ''', (days,))
        
        cursor.execute('''
            DELETE FROM scans 
            WHERE date(created_at) < date('now', '-? days')
        ''', (days,))
        
        conn.commit()
        deleted_count = cursor.rowcount
        
        conn.close()
        return deleted_count
        
    except Exception as e:
        print(f"Error deleting old scans: {e}")
        return 0