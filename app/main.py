"""Main Streamlit application for SecureText Vault"""
import streamlit as st
import sys
import os
import json
import re
from datetime import datetime
from typing import Tuple, Optional

# Add custom uuid module to path before system packages
sys.path.insert(0, '/workspace')

from app.config import config
from app.services.auth_service import auth_service
from app.services.supabase_client import supabase_client
from app.constants import (
    DEFAULT_TAB_NAME, MAX_TABS_PER_SITE, MAX_TAB_NAME_LENGTH,
    MAX_CONTENT_SIZE_BYTES, EXPORT_FORMATS, EXPORT_OPTIONS,
    ERROR_INVALID_USERNAME, ERROR_INVALID_PASSWORD_FORMAT
)

def validate_tab_name(tab_name: str) -> Tuple[bool, Optional[str]]:
    """Validate tab name"""
    if not tab_name or not isinstance(tab_name, str):
        return False, "Tab name must be a non-empty string"
    
    if len(tab_name) > MAX_TAB_NAME_LENGTH:
        return False, f"Tab name exceeds maximum length of {MAX_TAB_NAME_LENGTH} characters"
    
    # Allow letters, numbers, spaces, underscores, hyphens, and basic punctuation
    if not re.match(r'^[a-zA-Z0-9 _\-.,!?()]+$', tab_name):
        return False, "Tab name can only contain letters, numbers, spaces, and basic punctuation"
    
    return True, None

def validate_content(content: str) -> Tuple[bool, Optional[str]]:
    """Validate content size"""
    content_size = len(content.encode('utf-8'))
    if content_size > MAX_CONTENT_SIZE_BYTES:
        return False, f"Content exceeds maximum size of {MAX_CONTENT_SIZE_BYTES} bytes"
    
    return True, None

def export_as_text(content: str, username: str) -> str:
    """Export content as plain text"""
    return f"SecureText Vault Export\nUsername: {username}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{content}"

def export_as_json(content: str, username: str) -> str:
    """Export content as JSON"""
    export_data = {
        "username": username,
        "export_date": datetime.now().isoformat(),
        "content": content,
        "content_length": len(content),
        "application": "SecureText Vault"
    }
    return json.dumps(export_data, indent=2, ensure_ascii=False)

def export_as_markdown(content: str, username: str) -> str:
    """Export content as Markdown"""
    return f"""# SecureText Vault Export

**Username:** {username}  
**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

---

{content}
"""

EXPORT_FUNCTIONS = {
    "txt": export_as_text,
    "json": export_as_json,
    "md": export_as_markdown
}

EXPORT_MIME_TYPES = {
    "txt": "text/plain",
    "json": "application/json",
    "md": "text/markdown"
}

def show_setup_instructions():
    """Show setup instructions when Supabase is not configured"""
    st.title("🔐 SecureText Vault - Setup Required")
    
    st.error("⚠️ Supabase configuration is required to run this application.")
    
    st.markdown("""
    ### Configuration Steps:
    
    1. **Get your Supabase credentials:**
       - Go to your [Supabase project dashboard](https://app.supabase.com)
       - Navigate to **Settings > API**
       - Copy these three values:
         - **Project URL** (e.g., `https://xxxxxxxxxxxx.supabase.co`)
         - **anon/public key** (starts with `eyJ...`)
         - **service_role key** (starts with `eyJ...`)
    
    2. **Update the `.env` file:**
       - Open `/workspace/.env` in the editor
       - Replace the placeholder values with your actual credentials
    
    3. **Create database tables:**
       - Run the setup script: `python setup_database.py`
       - Or execute the SQL manually in Supabase SQL Editor
    
    4. **Restart the application**
    """)
    
    st.info("💡 **Tip:** You can find the `.env` file in the file browser on the right side panel.")

def create_site_page():
    """Page for creating a new site"""
    st.title("🏗️ Create New Site")
    
    st.markdown("""
    Create a new password-protected text storage site with a unique username.
    Your site will be accessible only with your username and password.
    """)
    
    with st.form("create_site_form"):
        username = st.text_input(
            "Username (3-50 characters, letters, numbers, underscores, hyphens)",
            placeholder="e.g., my_secure_notes",
            help="This will be part of your site URL"
        )
        
        password = st.text_input(
            "Password (8-100 characters)",
            type="password",
            placeholder="Enter a strong password",
            help="Choose a secure password you'll remember"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password"
        )
        
        submitted = st.form_submit_button("Create Site")
        
        if submitted:
            # Validate inputs
            if not username or not password:
                st.error("Please fill in all fields")
                return
            
            if password != confirm_password:
                st.error("Passwords do not match")
                return
            
            # Create site
            success, message, site = auth_service.create_site(username, password)
            
            if success:
                st.success(f"✅ Site created successfully!")
                st.info(f"**Username:** {username}")
                st.info("**Important:** Save your password securely. It cannot be recovered if lost.")
                
                # Create session and redirect to site
                session_token = auth_service.create_session_token(site['id'], username)
                st.session_state['session_token'] = session_token
                st.session_state['current_site'] = site
                st.rerun()
            else:
                st.error(f"❌ {message}")

