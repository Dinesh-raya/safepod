# SecureText Vault 🔐

A password-protected text storage website similar to protectedtext.com, built with Streamlit and Supabase.

## Features

- 🔐 **Password Protection**: Each site is protected with a unique username and password
- 🏷️ **Multi-Tab Support**: Organize your content in multiple tabs
- 💾 **Auto-Save**: Content is automatically saved as you type
- 📥 **Export Options**: Download your content as Text, JSON, or Markdown
- 🌐 **Unique URLs**: Each site has a unique username-based identifier
- 🔒 **Secure Storage**: Passwords are hashed with bcrypt, content stored in Supabase
- 📱 **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### 1. Install Dependencies
```bash
uv pip install -r requirements.txt
```

### 2. Configure Supabase

#### Step 1: Create a Supabase Project
1. Go to [Supabase](https://supabase.com) and sign up/login
2. Create a new project
3. Wait for the project to be provisioned

#### Step 2: Get Your Credentials
1. Go to **Project Settings > API**
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxxxxxxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)
   - **service_role key** (starts with `eyJ...`)

#### Step 3: Update Environment Variables
Edit the `.env` file in the workspace:
```bash
# Supabase Configuration
SUPABASE_URL=your_actual_supabase_project_url_here
SUPABASE_KEY=your_actual_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_actual_supabase_service_key_here

# Application Configuration
SESSION_SECRET=generate_a_random_secret_string_here
BCRYPT_ROUNDS=12
MAX_CONTENT_SIZE_MB=1
RATE_LIMIT_PER_MINUTE=60
```

### 3. Setup Database

#### Option A: Run the Setup Script
```bash
python setup_database.py
```
Follow the instructions to copy and execute the SQL in Supabase SQL Editor.

#### Option B: Manual SQL Execution
1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the SQL from `setup_database.py` (lines 163-222)
4. Execute the SQL
5. Verify tables are created in **Table Editor**

### 4. Run the Application
```bash
streamlit run run_app.py
```

## Application Structure

```
/workspace/
├── app/
│   ├── __init__.py
│   ├── main.py              # Main Streamlit application
│   ├── config.py            # Configuration management
│   ├── constants.py         # Application constants
│   └── services/
│       ├── __init__.py
│       ├── supabase_client.py  # Supabase database operations
│       └── auth_service.py     # Authentication and site management
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .env                    # Your environment configuration
├── setup_database.py       # Database setup script
├── uuid.py                 # Custom UUID module (workaround)
├── run_app.py             # Wrapper script to run the app
└── README.md              # This file
```

## Database Schema

### Sites Table
Stores site information and authentication details.
```sql
CREATE TABLE sites (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    last_accessed TIMESTAMP WITH TIME ZONE
);
```

### Tabs Table
Stores content for each tab within a site.
```sql
CREATE TABLE tabs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
    tab_name VARCHAR(100) NOT NULL,
    tab_order INTEGER NOT NULL,
    content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);
```

### Access Logs Table
Logs access attempts for security monitoring.
```sql
CREATE TABLE access_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    ip_address INET,
    user_agent TEXT
);
```

## Usage Guide

### Creating a New Site
1. Open the application
2. Click "Create New Site"
3. Enter a unique username (3-50 characters)
4. Enter a strong password (8-100 characters)
5. Confirm the password
6. Click "Create Site"

### Accessing an Existing Site
1. Open the application
2. Click "Access Existing Site"
3. Enter your username and password
4. Click "Access Site"

### Managing Your Content
- **Create Tabs**: Use the sidebar to create new tabs (max 10 per site)
- **Edit Content**: Type in the main text area
- **Save**: Click the save button or content auto-saves
- **Export**: Use the sidebar to export as Text, JSON, or Markdown
- **Logout**: Click the logout button in the sidebar

## Security Features

- **Password Hashing**: Passwords are hashed using bcrypt with configurable rounds
- **Session Management**: Secure session tokens with expiration
- **Rate Limiting**: Configurable rate limiting for access attempts
- **Access Logging**: All access attempts are logged for security monitoring
- **Row Level Security**: Database tables use RLS policies for data isolation

## Troubleshooting

### Common Issues

1. **"Invalid URL" error**
   - Check your `.env` file has correct Supabase credentials
   - Ensure SUPABASE_URL starts with `https://`

2. **Database connection errors**
   - Verify database tables are created
   - Check Supabase project is active
   - Ensure service role key has proper permissions

3. **UUID module errors**
   - The application includes a custom `uuid.py` module as a workaround
   - Use `run_app.py` instead of running directly

4. **Streamlit not starting**
   - Check all dependencies are installed: `uv pip install -r requirements.txt`
   - Ensure port 8501 is available

### Getting Help

If you encounter issues:
1. Check the application shows setup instructions
2. Verify your `.env` file configuration
3. Ensure database tables are created
4. Check the browser console for errors

## Development

### Adding New Features
1. Update the database schema in `setup_database.py`
2. Add new methods to `supabase_client.py`
3. Update the Streamlit interface in `main.py`
4. Test thoroughly

### Testing
Run the application and test:
- Site creation and authentication
- Tab creation and management
- Content editing and saving
- Export functionality
- Session management

## License

This project is for educational and demonstration purposes.

## Support

For issues or questions, please check the application's setup instructions or consult the Supabase documentation.
