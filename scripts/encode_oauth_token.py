#!/usr/bin/env python3
"""
Helper script to encode OAuth token for Streamlit Cloud secrets
Run this on local machine after OAuth authentication
"""

import base64
import pickle
from pathlib import Path


def encode_token():
    """Encode token.pickle to base64 for Streamlit secrets"""

    token_file = Path("token.pickle")

    if not token_file.exists():
        print("❌ token.pickle not found!")
        print("📖 Please run OAuth authentication first:")
        print("   python scripts/test_oauth_setup.py")
        return

    try:
        # Read token file
        with open(token_file, 'rb') as f:
            token_data = f.read()

        # Encode to base64
        encoded = base64.b64encode(token_data).decode('utf-8')

        print("=" * 60)
        print("✅ Token encoded successfully!")
        print("=" * 60)
        print("\n📋 Copy this value to Streamlit Cloud secrets:\n")
        print("[default]")
        print(f'oauth_token_base64 = "{encoded}"')
        print("\n" + "=" * 60)
        print("\n💡 How to add to Streamlit Cloud:")
        print("   1. Go to your app settings")
        print("   2. Navigate to 'Secrets' section")
        print("   3. Add the line above to your secrets.toml")
        print("   4. Click 'Save' and reboot app")
        print("=" * 60)

        # Also save to file for easy copy
        output_file = Path("token_encoded.txt")
        with open(output_file, 'w') as f:
            f.write(f'oauth_token_base64 = "{encoded}"\n')

        print(f"\n💾 Also saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error encoding token: {e}")


if __name__ == "__main__":
    encode_token()