#!/usr/bin/env python3
"""
Test OAuth setup for Google Drive
Run this on local machine to generate token.pickle
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_oauth():
    """Test OAuth authentication flow"""

    print("=" * 60)
    print("🔐 Google Drive OAuth Setup Test")
    print("=" * 60)

    # Check prerequisites
    print("\n📋 Checking prerequisites...")

    oauth_cred_file = Path("oauth_credentials.json")
    if not oauth_cred_file.exists():
        print("❌ oauth_credentials.json not found!")
        print("\n📖 Please follow these steps:")
        print("   1. Go to: https://console.cloud.google.com/apis/credentials")
        print("   2. Create OAuth 2.0 Client ID (Desktop app)")
        print("   3. Download JSON file")
        print("   4. Rename to 'oauth_credentials.json'")
        print("   5. Place in project root folder")
        return False

    print("✅ oauth_credentials.json found")

    # Try to import and initialize
    try:
        from integrations.google_drive_oauth import GoogleDriveOAuthManager

        print("\n🚀 Starting OAuth flow...")
        print("⏳ Browser will open - please authenticate with Google account")

        manager = GoogleDriveOAuthManager()

        if manager.connected:
            print("\n" + "=" * 60)
            print("✅ OAuth authentication successful!")
            print("=" * 60)

            # Test connection
            result = manager.test_connection()

            if result['connected']:
                print(f"\n👤 Connected as: {result['user']['email']}")
                print(f"📁 Folder access: {'✅' if result['folder_access'] else '❌'}")
                print(f"📊 Files in folder: {result['files_count']}")

                print("\n🎉 Setup complete!")
                print("\n📋 Next steps:")
                print("   1. Run: python scripts/encode_oauth_token.py")
                print("   2. Copy encoded token to Streamlit Cloud secrets")
                print("   3. Deploy your app!")

                return True
            else:
                print("\n⚠️ Connected but folder access issue")
                if result['errors']:
                    for error in result['errors']:
                        print(f"   - {error}")
                return False
        else:
            print("\n❌ OAuth authentication failed")
            print("Please check:")
            print("   - OAuth credentials are valid")
            print("   - App is authorized in Google Cloud Console")
            print("   - Your email is added as test user")
            return False

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_oauth()

    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Setup incomplete - please fix errors above")
        sys.exit(1)