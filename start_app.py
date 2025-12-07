#!/usr/bin/env python3
"""
SecureText Vault - Application Entry Point
This script patches the uuid module before importing Streamlit to avoid the corrupted system module.
"""
import sys
import os

# Add workspace to path
workspace_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, workspace_dir)

# First, let's patch the uuid module before anything else imports it
print("Patching uuid module...")

# Create a simple uuid module that mimics the standard library
class SimpleUUID:
    def __init__(self, hex=None, bytes=None, int=None):
        if hex:
            self.hex = hex.lower()
        elif bytes:
            self.hex = bytes.hex()
        elif int is not None:
            self.hex = format(int, '032x')
        else:
            import secrets
            self.hex = secrets.token_hex(16)
    
    @property
    def bytes(self):
        return bytes.fromhex(self.hex)
    
    @property
    def int(self):
        return int(self.hex, 16)
    
    def __str__(self):
        h = self.hex
        return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
    
    def __repr__(self):
        return f"UUID('{self}')"
    
    def __eq__(self, other):
        if isinstance(other, SimpleUUID):
            return self.hex == other.hex
        return False

# Create module functions
def uuid4():
    import secrets
    return SimpleUUID(hex=secrets.token_hex(16))

# Create a fake uuid module
class FakeUUIDModule:
    UUID = SimpleUUID
    uuid4 = staticmethod(uuid4)
    
    # Add namespace constants
    NAMESPACE_DNS = SimpleUUID(hex='6ba7b8109dad11d180b400c04fd430c8')
    NAMESPACE_URL = SimpleUUID(hex='6ba7b8119dad11d180b400c04fd430c8')
    NAMESPACE_OID = SimpleUUID(hex='6ba7b8129dad11d180b400c04fd430c8')
    NAMESPACE_X500 = SimpleUUID(hex='6ba7b8149dad11d180b400c04fd430c8')

# Patch sys.modules before importing anything
sys.modules['uuid'] = FakeUUIDModule()

print("✓ uuid module patched successfully")

# Now import and run our app
try:
    print("Starting SecureText Vault...")
    
    # Import streamlit components
    import streamlit.web.cli as stcli
    
    # Set up command line arguments
    sys.argv = ['streamlit', 'run', 'app/main.py', '--server.port=8501', '--server.address=0.0.0.0']
    
    # Run streamlit
    stcli.main()
    
except Exception as e:
    print(f"Error starting application: {e}")
    import traceback
    traceback.print_exc()
    
    # Fallback: try to run the app directly
    print("\nTrying alternative startup method...")
    try:
        # Import our app module
        from app.main import main as app_main
        
        # Run the app directly (for testing)
        print("Running app in test mode...")
        app_main()
    except Exception as e2:
        print(f"Alternative startup also failed: {e2}")
        sys.exit(1)
