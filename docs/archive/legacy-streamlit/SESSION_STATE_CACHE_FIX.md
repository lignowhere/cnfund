# Fix: Session State Cache Invalidation Issue

**Date**: 2025-09-30
**Issue**: Streamlit Cloud not reflecting new data after transactions, while local environment updates immediately

## 🐛 Problem Description

### Symptoms
- ✅ Local: Add transaction → Reload → Data appears ✅
- ❌ Cloud: Add transaction → Reload → Data MISSING ❌
- Data saved successfully (backup created on Drive)
- But Cloud environment uses stale cached data

### Root Cause

**Session State Persistence Issue**:

Streamlit's session state persists across app reloads, which causes:

1. **First Load**: App loads data from Drive → Stores in session state → Sets `last_load` timestamp
2. **User Adds Transaction**: Data saved to Drive ✅ Session state updated ✅
3. **App Reloads** (user refresh or Streamlit Cloud restart):
   - Session state STILL EXISTS with old data
   - `_is_data_loaded()` returns `True` (because data was loaded before)
   - `ensure_data_loaded()` SKIPS loading from Drive
   - App uses STALE session state data ❌

**The Problem**:
```python
def ensure_data_loaded(self):
    if not self._is_data_loaded():  # ❌ Returns True (from old session)
        self.load_from_drive()      # ❌ NEVER EXECUTES
```

**Result**: App uses old cached data from session state instead of fetching fresh data from Drive.

## ✅ Solution

### 1. Added Data Freshness Check

Check age of cached data and reload if too old:

```python
def ensure_data_loaded(self, force_reload: bool = False, max_age_seconds: int = 300):
    """
    Ensure data is loaded - load from Drive if needed

    Args:
        force_reload: Force reload from Drive even if already loaded
        max_age_seconds: Maximum age of cached data in seconds (default: 5 minutes)
    """
    should_reload = force_reload or not self._is_data_loaded()

    # Check data freshness - reload if too old
    if not should_reload and self._is_data_loaded():
        last_load_key = f'{self.session_key_prefix}last_load'
        if last_load_key in st.session_state:
            last_load_time = st.session_state[last_load_key]
            age_seconds = (datetime.now() - last_load_time).total_seconds()

            if age_seconds > max_age_seconds:
                print(f"🔄 Data cached for {age_seconds:.0f}s (max: {max_age_seconds}s) - reloading from Drive")
                should_reload = True

    if should_reload:
        self.load_from_drive()
```

**Benefits**:
- ✅ Automatic reload after 5 minutes (configurable)
- ✅ Prevents extremely stale data
- ✅ Works across app restarts

### 2. Update Timestamp on Save

When saving data, update `last_load` to mark data as fresh:

```python
def save_all_data_enhanced(...) -> bool:
    # Save to session state
    self._set_session_data('investors', investors_df)
    self._set_session_data('tranches', tranches_df)
    self._set_session_data('transactions', transactions_df)
    self._set_session_data('fee_records', fee_records_df)

    # ✅ Update last_load timestamp to mark data as fresh
    st.session_state[f'{self.session_key_prefix}last_load'] = datetime.now()

    # Backup to Drive...
```

**Benefits**:
- ✅ Prevents immediate reload after save
- ✅ Recognizes session state data is current
- ✅ Improves performance (no unnecessary Drive fetch)

### 3. Added Manual Reload Button

For immediate refresh without waiting for timeout:

**UI (sidebar_manager.py)**:
```python
def render_action_buttons(self):
    # ... existing buttons ...

    # Reload data button (full width)
    if st.sidebar.button("🔄 Reload Data", use_container_width=True,
                        help="Tải lại dữ liệu mới nhất từ Google Drive"):
        self.handle_reload_data()
```

**Handler**:
```python
def handle_reload_data(self):
    """Handle reload data from Google Drive"""
    try:
        with st.spinner("🔄 Đang tải lại dữ liệu từ Google Drive..."):
            # Force reload from Drive
            self.data_handler.ensure_data_loaded(force_reload=True)

            # Reload fund manager data
            self.fund_manager.load_data()

            st.success("✅ Đã tải lại dữ liệu mới nhất!")
            st.toast("🔄 Data reloaded successfully", icon="✅")

            # Rerun to refresh UI
            st.rerun()

    except Exception as e:
        st.error(f"❌ Lỗi tải lại dữ liệu: {str(e)}")
```

