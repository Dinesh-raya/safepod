import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Application Configuration
    SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-secret-key-change-in-production")
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))
    MAX_CONTENT_SIZE_MB = int(os.getenv("MAX_CONTENT_SIZE_MB", "1"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Optional Features
    ENCRYPTION_ENABLED = os.getenv("ENCRYPTION_ENABLED", "false").lower() == "true"
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "")
    
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