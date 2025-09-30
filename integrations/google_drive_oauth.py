#!/usr/bin/env python3
"""
Google Drive OAuth Manager for Personal Accounts
Uses OAuth 2.0 flow to authenticate with personal Google account directly
"""

import os
import io
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING
import streamlit as st

# Google Drive API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow, InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    from googleapiclient.errors import HttpError
    GOOGLE_OAUTH_AVAILABLE = True
except ImportError:
    GOOGLE_OAUTH_AVAILABLE = False
    if TYPE_CHECKING:
        from google.oauth2.credentials import Credentials
    st.warning("⚠️ Google OAuth libraries not installed. Run: pip install google-auth-oauthlib")

if GOOGLE_OAUTH_AVAILABLE:
    class GoogleDriveOAuthManager:
        """OAuth-based Google Drive manager for personal accounts"""

        # OAuth scopes needed
        SCOPES = ['https://www.googleapis.com/auth/drive.file']

        def __init__(self):
            self.service = None
            self.folder_id = None
            self.connected = False
            self.credentials = None
            self.token_file = Path("token.pickle")
            self.credentials_file = Path("oauth_credentials.json")
        
            if GOOGLE_OAUTH_AVAILABLE:
                self._initialize_oauth_service()

        def _initialize_oauth_service(self):
            """Initialize OAuth service"""
            try:
                # Check if we have saved credentials
                creds = self._load_saved_credentials()

                if not creds:
                    # On cloud: Cannot do OAuth flow (no browser)
                    # On local: Can do OAuth flow
                    is_cloud = os.getenv('STREAMLIT_CLOUD') or '/mount/src' in os.getcwd()

                    if is_cloud:
                        print("❌ No OAuth token found in Streamlit secrets")
                        st.error("❌ OAuth token not found in secrets")
                        st.info("📖 Setup guide: docs/STREAMLIT_CLOUD_SETUP.md")
                        self.connected = False
                        return
                    else:
                        # Local: Try OAuth flow
                        print("🔐 Attempting OAuth flow (local only)...")
                        creds = self._do_oauth_flow()

                if creds:
                    # Build service
                    self.service = build('drive', 'v3', credentials=creds)
                    self.credentials = creds

                    # Get folder ID
                    self.folder_id = self._get_folder_id()

                    # Test connection
                    try:
                        about = self.service.about().get(fields="user").execute()
                        user = about.get('user', {})
                        print(f"✅ OAuth connected as: {user.get('emailAddress', 'Unknown')}")
                        self.connected = True
                    except Exception as test_error:
                        print(f"❌ OAuth connection test failed: {test_error}")
                        self.connected = False

            except Exception as e:
                print(f"❌ OAuth initialization failed: {e}")
                self.connected = False
    
        def _load_saved_credentials(self) -> Optional['Credentials']:
            """Load saved OAuth credentials from file or Streamlit secrets"""
            # Try from file first (for local development)
            try:
                if self.token_file.exists():
                    with open(self.token_file, 'rb') as token:
                        creds = pickle.load(token)

                    # Refresh if expired
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        # Save refreshed credentials
                        self._save_credentials(creds)

                    if creds and creds.valid:
                        print("✅ Using saved OAuth credentials from file")
                        return creds

            except Exception as e:
                print(f"⚠️ Could not load credentials from file: {e}")

            # Try from Streamlit secrets (for Streamlit Cloud)
            try:
                if hasattr(st, 'secrets') and 'oauth_token_base64' in st.secrets:
                    import base64

                    print("🔐 Loading OAuth token from Streamlit secrets...")

                    # Decode base64 token
                    token_data = base64.b64decode(st.secrets['oauth_token_base64'])
                    creds = pickle.loads(token_data)

                    # Refresh if expired
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        print("🔄 Token refreshed successfully")

                    if creds and creds.valid:
                        print("✅ Using OAuth credentials from Streamlit secrets")
                        return creds
                    else:
                        print("⚠️ Token from secrets is invalid")

            except Exception as e:
                print(f"⚠️ Could not load credentials from secrets: {e}")

            return None

        def _save_credentials(self, creds: 'Credentials'):
            """Save OAuth credentials"""
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                print("💾 OAuth credentials saved")
            except Exception as e:
                print(f"⚠️ Could not save credentials: {e}")
    
        def _do_oauth_flow(self) -> Optional['Credentials']:
            """Perform OAuth 2.0 flow"""
            try:
                # Try to get credentials from Streamlit secrets (for cloud)
                if hasattr(st, 'secrets') and 'oauth_credentials' in st.secrets:
                    print("🔐 Using OAuth credentials from Streamlit secrets...")
                    try:
                        import json
                        import tempfile

                        # Convert AttrDict to regular dict (Streamlit secrets issue)
                        def convert_to_dict(obj):
                            """Recursively convert AttrDict to dict"""
                            if hasattr(obj, 'to_dict'):
                                return obj.to_dict()
                            elif isinstance(obj, dict):
                                return {k: convert_to_dict(v) for k, v in obj.items()}
                            elif isinstance(obj, list):
                                return [convert_to_dict(item) for item in obj]
                            else:
                                return obj

                        # Create temp credentials file from secrets
                        creds_dict = convert_to_dict(st.secrets['oauth_credentials'])

                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                            json.dump(creds_dict, f)
                            temp_creds_file = f.name

                        # Create flow from temp file
                        flow = InstalledAppFlow.from_client_secrets_file(
                            temp_creds_file, self.SCOPES
                        )

                        # Clean up temp file
                        import os
                        os.unlink(temp_creds_file)

                    except Exception as e:
                        print(f"⚠️ Could not create flow from secrets: {e}")
                        st.error(f"❌ Error loading OAuth credentials from secrets: {e}")
                        return None

                # Try to get from file (for local development)
                elif self.credentials_file.exists():
                    # Create flow
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), self.SCOPES
                    )
                else:
                    st.error(f"❌ OAuth credentials not found")
                    st.info("📋 For local: Create oauth_credentials.json")
                    st.info("📋 For cloud: Add oauth_credentials to Streamlit secrets")
                    return None

                # For Streamlit, we need to use manual flow
                st.info("🔐 OAuth authentication required...")
                st.warning("⚠️ This requires manual OAuth setup. See oauth_setup_instructions.md")

                # Try to run local server flow
                try:
                    creds = flow.run_local_server(port=0, open_browser=True)
                    self._save_credentials(creds)
                    return creds
                except Exception as flow_error:
                    st.error(f"❌ OAuth flow failed: {flow_error}")
                    return None

            except Exception as e:
                st.error(f"❌ OAuth flow error: {e}")
                return None
    
        def _get_folder_id(self) -> str:
            """Get folder ID from various sources with caching"""
            folder_id = None

            # PRIORITY 1: Try to get from Streamlit secrets (highest priority)
            if hasattr(st, 'secrets'):
                if 'drive_folder_id' in st.secrets:
                    folder_id = st.secrets['drive_folder_id']
                elif 'default' in st.secrets and 'drive_folder_id' in st.secrets['default']:
                    folder_id = st.secrets['default']['drive_folder_id']

            # PRIORITY 2: Try environment variable
            if not folder_id:
                folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')

            # PRIORITY 3: Try cached folder ID from session state
            if not folder_id and hasattr(st, 'session_state'):
                folder_id = st.session_state.get('cached_drive_folder_id')

            # PRIORITY 4: Try cached folder ID from local file
            if not folder_id:
                cache_file = Path('.drive_folder_cache')
                if cache_file.exists():
                    try:
                        folder_id = cache_file.read_text().strip()
                        print(f"📦 Loaded cached folder ID from file: {folder_id}")
                    except Exception as e:
                        print(f"⚠️ Could not read folder cache: {e}")

            # PRIORITY 5: Search for existing or create new folder
            if not folder_id:
                folder_id = self._create_backup_folder()

                # Cache the folder ID for future use
                if folder_id:
                    # Save to session state
                    if hasattr(st, 'session_state'):
                        st.session_state.cached_drive_folder_id = folder_id

                    # Save to local cache file
                    try:
                        cache_file = Path('.drive_folder_cache')
                        cache_file.write_text(folder_id)
                        print(f"💾 Cached folder ID to file for future use")
                    except Exception as e:
                        print(f"⚠️ Could not save folder cache: {e}")

            print(f"📂 Using folder ID: {folder_id}")
            return folder_id

        def _create_backup_folder(self) -> Optional[str]:
            """Find existing or create a backup folder in Google Drive"""
            try:
                if not self.service:
                    return None

                # STEP 1: Search for existing "CNFund Backup" folder first
                print("🔍 Searching for existing 'CNFund Backup' folder...")
                query = "name='CNFund Backup' and mimeType='application/vnd.google-apps.folder' and trashed=false"

                results = self.service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name, webViewLink)',
                    pageSize=10
                ).execute()

                files = results.get('files', [])

                # If folder exists, use it
                if files:
                    folder_id = files[0].get('id')
                    print(f"✅ Found existing backup folder: {folder_id}")
                    print(f"🔗 Folder link: {files[0].get('webViewLink', '')}")
                    return folder_id

                # STEP 2: Create new folder only if not found
                print("📁 Creating new 'CNFund Backup' folder...")
                folder_metadata = {
                    'name': 'CNFund Backup',
                    'mimeType': 'application/vnd.google-apps.folder'
                }

                folder = self.service.files().create(
                    body=folder_metadata,
                    fields='id,name,webViewLink'
                ).execute()

                folder_id = folder.get('id')
                if folder_id:
                    st.success(f"📁 Created backup folder: CNFund Backup")
                    st.info(f"🔗 Folder link: {folder.get('webViewLink', '')}")
                    print(f"💾 IMPORTANT: Save this folder ID to Streamlit secrets: {folder_id}")
                    print(f"💾 Add to .streamlit/secrets.toml: drive_folder_id = \"{folder_id}\"")
                    return folder_id

            except Exception as e:
                print(f"❌ Could not create/find backup folder: {e}")

            return None
    
        def test_connection(self) -> Dict[str, Any]:
            """Test OAuth connection"""
            result = {
                'connected': False,
                'user': None,
                'folder_access': False,
                'files_count': 0,
                'errors': []
            }

            if not self.connected or not self.service:
                result['errors'].append("Not connected to Google Drive")
                return result

            try:
                # Get user info
                about = self.service.about().get(fields="user").execute()
                user_info = about.get('user', {})
                result['user'] = {
                    'name': user_info.get('displayName', 'Unknown'),
                    'email': user_info.get('emailAddress', 'Unknown')
                }
                result['connected'] = True

                # Test folder access
                if self.folder_id:
                    try:
                        results = self.service.files().list(
                            q=f"'{self.folder_id}' in parents and trashed=false",
                            fields="files(id, name)",
                            pageSize=10
                        ).execute()
                        files = results.get('files', [])
                        result['folder_access'] = True
                        result['files_count'] = len(files)
                    except Exception as folder_error:
                        result['errors'].append(f"Folder access error: {str(folder_error)}")
                else:
                    result['errors'].append("No folder ID configured")

            except Exception as e:
                result['errors'].append(f"Connection test error: {str(e)}")

            return result
    
        def upload_to_drive(self, file_buffer: io.BytesIO, filename: str) -> bool:
            """Upload file using OAuth credentials (personal account)"""
            if not self.connected or not self.service:
                st.error("❌ Google Drive not connected")
                return False

            try:
                file_metadata = {
                    'name': filename,
                    'parents': [self.folder_id] if self.folder_id else []
                }

                file_buffer.seek(0)

                media = MediaIoBaseUpload(
                    file_buffer,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    resumable=False
                )

                # Upload with personal account OAuth - should work!
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id,name,webViewLink'
                ).execute()

                file_id = file.get('id')
                if file_id:
                    # Set anyone can view permissions (optional)
                    try:
                        self.service.permissions().create(
                            fileId=file_id,
                            body={'type': 'anyone', 'role': 'reader'}
                        ).execute()
                    except:
                        pass  # Ignore permission errors

                    web_link = file.get('webViewLink', '')
                    if web_link:
                        st.success(f"✅ Uploaded: [{filename}]({web_link})")
                    else:
                        st.success(f"✅ Uploaded: {filename}")
                    return True

                return False

            except Exception as e:
                st.error(f"❌ Upload error: {str(e)}")
                return False

        def is_authenticated(self) -> bool:
            """Check if OAuth is authenticated"""
            return self.connected and self.credentials and self.credentials.valid

        def force_reauthenticate(self):
            """Force re-authentication by deleting saved credentials"""
            try:
                if self.token_file.exists():
                    self.token_file.unlink()
                    st.info("🔄 Saved credentials cleared. Re-authentication required.")

                # Reinitialize
                self._initialize_oauth_service()

            except Exception as e:
                st.error(f"❌ Could not clear credentials: {e}")

else:
    # Dummy class when OAuth libraries not available
    class GoogleDriveOAuthManager:
        """Dummy OAuth manager when libraries not installed"""
        def __init__(self):
            self.connected = False
            self.service = None
            self.folder_id = None

        def test_connection(self):
            return {'connected': False, 'errors': ['OAuth libraries not installed']}

        def upload_to_drive(self, file_buffer, filename):
            st.error("❌ Google OAuth not available. Install: pip install google-auth-oauthlib")
            return False

        def is_authenticated(self):
            return False