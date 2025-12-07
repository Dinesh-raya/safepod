import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_config_value(key, default=None):
    """
    Retrieve configuration value from Streamlit secrets (if available) 
    or environment variables.
    """
    # Try getting from Streamlit secrets first
    try:
        import streamlit as st
        # Check if secrets are available and the key exists
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError, Exception):
        # Streamlit might not be installed or secrets file not found
        pass
    
    # Fallback to environment variables
    return os.getenv(key, default)

class Config:
    """Application configuration"""
    
    # Supabase Configuration
    SUPABASE_URL = get_config_value("SUPABASE_URL", "")
    SUPABASE_KEY = get_config_value("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY = get_config_value("SUPABASE_SERVICE_KEY", "")
    
    # Application Configuration
    SESSION_SECRET = get_config_value("SESSION_SECRET", "dev-secret-key-change-in-production")
    
    # Handle integer conversions safely
    try:
        BCRYPT_ROUNDS = int(get_config_value("BCRYPT_ROUNDS", "12"))
    except (ValueError, TypeError):
        BCRYPT_ROUNDS = 12
        
    try:
        MAX_CONTENT_SIZE_MB = int(get_config_value("MAX_CONTENT_SIZE_MB", "1"))
    except (ValueError, TypeError):
        MAX_CONTENT_SIZE_MB = 1
        
    try:
        RATE_LIMIT_PER_MINUTE = int(get_config_value("RATE_LIMIT_PER_MINUTE", "60"))
    except (ValueError, TypeError):
        RATE_LIMIT_PER_MINUTE = 60
    
    # Optional Features
    ENCRYPTION_ENABLED = str(get_config_value("ENCRYPTION_ENABLED", "false")).lower() == "true"
    ENCRYPTION_KEY = get_config_value("ENCRYPTION_KEY", "")
    
    # Validation
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        
        if not cls.SUPABASE_URL:
            errors.append("SUPABASE_URL is not set")
        if not cls.SUPABASE_KEY:
            errors.append("SUPABASE_KEY is not set")
        if not cls.SUPABASE_SERVICE_KEY:
            errors.append("SUPABASE_SERVICE_KEY is not set")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_supabase_config(cls):
        """Get Supabase configuration as dict"""
        return {
            "url": cls.SUPABASE_URL,
            "key": cls.SUPABASE_KEY,
            "service_key": cls.SUPABASE_SERVICE_KEY
        }

# Create global config instance
config = Config()
