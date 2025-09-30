# 🔄 Data Synchronization Guide

## 📊 Current Situation

- **Local**: Has production data (CSV files)
- **Cloud**: Has different data (might be test data)
- **Issue**: Data inconsistency between environments

---

## 🎯 Solution: Sync via Google Drive

### **Method 1: Local → Cloud (Recommended)**

Use local data as the source of truth.

#### **Step 1: Backup local data to Drive**

On **local machine**:

```bash
cd D:\Đầu tư\CNFund
streamlit run app.py
```

In the UI:
1. Navigate to "💾 Backup Management" page
2. Click "💾 Backup Ngay" button
3. Wait for success message
4. ✅ Check Google Drive → New backup file created

#### **Step 2: Load data on Cloud**

On **Streamlit Cloud** (https://cnfund.streamlit.app):
1. Refresh the page
2. Navigate to "💾 Backup Management" page
3. Click "🔄 Reload từ Drive" button
4. Wait for success message
5. ✅ Data synced!

#### **Step 3: Verify sync**

Check data on both environments:
- Local: Check investor list
- Cloud: Check investor list
- ✅ Should match perfectly!

---

### **Method 2: Cloud → Local (If cloud has correct data)**

If cloud data is correct instead:

#### **Step 1: Backup cloud data**

On **Streamlit Cloud**:
1. Go to "💾 Backup Management"
2. Click "💾 Backup Ngay"
3. ✅ Backup uploaded to Drive

#### **Step 2: Download backup manually**

1. Go to Google Drive
2. Open "CNFund Backup" folder
3. Download latest backup file (Excel)
4. Save to `D:\Đầu tư\CNFund\exports\`

#### **Step 3: Restore on local**

On **local machine**:
1. Run `streamlit run app.py`
2. Go to "💾 Backup Management"
3. Find the backup file in history
4. Click "Restore" button
5. ✅ Data restored!

---

## ⏰ Timezone Synchronization

### **Issue: UTC vs UTC+7**

- **Local**: Uses UTC+7 (Asia/Ho_Chi_Minh) ✅
- **Cloud**: Should use UTC+7 but might show UTC ❌

### **Verify timezone**

Run verification script:

**On local:**
```bash
python scripts/verify_timezone.py
```

**Expected output:**
```
🌍 Timezone Verification
📍 Environment: 🏠 Local
⏰ App Timezone: Asia/Ho_Chi_Minh
📅 Current Time:
   App (Vietnam): 2025-09-30 20:00:00 +07
   UTC:           2025-09-30 13:00:00 UTC
   Offset:        +0700 (UTC+7)

✅ Verification:
   ✅ Timezone set to Asia/Ho_Chi_Minh
   ✅ UTC offset is +07:00
   ✅ Time conversion working correctly

🎉 All timezone checks passed!
```

### **Fix timezone on cloud**

If cloud shows wrong timezone:

1. Check `app.py` line 11-12:
   ```python
   from utils.timezone_manager import TimezoneManager
   TimezoneManager.setup_environment_timezone()
   ```

2. This should already be there ✅

3. Verify `pytz` is in requirements.txt:
   ```
   python-dateutil>=2.8.2
   ```

4. If still wrong, add to Streamlit secrets:
   ```toml
   APP_TIMEZONE = "Asia/Ho_Chi_Minh"
   ```

---

## 🔍 Common Issues

### Issue 1: "Backup thất bại"

**Cause**: Drive not connected

**Solution**:
- Check OAuth token in secrets
- Reboot app
- Check logs for connection errors

### Issue 2: "Reload thất bại"

**Cause**: No backup file on Drive

**Solution**:
- Check Drive folder has backup files
- Verify folder_id in secrets is correct
- Try manual backup first

### Issue 3: "Data mất sau restart"

**Cause**: Not using Drive storage on cloud

**Solution**:
- Check app logs: Should see "✅ Sử dụng Google Drive Storage (Cloud)"
- If sees "CSV Local Storage" → OAuth not working
- Fix OAuth as per STREAMLIT_CLOUD_SETUP.md

### Issue 4: "Thời gian không đúng"

**Cause**: Timezone not set properly

**Solution**:
- Run `python scripts/verify_timezone.py`
- Check output for errors
- Ensure `TimezoneManager.setup_environment_timezone()` is called in app.py

---

## 📋 Best Practices

### **Daily Operations**

1. **Always backup before major changes**
   - Click "💾 Backup Ngay" before adding many transactions
   - Keep multiple backups for safety

2. **Use cloud as primary after sync**
   - Access from anywhere
   - Automatic backups
   - No local dependency

3. **Regular verification**
   - Check Drive backups weekly
   - Download backup for offline storage monthly

### **Development Workflow**

```
Local Dev → Test changes → Backup to Drive
                            ↓
Cloud Production ← Load from Drive ← Verify
```

### **Backup Schedule**

- **Automatic**: After each transaction
- **Manual**: Before major changes
- **Full backup**: Weekly (download from Drive)

---

## ✅ Verification Checklist

After sync, verify:

- [ ] Investor list matches on both environments
- [ ] Transaction history matches
- [ ] Fee records match
- [ ] Tranche data matches
- [ ] Timestamps show correct timezone (+07:00)
- [ ] Latest backup on Drive is accessible
- [ ] Manual backup/restore works

---

## 🆘 Need Help?

If data sync issues persist:

1. Check logs on cloud
2. Verify OAuth connection
3. Try manual sync (download + upload)
4. Check timezone with verify script
5. Review backup files on Drive

---

**Remember**: Google Drive is now your **primary storage** on cloud. Local CSV is only for development! 🚀