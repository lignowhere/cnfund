# 🚀 Hướng Dẫn Deploy CNFund lên Streamlit Cloud

## Tổng Quan Kiến Trúc

CNFund sử dụng **hybrid storage architecture**:
- **Local**: CSV files (cho development)
- **Cloud**: Google Drive + Session State (cho production trên Streamlit Cloud)

---

## 📋 Bước 1: Setup Google Drive OAuth

### 1.1. Tạo Google Cloud Project

1. Truy cập: https://console.cloud.google.com/
2. Tạo project mới: "CNFund App"
3. Enable Google Drive API:
   - Navigation menu → APIs & Services → Library
   - Tìm "Google Drive API" → Enable

### 1.2. Tạo OAuth 2.0 Credentials

1. APIs & Services → Credentials
2. Click "Create Credentials" → OAuth client ID
3. Chọn "Application type": **Desktop app**
4. Name: "CNFund Desktop Client"
5. Click "Create"
6. Download JSON file → Rename thành `oauth_credentials.json`

### 1.3. Configure OAuth Consent Screen

1. APIs & Services → OAuth consent screen
2. Chọn "External" (nếu không có G Suite)
3. Điền thông tin:
   - App name: CNFund Management System
   - User support email: your-email@example.com
   - Developer contact: your-email@example.com
4. Scopes: Thêm `../auth/drive.file` (Google Drive API)
5. Test users: Thêm email của bạn
6. Save and Continue

---

## 📋 Bước 2: Tạo Google Drive Folder

1. Truy cập: https://drive.google.com
2. Tạo folder mới: "CNFund Backup"
3. Lấy Folder ID từ URL:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                           ^^^^^^^^^^^^^^^^^^
                                           (Folder ID này)
   ```
4. Lưu lại Folder ID để dùng sau

---

## 📋 Bước 3: OAuth Authentication (Local - 1 lần)

**Chạy trên máy local để generate token:**

### 3.1. Setup môi trường local

```bash
cd D:\Đầu tư\CNFund

# Copy oauth_credentials.json vào root folder
# (file download từ Google Cloud Console)

# Install dependencies
pip install -r requirements.txt
```

### 3.2. Run OAuth flow

```python
# Tạo file test_oauth.py
from integrations.google_drive_oauth import GoogleDriveOAuthManager

# Run OAuth flow
manager = GoogleDriveOAuthManager()

# Sẽ mở browser tự động
# → Chọn Google account
# → Accept permissions
# → Token sẽ được lưu vào token.pickle
```

### 3.3. Verify OAuth success

Sau khi authenticate thành công:
- File `token.pickle` được tạo trong root folder
- Console hiển thị: "✅ OAuth connected as: your-email@gmail.com"

---

## 📋 Bước 4: Deploy lên Streamlit Cloud

### 4.1. Prepare Repository

1. Push code lên GitHub (public hoặc private repo)
```bash
git add .
git commit -m "Deploy CNFund to Streamlit Cloud"
git push origin main
```

2. Đảm bảo có các files:
   - `requirements.txt` ✅
   - `app.py` ✅
   - `.streamlit/config.toml` (optional)

### 4.2. Deploy trên Streamlit Cloud

1. Truy cập: https://share.streamlit.io
2. Click "New app"
3. Connect GitHub repository
4. Settings:
   - **Main file path**: `app.py`
   - **Python version**: 3.9+
   - **Advanced settings** → Secrets (xem bước 5)

### 4.3. Configure Streamlit Secrets

Trong "Advanced settings" → "Secrets":

```toml
# .streamlit/secrets.toml

[default]
# Google Drive Folder ID
drive_folder_id = "1a2b3c4d5e6f7g8h9i0j"

# OAuth Credentials (copy from oauth_credentials.json)
[oauth_credentials]
installed.client_id = "your-client-id.apps.googleusercontent.com"
installed.client_secret = "your-client-secret"
installed.auth_uri = "https://accounts.google.com/o/oauth2/auth"
installed.token_uri = "https://oauth2.googleapis.com/token"
installed.auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
installed.redirect_uris = ["http://localhost"]
```

**Cách lấy OAuth credentials:**

1. Mở file `oauth_credentials.json` download từ Google Cloud
2. Copy các giá trị vào secrets format trên

---

## 📋 Bước 5: Upload OAuth Token

**Quan trọng**: Token không thể generate trên Streamlit Cloud (không có browser).

### Option A: Manual Token Upload (Khuyên dùng)

1. Encode `token.pickle` thành base64:

```python
# run_on_local.py
import base64
import pickle

with open('token.pickle', 'rb') as f:
    token_data = f.read()

encoded = base64.b64encode(token_data).decode('utf-8')
print(encoded)
```

2. Add vào Streamlit secrets:

```toml
[default]
drive_folder_id = "..."

