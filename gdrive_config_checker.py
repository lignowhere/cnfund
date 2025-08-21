#!/usr/bin/env python3
"""
Google Drive Configuration Checker
Kiểm tra và validate cấu hình Google Drive
"""

import os
import json
from pathlib import Path
import sys


def check_service_account_json():
    """Kiểm tra service account JSON"""
    print("\n🔍 Checking service_account.json...")
    
    service_file = Path('service_account.json')
    if not service_file.exists():
        print("❌ service_account.json not found")
        return False
    
    try:
        with open(service_file, 'r') as f:
            data = json.load(f)
        
        # Required fields
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        print("✅ service_account.json found")
        print(f"📊 File size: {service_file.stat().st_size:,} bytes")
        
        missing_fields = []
        for field in required_fields:
            if field in data:
                if field == 'private_key':
                    print(f"  ✅ {field}: {data[field][:50]}...")
                elif field == 'client_email':
                    print(f"  ✅ {field}: {data[field]}")
                else:
                    print(f"  ✅ {field}: {str(data[field])[:50]}")
            else:
                missing_fields.append(field)
                print(f"  ❌ {field}: MISSING")
        
        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False
        
        # Validate type
        if data.get('type') != 'service_account':
            print(f"❌ Invalid type: {data.get('type')} (should be 'service_account')")
            return False
        
        # Validate private key format
        private_key = data.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ Invalid private key format")
            return False
        
        # Validate email format
        client_email = data.get('client_email', '')
        if '@' not in client_email or not client_email.endswith('.iam.gserviceaccount.com'):
            print(f"❌ Invalid client_email format: {client_email}")
            return False
        
        print("✅ service_account.json is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def check_streamlit_secrets():
    """Kiểm tra Streamlit secrets"""
    print("\n🔍 Checking Streamlit secrets...")
    
    secrets_file = Path('.streamlit/secrets.toml')
    if not secrets_file.exists():
        print("❌ .streamlit/secrets.toml not found")
        return False
    
    try:
        # Simple TOML parsing (basic)
        with open(secrets_file, 'r') as f:
            content = f.read()
        
        print("✅ .streamlit/secrets.toml found")
        print(f"📊 File size: {secrets_file.stat().st_size:,} bytes")
        
        # Check for google_service_account section
        if '[google_service_account]' in content:
            print("✅ [google_service_account] section found")
            
            # Check for required fields in content
            required_fields = [
                'type', 'project_id', 'private_key_id', 'private_key',
                'client_email', 'client_id'
            ]
            
            for field in required_fields:
                if f'{field}=' in content or f'{field} =' in content:
                    print(f"  ✅ {field}: Found")
                else:
                    print(f"  ❌ {field}: Missing")
            
            return True
        else:
            print("❌ [google_service_account] section not found")
            return False
            
    except Exception as e:
        print(f"❌ Error reading secrets file: {e}")
        return False

def check_environment_variables():
    """Kiểm tra environment variables"""
    print("\n🔍 Checking environment variables...")
    
    # Check GOOGLE_SERVICE_ACCOUNT_JSON
    env_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    if not env_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not set")
        return False
    
    try:
        data = json.loads(env_json)
        print("✅ GOOGLE_SERVICE_ACCOUNT_JSON found")
        print(f"📊 JSON size: {len(env_json):,} characters")
        
        # Check required fields
        if data.get('type') == 'service_account':
            print("  ✅ type: service_account")
        else:
            print(f"  ❌ type: {data.get('type')} (invalid)")
            return False
            
        if data.get('client_email'):
            print(f"  ✅ client_email: {data['client_email']}")
        else:
            print("  ❌ client_email: missing")
            return False
        
        return True
        
    except json.JSONDecodeError:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error parsing environment variable: {e}")
        return False

def test_google_api_import():
    """Test Google API imports"""
    print("\n🔍 Testing Google API imports...")
    
    try:
        from google.oauth2 import service_account
        print("✅ google.oauth2.service_account imported")
    except ImportError:
        print("❌ google.oauth2.service_account failed")
        print("   Run: pip install google-auth")
        return False
    
    try:
        from googleapiclient.discovery import build
        print("✅ googleapiclient.discovery imported")
    except ImportError:
        print("❌ googleapiclient.discovery failed")
        print("   Run: pip install google-api-python-client")
        return False
    
    try:
        from googleapiclient.http import MediaIoBaseUpload
        print("✅ googleapiclient.http imported")
    except ImportError:
        print("❌ googleapiclient.http failed")
        return False
    
    try:
        from googleapiclient.errors import HttpError
        print("✅ googleapiclient.errors imported")
    except ImportError:
        print("❌ googleapiclient.errors failed")
        return False
    
    return True

def test_basic_authentication():
    """Test basic Google authentication"""
    print("\n🔍 Testing basic Google authentication...")
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        # Try to load credentials from available sources
        creds = None
        cred_source = None
        
        # Method 1: service_account.json
        service_file = Path('service_account.json')
        if service_file.exists():
            try:
                creds = service_account.Credentials.from_service_account_file(
                    str(service_file),
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                cred_source = "service_account.json"
                print(f"✅ Credentials loaded from: {cred_source}")
            except Exception as e:
                print(f"❌ Failed to load from service_account.json: {e}")
        
        # Method 2: Environment variable
        if not creds:
            env_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if env_json:
                try:
                    service_account_info = json.loads(env_json)
                    creds = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                    cred_source = "Environment Variable"
                    print(f"✅ Credentials loaded from: {cred_source}")
                except Exception as e:
                    print(f"❌ Failed to load from environment variable: {e}")
        
        if not creds:
            print("❌ No valid credentials found")
            return False
        
        # Test API connection
        print("🔗 Testing Google Drive API connection...")
        service = build('drive', 'v3', credentials=creds)
        
        # Simple API call to test connection
        about = service.about().get(fields="user").execute()
        user_info = about.get('user', {})
        
        print(f"✅ Successfully connected to Google Drive API")
        print(f"👤 Connected as: {user_info.get('displayName', 'Unknown')}")
        print(f"📧 Email: {user_info.get('emailAddress', 'Unknown')}")
        
        # Test folder operations
        print("📁 Testing folder operations...")
        try:
            # Create a test folder
            test_folder_name = f"Test_Folder_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_metadata = {
                'name': test_folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = service.files().create(body=file_metadata, fields='id').execute()
            folder_id = folder.get('id')
            print(f"✅ Created test folder: {folder_id}")
            
            # List folder contents (should be empty)
            results = service.files().list(
                q=f"'{folder_id}' in parents",
                fields="files(id, name)"
            ).execute()
            files = results.get('files', [])
            print(f"✅ Listed folder contents: {len(files)} files")
            
            # Delete test folder
            service.files().delete(fileId=folder_id).execute()
            print("✅ Deleted test folder")
            
        except Exception as folder_error:
            print(f"⚠️ Folder operations failed: {folder_error}")
            # This might fail due to permissions, but basic auth still works
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        import traceback
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

def create_sample_config_files():
    """Create sample configuration files"""
    print("\n🛠️ Creating sample configuration files...")
    
    # Sample secrets.toml
    secrets_dir = Path('.streamlit')
    secrets_dir.mkdir(exist_ok=True)
    
    secrets_file = secrets_dir / 'secrets.toml'
    if not secrets_file.exists():
        sample_secrets = '''# Supabase PostgreSQL Configuration
database_url = "your_database_url_here"

# Admin password for application
ADMIN_PASSWORD = "1997"

[google_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
'''
        with open(secrets_file, 'w') as f:
            f.write(sample_secrets)
        print(f"✅ Created sample: {secrets_file}")
        print("   ⚠️ Please update with your actual credentials")
    else:
        print(f"✅ {secrets_file} already exists")
    
    # Sample service_account.json template
    if not Path('service_account.json').exists():
        sample_service_account = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "your-private-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY_HERE\n-----END PRIVATE KEY-----\n",
            "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        with open('service_account_template.json', 'w') as f:
            json.dump(sample_service_account, f, indent=2)
        print("✅ Created sample: service_account_template.json")
        print("   ⚠️ Rename to service_account.json and update with your credentials")

def show_setup_instructions():
    """Show detailed setup instructions"""
    print("\n📋 Google Drive Setup Instructions:")
    print("=" * 50)
    
    print("""
🔧 Step 1: Create Google Cloud Project
   1. Go to https://console.cloud.google.com/
   2. Create a new project or select existing one
   3. Enable Google Drive API in API Library

🔑 Step 2: Create Service Account
   1. Go to IAM & Admin > Service Accounts
   2. Click "Create Service Account"
   3. Give it a name and description
   4. Skip role assignment (optional step)
   5. Click "Create and Continue"

🗝️ Step 3: Generate Service Account Key
   1. Click on created service account
   2. Go to "Keys" tab
   3. Click "Add Key" > "Create new key"
   4. Choose JSON format
   5. Download the JSON file

📁 Step 4: Configure Credentials
   Choose ONE of these methods:

   Method A - Local File:
   • Rename downloaded JSON to 'service_account.json'
   • Place in your project root directory

   Method B - Streamlit Secrets:
   • Copy JSON content to .streamlit/secrets.toml
   • Under [google_service_account] section

   Method C - Environment Variable:
   • Set GOOGLE_SERVICE_ACCOUNT_JSON with JSON content
   • export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

🚀 Step 5: Test Configuration
   • Run this script: python gdrive_config_checker.py
   • Run export test: python enhanced_test_export.py

⚠️ Important Notes:
   • Keep service account JSON secure and private
   • Don't commit service_account.json to version control
   • Add service_account.json to .gitignore
   • Service account needs Google Drive API access
    """)

def main():
    """Main configuration checker"""
    print("=" * 60)
    print("🔧 Google Drive Configuration Checker")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Import datetime
    from datetime import datetime
    
    checks = [
        ("Google API Libraries", test_google_api_import),
        ("Service Account JSON", check_service_account_json),
        ("Streamlit Secrets", check_streamlit_secrets),
        ("Environment Variables", check_environment_variables),
        ("Basic Authentication", test_basic_authentication)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            success = check_func()
            results.append((check_name, success))
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Configuration Check Summary:")
    print("=" * 60)
    
    for check_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{check_name:<25}: {status}")
    
    passed_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n🎯 Result: {passed_count}/{total_count} checks passed")
    
    if passed_count == total_count:
        print("🎉 All configuration checks passed!")
        print("✅ Google Drive integration should work correctly")
    else:
        print("⚠️ Some configuration checks failed")
        
        # Show specific guidance
        failed_checks = [name for name, success in results if not success]
        
        if "Google API Libraries" in failed_checks:
            print("\n📦 Install required packages:")
            print("pip install google-api-python-client google-auth")
        
        if any(check in failed_checks for check in ["Service Account JSON", "Streamlit Secrets", "Environment Variables"]):
            print("\n🔧 Configuration needed:")
            create_sample_config_files()
            show_setup_instructions()
        
        if "Basic Authentication" in failed_checks and passed_count > 0:
            print("\n🔍 Authentication issues:")
            print("• Check service account permissions")
            print("• Verify Google Drive API is enabled")
            print("• Ensure service account has necessary roles")

if __name__ == "__main__":
    main()