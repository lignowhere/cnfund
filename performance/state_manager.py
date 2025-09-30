"""
Optimized Session State Management for CNFund
Efficient state handling with compression, cleanup, and versioning
"""

import streamlit as st
import json
import pickle
import zlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from .performance_monitor import track_performance

class StateManager:
    """Optimized session state management"""

    def __init__(self):
        self._initialize_state_registry()

    def _initialize_state_registry(self):
        """Initialize state registry"""
        if '_state_registry' not in st.session_state:
            st.session_state._state_registry = {
                'compressed_keys': set(),
                'temporary_keys': {},
                'version': '1.0',
                'last_cleanup': datetime.now()
            }

    @track_performance("state_set")
    def set(self, key: str, value: Any, compress: bool = False, ttl: Optional[int] = None):
        """
        Set state value with optional compression and TTL

        Args:
            key: State key
            value: Value to store
            compress: Whether to compress large objects
            ttl: Time to live in seconds
        """
        if compress:
            # Compress large objects
            try:
                serialized = pickle.dumps(value)
                if len(serialized) > 10000:  # Compress if > 10KB
                    compressed = zlib.compress(serialized)
                    st.session_state[key] = compressed
                    st.session_state._state_registry['compressed_keys'].add(key)
                else:
                    st.session_state[key] = value
            except Exception as e:
                print(f"Compression failed for {key}: {e}")
                st.session_state[key] = value
        else:
            st.session_state[key] = value

        # Handle TTL
        if ttl is not None:
            st.session_state._state_registry['temporary_keys'][key] = {
                'expires_at': datetime.now() + timedelta(seconds=ttl),
                'ttl': ttl
            }

    @track_performance("state_get")
    def get(self, key: str, default: Any = None, decompress: bool = False) -> Any:
        """
        Get state value with optional decompression

        Args:
            key: State key
            default: Default value if key not found
            decompress: Whether to decompress value

        Returns:
            State value or default
        """
        if key not in st.session_state:
            return default

        # Check TTL expiration
        if key in st.session_state._state_registry.get('temporary_keys', {}):
            temp_info = st.session_state._state_registry['temporary_keys'][key]
            if datetime.now() > temp_info['expires_at']:
                # Expired, remove and return default
                self.remove(key)
                return default

        value = st.session_state[key]

        # Decompress if needed
        if decompress or key in st.session_state._state_registry.get('compressed_keys', set()):
            try:
                decompressed = zlib.decompress(value)
                value = pickle.loads(decompressed)
            except Exception as e:
                print(f"Decompression failed for {key}: {e}")

        return value

    def remove(self, key: str):
        """Remove state key"""
        if key in st.session_state:
            del st.session_state[key]

        # Clean up registry
        if key in st.session_state._state_registry.get('compressed_keys', set()):
            st.session_state._state_registry['compressed_keys'].remove(key)

        if key in st.session_state._state_registry.get('temporary_keys', {}):
            del st.session_state._state_registry['temporary_keys'][key]

    def cleanup_expired(self):
        """Clean up expired temporary keys"""
        now = datetime.now()
        expired_keys = []

        for key, info in st.session_state._state_registry.get('temporary_keys', {}).items():
            if now > info['expires_at']:
                expired_keys.append(key)

        for key in expired_keys:
            self.remove(key)

        if expired_keys:
            print(f"Cleaned up {len(expired_keys)} expired state keys")

        st.session_state._state_registry['last_cleanup'] = now

    def cleanup_navigation_state(self, current_page: str):
        """Clean up state from previous pages"""
        # Define page-specific state prefixes
        page_prefixes = {
            'investor': ['investor_', 'add_investor_', 'edit_investor_'],
            'transaction': ['transaction_', 'add_transaction_', 'nav_'],
            'fee': ['fee_', 'calculate_fee_'],
            'report': ['report_', 'chart_'],
            'backup': ['backup_']
        }

        # Get prefixes for other pages (not current)
        prefixes_to_clean = []
        for page, prefixes in page_prefixes.items():
            if page not in current_page.lower():
                prefixes_to_clean.extend(prefixes)

        # Remove state keys with those prefixes
        keys_to_remove = [
            key for key in list(st.session_state.keys())
            if any(key.startswith(prefix) for prefix in prefixes_to_clean)
        ]

        for key in keys_to_remove:
            if key not in ['fund_manager', 'data_handler', 'sidebar_manager', 'pages']:
                self.remove(key)

        if keys_to_remove:
            print(f"Cleaned up {len(keys_to_remove)} navigation state keys")

    def auto_cleanup(self):
        """Automatic cleanup on every run"""
        last_cleanup = st.session_state._state_registry.get('last_cleanup', datetime.now())

        # Cleanup every 5 minutes
        if datetime.now() - last_cleanup > timedelta(minutes=5):
            self.cleanup_expired()

    def get_state_size(self) -> Dict[str, int]:
        """Get approximate size of session state"""
        sizes = {}

        for key, value in st.session_state.items():
            if not key.startswith('_'):
                try:
                    size = len(pickle.dumps(value))
                    sizes[key] = size
                except Exception:
                    sizes[key] = 0

        return sizes

    def get_total_size(self) -> int:
        """Get total session state size"""
        return sum(self.get_state_size().values())

    def render_state_monitor(self):
        """Render state monitoring dashboard"""
        st.subheader("🗄️ Session State Monitor")

        # Summary
        total_keys = len([k for k in st.session_state.keys() if not k.startswith('_')])
        compressed_keys = len(st.session_state._state_registry.get('compressed_keys', set()))
        temporary_keys = len(st.session_state._state_registry.get('temporary_keys', {}))
        total_size = self.get_total_size()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Keys", total_keys)

        with col2:
            st.metric("Compressed", compressed_keys)

        with col3:
            st.metric("Temporary", temporary_keys)

        with col4:
            size_kb = total_size / 1024
            st.metric("Total Size", f"{size_kb:.1f} KB")

        # Top memory consumers
        st.subheader("Top Memory Consumers")
        sizes = self.get_state_size()
        top_consumers = sorted(sizes.items(), key=lambda x: x[1], reverse=True)[:10]

        for key, size in top_consumers:
            size_kb = size / 1024
            st.text(f"{key}: {size_kb:.2f} KB")

        # Cleanup button
        if st.button("🧹 Manual Cleanup"):
            self.cleanup_expired()
            st.success("Expired keys cleaned up")