def access_site_page():
    """Page for accessing an existing site"""
    st.title("🔑 Access Existing Site")
    
    st.markdown("""
    Enter your username and password to access your secure text storage.
    """)
    
    with st.form("access_site_form"):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            help="The username you created when setting up your site"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="The password for your site"
        )
        
        submitted = st.form_submit_button("Access Site")
        
        if submitted:
            if not username or not password:
                st.error("Please enter both username and password")
                return
            
            # Authenticate
            success, message, site = auth_service.authenticate_site(username, password)
            
            if success:
                st.success("✅ Authentication successful!")
                
                # Create session and redirect to site
                session_token = auth_service.create_session_token(site['id'], username)
                st.session_state['session_token'] = session_token
                st.session_state['current_site'] = site
                st.rerun()
            else:
                st.error(f"❌ {message}")

def site_management_page(site):
    """Main site management page"""
    st.title(f"📝 {site['username']}'s SecureText Vault")
    
    # Initialize session state for tabs
    if 'current_tab' not in st.session_state:
        st.session_state['current_tab'] = None
    if 'tabs' not in st.session_state:
        st.session_state['tabs'] = []
    
    # Sidebar for site management
    with st.sidebar:
        st.header("Site Management")
        
        # Display site info
        st.subheader("Site Info")
        st.write(f"**Username:** {site['username']}")
        st.write(f"**Created:** {site['created_at'][:10] if site['created_at'] else 'N/A'}")
        
        # Tab management
        st.subheader("Tabs")
        
        # Get tabs from database
        tabs = supabase_client.get_tabs_by_site(site['id'])
        st.session_state['tabs'] = tabs
        
        if tabs:
            tab_names = [tab['tab_name'] for tab in tabs]
            current_tab_name = st.selectbox(
                "Select Tab",
                tab_names,
                index=0 if not st.session_state['current_tab'] else tab_names.index(st.session_state['current_tab']['tab_name'])
            )
            
            # Find the selected tab
            selected_tab = next((tab for tab in tabs if tab['tab_name'] == current_tab_name), None)
            st.session_state['current_tab'] = selected_tab
            
            # Create new tab button
            if len(tabs) < MAX_TABS_PER_SITE:
                if st.button("➕ New Tab"):
                    with st.form("new_tab_form"):
                        new_tab_name = st.text_input("Tab Name", placeholder="Enter tab name", max_chars=MAX_TAB_NAME_LENGTH)
                        create_clicked = st.form_submit_button("Create")
                        
                        if create_clicked and new_tab_name:
                            # Validate tab name
                            is_valid, error_msg = validate_tab_name(new_tab_name)
                            if not is_valid:
                                st.error(f"Invalid tab name: {error_msg}")
                            else:
                                # Check if tab name already exists
                                if new_tab_name in tab_names:
                                    st.error(f"Tab '{new_tab_name}' already exists")
                                else:
                                    new_tab = supabase_client.create_tab(site['id'], new_tab_name, len(tabs))
                                    if new_tab:
                                        st.success(f"Tab '{new_tab_name}' created!")
                                        st.rerun()
        else:
            # Create first tab
            st.info("No tabs yet. Create your first tab below.")
            with st.form("first_tab_form"):
                new_tab_name = st.text_input("First Tab Name", value=DEFAULT_TAB_NAME, max_chars=MAX_TAB_NAME_LENGTH)
                create_clicked = st.form_submit_button("Create First Tab")
                
                if create_clicked and new_tab_name:
                    # Validate tab name
                    is_valid, error_msg = validate_tab_name(new_tab_name)
                    if not is_valid:
                        st.error(f"Invalid tab name: {error_msg}")
                    else:
                        new_tab = supabase_client.create_tab(site['id'], new_tab_name, 0)
                        if new_tab:
                            st.success(f"Tab '{new_tab_name}' created!")
                            st.rerun()
        
        # Export options
        st.subheader("Export")
        export_format = st.selectbox("Format", options=list(EXPORT_OPTIONS.keys()), format_func=lambda x: EXPORT_OPTIONS[x])
        
        if st.button("📥 Export Content"):
            if st.session_state['current_tab']:
                content = st.session_state['current_tab'].get('content', '')
                if content:
                    export_function = EXPORT_FUNCTIONS.get(export_format)
                    if export_function:
                        export_data = export_function(content, site['username'])
                        
                        st.download_button(
                            label=f"Download as {EXPORT_OPTIONS[export_format]}",
                            data=export_data,
                            file_name=f"{site['username']}_content.{export_format}",
                            mime=EXPORT_MIME_TYPES.get(export_format, "text/plain")
                        )
                    else:
                        st.error(f"Export format '{export_format}' not supported")
                else:
                    st.warning("No content to export")
            else:
                st.warning("Select a tab to export")
        
        # Logout button
        if st.button("🚪 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content area
    if st.session_state['current_tab']:
        tab = st.session_state['current_tab']
        
        st.header(f"📄 {tab['tab_name']}")
        
        # Content editor
        content = st.text_area(
            "Content",
            value=tab.get('content', ''),
            height=400,
            placeholder="Start typing your secure notes here...",
            key=f"editor_{tab['id']}"
        )
        
        # Character count and size warning
        char_count = len(content)
        content_size = len(content.encode('utf-8'))
        size_percentage = (content_size / MAX_CONTENT_SIZE_BYTES) * 100
        
        st.caption(f"Characters: {char_count} | Size: {content_size:,} bytes ({size_percentage:.1f}% of limit)")
        
        if content_size > MAX_CONTENT_SIZE_BYTES:
            st.error(f"⚠️ Content exceeds maximum size of {MAX_CONTENT_SIZE_BYTES:,} bytes")
        
        # Save button
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 Save", type="primary"):
                if content != tab.get('content', ''):
                    # Validate content size
                    is_valid, error_msg = validate_content(content)
                    if not is_valid:
                        st.error(f"Cannot save: {error_msg}")
                    else:
                        try:
                            updated_tab = supabase_client.update_tab_content(tab['id'], content)
                            if updated_tab:
                                st.success("Content saved!")
                                # Update local state
                                tab['content'] = content
                                tab['updated_at'] = updated_tab.get('updated_at')
                                st.session_state['current_tab'] = tab
                                st.rerun()
                            else:
                                st.error("Failed to save content")
                        except Exception as e:
                            st.error(f"Error saving content: {str(e)}")
                else:
                    st.info("No changes to save")
        
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # Last updated
        if tab.get('updated_at'):
            st.caption(f"Last updated: {tab['updated_at']}")
    else:
        st.info("👈 Select or create a tab from the sidebar to start writing")

def main():
    """Main application entry point"""
    # Page configuration
    st.set_page_config(
        page_title="SecureText Vault",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
    }
    .stTextInput > div > div > input {
        font-family: monospace;
    }
    .warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check if Supabase is configured
    try:
        config.validate()
    except ValueError as e:
        show_setup_instructions()
        return
    
    # Initialize session state
    if 'session_token' not in st.session_state:
        st.session_state['session_token'] = None
    if 'current_site' not in st.session_state:
        st.session_state['current_site'] = None
    
    # Check for valid session
    if st.session_state['session_token']:
        valid, message, site = auth_service.validate_session_token(st.session_state['session_token'])
        if valid and site:
            st.session_state['current_site'] = site
            site_management_page(site)
            return
        else:
            # Invalid session, clear it
            st.session_state['session_token'] = None
            st.session_state['current_site'] = None
    
    # Show landing page
    st.title("🔐 SecureText Vault")
    st.markdown("""
    ### Password-protected text storage with multi-tab support
    
    Store your notes, code snippets, or any text securely with:
    - 🔐 **Password protection** - Only you can access your content
    - 🏷️ **Multi-tab organization** - Organize content in separate tabs
    - 💾 **Auto-save** - Your content is saved automatically
    - 📥 **Export options** - Download as TXT, JSON, or Markdown
    - 🌐 **Unique URLs** - Each site has a unique username-based URL
    
    **How it works:**
    1. Create a site with a unique username and password
    2. Access your site anytime with your credentials
    3. Organize content in multiple tabs
    4. Export your data when needed
    """)
    
    # Security notice
    st.markdown("""
    <div class="warning">
    <strong>⚠️ Security Notice:</strong><br>
    - Use a strong, unique password for each site<br>
    - Never share your password with anyone<br>
    - Export and backup your important content regularly<br>
    - This service uses bcrypt password hashing and secure session tokens
    </div>
    """, unsafe_allow_html=True)
    
    # Create two columns for site creation and access
    col1, col2 = st.columns(2)
    
    with col1:
        create_site_page()
    
    with col2:
        access_site_page()
    
    # Footer
    st.markdown("---")
    st.caption("🔒 **SecureText Vault** - Your text, your control, always secure")

if __name__ == "__main__":
    main()
