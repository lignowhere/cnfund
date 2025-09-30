"""
Gradual UI/UX Improvements
Subtle enhancements without breaking existing design
"""

import streamlit as st

def apply_subtle_improvements():
    """Apply subtle UI improvements incrementally"""

    css = """
    <style>
    /* === IMPROVEMENT 1: Better spacing for readability === */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* === IMPROVEMENT 2: Smoother button interactions === */
    .stButton > button {
        transition: all 0.2s ease;
        font-weight: 500;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* === IMPROVEMENT 3: Better form field focus === */
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1) !important;
    }

    /* === IMPROVEMENT 4: Card-like containers with subtle elevation === */
    .element-container:has(> .stAlert),
    .element-container:has(> .stDataFrame) {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 1rem;
    }

    /* === IMPROVEMENT 5: Better metric visibility === */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
        padding: 1.25rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }

    /* === IMPROVEMENT 6: Nicer table styling === */
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        overflow: hidden;
    }

    .stDataFrame thead tr th {
        background-color: #f9fafb !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.5px;
        padding: 0.75rem !important;
    }

    .stDataFrame tbody tr:hover {
        background-color: #f9fafb !important;
    }

    /* === IMPROVEMENT 7: Better mobile touch targets === */
    @media (max-width: 768px) {
        .stButton > button {
            min-height: 48px !important;
            padding: 12px 20px !important;
            font-size: 16px !important;
        }

        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            min-height: 48px !important;
            font-size: 16px !important;
        }
    }

    /* === IMPROVEMENT 8: Loading state visibility === */
    .stSpinner > div {
        border-color: #667eea !important;
    }

    /* === IMPROVEMENT 9: Better tab navigation === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 2px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #6b7280;
        border-radius: 4px 4px 0 0;
    }

    .stTabs [aria-selected="true"] {
        background-color: #667eea !important;
        color: white !important;
    }

    /* === IMPROVEMENT 10: Success/Error feedback === */
    .stSuccess {
        background-color: #ecfdf5 !important;
        border-left: 4px solid #10b981 !important;
        padding: 1rem !important;
        border-radius: 4px;
    }

    .stError {
        background-color: #fef2f2 !important;
        border-left: 4px solid #ef4444 !important;
        padding: 1rem !important;
        border-radius: 4px;
    }

    .stWarning {
        background-color: #fffbeb !important;
        border-left: 4px solid #f59e0b !important;
        padding: 1rem !important;
        border-radius: 4px;
    }

    .stInfo {
        background-color: #eff6ff !important;
        border-left: 4px solid #3b82f6 !important;
        padding: 1rem !important;
        border-radius: 4px;
    }

    /* === IMPROVEMENT 11: Smoother page transitions === */
    .main .block-container {
        animation: fadeIn 0.3s ease-in;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* === IMPROVEMENT 12: Better expander styling === */
    .streamlit-expanderHeader {
        background-color: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem !important;
        font-weight: 600;
    }

    .streamlit-expanderHeader:hover {
        background-color: #f3f4f6;
    }

    /* === IMPROVEMENT 13: Form container polish === */
    .stForm {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        background: white;
    }

    /* === IMPROVEMENT 14: Better checkbox/radio styling === */
    .stCheckbox, .stRadio {
        padding: 0.5rem 0;
    }

    .stCheckbox label, .stRadio label {
        font-weight: 500;
    }

    /* === IMPROVEMENT 15: Sidebar visual refinement === */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f9fafb 100%);
    }

    /* Dark mode adjustments */
    @media (prefers-color-scheme: dark) {
        .element-container:has(> .stAlert),
        .element-container:has(> .stDataFrame),
        [data-testid="stMetric"],
        .stForm {
            background: #1f2937;
            border-color: #374151;
        }

        .stDataFrame thead tr th {
            background-color: #374151 !important;
        }

        .streamlit-expanderHeader {
            background-color: #374151;
            border-color: #4b5563;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
        }
    }
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)


def show_loading_feedback(message: str = "Đang xử lý..."):
    """Show user-friendly loading indicator"""
    return st.spinner(message)


def show_success_toast(message: str):
    """Simple success feedback"""
    st.success(f"✅ {message}")


def show_error_toast(message: str):
    """Simple error feedback"""
    st.error(f"❌ {message}")


def show_warning_toast(message: str):
    """Simple warning feedback"""
    st.warning(f"⚠️ {message}")


def show_info_toast(message: str):
    """Simple info feedback"""
    st.info(f"ℹ️ {message}")