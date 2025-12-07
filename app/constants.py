"""Application constants"""

# Site configuration
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 100

# Tab configuration
MAX_TABS_PER_SITE = 20
MAX_TAB_NAME_LENGTH = 100
DEFAULT_TAB_NAME = "Main"

# Content limits
MAX_CONTENT_SIZE_BYTES = 1024 * 1024  # 1MB

# Session configuration
SESSION_EXPIRY_HOURS = 24
SESSION_COOKIE_NAME = "securetext_session"

# URL patterns
SITE_URL_PATTERN = r"^[a-zA-Z0-9_-]+$"

# Export configuration
EXPORT_FORMATS = ["txt", "json", "md"]
EXPORT_OPTIONS = {
    "txt": "Text File (.txt)",
    "json": "JSON File (.json)", 
    "md": "Markdown File (.md)"
}

# Error messages
ERROR_USERNAME_EXISTS = "Username already exists. Please choose a different username or access the existing site."
ERROR_USERNAME_NOT_FOUND = "Site not found. Please check the username or create a new site."
ERROR_INVALID_PASSWORD = "Invalid password. Please try again."
ERROR_INVALID_USERNAME = "Username must be 3-50 characters and contain only letters, numbers, underscores, and hyphens."
ERROR_INVALID_PASSWORD_FORMAT = "Password must be 8-100 characters."
ERROR_SESSION_EXPIRED = "Your session has expired. Please enter the password again."
ERROR_RATE_LIMIT = "Too many attempts. Please try again later."

# Success messages
SUCCESS_SITE_CREATED = "Site created successfully! You can now access your site anytime using this username and password."
SUCCESS_PASSWORD_VERIFIED = "Password verified! Loading your site..."
SUCCESS_CONTENT_SAVED = "Content saved successfully."
SUCCESS_TAB_CREATED = "New tab created successfully."
SUCCESS_TAB_RENAMED = "Tab renamed successfully."
SUCCESS_TAB_DELETED = "Tab deleted successfully."

# UI constants
APP_TITLE = "SecureText Vault"
APP_DESCRIPTION = "Password-protected text storage - No registration required"
APP_ICON = "🔒"
