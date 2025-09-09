#!/usr/bin/env python3
"""
Authentication Helper for Admin Operations
Provides unified authentication for sensitive operations like backup, restore, etc.
"""

import streamlit as st
import time

def check_admin_authentication():
    """
    Check if user is authenticated as admin for sensitive operations
    This uses the same authentication state as the main app (st.session_state.logged_in)
    """
    # Check if already logged in using main app authentication
    if st.session_state.get("logged_in", False):
        return True
    
    # Use the admin password from main app session (already loaded)
    admin_password = st.session_state.get("admin_password", "1997")
    
    # Show authentication form using same style as main app
    st.markdown("""
        <div style='max-width: 400px; margin: 3rem auto; padding: 2rem;
                    background: white; border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                    border: 1px solid rgba(255,255,255,0.2);'>
            <h3 style='text-align: center; color: #2c3e50; margin-bottom: 2rem;
                       font-weight: 600;'>
                🔐 Xác thực quyền quản trị
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    st.warning("🔐 This operation requires admin authentication")
    st.info("💡 This protects critical system operations from unauthorized access")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password_input = st.text_input(
            "Mật khẩu quản trị",
            type="password",
            placeholder="Nhập mật khẩu để tiếp tục...",
            help="Cần mật khẩu admin để truy cập tính năng chỉnh sửa",
            label_visibility="visible"
        )
        
        if st.button("🚀 Xác thực", type="primary", use_container_width=True):
            if password_input == admin_password:
                st.session_state.logged_in = True
                st.success("✅ Xác thực thành công!")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác.")
                time.sleep(1)
                return False
    
    return False

def show_admin_status():
    """
    Show admin authentication status with logout option
    """
    col1, col2 = st.columns([1, 4])
    
    with col1:
        if st.button("🔓 Logout", help="Logout from admin session"):
            st.session_state.logged_in = False
            st.rerun()
    
    with col2:
        st.success("🔐 Authenticated as Administrator")

def is_admin_authenticated():
    """
    Simple check if admin is currently authenticated (without UI)
    """
    return st.session_state.get("logged_in", False)