"""Database setup script for SecureText Vault"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import config

def get_setup_sql():
    """Return the SQL for setting up the database"""
    return """
-- Create sites table
CREATE TABLE IF NOT EXISTS sites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE,
    CONSTRAINT username_pattern CHECK (username ~ '^[a-zA-Z0-9_-]+$'),
    CONSTRAINT username_length CHECK (LENGTH(username) BETWEEN 3 AND 50)
);

-- Create tabs table
CREATE TABLE IF NOT EXISTS tabs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    tab_name VARCHAR(100) NOT NULL,
    tab_order INTEGER DEFAULT 0,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    CONSTRAINT unique_tab_per_site UNIQUE(site_id, tab_name)
);

-- Create access_logs table
CREATE TABLE IF NOT EXISTS access_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id UUID NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sites_username ON sites(username) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_sites_last_accessed ON sites(last_accessed);
CREATE INDEX IF NOT EXISTS idx_tabs_site_id ON tabs(site_id);
CREATE INDEX IF NOT EXISTS idx_tabs_site_order ON tabs(site_id, tab_order);
CREATE INDEX IF NOT EXISTS idx_access_logs_site_id ON access_logs(site_id);
CREATE INDEX IF NOT EXISTS idx_access_logs_accessed_at ON access_logs(accessed_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE tabs ENABLE ROW LEVEL SECURITY;
ALTER TABLE access_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for sites table
-- Allow anyone to insert new sites (site creation)
CREATE POLICY "allow_insert_sites" ON sites FOR INSERT WITH CHECK (true);

-- Allow anyone to select active sites (for authentication)
CREATE POLICY "allow_select_active_sites" ON sites FOR SELECT USING (is_active = TRUE);

-- Allow updates to sites (for last_accessed timestamp)
CREATE POLICY "allow_update_sites" ON sites FOR UPDATE USING (true);

-- RLS Policies for tabs table
-- Allow insert for any authenticated user (through application logic)
CREATE POLICY "allow_insert_tabs" ON tabs FOR INSERT WITH CHECK (true);

-- Allow select for any authenticated user
CREATE POLICY "allow_select_tabs" ON tabs FOR SELECT USING (true);

-- Allow update for any authenticated user
CREATE POLICY "allow_update_tabs" ON tabs FOR UPDATE USING (true);

-- Allow delete for any authenticated user
CREATE POLICY "allow_delete_tabs" ON tabs FOR DELETE USING (true);

-- RLS Policies for access_logs table
-- Allow insert for any authenticated user
CREATE POLICY "allow_insert_access_logs" ON access_logs FOR INSERT WITH CHECK (true);

-- Allow select for any authenticated user (site owners can see their logs)
CREATE POLICY "allow_select_access_logs" ON access_logs FOR SELECT USING (true);
"""

def main():
    """Main setup function"""
    print("=" * 60)
    print("SecureText Vault - Database Setup")
    print("=" * 60)
    
    try:
        # Validate configuration
        config.validate()
        print("✓ Configuration validated")
        print("\nYour Supabase credentials are properly configured!")
    except ValueError as e:
        print(f"✗ Configuration error: {str(e)}")
        print("\nPlease set the following environment variables in your .env file:")
        print("1. SUPABASE_URL - Your Supabase project URL")
        print("2. SUPABASE_KEY - Your Supabase anon/public key")
        print("3. SUPABASE_SERVICE_KEY - Your Supabase service role key")
        print("\nYou can find these in your Supabase project settings > API")
        print("\nExample .env file content:")
        print("SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co")
        print("SUPABASE_KEY=eyJ... (your anon key)")
        print("SUPABASE_SERVICE_KEY=eyJ... (your service role key)")
        print("SESSION_SECRET=your_random_secret_string")
        print("BCRYPT_ROUNDS=12")
        print("MAX_CONTENT_SIZE_MB=1")
        print("RATE_LIMIT_PER_MINUTE=60")
    
    print("\n" + "=" * 60)
    print("Database Setup Instructions")
    print("=" * 60)
    
    print("\nTo set up the database, follow these steps:")
    print("\n1. Go to your Supabase project dashboard")
    print("2. Navigate to SQL Editor")
    print("3. Copy the SQL below and paste it into the SQL Editor")
    print("4. Click 'Run' to execute the SQL")
    print("5. Verify tables are created in the Table Editor")
    
    print("\n" + "=" * 60)
    print("SQL for Database Setup")
    print("=" * 60)
    print(get_setup_sql())
    
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\nAfter setting up the database:")
    print("1. Run the application: streamlit run run_app.py")
    print("2. Open your browser to http://localhost:8501")
    print("3. Create your first secure text storage site!")
    
    print("\nSetup instructions completed!")

if __name__ == "__main__":
    main()