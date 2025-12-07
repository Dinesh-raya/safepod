"""Authentication and password management service"""
import bcrypt
import re
import secrets
import string
import time
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
import json

from app.constants import (
    MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH,
    MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH,
    SESSION_EXPIRY_HOURS, SESSION_COOKIE_NAME,
    ERROR_USERNAME_EXISTS, ERROR_USERNAME_NOT_FOUND,
    ERROR_INVALID_PASSWORD, ERROR_INVALID_USERNAME,
    ERROR_INVALID_PASSWORD_FORMAT, ERROR_SESSION_EXPIRED,
    ERROR_RATE_LIMIT, SITE_URL_PATTERN
)
from app.services.supabase_client import supabase_client
from app.config import config

class AuthService:
    """Authentication service for password management and session handling"""
    
    def __init__(self):
        self.bcrypt_rounds = config.BCRYPT_ROUNDS
        # Rate limiting storage (in-memory for simplicity, in production use Redis)
        self._rate_limit_cache = {}
        self._rate_limit_window = 60  # 1 minute window
        self._rate_limit_max_attempts = config.RATE_LIMIT_PER_MINUTE
    
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
        """Validate password format and strength"""
        # Check length
        if len(password) < MIN_PASSWORD_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
            return False, ERROR_INVALID_PASSWORD_FORMAT
        
        # Password strength requirements
        errors = []
        
        # At least one uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("at least one uppercase letter")
        
        # At least one lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append("at least one lowercase letter")
        
        # At least one number
        if not re.search(r'\d', password):
            errors.append("at least one number")
        
        # At least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("at least one special character (!@#$%^&* etc.)")
        
        if errors:
            error_msg = f"Password must contain: {', '.join(errors)}"
            return False, error_msg
        
        return True, None
    
    def check_rate_limit(self, identifier: str, action: str = "login") -> Tuple[bool, Optional[str]]:
        """Check if request exceeds rate limit"""
        current_time = time.time()
        key = f"{identifier}:{action}"
        
        # Clean old entries
        self._clean_rate_limit_cache(current_time)
        
        # Get attempts for this key
        attempts = self._rate_limit_cache.get(key, [])
        
        # Remove attempts outside the time window
        attempts = [t for t in attempts if current_time - t < self._rate_limit_window]
        
        # Check if limit exceeded
        if len(attempts) >= self._rate_limit_max_attempts:
            return False, ERROR_RATE_LIMIT
        
        # Add current attempt
        attempts.append(current_time)
        self._rate_limit_cache[key] = attempts
        
        return True, None
    
    def _clean_rate_limit_cache(self, current_time: float):
        """Clean old entries from rate limit cache"""
        keys_to_remove = []
        for key, attempts in self._rate_limit_cache.items():
            # Keep only attempts within the time window
            valid_attempts = [t for t in attempts if current_time - t < self._rate_limit_window]
            if valid_attempts:
                self._rate_limit_cache[key] = valid_attempts
            else:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._rate_limit_cache[key]
    
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
        # Check rate limit for site creation
        is_allowed, rate_limit_error = self.check_rate_limit(username, "create_site")
        if not is_allowed:
            return False, rate_limit_error, None
        
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
        # Check rate limit for authentication
        is_allowed, rate_limit_error = self.check_rate_limit(username, "authenticate")
        if not is_allowed:
            return False, rate_limit_error, None
        
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
    
    def _create_hmac_signature(self, data: str) -> str:
        """Create HMAC signature for data"""
        secret = config.SESSION_SECRET.encode('utf-8')
        data_bytes = data.encode('utf-8')
        signature = hmac.new(secret, data_bytes, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    def _verify_hmac_signature(self, data: str, signature: str) -> bool:
        """Verify HMAC signature for data"""
        expected_signature = self._create_hmac_signature(data)
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)
    
    def create_session_token(self, site_id: str, username: str) -> str:
        """Create a secure session token using JWT-like structure"""
        # Generate unique session ID
        session_id = self._generate_session_id()
        
        # Create token header
        header = {
            'alg': 'HS256',
            'typ': 'JWT'
        }
        
        # Create token payload
        payload = {
            'session_id': session_id,
            'site_id': site_id,
            'username': username,
            'exp': int((datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)).timestamp()),
            'iat': int(datetime.utcnow().timestamp())
        }
        
        # Encode header and payload
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        
        # Create signature
        data_to_sign = f"{header_b64}.{payload_b64}"
        signature = self._create_hmac_signature(data_to_sign)
        
        # Combine all parts
        token = f"{header_b64}.{payload_b64}.{signature}"
        
        return token
    
    def validate_session_token(self, token: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate session token and return site data if valid"""
        try:
            # Split token
            parts = token.split('.')
            if len(parts) != 3:
                return False, "Invalid token format", None
            
            header_b64, payload_b64, signature = parts
            
            # Verify signature
            data_to_verify = f"{header_b64}.{payload_b64}"
            if not self._verify_hmac_signature(data_to_verify, signature):
                return False, "Invalid token signature", None
            
            # Decode payload
            # Add padding if needed
            payload_b64_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64_padded).decode('utf-8')
            payload = json.loads(payload_json)
            
            # Check expiration
            current_time = int(datetime.utcnow().timestamp())
            if payload.get('exp', 0) < current_time:
                return False, ERROR_SESSION_EXPIRED, None
            
            # Get site data
            site_id = payload.get('site_id')
            username = payload.get('username')
            
            if not site_id or not username:
                return False, "Invalid token payload", None
            
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
