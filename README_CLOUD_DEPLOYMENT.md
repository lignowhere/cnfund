# ☁️ CNFund - Cloud Deployment Ready

## 🎯 Quick Start

CNFund hiện đã sẵn sàng deploy lên **Streamlit Cloud** với Google Drive làm persistent storage!

### 🚀 Deploy trong 5 bước:

```bash
# 1. Setup OAuth (local - 1 lần)
python scripts/test_oauth_setup.py

# 2. Encode token
python scripts/encode_oauth_token.py

# 3. Push to GitHub
git add .
git commit -m "Deploy to Streamlit Cloud"
git push

# 4. Deploy trên share.streamlit.io
#    → Connect GitHub repo
#    → Add secrets (copy từ token_encoded.txt)

# 5. Done! 🎉
```

📖 **Chi tiết**: Xem [docs/STREAMLIT_CLOUD_SETUP.md](docs/STREAMLIT_CLOUD_SETUP.md)

---

## 🏗️ Architecture

### **Local Development**
```
App ← CSV Files (data/)
```

### **Production (Streamlit Cloud)**
```
App ← Session State (RAM) ← Google Drive (Persistent)
     ↑                           ↑
     └─── Auto backup mỗi transaction ───┘
```

---

## ✨ Features

### ✅ Hybrid Storage System
- **Local**: CSV files cho development
- **Cloud**: Google Drive + Session State cho production
- **Auto-detection**: App tự động chọn storage phù hợp

### ✅ Data Persistence
- Mỗi transaction → Auto backup lên Drive
- App restart → Auto restore từ Drive
- **Zero data loss** trên Streamlit Cloud

### ✅ Manual Controls
- 💾 **Backup Ngay**: Force backup bất cứ lúc nào
- 🔄 **Reload từ Drive**: Restore data từ backup mới nhất
- 📊 **Backup Management**: Dashboard quản lý backups

### ✅ Security
- OAuth 2.0 authentication
- Encrypted token storage
- `.gitignore` cho sensitive files
- Drive permissions control

---

## 📁 Project Structure

```
CNFund/
├── app.py                          # Main entry point
├── core/
│   ├── csv_data_handler.py        # Local CSV storage
│   ├── drive_data_handler.py      # Drive + Session State storage (NEW!)
│   ├── models.py                   # Data models
│   └── services_enhanced.py       # Business logic
├── integrations/
│   └── google_drive_oauth.py      # OAuth & Drive API (ENHANCED!)
├── pages/
│   └── backup_page.py             # Backup management UI (UPDATED!)
├── scripts/
│   ├── test_oauth_setup.py        # OAuth setup test (NEW!)
│   └── encode_oauth_token.py      # Token encoder (NEW!)
├── docs/
│   └── STREAMLIT_CLOUD_SETUP.md   # Deployment guide (NEW!)
└── requirements.txt               # Dependencies
```

---

## 🔧 Configuration

### Local Development
```bash
# No configuration needed - uses CSV automatically
streamlit run app.py
```

### Streamlit Cloud
```toml
# .streamlit/secrets.toml
[default]
drive_folder_id = "your-folder-id"
oauth_token_base64 = "encoded-token-here"
```

---

## 📊 Performance

| Environment | Startup Time | Transaction Save | Data Load |
|-------------|--------------|------------------|-----------|
| **Local (CSV)** | ~2s | <1s | <1s |
| **Cloud (Drive)** | ~15s (first) | ~5s | ~10s |
| **Cloud (cached)** | ~5s | ~5s | <1s |

**Note**: Cold start trên Streamlit Cloud ~30s (pip install)

---

## 🎓 Usage Examples

### Adding a Transaction

**Local:**
```python
# Save to CSV immediately
fund_manager.add_transaction(...)
# Done!
```

**Cloud:**
```python
# Save to session state + backup to Drive
fund_manager.add_transaction(...)
# ✅ Transaction saved
# 💾 Auto backup to Drive
# Done!
```

### App Restart

**Local:**
```python
# Read from CSV files
data_handler = CSVDataHandler()
```

**Cloud:**
```python
# Restore from Drive
data_handler = DriveBackedDataManager()
# 📥 Downloading from Drive...
# ✅ Data restored!
```

---

## 🐛 Troubleshooting

### "Google Drive chưa kết nối"
→ Check OAuth token trong Streamlit secrets

### "Backup thất bại"
→ Check Drive folder permissions & folder_id

### "Data mất sau restart"
→ Check logs: Có backup thành công không?

📖 **Full troubleshooting guide**: [docs/STREAMLIT_CLOUD_SETUP.md#troubleshooting](docs/STREAMLIT_CLOUD_SETUP.md#troubleshooting)

---

## 🔐 Security Checklist

- [ ] `.gitignore` includes sensitive files
- [ ] OAuth credentials NOT committed
- [ ] Token NOT committed
- [ ] Streamlit secrets configured
- [ ] Drive folder permissions reviewed
- [ ] Token auto-refresh enabled

---

## 📚 Documentation

- [📖 Deployment Guide](docs/STREAMLIT_CLOUD_SETUP.md) - Chi tiết setup
- [🔧 API Reference](docs/API_REFERENCE.md) - Drive API usage
- [🎯 Best Practices](docs/BEST_PRACTICES.md) - Production tips

---

## 💡 FAQ

**Q: Có cần database không?**
A: Không! Drive + Session State đủ cho 1-2 transactions/tháng.

**Q: Chi phí bao nhiêu?**
A: $0/tháng (Streamlit Cloud free + Google Drive 15GB free)

**Q: Data có an toàn không?**
A: Có! Mỗi transaction = 1 backup. Drive không xóa data.

**Q: Performance có chậm không?**
A: Startup hơi chậm (~15s), nhưng usage bình thường ok.

**Q: Có thể dùng local không?**
A: Có! App auto-detect và dùng CSV cho local dev.

---

## 🎉 Ready to Deploy?

```bash
# Test trên local trước
streamlit run app.py

# Nếu OK → Deploy!
python scripts/test_oauth_setup.py
python scripts/encode_oauth_token.py
git push

# Go to share.streamlit.io → Deploy!
```

**Good luck! 🚀**