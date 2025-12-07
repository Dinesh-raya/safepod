#!/usr/bin/env python3
"""
Wrapper script to run Streamlit with custom uuid module.
This ensures our custom uuid module is loaded before Streamlit imports the corrupted system one.
"""
import sys
import os

# Add our custom uuid module to the beginning of sys.path
workspace_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, workspace_dir)

# Create a custom module loader that intercepts uuid imports
import importlib.util
import importlib.machinery

# Save the original import function
original_import = __import__

def custom_import(name, *args, **kwargs):
    """Custom import function that intercepts uuid imports"""
    if name == 'uuid':
        # Try to import our custom uuid module
        try:
            # First check if we can load our custom module
            custom_uuid_path = os.path.join(workspace_dir, 'uuid.py')
            if os.path.exists(custom_uuid_path):
                # Use importlib to load our custom module
                spec = importlib.util.spec_from_file_location('uuid', custom_uuid_path)
                custom_uuid = importlib.util.module_from_spec(spec)
                sys.modules['uuid'] = custom_uuid
                spec.loader.exec_module(custom_uuid)
                return custom_uuid
        except Exception as e:
            print(f"Warning: Failed to load custom uuid module: {e}")
    
    # For all other imports, use the original function
    return original_import(name, *args, **kwargs)

# Replace the built-in __import__ with our custom version
builtins = __import__('builtins')
builtins.__import__ = custom_import

# Now import and run streamlit
if __name__ == "__main__":
    # Import streamlit after setting up our custom import
    from streamlit.web.cli import main
    
    # Get command line arguments
    args = sys.argv[1:]
    
    # Add our main app file if not specified
    if not any(arg.endswith('main.py') for arg in args):
        args = ['app/main.py'] + args
    
    # Run streamlit with our custom import setup
    sys.argv = ['streamlit'] + args
    main()
