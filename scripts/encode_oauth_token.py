#!/usr/bin/env python3
"""Encode OAuth token file for backend env var GOOGLE_OAUTH_TOKEN_BASE64."""

import base64
from pathlib import Path


def encode_token() -> None:
    token_file = Path("token.pickle")
    if not token_file.exists():
        print("token.pickle not found.")
        print("Create OAuth token first, then run this script again.")
        return

    try:
        token_data = token_file.read_bytes()
        encoded = base64.b64encode(token_data).decode("utf-8")

        print("=" * 72)
        print("Token encoded successfully")
        print("Set this value in Railway/Vercel backend env var:")
        print("GOOGLE_OAUTH_TOKEN_BASE64")
        print("=" * 72)
        print(encoded)
        print("=" * 72)

        Path("token_encoded.txt").write_text(encoded + "\n", encoding="utf-8")
        print("Saved plain encoded value to token_encoded.txt")
    except Exception as exc:
        print(f"Error encoding token: {exc}")


if __name__ == "__main__":
    encode_token()
