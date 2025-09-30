"""
Enhanced Skeleton Loader Components for CNFund
Provides realistic loading placeholders for better UX
"""

import streamlit as st
from typing import Literal

def inject_skeleton_css():
    """Inject CSS for skeleton animations"""
    st.markdown("""
    <style>
    @keyframes skeleton-loading {
        0% {
            background-position: 200% 0;
        }
        100% {
            background-position: -200% 0;
        }
    }

    .skeleton {
        background: linear-gradient(
            90deg,
            #f0f0f0 0%,
            #f8f8f8 20%,
            #f0f0f0 40%,
            #f0f0f0 100%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
        border-radius: 4px;
    }

    .skeleton-dark {
        background: linear-gradient(
            90deg,
            #2a2a2a 0%,
            #3a3a3a 20%,
            #2a2a2a 40%,
            #2a2a2a 100%
        );
        background-size: 200% 100%;
        animation: skeleton-loading 1.5s ease-in-out infinite;
    }

    .skeleton-card {
        border: 1px solid #e5e5e5;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        background: white;
    }

    .skeleton-card-dark {
        border: 1px solid #404040;
        background: #1a1a1a;
    }

    .skeleton-table {
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        overflow: hidden;
    }

    .skeleton-table-header {
        background: #f8f9fa;
        padding: 12px;
        border-bottom: 2px solid #e5e5e5;
    }

    .skeleton-table-row {
        padding: 12px;
        border-bottom: 1px solid #f0f0f0;
    }
    </style>
    """, unsafe_allow_html=True)

def skeleton_text(width: str = "100%", height: str = "16px", style: str = "light"):
    """Render skeleton text line"""
    skeleton_class = "skeleton" if style == "light" else "skeleton-dark"

    st.markdown(f"""
    <div class="{skeleton_class}" style="width: {width}; height: {height}; margin-bottom: 8px;"></div>
    """, unsafe_allow_html=True)

def skeleton_metric_card(dark_mode: bool = False):
    """Render skeleton for metric card"""
    card_class = "skeleton-card" + ("-dark" if dark_mode else "")
    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    st.markdown(f"""
    <div class="{card_class}">
        <div class="{skeleton_class}" style="width: 40%; height: 14px; margin-bottom: 8px;"></div>
        <div class="{skeleton_class}" style="width: 60%; height: 28px; margin-bottom: 4px;"></div>
        <div class="{skeleton_class}" style="width: 30%; height: 12px;"></div>
    </div>
    """, unsafe_allow_html=True)

def skeleton_investor_card(dark_mode: bool = False):
    """Render skeleton for investor card"""
    card_class = "skeleton-card" + ("-dark" if dark_mode else "")
    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div class="{skeleton_class}" style="width: 120px; height: 20px;"></div>
            <div class="{skeleton_class}" style="width: 80px; height: 28px; border-radius: 14px;"></div>
        </div>
        <div class="{skeleton_class}" style="width: 100%; height: 1px; margin: 12px 0;"></div>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
            <div>
                <div class="{skeleton_class}" style="width: 60%; height: 12px; margin-bottom: 6px;"></div>
                <div class="{skeleton_class}" style="width: 80%; height: 18px;"></div>
            </div>
            <div>
                <div class="{skeleton_class}" style="width: 60%; height: 12px; margin-bottom: 6px;"></div>
                <div class="{skeleton_class}" style="width: 80%; height: 18px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def skeleton_transaction_table(rows: int = 5, dark_mode: bool = False):
    """Render skeleton for transaction table"""
    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    header_html = f"""
    <div class="skeleton-table">
        <div class="skeleton-table-header" style="display: grid; grid-template-columns: 100px 150px 1fr 120px 120px 100px; gap: 12px; padding: 12px;">
            <div class="{skeleton_class}" style="height: 16px;"></div>
            <div class="{skeleton_class}" style="height: 16px;"></div>
            <div class="{skeleton_class}" style="height: 16px;"></div>
            <div class="{skeleton_class}" style="height: 16px;"></div>
            <div class="{skeleton_class}" style="height: 16px;"></div>
            <div class="{skeleton_class}" style="height: 16px;"></div>
        </div>
    """

    rows_html = ""
    for i in range(rows):
        rows_html += f"""
        <div class="skeleton-table-row" style="display: grid; grid-template-columns: 100px 150px 1fr 120px 120px 100px; gap: 12px; padding: 12px;">
            <div class="{skeleton_class}" style="height: 14px;"></div>
            <div class="{skeleton_class}" style="height: 14px;"></div>
            <div class="{skeleton_class}" style="height: 14px;"></div>
            <div class="{skeleton_class}" style="height: 14px;"></div>
            <div class="{skeleton_class}" style="height: 14px;"></div>
            <div class="{skeleton_class}" style="height: 14px; width: 60%;"></div>
        </div>
        """

    footer_html = "</div>"

    st.markdown(header_html + rows_html + footer_html, unsafe_allow_html=True)

