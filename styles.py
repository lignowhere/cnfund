# styles.py

import streamlit as st

def apply_global_styles():
    """
    Áp dụng CSS và JS. Đã sửa lỗi triệt để để không ảnh hưởng đến nút đóng/mở sidebar trên desktop.
    """
    
    full_html_and_css = """
    <!-- HTML: Các thành phần này mặc định bị ẩn và chỉ được kích hoạt bởi CSS trên màn hình nhỏ -->
    <button class="mobile-toggle-button" onclick="toggleMobileSidebar()">☰</button>
    <div class="sidebar-overlay" onclick="toggleMobileSidebar()"></div>

    <style>
        /* === PHẦN 1: CÁC STYLE LÀM ĐẸP GIAO DIỆN (AN TOÀN CHO DESKTOP) === */
        
        /* Ẩn Streamlit Cloud file explorer/navigation */
    .css-1d391kg, 
    .css-17eq0hr,
    .css-1y4p8pa,
    .css-12oz5g7,
    section[data-testid="stSidebarNav"],
    div[data-testid="stSidebarNav"],
    .css-163ttbj,
    ul[data-testid="stSidebarNavItems"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
    }
    

        /* Thiết lập chiều rộng mặc định cho sidebar trên desktop */
        .css-1d391kg {
            width: 280px !important;
        }

        /* Các style làm đẹp cho card, stats, menu... */
        .nav-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 1rem;
        }
        .nav-title { font-size: 0.8rem; opacity: 0.8; text-transform: uppercase; }
        .nav-value { font-size: 1.75rem; font-weight: bold; margin: 4px 0; }
        .fm-info { font-size: 0.8rem; opacity: 0.9; margin-top: 5px; }

        .stats-grid {
            display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 1rem;
        }
        .stat-item {
            background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 8px; text-align: center;
        }
        .stat-value { font-size: 1.2rem; font-weight: 600; }
        .stat-label { font-size: 0.65rem; text-transform: uppercase; color: #6c757d; }

        .sidebar-section {
            margin: 1.5rem 0 0.5rem 0; padding-bottom: 0.25rem; border-bottom: 2px solid #f0f2f6;
            font-size: 0.75rem; font-weight: 600; color: #495057; text-transform: uppercase; letter-spacing: 0.5px;
        }
        
        .stRadio > div {
            border: 1px solid #e9ecef; border-radius: 8px; padding: 5px; background: #f8f9fa;
        }
        .stRadio > div > label:hover { background-color: #e9ecef; }
        .stRadio > div > label[data-checked="true"] {
            background-color: white; color: #667eea; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }

        .stSelectbox > div > div > div[role="listbox"] { z-index: 9999 !important; }

        /* === PHẦN 2: LOGIC THÔNG MINH CHO SIDEBAR (CHỈ DÀNH CHO MOBILE/TABLET) === */

        /* Mặc định trên desktop, các thành phần tùy chỉnh này hoàn toàn bị vô hiệu hóa */
        .mobile-toggle-button, .sidebar-overlay {
            display: none;
        }

        /* CHỈ áp dụng các quy tắc sau khi màn hình nhỏ hơn hoặc bằng 768px */
        @media (max-width: 768px) {
            
            /* 1. Hiển thị nút hamburger */
            .mobile-toggle-button {
                display: block;
                position: fixed; top: 12px; left: 12px; z-index: 10001;
                background-color: #667eea; color: white; border: none; border-radius: 6px;
                padding: 8px 12px; font-size: 18px; cursor: pointer; box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            }

            /* 2. Hiển thị lớp phủ khi sidebar mở */
            .sidebar-overlay.active {
                display: block;
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0, 0, 0, 0.5); z-index: 9998;
            }

            /* 3. Ẩn nút đóng/mở mặc định của Streamlit để thay bằng nút hamburger */
            [data-testid="stSidebarCollapseButton"] {
                display: none !important;
            }

            /* 4. Biến sidebar thành một thanh trượt "drawer" */
            .css-1d391kg {
                position: fixed; top: 0; left: 0; height: 100%; z-index: 9999;
                /* Bắt đầu ở trạng thái ẩn (trượt ra ngoài màn hình) */
                transform: translateX(-100%);
                transition: transform 0.3s ease-in-out;
                width: 280px !important; /* Duy trì chiều rộng khi mở ra */
            }

            /* Khi JS thêm class 'mobile-active', trượt sidebar vào trong màn hình */
            .css-1d391kg.mobile-active {
                transform: translateX(0);
            }
        }
    </style>

    <script>
        // Script này chỉ có tác dụng khi các phần tử mobile-toggle-button hiển thị
        function toggleMobileSidebar() {
            const sidebar = window.parent.document.querySelector('.css-1d391kg');
            const overlay = window.parent.document.querySelector('.sidebar-overlay');
            if (sidebar && overlay) {
                sidebar.classList.toggle('mobile-active');
                overlay.classList.toggle('active');
            }
        }
    </script>
    """
    st.markdown(full_html_and_css, unsafe_allow_html=True)