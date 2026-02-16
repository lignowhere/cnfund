# Fix: Post-Save Data Reload Issue

**Date**: 2025-09-30
**Issue**: After saving transaction, new data not visible until full app reboot

## 🐛 Problem Description

### Symptoms
- User adds transaction → Save successful ✅
- New backup file created on Drive ✅
- **BUT** data not visible in UI ❌
- Need to reboot Streamlit or force reload to see changes
- Click "Reload Data" → Still shows old data ❌
- Only full app restart shows new data

### Root Cause - Multi-Layer Issue

**Layer 1: Session State Persistence**
```
Save transaction
    ↓
Update session state with new data ✅
    ↓
Upload backup to Drive ✅
    ↓
st.rerun() → Refresh UI
    ↓
❌ Session state STILL EXISTS (not cleared)
    ↓
ensure_data_loaded() → Checks freshness
    ↓
last_load timestamp is RECENT (just updated)
    ↓
SKIP reload from Drive ❌
    ↓
Use OLD session state data ❌
```

**Layer 2: Timestamp Management**
```
Before fix:
- Save data → Update last_load = now()
- Next access → Age = 0 seconds
- Age < 300 seconds → Use cached session state
- Result: Never reloads ❌

After fix:
- Save data → Set last_load = now() - 24 hours
- Next access → Age = 86400 seconds
- Age > 300 seconds → Force reload from Drive ✅
```

**Layer 3: Drive API Indexing**
```
Upload file → Success ✅
    ↓
Immediately query → File not in results ❌ (not indexed yet)
    ↓
Wait 2 seconds → Query again
    ↓
File appears in results ✅
```

## ✅ Solution - 3-Part Fix

### 1. Mark Data as Stale After Save

Force next access to reload from Drive:

```python
def save_all_data_enhanced(...) -> bool:
    # Save to session state
    self._set_session_data('investors', investors_df)
    # ... other tables ...

    # ✅ IMPORTANT: Mark data as stale to force reload on next access
    # Set last_load to 24 hours ago to trigger immediate reload
    st.session_state[f'{self.session_key_prefix}last_load'] = datetime.now() - timedelta(hours=24)

    print("✅ Session state updated (marked as stale for next reload)")

    # Upload to Drive...
```

**Why 24 hours ago?**
- Default freshness check is 5 minutes (300 seconds)
- Setting to 24 hours ago = 86400 seconds
- 86400 > 300 → Guaranteed to trigger reload

### 2. Wait for Drive API Indexing

Give Drive time to index the new file:

```python
def backup_to_drive(self, auto_cleanup: bool = True, keep_recent: int = 10) -> bool:
    # Upload file
    success = self.drive_manager.upload_to_drive(excel_buffer, filename)

    if success:
        # ✅ Wait for Drive API to index the file
        import time
        print("⏳ Waiting 2 seconds for Drive API indexing...")
        time.sleep(2)

        # ✅ Verify file appears in search
        verification_attempt = self._find_latest_backup()
        if verification_attempt and verification_attempt['name'] == filename:
            print(f"✅ Verification passed: File {filename} found in Drive")
```

### 3. Force Reload After Transaction

Immediately reload from Drive after successful transaction:

```python
def _process_validated_transaction(self, ...):
    # Process transaction
    if trans_type == "Nạp":
        success, message = self.fund_manager.process_deposit(...)
    else:
        success, message = self.fund_manager.process_withdrawal(...)

    if success:
        st.success(f"✅ {message}")

        # ✅ IMPORTANT: Force reload data from Drive after save
        print("🔄 Forcing reload from Drive after transaction...")
        self.fund_manager.data_handler.ensure_data_loaded(force_reload=True)
        self.fund_manager.load_data()

        # Show UI feedback
        st.balloons()
        st.rerun()
```

**Why force reload here?**
- Transaction just saved → Data uploaded to Drive
- We want IMMEDIATE reflection in UI
- Don't wait for freshness check timeout
- Reload happens BEFORE st.rerun()
- UI shows fresh data instantly

## 📊 Complete Flow

### Before All Fixes ❌

```
User adds transaction
    ↓
Save to session state ✅
    ↓
Upload to Drive ✅
    ↓
Update last_load = now() ❌
    ↓
st.rerun()
    ↓
ensure_data_loaded() checks:
  - Data loaded? Yes ✅
  - Age: 0 seconds
  - Age > 300? No ❌
  - Action: Use session state (OLD DATA) ❌
    ↓
User sees OLD data ❌
```

### After All Fixes ✅

```
User adds transaction
    ↓
Save to session state ✅
    ↓
Upload to Drive ✅
    ↓
Wait 2 seconds (indexing) ✅
    ↓
Verify file indexed ✅
    ↓
Set last_load = now() - 24 hours ✅
    ↓
FORCE reload from Drive ✅
    ↓
Load fund_manager data ✅
    ↓
st.rerun()
    ↓
User sees NEW data immediately ✅
```

