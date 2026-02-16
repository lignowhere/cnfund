# Streamlit Cloud Setup (Low Cost Mode)

This guide is for the production setup target:
- 1 private app on Streamlit Community Cloud
- Google Drive as source of truth
- Auto deploy from `main`

## 1. Connect app on Streamlit Community Cloud

1. Open Streamlit Community Cloud dashboard.
2. Create app from GitHub repo: `lignowhere/cnfund`.
3. Branch: `main`.
4. Main file path: `app.py`.
5. Set app visibility to `Private`.

## 2. Configure secrets (required)

In app settings, add these secrets:

```toml
ADMIN_PASSWORD = "CHANGE_THIS_STRONG_PASSWORD"

[default]
drive_folder_id = "YOUR_DRIVE_FOLDER_ID_HERE"
oauth_token_base64 = "YOUR_BASE64_TOKEN_HERE"

[oauth_credentials.installed]
client_id = "your-client-id.apps.googleusercontent.com"
project_id = "your-project-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_secret = "your-client-secret"
redirect_uris = ["http://localhost"]
```

Notes:
- `ADMIN_PASSWORD` is mandatory for edit pages.
- In cloud mode, the app will fail fast if Drive is not connected.
- Do not commit `secrets.toml`, OAuth files, or token files.

## 3. Google Drive setup

1. Create folder `CNFund Backup` on Google Drive.
2. Copy folder ID from URL into `default.drive_folder_id`.
3. Prepare OAuth credentials and token.
4. Verify app can list/upload backup files in that folder.

## 4. Validation checklist before go-live

1. Startup validation:
- App starts without CSV fallback in cloud mode.
- App shows Drive as active data source.

2. Permissions:
- Viewer can open report pages.
- Viewer is blocked on edit pages.
- Admin can login and mutate data.

3. Persistence:
- Create one test transaction.
- Reload app and confirm transaction remains.

4. Backup retention:
- Trigger multiple saves.
- Confirm old Drive backups are not auto-deleted.

## 5. Operations

1. Monitor Google Drive storage usage weekly.
2. Raise internal alert around 80% usage.
3. Keep single production app to stay within lowest-cost setup.