# Global state manager instance
_state_manager = None

def get_state_manager() -> StateManager:
    """Get or create global state manager"""
    global _state_manager
    if _state_manager is None:
        _state_manager = StateManager()
    return _state_manager

# Optimistic UI updates
class OptimisticUpdate:
    """Handle optimistic UI updates"""

    def __init__(self, key: str):
        self.key = key
        self.original_value = None
        self.state_manager = get_state_manager()

    def __enter__(self):
        # Save original value
        self.original_value = self.state_manager.get(self.key)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Rollback on error
        if exc_type is not None:
            self.state_manager.set(self.key, self.original_value)
            st.error("Operation failed. Changes rolled back.")
            return True  # Suppress exception

        return False

# State persistence across pages
class StatePersistence:
    """Persist state across page navigation"""

    def __init__(self, keys: List[str]):
        self.keys = keys
        self.state_manager = get_state_manager()

    def save(self):
        """Save specified keys for persistence"""
        persistence_data = {}

        for key in self.keys:
            if key in st.session_state:
                persistence_data[key] = st.session_state[key]

        self.state_manager.set('_persisted_state', persistence_data, compress=True)

    def restore(self):
        """Restore persisted state"""
        persisted = self.state_manager.get('_persisted_state', {}, decompress=True)

        for key, value in persisted.items():
            if key not in st.session_state:
                st.session_state[key] = value

# Form state management
class FormStateManager:
    """Manage form state with auto-save"""

    def __init__(self, form_id: str):
        self.form_id = form_id
        self.state_key = f"form_state_{form_id}"
        self.state_manager = get_state_manager()

    def save_field(self, field_name: str, value: Any):
        """Save individual form field"""
        form_state = self.state_manager.get(self.state_key, {})
        form_state[field_name] = value
        self.state_manager.set(self.state_key, form_state, ttl=3600)  # 1 hour TTL

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """Get form field value"""
        form_state = self.state_manager.get(self.state_key, {})
        return form_state.get(field_name, default)

    def clear(self):
        """Clear form state"""
        self.state_manager.remove(self.state_key)

    def has_unsaved_changes(self) -> bool:
        """Check if form has unsaved changes"""
        form_state = self.state_manager.get(self.state_key, {})
        return len(form_state) > 0

# State versioning for compatibility
class StateVersionManager:
    """Manage state version for backward compatibility"""

    CURRENT_VERSION = "1.0"

    @staticmethod
    def get_version() -> str:
        """Get current state version"""
        return st.session_state._state_registry.get('version', '1.0')

    @staticmethod
    def migrate_if_needed():
        """Migrate state if version mismatch"""
        current_version = StateVersionManager.get_version()

        if current_version != StateVersionManager.CURRENT_VERSION:
            print(f"Migrating state from {current_version} to {StateVersionManager.CURRENT_VERSION}")
            # Add migration logic here
            st.session_state._state_registry['version'] = StateVersionManager.CURRENT_VERSION

# Efficient state watchers
class StateWatcher:
    """Watch for state changes"""

    def __init__(self, keys: List[str], callback: callable):
        self.keys = keys
        self.callback = callback
        self.last_values = {}

        # Initialize last values
        for key in keys:
            if key in st.session_state:
                self.last_values[key] = st.session_state[key]

    def check_changes(self):
        """Check for changes and trigger callback"""
        changes = {}

        for key in self.keys:
            current_value = st.session_state.get(key)
            last_value = self.last_values.get(key)

            if current_value != last_value:
                changes[key] = {
                    'old': last_value,
                    'new': current_value
                }
                self.last_values[key] = current_value

        if changes:
            self.callback(changes)