**Benefits**:
- ✅ User can manually force reload
- ✅ Useful for multi-user scenarios
- ✅ Immediate feedback with success message

## 📊 Cache Invalidation Strategy

### Automatic Invalidation (Time-Based)

```
┌─────────────────────────────────────┐
│ Data loaded at: 10:00:00            │
│ Current time:   10:06:00            │
│ Age:            360 seconds         │
│ Max age:        300 seconds         │
│ ↓                                   │
│ 360 > 300 → RELOAD from Drive ✅    │
└─────────────────────────────────────┘
```

### Manual Invalidation (User-Triggered)

```
┌─────────────────────────────────────┐
│ User clicks "🔄 Reload Data"        │
│ ↓                                   │
│ force_reload=True                   │
│ ↓                                   │
│ RELOAD from Drive ✅                │
│ ↓                                   │
│ Update last_load timestamp          │
│ ↓                                   │
│ st.rerun() → Refresh UI             │
└─────────────────────────────────────┘
```

### Save Timestamp Update

```
┌─────────────────────────────────────┐
│ Transaction saved                   │
│ ↓                                   │
│ Update session state                │
│ ↓                                   │
│ Update last_load = now() ✅         │
│ ↓                                   │
│ Next load: Uses session state       │
│ (because last_load is fresh)        │
└─────────────────────────────────────┘
```

## 🎯 Configuration

### Adjust Cache Timeout

Default: 5 minutes (300 seconds)

**For faster refresh** (more Drive API calls):
```python
data_handler.ensure_data_loaded(max_age_seconds=60)  # 1 minute
```

**For slower refresh** (fewer Drive API calls):
```python
data_handler.ensure_data_loaded(max_age_seconds=600)  # 10 minutes
```

**No automatic refresh** (manual only):
```python
data_handler.ensure_data_loaded(max_age_seconds=float('inf'))  # Never expire
```

## 📝 Usage Examples

### Normal Operation (Automatic)

```python
# App loads data - checks freshness automatically
investors = data_handler.load_investors()

# If data is older than 5 minutes, reloads from Drive
# Otherwise uses cached session state
```

### Force Reload (Manual)

```python
# User clicks "🔄 Reload Data" button
data_handler.ensure_data_loaded(force_reload=True)

# Always reloads from Drive regardless of cache age
```

### After Save Operation

```python
# Save transaction
data_handler.save_all_data_enhanced(...)

# last_load timestamp automatically updated
# Next load will use session state (no Drive fetch needed)
```

## 🐛 Troubleshooting

### Issue: Still seeing old data

**Check**:
1. Wait 5+ minutes and reload (automatic invalidation)
2. Click "🔄 Reload Data" button (manual reload)
3. Check logs for `🔄 Data cached for XXs` message
4. Verify Drive backup was created

### Issue: Too many Drive API calls

**Solution**: Increase `max_age_seconds`:
```python
# In core/drive_data_handler.py
def ensure_data_loaded(self, force_reload: bool = False, max_age_seconds: int = 600):
```

### Issue: Data never refreshes

**Check**:
1. `last_load` timestamp exists in session state
2. Freshness check is executing
3. Drive connection is working
4. Look for error messages in logs

## 📚 Related Files

- `core/drive_data_handler.py` - Cache invalidation logic
- `ui/sidebar_manager.py` - Reload button UI
- `app.py` - Data handler initialization

## 🎉 Result

### Before ❌
```
Local:  Add transaction → Reload → ✅ Data appears
Cloud:  Add transaction → Reload → ❌ Data missing
```

### After ✅
```
Local:  Add transaction → Reload → ✅ Data appears
Cloud:  Add transaction → Reload → ✅ Data appears
        OR click "🔄 Reload Data" → ✅ Instant refresh
```

**Benefits**:
- ✅ Automatic data refresh every 5 minutes
- ✅ Manual reload button for immediate refresh
- ✅ Proper timestamp management
- ✅ Multi-user support
- ✅ Performance optimization (no unnecessary fetches)

---

**Key Lesson**: Session state persistence is powerful but requires proper cache invalidation strategies. Always implement both automatic (time-based) and manual (user-triggered) invalidation for production apps!