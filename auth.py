import hashlib
from datetime import datetime

class AuthManager:
    def __init__(self, database):
        self.db = database
    
    def hash_password(self, password):
        """Hash a password for secure storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """Authenticate a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # For demo purposes, we're not hashing passwords
        # In production, you should use proper password hashing
        cursor.execute('''
            SELECT id, username, full_name, role 
            FROM users 
            WHERE username = ? AND password = ? AND is_active = 1
        ''', (username, password))
        
        user = cursor.fetchone()
        
        if user:
            # Update last login
            self.db.update_last_login(username)
            self.db.log_activity(username, 'LOGIN', 'User logged in')
            conn.close()
            return dict(user)
        
        conn.close()
        return None
    
    def check_permission(self, role, action):
        """Check if a role has permission for an action"""
        permissions = {
            'Admin': ['view', 'create', 'edit', 'delete', 'manage_users'],
            'Investigator': ['view', 'create', 'edit'],
            'Analyst': ['view', 'create'],
            'Viewer': ['view']
        }
        
        return action in permissions.get(role, [])
