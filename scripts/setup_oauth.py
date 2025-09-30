#!/usr/bin/env python3
"""
OAuth Setup Script for Local Development
Helps setup Google Drive OAuth authentication on local machine
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """Run OAuth setup for local development"""
    print("="*70)
    print("🔐 GOOGLE DRIVE OAUTH SETUP - LOCAL DEVELOPMENT")
    print("="*70)
    print()

    # Check if oauth_credentials.json exists
    credentials_file = Path("oauth_credentials.json")

    if not credentials_file.exists():
        print("❌ oauth_credentials.json không tìm thấy!")
        print()
        print("📖 Hướng dẫn lấy OAuth credentials:")
        print("   1. Truy cập: https://console.cloud.google.com/")
        print("   2. Tạo project mới (hoặc chọn project có sẵn)")
        print("   3. Enable 'Google Drive API'")
        print("   4. Credentials → Create OAuth 2.0 Client ID")
        print("   5. Application type: Desktop app")
        print("   6. Download JSON và lưu thành 'oauth_credentials.json'")
        print()
        print("📄 Chi tiết: docs/STREAMLIT_CLOUD_SETUP.md")
        print()
        return False

    print("✅ Tìm thấy oauth_credentials.json")
    print()

    # Import OAuth manager
    try:
        from integrations.google_drive_oauth import GoogleDriveOAuthManager

        print("🚀 Khởi động OAuth flow...")
        print("   → Browser sẽ tự động mở")
        print("   → Đăng nhập Google account của bạn")
        print("   → Cho phép app truy cập Google Drive")
        print()

        # Initialize OAuth (will trigger flow if needed)
        manager = GoogleDriveOAuthManager()

        if manager.connected:
            print()
            print("="*70)
            print("✅ OAUTH SETUP THÀNH CÔNG!")
            print("="*70)
            print()
            print(f"📂 Token đã lưu tại: token.pickle")
            print()

            if manager.folder_id:
                print(f"📁 Backup Folder ID: {manager.folder_id}")
                print()
                print("💡 Lưu Folder ID này vào .streamlit/secrets.toml:")
                print(f'   drive_folder_id = "{manager.folder_id}"')
                print()

            print("🎉 Bạn có thể chạy app ngay bây giờ:")
            print("   streamlit run app.py")
            print()

            return True
        else:
            print()
            print("❌ OAuth authentication thất bại")
            print("💡 Kiểm tra lại credentials và thử lại")
            print()
            return False

    except ImportError as e:
        print("❌ Thiếu dependencies!")
        print()
        print("Cài đặt các package cần thiết:")
        print("   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        print()
        return False
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print()
        print("⚠️ Setup bị hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Lỗi không mong đợi: {e}")
        sys.exit(1)