"""Supabase client for database operations"""
import os
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from app.config import config

class SupabaseClient:
    """Singleton Supabase client"""
    
    _instance: Optional['SupabaseClient'] = None
    _client: Optional[Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Supabase client"""
        try:
            config.validate()
            self._client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        except Exception as e:
            raise ConnectionError(f"Failed to initialize Supabase client: {str(e)}")
    
    @property
    def client(self) -> Client:
        """Get Supabase client instance"""
        if self._client is None:
            self._initialize()
        return self._client
    
    def get_service_client(self) -> Client:
        """Get Supabase client with service role key for admin operations"""
        return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    
    # Site operations
    def create_site(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Create a new site"""
        try:
            response = self.client.table('sites').insert({
                'username': username,
                'password_hash': password_hash,
                'is_active': True
            }).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise ValueError("Failed to create site: No data returned")
        except Exception as e:
            raise Exception(f"Failed to create site: {str(e)}")
    
    def get_site_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get site by username"""
        try:
            response = self.client.table('sites').select('*').eq('username', username).eq('is_active', True).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise Exception(f"Failed to get site: {str(e)}")
    
    def get_site_by_id(self, site_id: str) -> Optional[Dict[str, Any]]:
        """Get site by ID"""
        try:
            response = self.client.table('sites').select('*').eq('id', site_id).eq('is_active', True).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            raise Exception(f"Failed to get site by ID: {str(e)}")
    
    def update_site_last_accessed(self, site_id: str) -> bool:
        """Update site's last accessed timestamp"""
        try:
            response = self.client.table('sites').update({
                'last_accessed': 'now()'
            }).eq('id', site_id).execute()
            
            return True
        except Exception as e:
            print(f"Warning: Failed to update last accessed: {str(e)}")
            return False
    
    # Tab operations
    def create_tab(self, site_id: str, tab_name: str, tab_order: int = 0) -> Dict[str, Any]:
        """Create a new tab for a site"""
        try:
            response = self.client.table('tabs').insert({
                'site_id': site_id,
                'tab_name': tab_name,
                'tab_order': tab_order,
                'content': ''
            }).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise ValueError("Failed to create tab: No data returned")
        except Exception as e:
            raise Exception(f"Failed to create tab: {str(e)}")
    
    def get_tabs_by_site(self, site_id: str) -> List[Dict[str, Any]]:
        """Get all tabs for a site, ordered by tab_order"""
        try:
            response = self.client.table('tabs').select('*').eq('site_id', site_id).order('tab_order').execute()
            
            return response.data if response.data else []
        except Exception as e:
            raise Exception(f"Failed to get tabs: {str(e)}")
    
    def update_tab_content(self, tab_id: str, content: str) -> Dict[str, Any]:
        """Update tab content"""
        try:
            response = self.client.table('tabs').update({
                'content': content,
                'updated_at': 'now()'
            }).eq('id', tab_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise ValueError("Failed to update tab: No data returned")
        except Exception as e:
            raise Exception(f"Failed to update tab content: {str(e)}")
    
    def update_tab_name(self, tab_id: str, tab_name: str) -> Dict[str, Any]:
        """Update tab name"""
        try:
            response = self.client.table('tabs').update({
                'tab_name': tab_name,
                'updated_at': 'now()'
            }).eq('id', tab_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise ValueError("Failed to update tab name: No data returned")
        except Exception as e:
            raise Exception(f"Failed to update tab name: {str(e)}")
    
    def delete_tab(self, tab_id: str) -> bool:
        """Delete a tab"""
        try:
            response = self.client.table('tabs').delete().eq('id', tab_id).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete tab: {str(e)}")
    
    def update_tab_order(self, site_id: str, tab_order_mapping: Dict[str, int]) -> bool:
        """Update tab order for multiple tabs"""
        try:
            for tab_id, order in tab_order_mapping.items():
                self.client.table('tabs').update({
                    'tab_order': order
                }).eq('id', tab_id).eq('site_id', site_id).execute()
            return True
        except Exception as e:
            raise Exception(f"Failed to update tab order: {str(e)}")
    
    # Access logs
    def log_access(self, site_id: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Log site access"""
        try:
            log_data = {
                'site_id': site_id,
                'accessed_at': 'now()'
            }
            
            if ip_address:
                log_data['ip_address'] = ip_address
            if user_agent:
                log_data['user_agent'] = user_agent
            
            self.client.table('access_logs').insert(log_data).execute()
            return True
        except Exception as e:
            print(f"Warning: Failed to log access: {str(e)}")
            return False

# Global instance
supabase_client = SupabaseClient()