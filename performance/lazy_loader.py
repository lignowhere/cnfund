"""
Lazy Loading System for CNFund
Dynamically load components and data only when needed
"""

import streamlit as st
import importlib
from typing import Any, Callable, Optional, Dict
from functools import wraps
from .performance_monitor import track_performance

class LazyLoader:
    """Lazy loading manager for components and modules"""

    def __init__(self):
        if 'lazy_loaded_modules' not in st.session_state:
            st.session_state.lazy_loaded_modules = {}

        if 'lazy_loaded_components' not in st.session_state:
            st.session_state.lazy_loaded_components = {}

    @track_performance("lazy_load_module")
    def load_module(self, module_name: str, force_reload: bool = False):
        """
        Lazy load a Python module

        Args:
            module_name: Name of the module to load
            force_reload: Force reload even if cached

        Returns:
            Loaded module
        """
        if not force_reload and module_name in st.session_state.lazy_loaded_modules:
            return st.session_state.lazy_loaded_modules[module_name]

        try:
            module = importlib.import_module(module_name)
            st.session_state.lazy_loaded_modules[module_name] = module
            return module
        except Exception as e:
            st.error(f"Failed to load module {module_name}: {e}")
            return None

    @track_performance("lazy_load_page")
    def load_page(self, page_module: str, page_class: str):
        """
        Lazy load a page component

        Args:
            page_module: Module path (e.g., 'pages.investor_page')
            page_class: Class name (e.g., 'InvestorPage')

        Returns:
            Page class or None
        """
        cache_key = f"{page_module}.{page_class}"

        if cache_key in st.session_state.lazy_loaded_components:
            return st.session_state.lazy_loaded_components[cache_key]

        try:
            module = self.load_module(page_module)
            if module:
                page_cls = getattr(module, page_class)
                st.session_state.lazy_loaded_components[cache_key] = page_cls
                return page_cls
        except Exception as e:
            st.error(f"Failed to load page {page_class}: {e}")
            return None

        return None

    def get_or_load(self, key: str, loader_func: Callable):
        """
        Get cached value or load using provided function

        Args:
            key: Cache key
            loader_func: Function to call if not cached

        Returns:
            Cached or freshly loaded value
        """
        if key in st.session_state.lazy_loaded_components:
            return st.session_state.lazy_loaded_components[key]

        value = loader_func()
        st.session_state.lazy_loaded_components[key] = value
        return value

    def clear_cache(self):
        """Clear all lazy loaded caches"""
        st.session_state.lazy_loaded_modules = {}
        st.session_state.lazy_loaded_components = {}

# Global lazy loader instance
_lazy_loader = None

def get_lazy_loader() -> LazyLoader:
    """Get or create global lazy loader"""
    global _lazy_loader
    if _lazy_loader is None:
        _lazy_loader = LazyLoader()
    return _lazy_loader

# Decorator for lazy component initialization
def lazy_component(component_name: str):
    """
    Decorator to make component loading lazy

    Usage:
        @lazy_component("chart")
        def render_chart():
            # Heavy chart rendering code
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            loader = get_lazy_loader()

            # Check if component already rendered in this session
            cache_key = f"component_{component_name}"
            if cache_key in st.session_state:
                return st.session_state[cache_key]

            # Render component
            with st.spinner(f"Loading {component_name}..."):
                result = func(*args, **kwargs)

            st.session_state[cache_key] = result
            return result

        return wrapper
    return decorator

# Progressive data loading
class ProgressiveDataLoader:
    """Load data progressively to improve perceived performance"""

    def __init__(self, data_source: Callable, page_size: int = 50):
        self.data_source = data_source
        self.page_size = page_size

        if 'progressive_data' not in st.session_state:
            st.session_state.progressive_data = {}

    def load_page(self, page_num: int = 0):
        """Load a specific page of data"""
        cache_key = f"data_page_{page_num}"

        if cache_key in st.session_state.progressive_data:
            return st.session_state.progressive_data[cache_key]

        # Load data
        all_data = self.data_source()

        start_idx = page_num * self.page_size
        end_idx = start_idx + self.page_size

        page_data = all_data[start_idx:end_idx] if hasattr(all_data, '__getitem__') else list(all_data)[start_idx:end_idx]

        st.session_state.progressive_data[cache_key] = page_data
        return page_data

    def load_all_progressively(self, callback: Optional[Callable] = None):
        """Load all data progressively with optional progress callback"""
        all_data = self.data_source()
        total_items = len(all_data) if hasattr(all_data, '__len__') else sum(1 for _ in all_data)
        total_pages = (total_items + self.page_size - 1) // self.page_size

        loaded_data = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for page in range(total_pages):
            page_data = self.load_page(page)
            loaded_data.extend(page_data)

            # Update progress
            progress = (page + 1) / total_pages
            progress_bar.progress(progress)
            status_text.text(f"Loading... {len(loaded_data)}/{total_items}")

            if callback:
                callback(loaded_data, page, total_pages)

        progress_bar.empty()
        status_text.empty()

        return loaded_data

# Viewport visibility detection
def render_when_visible(container_key: str):
    """Only render component when it's likely to be visible"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if user has scrolled to this section
            if f"visible_{container_key}" not in st.session_state:
                st.session_state[f"visible_{container_key}"] = False

            # Render placeholder initially
            if not st.session_state[f"visible_{container_key}"]:
                # Show "Load More" button or auto-load on scroll simulation
                if st.button(f"Load {container_key}", key=f"load_btn_{container_key}"):
                    st.session_state[f"visible_{container_key}"] = True
                    st.rerun()
                return None

            # Render actual content
            return func(*args, **kwargs)

        return wrapper
    return decorator