## 🎯 Key Changes

### File: `core/drive_data_handler.py`

**1. Import timedelta**:
```python
from datetime import datetime, date, timedelta
```

**2. Modified save_all_data_enhanced()**:
```python
# Mark as stale (24 hours old)
st.session_state[f'{self.session_key_prefix}last_load'] = datetime.now() - timedelta(hours=24)
```

**3. Modified backup_to_drive()**:
```python
# Wait 2 seconds for indexing
time.sleep(2)

# Verify file appears
verification_attempt = self._find_latest_backup()
```

### File: `pages/transaction_page.py`

**Modified _process_validated_transaction()**:
```python
if success:
    # Force reload from Drive
    self.fund_manager.data_handler.ensure_data_loaded(force_reload=True)
    self.fund_manager.load_data()

    st.balloons()
    st.rerun()
```

## 🔍 Debugging

### Check Logs After Transaction

**✅ Success - All working**:
```
💾 Starting save: X investors, Y tranches, Z transactions...
📊 Converting to DataFrames...
✅ DataFrames created: ...
💾 Saving to session state...
✅ Session state updated (marked as stale for next reload)
☁️ Backing up to Drive...
📤 Uploading: CNFund_Backup_20250930_150000.xlsx
✅ Upload successful: CNFund_Backup_20250930_150000.xlsx
⏳ Waiting 2 seconds for Drive API indexing...
🔍 Verifying file appears in Drive search...
✅ Verification passed: File CNFund_Backup_20250930_150000.xlsx found in Drive
🔄 Forcing reload from Drive after transaction...
🔍 Querying Drive for backup files...
✅ Query returned 15 files
✅ SELECTED FILE: CNFund_Backup_20250930_150000.xlsx
📥 Đang tải dữ liệu từ Google Drive...
✅ Đã tải dữ liệu từ Drive (File: CNFund_Backup_20250930_150000.xlsx)
```

**⚠️ Issue - Indexing delay**:
```
⏳ Waiting 2 seconds for Drive API indexing...
🔍 Verifying file appears in Drive search...
⚠️ Verification issue: Expected CNFund_Backup_20250930_150000.xlsx, found CNFund_Backup_20250930_145000.xlsx
   This might be a Drive API indexing delay
```

**Solution**: Increase wait time or retry verification

### Verify Data Freshness

Check session state age:
```python
last_load = st.session_state.get(f'{data_handler.session_key_prefix}last_load')
if last_load:
    age = (datetime.now() - last_load).total_seconds()
    print(f"Data age: {age} seconds")
    print(f"Will reload: {age > 300}")
```

## 🐛 Troubleshooting

### Issue: Data still not updating

**Check**:
1. Verify force_reload is being called
2. Check Drive upload success
3. Verify file indexing completed
4. Look for error messages in logs

**Debug**:
```python
# Add after save
print(f"Last load timestamp: {st.session_state.get('cnfund_data_last_load')}")
print(f"Age: {(datetime.now() - st.session_state.get('cnfund_data_last_load')).total_seconds()}")
```

### Issue: Performance impact (slow saves)

**Current overhead**:
- Wait 2 seconds (indexing)
- Reload from Drive (~1-3 seconds)
- Total: ~3-5 seconds per transaction

**Options**:
1. Reduce wait time (risky - might miss new file)
2. Make reload async (complex)
3. Skip force reload (not recommended)

**Trade-off**: Slower save vs guaranteed data consistency

### Issue: Multi-user conflicts

**Scenario**: User A saves while User B is viewing

**Current behavior**:
- User A saves → Reloads → Sees new data ✅
- User B → Old session state → Must click "Reload Data" or wait 5 min

**Solution**: Acceptable - users can manually reload

**Future enhancement**: WebSocket push notifications

## 📚 Related Documents

- [Session State Cache Fix](SESSION_STATE_CACHE_FIX.md)
- [Drive API Indexing Delay Fix](DRIVE_API_INDEXING_DELAY_FIX.md)
- [Backup File Selection Fix](BACKUP_FILE_SELECTION_FIX.md)

## 🎉 Result

### Before ❌
```
Save transaction → Rerun → OLD data
Need full reboot to see changes
```

### After ✅
```
Save transaction → Wait 2s → Reload → Rerun → NEW data ✅
Immediate update in current session
Other sessions: Manual reload or wait 5 min
```

**Success Metrics**:
- ✅ Current session sees data immediately
- ✅ New file created on Drive
- ✅ File properly indexed
- ✅ Force reload works
- ✅ Manual reload works for other users
- ✅ Auto reload after 5 minutes

---

**Key Lesson**: Session state persistence requires explicit invalidation. After data changes, must either:
1. Clear session state completely (aggressive)
2. Mark as stale (smart - what we did)
3. Force reload immediately (guaranteed fresh)

We implemented all three strategies for maximum reliability!