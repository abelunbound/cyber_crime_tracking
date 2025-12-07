import sqlite3
from datetime import datetime
import pandas as pd
from pathlib import Path

class Database:
    def __init__(self, db_path='/tmp/cybercrime.db'):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Create a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                crime_type TEXT NOT NULL,
                incident_date DATE NOT NULL,
                location TEXT,
                victim_name TEXT,
                victim_contact TEXT,
                suspect_name TEXT,
                suspect_details TEXT,
                description TEXT,
                evidence TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Pending',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Activity log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert default admin user if not exists
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, full_name, role)
            VALUES ('admin', 'admin123', 'System Administrator', 'Admin')
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_case_id(self):
        """Generate a unique case ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get the count of existing cases
        cursor.execute('SELECT COUNT(*) as count FROM cases')
        count = cursor.fetchone()['count']
        conn.close()
        
        # Generate case ID in format: CYB-YYYY-XXXX
        year = datetime.now().year
        case_number = str(count + 1).zfill(4)
        return f"CYB-{year}-{case_number}"
    
    def add_case(self, case_data):
        """Add a new case to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        case_id = self.generate_case_id()
        
        try:
            cursor.execute('''
                INSERT INTO cases (
                    case_id, title, crime_type, incident_date, location,
                    victim_name, victim_contact, suspect_name, suspect_details,
                    description, evidence, priority, status, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                case_id,
                case_data.get('title'),
                case_data.get('crime_type'),
                case_data.get('incident_date'),
                case_data.get('location'),
                case_data.get('victim_name'),
                case_data.get('victim_contact'),
                case_data.get('suspect_name'),
                case_data.get('suspect_details'),
                case_data.get('description'),
                case_data.get('evidence'),
                case_data.get('priority', 'Medium'),
                case_data.get('status', 'Pending'),
                case_data.get('created_by', 'system')
            ))
            
            conn.commit()
            
            # Log the activity
            self.log_activity(
                case_data.get('created_by', 'system'),
                'CREATE_CASE',
                f"Created case {case_id}"
            )
            
            conn.close()
            return {'success': True, 'case_id': case_id}
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def get_all_cases(self, status_filter='all'):
        """Get all cases, optionally filtered by status"""
        conn = self.get_connection()
        
        if status_filter == 'all':
            query = 'SELECT * FROM cases ORDER BY created_at DESC'
            df = pd.read_sql_query(query, conn)
        else:
            query = 'SELECT * FROM cases WHERE status = ? ORDER BY created_at DESC'
            df = pd.read_sql_query(query, conn, params=(status_filter,))
        
        conn.close()
        return df
    
    def get_case_by_id(self, case_id):
        """Get a specific case by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cases WHERE case_id = ?', (case_id,))
        case = cursor.fetchone()
        conn.close()
        
        return dict(case) if case else None
    
    def update_case(self, case_id, updates):
        """Update a case"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(case_id)
        
        try:
            cursor.execute(f'''
                UPDATE cases 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE case_id = ?
            ''', values)
            
            conn.commit()
            conn.close()
            return {'success': True}
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def search_cases(self, search_text='', crime_type='all', start_date=None, end_date=None):
        """Search cases with filters"""
        conn = self.get_connection()
        
        query = 'SELECT * FROM cases WHERE 1=1'
        params = []
        
        if search_text:
            query += ' AND (case_id LIKE ? OR title LIKE ? OR victim_name LIKE ? OR suspect_name LIKE ?)'
            search_pattern = f'%{search_text}%'
            params.extend([search_pattern, search_pattern, search_pattern, search_pattern])
        
        if crime_type != 'all':
            query += ' AND crime_type = ?'
            params.append(crime_type)
        
        if start_date:
            query += ' AND incident_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND incident_date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY created_at DESC'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def get_statistics(self):
        """Get dashboard statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total cases
        cursor.execute('SELECT COUNT(*) as count FROM cases')
        total_cases = cursor.fetchone()['count']
        
        # Pending cases
        cursor.execute("SELECT COUNT(*) as count FROM cases WHERE status = 'Pending'")
        pending_cases = cursor.fetchone()['count']
        
        # Resolved cases
        cursor.execute("SELECT COUNT(*) as count FROM cases WHERE status = 'Resolved'")
        resolved_cases = cursor.fetchone()['count']
        
        # Total users
        cursor.execute('SELECT COUNT(*) as count FROM users WHERE is_active = 1')
        total_users = cursor.fetchone()['count']
        
        conn.close()
        
        return {
            'total_cases': total_cases,
            'pending_cases': pending_cases,
            'resolved_cases': resolved_cases,
            'total_users': total_users
        }
    
    def get_cases_by_type(self):
        """Get case distribution by crime type"""
        conn = self.get_connection()
        
        query = '''
            SELECT crime_type, COUNT(*) as count 
            FROM cases 
            GROUP BY crime_type
            ORDER BY count DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_cases_by_status(self):
        """Get case distribution by status"""
        conn = self.get_connection()
        
        query = '''
            SELECT status, COUNT(*) as count 
            FROM cases 
            GROUP BY status
            ORDER BY count DESC
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_recent_cases(self, limit=10):
        """Get most recent cases"""
        conn = self.get_connection()
        
        query = f'SELECT * FROM cases ORDER BY created_at DESC LIMIT {limit}'
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_trend_data(self, start_date=None, end_date=None):
        """Get case trends over time"""
        conn = self.get_connection()
        
        query = '''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM cases
        '''
        
        params = []
        if start_date:
            query += ' WHERE created_at >= ?'
            params.append(start_date)
            
            if end_date:
                query += ' AND created_at <= ?'
                params.append(end_date)
        elif end_date:
            query += ' WHERE created_at <= ?'
            params.append(end_date)
        
        query += ' GROUP BY DATE(created_at) ORDER BY date'
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
    
    def add_user(self, username, password, full_name, role):
        """Add a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, password, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', (username, password, full_name, role))
            
            conn.commit()
            conn.close()
            return {'success': True}
        except sqlite3.IntegrityError:
            conn.close()
            return {'success': False, 'error': 'Username already exists'}
        except Exception as e:
            conn.close()
            return {'success': False, 'error': str(e)}
    
    def get_all_users(self):
        """Get all active users"""
        conn = self.get_connection()
        
        query = 'SELECT id, username, full_name, role, created_at, last_login FROM users WHERE is_active = 1'
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def update_last_login(self, username):
        """Update user's last login timestamp"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP 
            WHERE username = ?
        ''', (username,))
        
        conn.commit()
        conn.close()
    
    def log_activity(self, username, action, details=''):
        """Log user activity"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO activity_log (username, action, details)
            VALUES (?, ?, ?)
        ''', (username, action, details))
        
        conn.commit()
        conn.close()
    
    def get_activity_log(self, username=None, limit=100):
        """Get activity log"""
        conn = self.get_connection()
        
        if username:
            query = f'SELECT * FROM activity_log WHERE username = ? ORDER BY timestamp DESC LIMIT {limit}'
            df = pd.read_sql_query(query, conn, params=(username,))
        else:
            query = f'SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT {limit}'
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
