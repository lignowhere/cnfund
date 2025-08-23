# mobile_styles_addon.py - CSS bổ sung cho stats icons và mobile experience

def add_stats_icons_styles():
    """Thêm CSS cho stats icons và mobile experience cải thiện"""
    
    import streamlit as st
    
    additional_css = """
    <style>
        /* === STATS GRID ICONS === */
        .stat-icon {
            display: block;
            margin-bottom: 4px;
            opacity: 0.8;
            transition: transform 0.2s ease;
        }
        
        .stat-item:hover .stat-icon {
            transform: scale(1.2);
            opacity: 1;
        }
        
        /* === MOBILE SPECIFIC IMPROVEMENTS === */
        @media (max-width: 768px) {
            
            /* Cải thiện touch targets */
            .stButton > button {
                min-height: 44px !important;
                padding: 12px 16px !important;
                font-size: 14px !important;
            }
            
            /* Menu items touch-friendly */
            .stRadio > div > label {
                min-height: 44px !important;
                display: flex !important;
                align-items: center !important;
                padding: 12px 16px !important;
                font-size: 14px !important;
            }
            
            /* Stats grid mobile optimization - giữ 3 cột nhưng thu nhỏ */
            .stats-grid {
                grid-template-columns: 1fr 1fr 1fr !important;
                gap: 6px !important;
                margin: 0 0.5rem 1rem 0.5rem !important;
            }
            
            .stat-item {
                padding: 8px 4px !important;
                min-width: 0 !important;
            }
            
            .stat-icon {
                font-size: 1.1rem !important;
                margin-bottom: 2px !important;
            }
            
            .stat-value {
                font-size: 1.1rem !important;
                font-weight: 600 !important;
            }
            
            .stat-label {
                font-size: 0.6rem !important;
                line-height: 1.1 !important;
                margin-top: 2px !important;
            }
            
            /* Navigation card mobile */
            .nav-card {
                margin: 70px 0.5rem 1rem 0.5rem !important;
                padding: 1rem !important;
            }
            
            .nav-value {
                font-size: 1.6rem !important;
                word-break: break-all !important;
            }
            
            .fm-info {
                font-size: 0.8rem !important;
                padding: 6px 8px !important;
            }
            
            /* Sidebar sections mobile */
            .sidebar-section {
                margin: 1rem 0.5rem 0.5rem 0.5rem !important;
                font-size: 0.7rem !important;
                padding-bottom: 0.3rem !important;
            }
            
            /* Radio container mobile */
            .stRadio {
                margin: 0 0.5rem !important;
            }
            
            .stRadio > div {
                padding: 6px !important;
            }
            
            /* Button containers mobile */
            .stButton {
                margin: 0.2rem 0.5rem !important;
            }
            
            /* Success/error messages mobile */
            .stSuccess, .stError, .stWarning, .stInfo {
                font-size: 14px !important;
                padding: 8px 12px !important;
            }
            
            /* Caption text mobile */
            .css-1n76uvr {
                font-size: 12px !important;
                line-height: 1.3 !important;
            }
        }
        
        /* === TABLET SPECIFIC === */
        @media (min-width: 769px) and (max-width: 1024px) {
            .css-1d391kg {
                width: 280px !important;
            }
            
            .stats-grid {
                gap: 6px;
            }
            
            .stat-item {
                padding: 8px 6px;
            }
            
            .nav-value {
                font-size: 1.6rem !important;
            }
        }
        
        /* === LARGE DESKTOP === */
        @media (min-width: 1200px) {
            .css-1d391kg {
                width: 320px !important;
            }
            
            .nav-card {
                padding: 1.5rem;
            }
            
            .nav-value {
                font-size: 2rem !important;
            }
            
            .stats-grid {
                gap: 12px;
            }
            
            .stat-item {
                padding: 16px 12px;
            }
        }
        
        /* === DARK MODE SPECIFIC FIXES === */
        [data-theme="dark"] .stat-item {
            background: #2d2d2d !important;
            border-color: #404040 !important;
        }
        
        [data-theme="dark"] .sidebar-section {
            border-color: #404040 !important;
            color: #ffffff !important;
        }
        
        [data-theme="dark"] .stRadio > div {
            background: #2d2d2d !important;
            border-color: #404040 !important;
        }
        
        [data-theme="dark"] .stRadio > div > label {
            color: #ffffff !important;
        }
        
        [data-theme="dark"] .stRadio > div > label:hover {
            background-color: #404040 !important;
        }
        
        [data-theme="dark"] .stRadio > div > label[data-checked="true"] {
            background-color: #4a5568 !important;
            color: #ffffff !important;
        }
        
        /* === LOADING STATES === */
        .stat-item.loading {
            opacity: 0.6;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 0.6; }
            50% { opacity: 0.8; }
            100% { opacity: 0.6; }
        }
        
        /* === IMPROVED SCROLLBAR FOR SIDEBAR === */
        .css-1d391kg::-webkit-scrollbar {
            width: 6px;
        }
        
        .css-1d391kg::-webkit-scrollbar-track {
            background: var(--sidebar-bg);
        }
        
        .css-1d391kg::-webkit-scrollbar-thumb {
            background: var(--sidebar-border);
            border-radius: 3px;
        }
        
        .css-1d391kg::-webkit-scrollbar-thumb:hover {
            background: var(--button-bg);
        }
        
        /* === FOCUS STATES FOR ACCESSIBILITY === */
        .mobile-toggle-button:focus,
        .mobile-close-button:focus {
            outline: 2px solid #ffffff;
            outline-offset: 2px;
        }
        
        .stButton > button:focus {
            outline: 2px solid var(--button-bg) !important;
            outline-offset: 2px !important;
        }
        
        .stRadio > div > label:focus {
            outline: 2px solid var(--menu-active-text) !important;
            outline-offset: 2px !important;
        }
        
        /* === PRINT STYLES === */
        @media print {
            .css-1d391kg,
            .mobile-toggle-button,
            .sidebar-overlay {
                display: none !important;
            }
        }
        
        /* === HIGH CONTRAST MODE === */
        @media (prefers-contrast: high) {
            .nav-card {
                border: 2px solid #000000;
            }
            
            .stat-item {
                border: 2px solid #000000;
            }
            
            .stButton > button {
                border: 2px solid #000000 !important;
            }
        }
    </style>
    """
    
    st.markdown(additional_css, unsafe_allow_html=True)

# Integration function
def apply_complete_mobile_styles():
    """Apply complete mobile-optimized styles"""
    from styles import apply_global_styles
    apply_global_styles()
    add_stats_icons_styles()