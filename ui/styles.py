# styles.py - Clean Professional Styles - No Loading Screen Conflicts

import streamlit as st

def apply_global_styles():
    """
    Clean, professional CSS optimized for performance and user experience
    """
    css_and_js = """
    
    
    <!-- Mobile sidebar controls -->
    <button class="mobile-toggle-btn" onclick="toggleMobileSidebar()" title="Mở menu">
        <span class="hamburger">☰</span>
    </button>
    <div class="sidebar-overlay" onclick="closeMobileSidebar()"></div>
    <button class="mobile-close-btn" onclick="closeMobileSidebar()" title="Đóng menu">
        <span class="close">✕</span>
    </button>

    <style>
        
        /* === MODERN CSS VARIABLES === */
        :root {
            /* Light theme (default) */
            --sidebar-bg: #ffffff;
            --sidebar-text: #1f2937;
            --sidebar-border: #e5e7eb;
            --card-bg: #f9fafb;
            --card-border: #e5e7eb;
            --nav-gradient-start: #667eea;
            --nav-gradient-end: #764ba2;
            --accent-color: #667eea;
            --success-color: #10b981;
            --warning-color: #f59e0b;
            --error-color: #ef4444;
            --text-primary: #111827;
            --text-secondary: #6b7280;
            --hover-bg: #f3f4f6;
            --active-bg: #667eea;
            --active-text: #ffffff;
            --overlay-bg: rgba(0, 0, 0, 0.5);
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            --border-radius: 8px;
            --transition: all 0.2s ease;
        }

        /* Dark theme detection */
        @media (prefers-color-scheme: dark) {
            :root {
                --sidebar-bg: #1f2937;
                --sidebar-text: #f9fafb;
                --sidebar-border: #374151;
                --card-bg: #374151;
                --card-border: #4b5563;
                --nav-gradient-start: #4b5563;
                --nav-gradient-end: #374151;
                --text-primary: #f9fafb;
                --text-secondary: #d1d5db;
                --hover-bg: #4b5563;
                --active-bg: #4b5563;
                --overlay-bg: rgba(0, 0, 0, 0.7);
            }
        }

        /* Streamlit dark theme support */
        [data-theme="dark"] {
            --sidebar-bg: #1f2937;
            --sidebar-text: #f9fafb;
            --sidebar-border: #374151;
            --card-bg: #374151;
            --card-border: #4b5563;
            --text-primary: #f9fafb;
            --text-secondary: #d1d5db;
            --hover-bg: #4b5563;
            --active-bg: #4b5563;
        }

        /* === HIDE STREAMLIT DEFAULT NAVIGATION === */
        section[data-testid="stSidebarNav"],
        div[data-testid="stSidebarNav"],
        ul[data-testid="stSidebarNavItems"],
        .css-1d391kg nav,
        .css-17eq0hr,
        .css-1y4p8pa {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            overflow: hidden !important;
        }

        /* === SIDEBAR RESPONSIVE WIDTH === */
        /* Desktop large (>1200px) */
        @media (min-width: 1200px) {
            section[data-testid="stSidebar"],
            .css-1d391kg {
                width: 350px !important;
                min-width: 350px !important;
            }
        }

        /* Desktop medium (769px - 1199px) */
        @media (min-width: 769px) and (max-width: 1199px) {
            section[data-testid="stSidebar"],
            .css-1d391kg {
                width: 320px !important;
                min-width: 320px !important;
            }
        }

        /* Tablet (481px - 768px) */
        @media (min-width: 481px) and (max-width: 768px) {
            section[data-testid="stSidebar"],
            .css-1d391kg {
                width: 300px !important;
                min-width: 300px !important;
            }
        }

        /* === SIDEBAR CORE STYLING === */
        section[data-testid="stSidebar"],
        .css-1d391kg {
            background-color: var(--sidebar-bg) !important;
            border-right: 1px solid var(--sidebar-border) !important;
            z-index: 1000 !important;
            position: relative !important;
        }

        /* Sidebar text color fix */
        section[data-testid="stSidebar"] *:not(.stat-value),
        .css-1d391kg *:not(.stat-value) {
            color: var(--sidebar-text) !important;
        }

        /* === SIDEBAR CUSTOM COMPONENTS === */
        
        /* Sidebar section headers */
        .sidebar-section {
            margin: 1.2rem 0 0.5rem 0; /* Giảm margin top một chút */
            padding-bottom: 0.25rem; 
            border-bottom: 2px solid var(--sidebar-border);
            font-size: 0.75rem; 
            font-weight: 600; 
            text-transform: uppercase; 
            letter-spacing: 0.8px;
        }

        .sidebar-section::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 30px;
            height: 2px;
            background: linear-gradient(135deg, var(--nav-gradient-start), var(--nav-gradient-end));
            border-radius: 1px;
        }

        /* NAV Card */
        section[data-testid="stSidebar"] .nav-card {
            background: linear-gradient(135deg, var(--nav-gradient-start) 0%, var(--nav-gradient-end) 100%);
            color: white !important; 
            padding: 1rem; 
            border-radius: 10px; 
            text-align: center; 
            margin-bottom: 1rem;
        }

        section[data-testid="stSidebar"] .nav-card * {
            color: white !important;
        }
        
        .nav-title { 
            font-size: 0.8rem; 
            opacity: 0.9; 
            text-transform: uppercase; 
            letter-spacing: 0.5px;
        }
        
        .nav-value { 
            font-size: 1.75rem; 
            font-weight: bold; 
            margin: 4px 0; 
        }
        
        .fm-info { 
            font-size: 0.8rem; 
            opacity: 0.9; 
            margin-top: 5px; 
            padding: 2px 6px;
            # background: rgba(255,255,255,0.1);
            border-radius: 6px;
        }

        /* Stats Grid */
        .stats-grid {
            display: grid; 
            grid-template-columns: 1fr 1fr 1fr; 
            gap: 8px; 
            margin-bottom: 1.2rem;
        }
        .stat-item {
            background: var(--card-bg); 
            border: 1px solid var(--sidebar-border); 
            border-radius: 6px; 
            padding: 8px; 
            text-align: center;
            transition: transform 0.2s ease;
        }
        .stat-item:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md); /* Dùng biến để hợp nhất với dark mode */
        }
        .stat-value { 
            font-size: 1.2rem; 
            font-weight: 600; 
        }
        .stat-label { 
            font-size: 0.65rem; 
            text-transform: uppercase; 
            color: var(--text-secondary) !important; /* Dùng màu phụ, đẹp hơn trong cả 2 theme */
            opacity: 0.9;
        }
        
        /* Radio buttons (menu) */
        .stRadio > div {
            border: 1px solid var(--card-border) !important;
            border-radius: var(--border-radius) !important;
            padding: 5px !important;
            background: var(--card-bg) !important;
        }

        .stRadio > div > label {
            background-color: transparent !important;
            color: var(--sidebar-text) !important;
            padding: 8px 12px !important;
            border-radius: 6px !important;
            margin: 2px 0 !important;
            transition: var(--transition) !important;
            cursor: pointer !important;
            font-weight: 500 !important;
            position: relative !important;
        }

        .stRadio > div > label:hover {
            background-color: var(--hover-bg) !important;
            transform: translateX(2px);
        }

        .stRadio > div > label[data-checked="true"] {
            background-color: var(--active-bg) !important;
            color: var(--active-text) !important;
            font-weight: 600 !important;
            box-shadow: var(--shadow-md) !important;
            transform: translateX(2px);
        }

        .stRadio > div > label[data-checked="true"]::before {
            content: '';
            position: absolute;
            left: -8px;
            top: 50%;
            transform: translateY(-50%);
            width: 3px;
            height: 60%;
            background: var(--accent-color);
            border-radius: 2px;
        }

        /* Buttons */
        .stButton > button {
            background-color: var(--accent-color) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--border-radius) !important;
            padding: 10px 16px !important;
            font-weight: 500 !important;
            transition: var(--transition) !important;
            box-shadow: var(--shadow-sm) !important;
        }

        .stButton > button:hover {
            background-color: var(--nav-gradient-end) !important;
            transform: translateY(-1px);
            box-shadow: var(--shadow-md) !important;
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Success/Error/Info styling */
        .stSuccess, .stError, .stWarning, .stInfo {
            border-radius: var(--border-radius) !important;
            border: none !important;
        }

        .stSuccess {
            background-color: rgba(16, 185, 129, 0.1) !important;
            color: var(--success-color) !important;
        }

        .stError {
            background-color: rgba(239, 68, 68, 0.1) !important;
            color: var(--error-color) !important;
        }

        .stWarning {
            background-color: rgba(245, 158, 11, 0.1) !important;
            color: var(--warning-color) !important;
        }

        .stInfo {
            background-color: rgba(102, 126, 234, 0.1) !important;
            color: var(--accent-color) !important;
        }

        /* Progress bars */
        .stProgress > div > div {
            background: linear-gradient(90deg, var(--nav-gradient-start), var(--nav-gradient-end)) !important;
            height: 8px !important;
            border-radius: 4px !important;
        }

        /* Text inputs */
        .stTextInput > div > div > input {
            border-radius: var(--border-radius) !important;
            border: 1px solid var(--card-border) !important;
            padding: 10px 12px !important;
        }

        .stTextInput > div > div > input:focus {
            border-color: var(--accent-color) !important;
            box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
        }

        /* === MOBILE CONTROLS (Hidden by default) === */
        .mobile-toggle-btn,
        .mobile-close-btn,
        .sidebar-overlay {
            display: none;
        }

        /* === MOBILE RESPONSIVE === */
        @media (max-width: 768px) {
            
            /* Mobile toggle button */
            .mobile-toggle-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                position: fixed;
                top: 1rem;
                left: 1rem;
                z-index: 10001;
                background: var(--accent-color);
                color: white;
                border: none;
                border-radius: 10px;
                width: 48px;
                height: 48px;
                font-size: 18px;
                cursor: pointer;
                box-shadow: var(--shadow-lg);
                transition: var(--transition);
            }

            .mobile-toggle-btn:hover {
                transform: scale(1.05);
                box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.25);
            }

            .hamburger {
                transition: transform 0.3s ease;
            }

            .mobile-toggle-btn.active .hamburger {
                transform: rotate(90deg);
            }

            /* Mobile close button */
            .mobile-close-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                position: absolute;
                top: 1rem;
                right: 1rem;
                z-index: 10002;
                background: rgba(150, 150, 150, 0.2);
                color: white;
                border: none;
                border-radius: 50%;
                width: 36px;
                height: 36px;
                font-size: 16px;
                cursor: pointer;
                backdrop-filter: blur(10px);
                transition: var(--transition);
            }

            .mobile-close-btn:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: scale(1.1);
            }

            /* Overlay */
            .sidebar-overlay.active {
                display: block;
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: var(--overlay-bg);
                z-index: 9998;
                animation: fadeIn 0.3s ease;
            }

            /* Hide Streamlit default collapse button */
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }

            /* Mobile sidebar drawer */
            section[data-testid="stSidebar"],
            .css-1d391kg {
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                height: 100vh !important;
                z-index: 9999 !important;
                transform: translateX(-100%);
                transition: transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
                width: 320px !important;
                box-shadow: 0 0 50px rgba(0, 0, 0, 0.3);
                overflow-y: auto;
                overscroll-behavior: contain;
            }

            section[data-testid="stSidebar"].mobile-active,
            .css-1d391kg.mobile-active {
                transform: translateX(0);
            }

            /* Mobile sidebar content adjustments */
            section[data-testid="stSidebar"] .block-container,
            .css-1d391kg .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            /* Mobile stats grid adjustments */
            .stats-grid {
                display: grid !important;
                grid-template-columns: repeat(3, 1fr) !important;
                gap: 6px !important;
                margin: 0 0.5rem 1rem 0.5rem !important;
            }

            .stat-item {
                padding: 8px 4px !important;
                min-width: 0 !important;
                overflow: hidden !important;
            }

            .stat-value {
                font-size: 1rem !important;
                white-space: nowrap !important;
            }

            .stat-label {
                font-size: 0.55rem !important;
                line-height: 1 !important;
            }

            /* Mobile nav card adjustments */
            .nav-card {
                margin: 60px 1rem 1rem 1rem;
                padding: 1rem;
            }

            .nav-value {
                font-size: 1.5rem !important;
            }

            .nav-title {
                font-size: 0.7rem !important;
            }

            .fm-info {
                font-size: 0.75rem !important;
                padding: 6px 10px !important;
            }

            /* Mobile sidebar sections */
            .sidebar-section {
                margin: 1rem 1rem 0.5rem 1rem;
                font-size: 0.7rem;
            }

            /* Mobile content spacing */
            .stRadio {
                margin: 0 0.5rem;
            }

            .stButton {
                margin: 0 0.5rem;
            }
        }

        /* === ANIMATIONS === */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideInRight {
            from { transform: translateX(-100%); }
            to { transform: translateX(0); }
        }

        /* === ACCESSIBILITY === */
        @media (prefers-reduced-motion: reduce) {
            * {
                transition: none !important;
                animation: none !important;
            }
        }

        /* === TOUCH IMPROVEMENTS === */
        @media (hover: none) and (pointer: coarse) {
            .mobile-toggle-btn,
            .mobile-close-btn,
            .stButton > button,
            .stRadio > div > label {
                min-height: 44px;
                min-width: 44px;
            }
        }

        /* === PERFORMANCE OPTIMIZATIONS === */
        .mobile-toggle-btn,
        section[data-testid="stSidebar"],
        .css-1d391kg {
            will-change: transform;
            backface-visibility: hidden;
            transform: translateZ(0);
        }

        /* === PRINT STYLES === */
        @media print {
            section[data-testid="stSidebar"],
            .css-1d391kg,
            .mobile-toggle-btn,
            .mobile-close-btn,
            .sidebar-overlay {
                display: none !important;
            }
        }

        /* === HIGH CONTRAST MODE === */
        @media (prefers-contrast: high) {
            :root {
                --sidebar-border: #000000;
                --card-border: #000000;
                --text-secondary: #000000;
            }
        }

        /* === FOCUS STYLES === */
        .stButton > button:focus,
        .stRadio > div > label:focus,
        .mobile-toggle-btn:focus,
        .mobile-close-btn:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
    </style>

    <script>
        

        // Enhanced mobile sidebar functionality
        let sidebarOpen = false;
        let touchStartX = 0;
        let touchStartY = 0;
        let isDragging = false;

        function toggleMobileSidebar() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]') || 
                          document.querySelector('.css-1d391kg');
            const overlay = document.querySelector('.sidebar-overlay');
            const toggleButton = document.querySelector('.mobile-toggle-btn');
            
            if (sidebar && overlay && toggleButton) {
                sidebarOpen = !sidebarOpen;
                
                if (sidebarOpen) {
                    sidebar.classList.add('mobile-active');
                    overlay.classList.add('active');
                    toggleButton.classList.add('active');
                    document.body.style.overflow = 'hidden'; // Prevent background scroll
                } else {
                    closeMobileSidebar();
                }
            }
        }

        function closeMobileSidebar() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]') || 
                          document.querySelector('.css-1d391kg');
            const overlay = document.querySelector('.sidebar-overlay');
            const toggleButton = document.querySelector('.mobile-toggle-btn');
            
            if (sidebar && overlay && toggleButton) {
                sidebar.classList.remove('mobile-active');
                overlay.classList.remove('active');
                toggleButton.classList.remove('active');
                sidebarOpen = false;
                document.body.style.overflow = ''; // Restore scroll
            }
        }
        document.addEventListener("DOMContentLoaded", function() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]') || 
                    document.querySelector('.css-1d391kg');
        const overlay = document.querySelector('.sidebar-overlay');
        const toggleButton = document.querySelector('.mobile-toggle-btn');
        if (sidebar && overlay && toggleButton) {
            sidebar.classList.remove('mobile-active');
            overlay.classList.remove('active');
            toggleButton.classList.remove('active');
            sidebarOpen = false;
        }
    });

        // Touch gesture support
        function handleTouchStart(e) {
            if (window.innerWidth <= 768) {
                touchStartX = e.touches[0].clientX;
                touchStartY = e.touches[0].clientY;
                isDragging = true;
            }
        }

        function handleTouchMove(e) {
            if (!isDragging || window.innerWidth > 768) return;
            
            const touchCurrentX = e.touches[0].clientX;
            const touchCurrentY = e.touches[0].clientY;
            const deltaX = touchCurrentX - touchStartX;
            const deltaY = touchCurrentY - touchStartY;
            
            // Only process horizontal swipes
            if (Math.abs(deltaY) > Math.abs(deltaX)) return;
            
            // Close sidebar on left swipe when open
            if (sidebarOpen && deltaX < -50) {
                closeMobileSidebar();
                isDragging = false;
            }
            
            // Open sidebar on right swipe from left edge when closed
            if (!sidebarOpen && touchStartX < 50 && deltaX > 50) {
                toggleMobileSidebar();
                isDragging = false;
            }
        }

        function handleTouchEnd() {
            isDragging = false;
        }

        // Event listeners
        document.addEventListener('touchstart', handleTouchStart, { passive: true });
        document.addEventListener('touchmove', handleTouchMove, { passive: true });
        document.addEventListener('touchend', handleTouchEnd, { passive: true });

        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && sidebarOpen) {
                const sidebar = document.querySelector('[data-testid="stSidebar"]') || 
                              document.querySelector('.css-1d391kg');
                const toggleButton = document.querySelector('.mobile-toggle-btn');
                
                if (sidebar && toggleButton && 
                    !sidebar.contains(e.target) && 
                    !toggleButton.contains(e.target)) {
                    closeMobileSidebar();
                }
            }
        });

        // Keyboard support
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebarOpen) {
                closeMobileSidebar();
            }
        });

        // Handle window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768 && sidebarOpen) {
                closeMobileSidebar();
            }
        });

        // Ensure sidebar is properly initialized
        function initializeSidebar() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]') || 
                          document.querySelector('.css-1d391kg');
            
            if (sidebar) {
                sidebar.style.visibility = 'visible';
                sidebar.style.display = 'block';
                
                // Ensure sidebar content is visible
                const sidebarContent = sidebar.querySelectorAll('*');
                sidebarContent.forEach(element => {
                    if (element.style.display === 'none' && 
                        !element.classList.contains('loading-screen') &&
                        !element.id?.includes('loading')) {
                        element.style.display = '';
                    }
                });
            }
        }

        // Initialize immediately and on DOM changes
        initializeSidebar();
        
        // Watch for DOM changes (for Streamlit's dynamic content)
        if (window.MutationObserver) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        // Small delay to let Streamlit finish rendering
                        setTimeout(initializeSidebar, 100);
                    }
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }

        // Performance optimization: cleanup
        window.addEventListener('beforeunload', function() {
            document.removeEventListener('touchstart', handleTouchStart);
            document.removeEventListener('touchmove', handleTouchMove);
            document.removeEventListener('touchend', handleTouchEnd);
        });
    </script>
    """
    
    st.markdown(css_and_js, unsafe_allow_html=True)