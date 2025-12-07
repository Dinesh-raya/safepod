"""Supabase client for database operations"""
import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.config import config

# Set up logging
logger = logging.getLogger(__name__)

class SupabaseClient:
    """Singleton Supabase client with lazy initialization"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    _service_client: Optional[Client] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
        return cls._instance
    
    def _ensure_initialized(self):
        """Initialize Supabase client if not already initialized"""
        if not self._initialized:
            try:
                config.validate()
                self._client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                self._initialized = True
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                # Don't raise here - let the individual methods handle it
                self._initialized = False
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance with lazy initialization"""
        self._ensure_initialized()
        if self._client is None:
            raise ConnectionError("Supabase client not initialized. Please check your configuration.")
        return self._client
    
    def get_service_client(self) -> Client:
        """Get Supabase client with service role key for admin operations"""
        try:
            if self._service_client is None:
                config.validate()
                self._service_client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
            return self._service_client
        except Exception as e:
            logger.error(f"Failed to create service client: {str(e)}")
            raise
    
    def _validate_input(self, field_name: str, value: str, max_length: Optional[int] = None) -> None:
        """Validate input data"""
        if not value or not isinstance(value, str):
            raise ValueError(f"{field_name} must be a non-empty string")
        
        if max_length and len(value) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length} characters")
    
    # Site operations
    def create_site(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Create a new site"""
        try:
            # Validate inputs
            self._validate_input("Username", username, 50)
            self._validate_input("Password hash", password_hash, 255)
            
            logger.info(f"Creating site for username: {username}")
            response = self.client.table('sites').insert({
                'username': username,
                'password_hash': password_hash,
                'is_active': True
            }).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Site created successfully for username: {username}")
                return response.data[0]
            logger.error("Failed to create site: No data returned")
            raise ValueError("Failed to create site: No data returned")
        except Exception as e:
            logger.error(f"Failed to create site for username {username}: {str(e)}")
            raise Exception(f"Failed to create site: {str(e)}")
    
    def get_site_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get site by username"""
        try:
            self._validate_input("Username", username, 50)
            
            logger.debug(f"Getting site by username: {username}")
            response = self.client.table('sites').select('*').eq('username', username).eq('is_active', True).execute()
            
            if response.data and len(response.data) > 0:
                logger.debug(f"Site found for username: {username}")
                return response.data[0]
            logger.debug(f"No site found for username: {username}")
            return None
        except Exception as e:
            logger.error(f"Failed to get site by username {username}: {str(e)}")
            raise Exception(f"Failed to get site: {str(e)}")
    
    def get_site_by_id(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get site by ID"""
        try:
            self._validate_input("Site ID", site_id, 36)
            
            logger.debug(f"Getting site by ID: {site_id}")
            response = self.client.table('sites').select('*').eq('id', site_id).eq('is_active', True).execute()
            
            if response.data and len(response.data) > 0:
                logger.debug(f"Site found for ID: {site_id}")
                return response.data[0]
            logger.debug(f"No site found for ID: {site_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get site by ID {site_id}: {str(e)}")
            raise Exception(f"Failed to get site by ID: {str(e)}")
    
    def update_site_last_accessed(self, site_id: str) -> bool:
        """Update site's last accessed timestamp"""
        try:
            self._validate_input("Site ID", site_id, 36)
            
            logger.debug(f"Updating last accessed for site ID: {site_id}")
            response = self.client.table('sites').update({
                'last_accessed': 'now()'
            }).eq('id', site_id).execute()
            
            logger.debug(f"Last accessed updated for site ID: {site_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to update last accessed for site ID {site_id}: {str(e)}")
            return False
    
    # Tab operations
    def create_tab(self, site_id: str, tab_name: str, tab_order: int = 0) -> Dict[str, Any]:
        """Create a new tab for a site"""
        try:
            self._validate_input("Site ID", site_id, 36)
            self._validate_input("Tab name", tab_name, 100)
            
            if not isinstance(tab_order, int) or tab_order < 0:
                raise ValueError("Tab order must be a non-negative integer")
            
            logger.info(f"Creating tab '{tab_name}' for site ID: {site_id}")
            response = self.client.table('tabs').insert({
                'site_id': site_id,
                'tab_name': tab_name,
                'tab_order': tab_order,
                'content': ''
            }).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Tab '{tab_name}' created successfully for site ID: {site_id}")
                return response.data[0]
            logger.error(f"Failed to create tab '{tab_name}': No data returned")
            raise ValueError("Failed to create tab: No data returned")
        except Exception as e:
            logger.error(f"Failed to create tab '{tab_name}' for site ID {site_id}: {str(e)}")
            raise Exception(f"Failed to create tab: {str(e)}")
    
    def get_tabs_by_site(self, site_id: str) -> List[Dict[str, Any]]:
        """Get all tabs for a site, ordered by tab_order"""
        try:
            self._validate_input("Site ID", site_id, 36)
            
            logger.debug(f"Getting tabs for site ID: {site_id}")
            response = self.client.table('tabs').select('*').eq('site_id', site_id).order('tab_order').execute()
            
            tabs = response.data if response.data else []
            logger.debug(f"Found {len(tabs)} tabs for site ID: {site_id}")
            return tabs
        except Exception as e:
            logger.error(f"Failed to get tabs for site ID {site_id}: {str(e)}")
            raise Exception(f"Failed to get tabs: {str(e)}")
    
    def update_tab_content(self, tab_id: str, content: str) -> Dict[str, Any]:
        """Update tab content"""
        try:
            self._validate_input("Tab ID", tab_id, 36)
            
            # Validate content size
            from app.constants import MAX_CONTENT_SIZE_BYTES
            content_size = len(content.encode('utf-8'))
            if content_size > MAX_CONTENT_SIZE_BYTES:
                raise ValueError(f"Content exceeds maximum size of {MAX_CONTENT_SIZE_BYTES} bytes")
            
            logger.info(f"Updating content for tab ID: {tab_id} (size: {content_size} bytes)")
            response = self.client.table('tabs').update({
                'content': content,
                'updated_at': 'now()'
            }).eq('id', tab_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Content updated for tab ID: {tab_id}")
                return response.data[0]
            logger.error(f"Failed to update tab content for tab ID {tab_id}: No data returned")
            raise ValueError("Failed to update tab: No data returned")
        except Exception as e:
            logger.error(f"Failed to update tab content for tab ID {tab_id}: {str(e)}")
            raise Exception(f"Failed to update tab content: {str(e)}")
    
    def update_tab_name(self, tab_id: str, tab_name: str) -> Dict[str, Any]:
        """Update tab name"""
        try:
            self._validate_input("Tab ID", tab_id, 36)
            self._validate_input("Tab name", tab_name, 100)
            
            logger.info(f"Updating tab name to '{tab_name}' for tab ID: {tab_id}")
            response = self.client.table('tabs').update({
                'tab_name': tab_name,
                'updated_at': 'now()'
            }).eq('id', tab_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Tab name updated to '{tab_name}' for tab ID: {tab_id}")
                return response.data[0]
            logger.error(f"Failed to update tab name for tab ID {tab_id}: No data returned")
            raise ValueError("Failed to update tab name: No data returned")
        except Exception as e:
            logger.error(f"Failed to update tab name for tab ID {tab_id}: {str(e)}")
            raise Exception(f"Failed to update tab name: {str(e)}")
    
    def delete_tab(self, tab_id: str) -> bool:
        """Delete a tab"""
        try:
            self._validate_input("Tab ID", tab_id, 36)
            
            logger.warning(f"Deleting tab ID: {tab_id}")
            response = self.client.table('tabs').delete().eq('id', tab_id).execute()
            
            logger.warning(f"Tab deleted: {tab_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete tab {tab_id}: {str(e)}")
            raise Exception(f"Failed to delete tab: {str(e)}")
    
    def update_tab_order(self, site_id: str, tab_order_mapping: Dict[str, int]) -> bool:
        """Update tab order for multiple tabs"""
        try:
            self._validate_input("Site ID", site_id, 36)
            
            if not isinstance(tab_order_mapping, dict):
                raise ValueError("Tab order mapping must be a dictionary")
            
            logger.info(f"Updating tab order for site ID: {site_id}")
            for tab_id, order in tab_order_mapping.items():
                self._validate_input("Tab ID", tab_id, 36)
                if not isinstance(order, int) or order < 0:
                    raise ValueError(f"Invalid order value for tab {tab_id}: must be non-negative integer")
                
                self.client.table('tabs').update({
                    'tab_order': order
                }).eq('id', tab_id).eq('site_id', site_id).execute()
            
            logger.info(f"Tab order updated for site ID: {site_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update tab order for site ID {site_id}: {str(e)}")
            raise Exception(f"Failed to update tab order: {str(e)}")
    
    # Access logs
    def log_access(self, site_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Log site access"""
        try:
            self._validate_input("Site ID", site_id, 36)
            
            log_data = {
                'site_id': site_id,
                'accessed_at': 'now()'
            }
            
            if ip_address:
                self._validate_input("IP address", ip_address, 45)
                log_data['ip_address'] = ip_address
            
            if user_agent:
                self._validate_input("User agent", user_agent, 500)
                log_data['user_agent'] = user_agent
            
            logger.debug(f"Logging access for site ID: {site_id}")
            self.client.table('access_logs').insert(log_data).execute()
            
            logger.debug(f"Access logged for site ID: {site_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to log access for site ID {site_id}: {str(e)}")
            return False

# Global instance - note: initialization is lazy
supabase_client = SupabaseClient()
