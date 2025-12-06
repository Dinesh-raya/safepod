"""Authentication and password management service"""
import bcrypt
import re
import secrets
import string
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import hashlib

from app.constants import (
    MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH,
    SESSION_EXPIRY_HOURS, SESSION_COOKIE_NAME,
    ERROR_USERNAME_EXISTS, ERROR_USERNAME_NOT_FOUND,
    ERROR_INVALID_PASSWORD, ERROR_INVALID_USERNAME,
    ERROR_INVALID_PASSWORD_FORMAT, ERROR_SESSION_EXPIRED,
    SITE_URL_PATTERN
)
from app.services.supabase_client import supabase_client
from app.config import config

class AuthService:
    """Authentication service for password management and session handling"""
    
    def __init__(self):
        self.bcrypt_rounds = config.BCRYPT_ROUNDS
    
    def validate_username(self, username: str) -> Tuple[bool, Optional[str]]:
        """Validate username format and availability"""
        # Check length
        if len(username) < MIN_USERNAME_LENGTH or len(username) > MAX_USERNAME_LENGTH:
            return False, ERROR_INVALID_USERNAME
        
        # Check pattern
        if not re.match(SITE_URL_PATTERN, username):
            return False, ERROR_INVALID_USERNAME
        
        # Check if username exists
        existing_site = supabase_client.get_site_by_username(username)
        if existing_site:
            return False, ERROR_USERNAME_EXISTS
        
        return True, None
    
    def validate_password(self, password: str) -> Tuple[bool, Optional[str]]:
        """Validate password format"""
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            return False, ERROR_INVALID_PASSWORD_FORMAT
        
        # Optional: Add more password strength checks here
        # if not re.search(r'[A-Z]', password):
        #     return False, "Password must contain at least one uppercase letter"
        # if not re.search(r'[a-z]', password):
        #     return False, "Password must contain at least one lowercase letter"
        # if not re.search(r'\d', password):
        #     return False, "Password must contain at least one number"
        
        return True, None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        # Convert password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    def create_site(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Create a new site with username and password"""
        # Validate inputs
        is_valid_username, username_error = self.validate_username(username)
        if not is_valid_username:
            return False, username_error, None
        
        is_valid_password, password_error = self.validate_password(password)
        if not is_valid_password:
            return False, password_error, None
        
        # Hash password
        password_hash = self.hash_password(password)
        
        try:
            # Create site in database
            site = supabase_client.create_site(username, password_hash)
            
            # Create default tab
            from app.constants import DEFAULT_TAB_NAME
            tab = supabase_client.create_tab(site['id'], DEFAULT_TAB_NAME, 0)
            
            return True, None, site
        except Exception as e:
            return False, str(e), None
    
    def authenticate_site(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Authenticate user and return site data if successful"""
        # Get site by username
        site = supabase_client.get_site_by_username(username)
        if not site:
            return False, ERROR_USERNAME_NOT_FOUND, None
        
        # Verify password
        if not self.verify_password(password, site['password_hash']):
            return False, ERROR_INVALID_PASSWORD, None
        
        # Update last accessed timestamp
        supabase_client.update_site_last_accessed(site['id'])
        
        return True, None, site
    
    def _generate_session_id(self) -> str:
        """Generate a secure random session ID"""
        # Generate 32 random bytes and encode as hex
        random_bytes = secrets.token_bytes(32)
        return random_bytes.hex()
    
    def create_session_token(self, site_id: str, username: str) -> str:
        """Create a session token for authenticated user"""
        # Generate unique session ID
        session_id = self._generate_session_id()
        
        # Create token payload
        payload = {
            'session_id': session_id,
            'site_id': site_id,
            'username': username,
            'expires_at': (datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)).isoformat()
        }
        
        # Create signature (simplified - in production use JWT or similar)
        signature_data = f"{session_id}:{site_id}:{username}:{payload['expires_at']}:{config.SESSION_SECRET}"
        signature = hashlib.sha256(signature_data.encode()).hexdigest()
        
        # Combine payload and signature
        token = f"{session_id}.{site_id}.{username}.{payload['expires_at']}.{signature}"
        
        return token
    
    def validate_session_token(self, token: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate session token and return site data if valid"""
        try:
            # Split token
            parts = token.split('.')
            if len(parts) != 5:
                return False, "Invalid token format", None
            
            session_id, site_id, username, expires_at_str, signature = parts
            
            # Check expiration
            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.utcnow() > expires_at:
                return False, ERROR_SESSION_EXPIRED, None
            
            # Verify signature
            signature_data = f"{session_id}:{site_id}:{username}:{expires_at_str}:{config.SESSION_SECRET}"
            expected_signature = hashlib.sha256(signature_data.encode()).hexdigest()
            
            if signature != expected_signature:
                return False, "Invalid token signature", None
            
            # Get site data
            site = supabase_client.get_site_by_id(site_id)
            if not site:
                return False, "Site not found", None
            
            # Verify username matches
            if site['username'] != username:
                return False, "Token username mismatch", None
            
            # Update last accessed timestamp
            supabase_client.update_site_last_accessed(site_id)
            
            return True, None, site
        except Exception as e:
            return False, f"Token validation error: {str(e)}", None
    
    def get_session_cookie_name(self) -> str:
        """Get session cookie name"""
        return SESSION_COOKIE_NAME

# Global instance
auth_service = AuthService()