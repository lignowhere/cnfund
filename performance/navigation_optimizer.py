"""
Navigation Performance Optimizer
Reduce lag when switching between pages
"""

import streamlit as st
import time

class NavigationOptimizer:
    """Optimize page navigation performance"""

    @staticmethod
    def track_navigation_time(page_name: str):
        """Track how long navigation takes"""
        if 'nav_times' not in st.session_state:
            st.session_state.nav_times = {}

        start_time = time.time()
        return start_time

    @staticmethod
    def record_navigation_time(page_name: str, start_time: float):
        """Record navigation time for analysis"""
        elapsed = time.time() - start_time

        if 'nav_times' not in st.session_state:
            st.session_state.nav_times = {}

        st.session_state.nav_times[page_name] = elapsed

        # Debug: show in console
        if elapsed > 1.0:
            print(f"⚠️ Slow navigation to {page_name}: {elapsed:.2f}s")

    @staticmethod
    def optimize_page_switching():
        """Apply optimizations for faster page switching"""

        # Debounce rapid page changes
        if 'last_page_change' not in st.session_state:
            st.session_state.last_page_change = 0

        current_time = time.time()
        time_since_last = current_time - st.session_state.last_page_change

        # If user is rapidly clicking, wait a bit
        if time_since_last < 0.3:
            return False  # Skip this render

        st.session_state.last_page_change = current_time
        return True  # Continue with render

    @staticmethod
    def preload_common_data():
        """Preload commonly used data to avoid repeated loads"""

        if 'preloaded_data' not in st.session_state:
            st.session_state.preloaded_data = {}

        # Mark as preloaded
        st.session_state.preloaded_data['timestamp'] = time.time()

    @staticmethod
    def skip_expensive_operations_on_nav():
        """Skip expensive operations when just navigating"""

        # Check if we're just navigating (menu changed but nothing else)
        if 'last_menu_selection' not in st.session_state:
            st.session_state.last_menu_selection = None
            return False

        current_menu = st.session_state.get('menu_selection')
        if current_menu != st.session_state.last_menu_selection:
            # Just navigating, skip expensive ops
            st.session_state.last_menu_selection = current_menu
            return True

        return False

    @staticmethod
    def add_navigation_loading_indicator():
        """Show subtle loading indicator during navigation"""

        css = """
        <style>
        /* Navigation loading indicator */
        @keyframes nav-pulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 1; }
        }

        .nav-loading {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            z-index: 9999;
            animation: nav-pulse 1s ease-in-out infinite;
        }

        /* Hide after load */
        .nav-loaded .nav-loading {
            display: none;
        }
        </style>
        """

        st.markdown(css, unsafe_allow_html=True)


def optimize_sidebar_render():
    """Optimize sidebar rendering to reduce recomputation"""

    # Cache sidebar state to avoid re-renders
    if 'sidebar_rendered' not in st.session_state:
        st.session_state.sidebar_rendered = False

    # Only render once per page load
    if st.session_state.sidebar_rendered:
        return False

    st.session_state.sidebar_rendered = True
    return True


def lazy_load_page_content(page_name: str):
    """Lazy load page content only when needed"""

    if 'loaded_pages' not in st.session_state:
        st.session_state.loaded_pages = set()

    # Check if page already loaded
    if page_name in st.session_state.loaded_pages:
        return True  # Already loaded, fast path

    # First time loading this page
    st.session_state.loaded_pages.add(page_name)
    return False  # Need to load, slow path


def debounce_menu_clicks(delay_ms: int = 300):
    """Debounce rapid menu clicks to prevent lag"""

    if 'last_click_time' not in st.session_state:
        st.session_state.last_click_time = 0

    current_time = time.time() * 1000  # Convert to ms
    time_since_last = current_time - st.session_state.last_click_time

    if time_since_last < delay_ms:
        # Too fast, skip this click
        return False

    st.session_state.last_click_time = current_time
    return True