# Token encoded base64
oauth_token_base64 = "gASVpAYAAA..."
```

3. Update `google_drive_oauth.py` để decode token:

```python
def _load_saved_credentials(self):
    # Try file first
    if self.token_file.exists():
        # ... existing code ...

    # Try from secrets (for Streamlit Cloud)
    if hasattr(st, 'secrets') and 'oauth_token_base64' in st.secrets:
        try:
            import base64
            token_data = base64.b64decode(st.secrets['oauth_token_base64'])
            creds = pickle.loads(token_data)

            if creds and creds.valid:
                return creds
        except Exception as e:
            print(f"⚠️ Could not load token from secrets: {e}")

    return None
```

### Option B: Use Service Account (Alternative)

Service Account không cần OAuth flow nhưng cần setup phức tạp hơn. Xem: [Service Account Guide](SERVICE_ACCOUNT_SETUP.md)

---

## 📋 Bước 6: First Deployment Test

1. Deploy app lên Streamlit Cloud
2. Wait for deployment (~2-5 minutes)
3. Open app URL: `https://your-app-name.streamlit.app`

### Expected behavior:

**First run (no backup on Drive):**
```
ℹ️ Không tìm thấy backup - khởi tạo dữ liệu mới
✅ Sử dụng Google Drive Storage (Cloud)
```

**Add first transaction:**
```
💾 Đang sao lưu lên Google Drive...
✅ Uploaded: CNFund_Backup_20250930_143022.xlsx
```

**Subsequent runs:**
```
📥 Đang tải dữ liệu từ Google Drive...
✅ Đã tải dữ liệu từ Drive (File: CNFund_Backup_20250930_143022.xlsx)
```

---

## 📋 Bước 7: Verify Everything Works

### 7.1. Test Data Persistence

1. Thêm 1 nhà đầu tư mới
2. Check Drive → File backup mới được tạo
3. Restart app (Settings → Reboot)
4. Verify: Nhà đầu tư vẫn còn ✅

### 7.2. Test Backup/Restore

1. Vào page "Backup Management"
2. Click "💾 Backup Ngay"
3. Check Drive → Backup mới
4. Click "🔄 Reload từ Drive"
5. Verify: Data reload thành công

---

## 🔧 Troubleshooting

### Issue 1: "Google Drive chưa kết nối"

**Nguyên nhân**: OAuth token chưa được upload hoặc invalid

**Giải pháp**:
1. Check Streamlit secrets có `oauth_token_base64`?
2. Re-generate token trên local
3. Re-encode và update secrets
4. Reboot app

### Issue 2: "❌ Lỗi tải dữ liệu từ Drive"

**Nguyên nhân**: Folder ID sai hoặc quyền truy cập

**Giải pháp**:
1. Verify `drive_folder_id` trong secrets
2. Check folder permissions (anyone with link can view)
3. Check OAuth scope có `.../auth/drive.file`

### Issue 3: "Backup thành công nhưng không thấy file"

**Nguyên nhân**: Upload vào folder khác hoặc folder không tồn tại

**Giải pháp**:
1. Kiểm tra trong Drive: Search "CNFund_Backup"
2. Nếu không thấy → Check OAuth scope
3. Try tạo folder mới và update `drive_folder_id`

### Issue 4: App restart mất data

**Nguyên nhân**: Load from Drive bị lỗi

**Giải pháp**:
1. Check logs: Settings → Manage app → Logs
2. Look for: "❌ Load from Drive error"
3. Fix error (thường là OAuth issue)
4. Manual backup: Copy data từ local export

---

## 📊 Performance Expectations

| Operation | Time (Streamlit Cloud) |
|-----------|----------------------|
| **App startup (có backup)** | ~15-20s |
| **App startup (không có backup)** | ~5s |
| **Add transaction + backup** | ~5-8s |
| **Load data from Drive** | ~10-15s |
| **Manual backup** | ~3-5s |

**Note**: First cold start có thể mất ~30s (pip install dependencies)

---

## 🔒 Security Best Practices

1. **Secrets Management**:
   - Không commit `oauth_credentials.json` vào git
   - Không commit `token.pickle` vào git
   - Add to `.gitignore`:
     ```
     oauth_credentials.json
     token.pickle
     .streamlit/secrets.toml
     ```

2. **Drive Permissions**:
   - Folder nên set "Restricted" (only you)
   - Hoặc "Anyone with link" nếu cần share với team

3. **Token Refresh**:
   - Token tự động refresh khi expired
   - Refresh token valid ~6 months
   - Sau 6 months: Re-authenticate trên local → Update secrets

---

## 📚 Additional Resources

- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud)
- [Google Drive API](https://developers.google.com/drive/api/guides/about-sdk)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)

---

## 🎯 Success Checklist

- [ ] Google Cloud project created
- [ ] Drive API enabled
- [ ] OAuth credentials downloaded
- [ ] Drive folder created
- [ ] Folder ID saved
- [ ] OAuth flow completed (local)
- [ ] `token.pickle` generated
- [ ] Token encoded to base64
- [ ] Streamlit secrets configured
- [ ] App deployed to Streamlit Cloud
- [ ] First data test successful
- [ ] Backup/restore tested
- [ ] App restart persistence verified

---

**Chúc mừng! CNFund của bạn đã chạy trên Streamlit Cloud với data persistent! 🎉**