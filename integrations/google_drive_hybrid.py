#!/usr/bin/env python3
"""
Hybrid Google Drive Manager
Automatically chooses between OAuth (personal) and Service Account (business) based on available credentials
"""

import os
from pathlib import Path
import streamlit as st

class HybridGoogleDriveManager:
    """Auto-detects and uses best available Google Drive authentication method"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.auth_method = self._detect_auth_method()
        self.manager = None
        self.connected = False
        
        # Initialize appropriate manager
        if self.auth_method == "oauth":
            self._init_oauth_manager()
        elif self.auth_method == "service_account":
            self._init_service_account_manager()
        else:
            st.warning("⚠️ No Google Drive credentials found")
    
    def _detect_auth_method(self) -> str:
        """Detect which authentication method to use"""
        
        # Priority 1: OAuth credentials (personal account)
        oauth_file = Path("oauth_credentials.json")
        if oauth_file.exists():
            print("🔍 Found OAuth credentials - using personal account")
            return "oauth"
        
        # Priority 2: Service account credentials (business account)
        if hasattr(st, 'secrets') and 'google_service_account' in st.secrets:
            print("🔍 Found service account in secrets - using business account")
            return "service_account"
            
        if os.path.exists("service_account.json"):
            print("🔍 Found service account file - using business account")
            return "service_account"
            
        if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
            print("🔍 Found service account in env - using business account")
            return "service_account"
        
        print("❌ No Google Drive credentials found")
        return "none"
    
    def _init_oauth_manager(self):
        """Initialize OAuth manager for personal account"""
        try:
            from google_drive_oauth import GoogleDriveOAuthManager
            self.manager = GoogleDriveOAuthManager()
            self.connected = self.manager.is_authenticated()
            
            if self.connected:
                st.success("🏠 Personal Google Drive (OAuth) - Connected")
            else:
                st.warning("🔐 Personal Google Drive - Authentication required")
                st.info("📋 See oauth_setup_instructions.md for setup")
                
        except ImportError:
            st.error("❌ OAuth libraries not installed. Run: pip install google-auth-oauthlib")
        except Exception as e:
            st.error(f"❌ OAuth manager failed: {e}")
    
    def _init_service_account_manager(self):
        """Initialize service account manager for business account"""
        try:
            from google_drive_manager import GoogleDriveManager
            self.manager = GoogleDriveManager(self.fund_manager)
            self.connected = self.manager.connected
            
            if self.connected:
                st.success("🏢 Business Google Drive (Service Account) - Connected")
            else:
                st.error("❌ Business Google Drive - Connection failed")
                
        except Exception as e:
            st.error(f"❌ Service account manager failed: {e}")
    
    def test_connection(self):
        """Test connection using active manager"""
        if self.manager and hasattr(self.manager, 'test_connection'):
            return self.manager.test_connection()
        
        return {
            'connected': False,
            'errors': ['No manager available']
        }
    
    def upload_to_drive(self, file_buffer, filename: str) -> bool:
        """Upload file using active manager"""
        if not self.connected or not self.manager:
            st.error(f"❌ Google Drive not connected (method: {self.auth_method})")
            return False
        
        try:
            return self.manager.upload_to_drive(file_buffer, filename)
        except Exception as e:
            st.error(f"❌ Upload failed: {e}")
            return False
    
    def export_to_excel_buffer(self):
        """Export to Excel buffer"""
        if hasattr(self.manager, 'export_to_excel_buffer'):
            return self.manager.export_to_excel_buffer()
        
        # Fallback: create buffer using original GoogleDriveManager logic
        from google_drive_manager import GoogleDriveManager  
        temp_manager = GoogleDriveManager(self.fund_manager)
        return temp_manager.export_to_excel_buffer()
    
    def auto_export_and_upload(self, trigger: str = "manual") -> bool:
        """Auto export and upload using best available method"""
        try:
            # Always create local backup first
            from datetime import datetime
            from pathlib import Path
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Fund_Export_{timestamp}_{trigger}.xlsx"
            
            # Export to buffer
            buffer = self.export_to_excel_buffer()
            
            # Save local backup
            local_backup_dir = Path("exports")
            local_backup_dir.mkdir(exist_ok=True)
            local_file = local_backup_dir / filename
            
            with open(local_file, 'wb') as f:
                f.write(buffer.getvalue())
            
            st.success(f"💾 Local backup: {local_file}")
            
            # Try cloud backup
            if self.connected:
                buffer.seek(0)  # Reset buffer position
                cloud_success = self.upload_to_drive(buffer, filename)
                
                if cloud_success:
                    st.success(f"☁️ Cloud backup successful ({self.auth_method})")
                    return True
                else:
                    st.warning(f"⚠️ Cloud backup failed, but local backup saved")
                    return True  # Still success because local backup worked
            else:
                st.info("📁 Local backup only - cloud connection not available")
                return True
                
        except Exception as e:
            st.error(f"❌ Export failed: {e}")
            return False
    
    def get_status_info(self) -> dict:
        """Get detailed status information"""
        return {
            'auth_method': self.auth_method,
            'connected': self.connected,
            'manager_type': type(self.manager).__name__ if self.manager else None,
            'local_backup': True,  # Always available
            'cloud_backup': self.connected
        }

# Convenience function for existing code
def create_google_drive_manager(fund_manager):
    """Create the best available Google Drive manager"""
    return HybridGoogleDriveManager(fund_manager)