# Skeleton loader placeholder
def render_skeleton(skeleton_type: str = "text", count: int = 3):
    """Render skeleton loader placeholder"""
    if skeleton_type == "text":
        for _ in range(count):
            st.markdown(
                """
                <div style="background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                            background-size: 200% 100%;
                            animation: loading 1.5s infinite;
                            height: 20px;
                            margin: 10px 0;
                            border-radius: 4px;">
                </div>
                """,
                unsafe_allow_html=True
            )

    elif skeleton_type == "card":
        for _ in range(count):
            st.markdown(
                """
                <div style="border: 1px solid #e0e0e0;
                            padding: 20px;
                            border-radius: 8px;
                            margin: 10px 0;">
                    <div style="background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                                background-size: 200% 100%;
                                animation: loading 1.5s infinite;
                                height: 20px;
                                width: 60%;
                                margin-bottom: 10px;
                                border-radius: 4px;">
                    </div>
                    <div style="background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                                background-size: 200% 100%;
                                animation: loading 1.5s infinite;
                                height: 15px;
                                width: 80%;
                                border-radius: 4px;">
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    elif skeleton_type == "table":
        st.markdown(
            """
            <div style="border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
                <div style="background: #f8f8f8; padding: 15px; border-bottom: 1px solid #e0e0e0;">
                    <div style="background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                                background-size: 200% 100%;
                                animation: loading 1.5s infinite;
                                height: 20px;
                                width: 40%;
                                border-radius: 4px;">
                    </div>
                </div>
            """ +
            "".join([
                f"""
                <div style="padding: 15px; border-bottom: 1px solid #f0f0f0;">
                    <div style="background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                                background-size: 200% 100%;
                                animation: loading 1.5s infinite;
                                height: 15px;
                                width: 80%;
                                margin-bottom: 5px;
                                border-radius: 4px;">
                    </div>
                </div>
                """
                for _ in range(count)
            ]) +
            """
            </div>
            <style>
                @keyframes loading {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
            </style>
            """,
            unsafe_allow_html=True
        )

# Lazy page loader with skeleton
def lazy_load_with_skeleton(loader_func: Callable, skeleton_type: str = "text", skeleton_count: int = 3):
    """Load component with skeleton placeholder"""
    # Show skeleton while loading
    skeleton_placeholder = st.empty()

    with skeleton_placeholder:
        render_skeleton(skeleton_type, skeleton_count)

    # Load actual content
    result = loader_func()

    # Clear skeleton
    skeleton_placeholder.empty()

    return result

# Deferred chart rendering
def defer_chart_render(chart_func: Callable, chart_name: str):
    """Defer chart rendering until user requests it"""
    if f"chart_loaded_{chart_name}" not in st.session_state:
        st.session_state[f"chart_loaded_{chart_name}"] = False

    if not st.session_state[f"chart_loaded_{chart_name}"]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"📊 Chart: {chart_name}")
        with col2:
            if st.button("Load Chart", key=f"load_chart_{chart_name}"):
                st.session_state[f"chart_loaded_{chart_name}"] = True
                st.rerun()
        return

    # Render chart
    return chart_func()

# Image lazy loading
def lazy_load_image(image_url: str, placeholder_text: str = "Loading image..."):
    """Lazy load images"""
    if f"image_loaded_{image_url}" not in st.session_state:
        st.session_state[f"image_loaded_{image_url}"] = False

    if not st.session_state[f"image_loaded_{image_url}"]:
        if st.button(placeholder_text, key=f"load_img_{image_url}"):
            st.session_state[f"image_loaded_{image_url}"] = True
            st.rerun()
        return

    st.image(image_url)