def skeleton_chart(height: int = 300, dark_mode: bool = False):
    """Render skeleton for chart"""
    card_class = "skeleton-card" + ("-dark" if dark_mode else "")
    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    st.markdown(f"""
    <div class="{card_class}">
        <div class="{skeleton_class}" style="width: 40%; height: 20px; margin-bottom: 16px;"></div>
        <div class="{skeleton_class}" style="width: 100%; height: {height}px; border-radius: 8px;"></div>
        <div style="display: flex; justify-content: space-around; margin-top: 12px;">
            <div class="{skeleton_class}" style="width: 20%; height: 12px;"></div>
            <div class="{skeleton_class}" style="width: 20%; height: 12px;"></div>
            <div class="{skeleton_class}" style="width: 20%; height: 12px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def skeleton_report_header(dark_mode: bool = False):
    """Render skeleton for report header"""
    card_class = "skeleton-card" + ("-dark" if dark_mode else "")
    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="{skeleton_class}" style="width: 200px; height: 28px; margin-bottom: 8px;"></div>
                <div class="{skeleton_class}" style="width: 150px; height: 16px;"></div>
            </div>
            <div>
                <div class="{skeleton_class}" style="width: 120px; height: 40px; border-radius: 6px;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def skeleton_nav_update_form(dark_mode: bool = False):
    """Render skeleton for NAV update form"""
    card_class = "skeleton-card" + ("-dark" if dark_mode else "")
    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    st.markdown(f"""
    <div class="{card_class}">
        <div class="{skeleton_class}" style="width: 50%; height: 24px; margin-bottom: 20px;"></div>

        <div style="margin-bottom: 16px;">
            <div class="{skeleton_class}" style="width: 30%; height: 14px; margin-bottom: 8px;"></div>
            <div class="{skeleton_class}" style="width: 100%; height: 40px; border-radius: 4px;"></div>
        </div>

        <div style="margin-bottom: 16px;">
            <div class="{skeleton_class}" style="width: 30%; height: 14px; margin-bottom: 8px;"></div>
            <div class="{skeleton_class}" style="width: 100%; height: 40px; border-radius: 4px;"></div>
        </div>

        <div style="margin-bottom: 20px;">
            <div class="{skeleton_class}" style="width: 30%; height: 14px; margin-bottom: 8px;"></div>
            <div class="{skeleton_class}" style="width: 100%; height: 80px; border-radius: 4px;"></div>
        </div>

        <div style="display: flex; gap: 12px;">
            <div class="{skeleton_class}" style="width: 120px; height: 40px; border-radius: 6px;"></div>
            <div class="{skeleton_class}" style="width: 100px; height: 40px; border-radius: 6px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def skeleton_dashboard(dark_mode: bool = False):
    """Render complete dashboard skeleton"""
    inject_skeleton_css()

    # Metrics row
    st.markdown("### ")
    cols = st.columns(4)
    for col in cols:
        with col:
            skeleton_metric_card(dark_mode)

    # Charts row
    st.markdown("### ")
    col1, col2 = st.columns(2)
    with col1:
        skeleton_chart(250, dark_mode)
    with col2:
        skeleton_chart(250, dark_mode)

    # Table
    st.markdown("### ")
    skeleton_transaction_table(5, dark_mode)

def skeleton_loading_screen(message: str = "Đang tải dữ liệu...", dark_mode: bool = False):
    """Full page skeleton loading screen"""
    inject_skeleton_css()

    skeleton_class = "skeleton" + ("-dark" if dark_mode else "")

    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 60vh; padding: 40px;">
        <div style="margin-bottom: 24px;">
            <div class="{skeleton_class}" style="width: 60px; height: 60px; border-radius: 50%;"></div>
        </div>
        <div class="{skeleton_class}" style="width: 200px; height: 20px; margin-bottom: 12px;"></div>
        <div class="{skeleton_class}" style="width: 150px; height: 16px;"></div>
    </div>
    """, unsafe_allow_html=True)

# Context manager for skeleton loading
class SkeletonLoader:
    """Context manager for showing skeleton while loading"""

    def __init__(self, skeleton_type: Literal["text", "card", "table", "chart", "dashboard"] = "text",
                 skeleton_count: int = 3, dark_mode: bool = False):
        self.skeleton_type = skeleton_type
        self.skeleton_count = skeleton_count
        self.dark_mode = dark_mode
        self.container = None

    def __enter__(self):
        inject_skeleton_css()
        self.container = st.empty()

        with self.container:
            if self.skeleton_type == "text":
                for _ in range(self.skeleton_count):
                    skeleton_text(dark_mode=self.dark_mode)

            elif self.skeleton_type == "card":
                for _ in range(self.skeleton_count):
                    skeleton_investor_card(self.dark_mode)

            elif self.skeleton_type == "table":
                skeleton_transaction_table(self.skeleton_count, self.dark_mode)

            elif self.skeleton_type == "chart":
                skeleton_chart(300, self.dark_mode)

            elif self.skeleton_type == "dashboard":
                skeleton_dashboard(self.dark_mode)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clear skeleton
        if self.container:
            self.container.empty()

        return False

# Convenience functions
def with_skeleton(skeleton_type: str = "text", count: int = 3, dark_mode: bool = False):
    """Decorator for functions that need skeleton loading"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with SkeletonLoader(skeleton_type, count, dark_mode):
                import time
                time.sleep(0.3)  # Brief delay to show skeleton

            return func(*args, **kwargs)
        return wrapper
    return decorator

# Progressive loading with skeleton
def progressive_skeleton_load(data_loader, skeleton_type: str = "card", items_per_batch: int = 10, dark_mode: bool = False):
    """Load data progressively with skeleton placeholders"""
    inject_skeleton_css()

    container = st.container()

    # Initial skeleton
    with container:
        for _ in range(items_per_batch):
            if skeleton_type == "card":
                skeleton_investor_card(dark_mode)
            elif skeleton_type == "table":
                skeleton_transaction_table(1, dark_mode)

    # Load actual data
    data = data_loader()

    # Replace with real data
    container.empty()

    return data