# security_manager.py
"""
Quản lý bảo mật và authentication
"""

import streamlit as st
import os


class SecurityManager:
    """Quản lý bảo mật và authentication cho app"""
    
    def __init__(self):
        self.admin_password = self._get_admin_password()
        self.edit_pages = [
            "👥 Thêm Nhà Đầu Tư",
            "✏️ Sửa Thông Tin NĐT",
            "💸 Thêm Giao Dịch", 
            "📈 Thêm Total NAV",
            "🛒 Fund Manager Withdrawal",
            "🔧 Quản Lý Giao Dịch",
            "🧮 Tính Toán Phí"
        ]
    
    def _get_admin_password(self):
        """Get admin password từ secrets hoặc env vars"""
        try:
            return st.secrets["ADMIN_PASSWORD"]
        except (KeyError, FileNotFoundError, AttributeError):
            # Fallback cho local hoặc nếu secrets chưa set
            password = os.getenv("ADMIN_PASSWORD")
            if not password:
                password = "1997"  # Default cho development
            return password
    
    def is_edit_page(self, page_name):
        """Check xem page có cần quyền edit không"""
        return page_name in self.edit_pages
    
    def is_logged_in(self):
        """Check login status"""
        return st.session_state.get('logged_in', False)
    
    def login(self, password):
        """Thực hiện login"""
        if password == self.admin_password:
            st.session_state.logged_in = True
            return True
        return False
    
    def logout(self):
        """Thực hiện logout"""
        st.session_state.logged_in = False
    
    def render_login_form(self):
        """Render form login với styling cải tiến"""
        st.markdown("""
            <div style='max-width: 400px; margin: 2rem auto; padding: 2rem; 
                        background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h3 style='text-align: center; color: #2c3e50; margin-bottom: 1.5rem;'>
                    🔐 Yêu cầu đăng nhập để chỉnh sửa
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                password = st.text_input("Mật khẩu", type="password", 
                                       placeholder="Nhập mật khẩu admin...",
                                       key="login_password")
                
                if st.button("🚀 Đăng nhập", use_container_width=True, type="primary"):
                    if self.login(password):
                        st.success("✅ Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("⚠ Mật khẩu không chính xác")
                        st.info("💡 Liên hệ admin để được hỗ trợ")
    
    def check_page_access(self, page_name):
        """Check quyền truy cập page"""
        if self.is_edit_page(page_name) and not self.is_logged_in():
            return False
        return True
    
    def render_access_denied(self):
        """Render thông báo không có quyền truy cập"""
        self.render_login_form()
    
    def get_user_role(self):
        """Get user role hiện tại"""
        if self.is_logged_in():
            return "admin"
        return "viewer"
    
    def render_user_badge(self):
        """Render user status badge"""
        if self.is_logged_in():
            return """
                <div style='padding: 6px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
                            color: white; border-radius: 4px; text-align: center; margin-bottom: 6px;'>
                    <span style='font-size: 11px; font-weight: 500;'>👤 Chế độ Admin</span>
                </div>
            """
        else:
            return """
                <div style='padding: 6px; background: #fff3cd; color: #856404; 
                            border: 1px solid #ffeaa7; border-radius: 4px; text-align: center;'>
                    <span style='font-size: 10px;'>🔒 Chế độ chỉ xem</span>
                </div>
            """


class SessionManager:
    """Quản lý session state và data persistence"""
    
    @staticmethod
    def init_session_state():
        """Initialize session state variables"""
        default_values = {
            'logged_in': False,
            'current_page': "👥 Thêm Nhà Đầu Tư",
            'data_changed': False,
            'last_save_time': None,
            'fund_manager': None
        }
        
        for key, default_value in default_values.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def mark_data_changed():
        """Mark data as changed"""
        st.session_state.data_changed = True
    
    @staticmethod
    def mark_data_saved():
        """Mark data as saved"""
        st.session_state.data_changed = False
        st.session_state.last_save_time = st.session_state.get('current_time')
    
    @staticmethod
    def get_session_info():
        """Get session information for debugging"""
        return {
            'logged_in': st.session_state.get('logged_in', False),
            'current_page': st.session_state.get('current_page', 'Unknown'),
            'data_changed': st.session_state.get('data_changed', False),
            'session_keys': list(st.session_state.keys())
        }
    
    @staticmethod
    def clear_session():
        """Clear all session data"""
        keys_to_clear = [key for key in st.session_state.keys() 
                        if not key.startswith('FormSubmitter')]
        for key in keys_to_clear:
            del st.session_state[key]


class PermissionManager:
    """Quản lý permissions cho các features khác nhau"""
    
    PERMISSIONS = {
        'admin': {
            'can_add_investor': True,
            'can_edit_investor': True,
            'can_add_transaction': True,
            'can_edit_transaction': True,
            'can_calculate_fees': True,
            'can_export_data': True,
            'can_view_reports': True,
            'can_manage_nav': True,
            'can_withdraw_funds': True
        },
        'viewer': {
            'can_add_investor': False,
            'can_edit_investor': False,
            'can_add_transaction': False,
            'can_edit_transaction': False,
            'can_calculate_fees': False,
            'can_export_data': True,  # Viewer có thể export
            'can_view_reports': True,  # Viewer có thể xem reports
            'can_manage_nav': False,
            'can_withdraw_funds': False
        }
    }
    
    def __init__(self, security_manager):
        self.security_manager = security_manager
    
    def has_permission(self, action):
        """Check quyền thực hiện action"""
        user_role = self.security_manager.get_user_role()
        return self.PERMISSIONS.get(user_role, {}).get(action, False)
    
    def require_permission(self, action, error_message=None):
        """Decorator/context manager require permission"""
        if not self.has_permission(action):
            if error_message:
                st.error(error_message)
            else:
                st.error(f"⚠️ Bạn không có quyền thực hiện: {action}")
            return False
        return True
    
    def get_allowed_actions(self):
        """Get list of allowed actions cho user hiện tại"""
        user_role = self.security_manager.get_user_role()
        permissions = self.PERMISSIONS.get(user_role, {})
        return [action for action, allowed in permissions.items() if allowed]


class AuditLogger:
    """Log các hoạt động của user"""
    
    def __init__(self):
        self.log_file = "audit.log"
    
    def log_action(self, user_role, action, details=None):
        """Log user action"""
        try:
            import datetime
            timestamp = datetime.datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'user_role': user_role,
                'action': action,
                'details': details or {}
            }
            
            # Simple file logging
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\n")
        except Exception:
            # Silent fail for logging errors
            pass
    
    def log_login_attempt(self, success, ip_address=None):
        """Log login attempt"""
        self.log_action(
            'system',
            'login_attempt',
            {'success': success, 'ip_address': ip_address}
        )
    
    def log_data_change(self, user_role, change_type, entity_type):
        """Log data changes"""
        self.log_action(
            user_role,
            f'data_{change_type}',
            {'entity_type': entity_type}
        )