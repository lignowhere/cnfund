# security_manager.py
"""
Security and permission helpers for CNFund.
"""

import os
from typing import Dict, Any

import streamlit as st

from utils.timezone_manager import TimezoneManager


class SecurityManager:
    """Manage authentication state and edit-page access rules."""

    def __init__(self):
        self.edit_pages = [
            "👥 Thêm Nhà Đầu Tư",
            "✏️ Sửa Thông Tin NĐT",
            "💸 Thêm Giao Dịch",
            "📈 Cập Nhật NAV",
            "🛠 Rút Vốn Fund Manager",
            "🔧 Quản Lý Giao Dịch",
            "🧮 Tính Toán Phí",
            "📋 Tính Phí Riêng",
        ]
        self.admin_password = self._get_admin_password()

    def _is_cloud_environment(self) -> bool:
        """Detect Streamlit Cloud runtime."""
        return (
            bool(os.getenv("STREAMLIT_CLOUD"))
            or "streamlit.io" in os.getenv("HOSTNAME", "")
            or "/mount/src" in os.getcwd()
        )

    def _get_admin_password(self) -> str:
        """
        Get admin password from secrets or env.
        In cloud mode, missing ADMIN_PASSWORD is a hard error.
        """
        password = None
        try:
            password = st.secrets.get("ADMIN_PASSWORD")
        except Exception:
            password = None

        if not password:
            password = os.getenv("ADMIN_PASSWORD")

        if self._is_cloud_environment() and not password:
            raise RuntimeError("Missing ADMIN_PASSWORD in Streamlit secrets.")

        return str(password or "").strip()

    def is_edit_page(self, page_name: str) -> bool:
        """Return True if this page requires admin login."""
        return page_name in self.edit_pages

    def is_logged_in(self) -> bool:
        """Check login status from session state."""
        return st.session_state.get("logged_in", False)

    def login(self, password: str) -> bool:
        """Attempt login."""
        if not self.admin_password:
            st.error("ADMIN_PASSWORD is not configured.")
            return False
        if password == self.admin_password:
            st.session_state.logged_in = True
            return True
        return False

    def logout(self):
        """Log out current session."""
        st.session_state.logged_in = False

    def render_login_form(self):
        """Render login form for protected pages."""
        if not self.admin_password:
            st.error("ADMIN_PASSWORD is not configured. Viewer mode only.")
            return

        st.markdown(
            """
            <div style='max-width: 420px; margin: 1.5rem auto; padding: 1.5rem;
                        background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.08);'>
                <h3 style='text-align: center; color: #2c3e50; margin-bottom: 1rem;'>
                    🔐 Yêu cầu đăng nhập để chỉnh sửa
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            password = st.text_input(
                "Mật khẩu",
                type="password",
                placeholder="Nhập mật khẩu admin...",
                key="login_password",
            )

            if st.button("🚀 Đăng nhập", type="primary", use_container_width=True):
                if self.login(password):
                    st.success("✅ Đăng nhập thành công.")
                    st.rerun()
                else:
                    st.error("⚠ Mật khẩu không chính xác.")

    def check_page_access(self, page_name: str) -> bool:
        """Return True if current user can access this page."""
        if self.is_edit_page(page_name) and not self.is_logged_in():
            return False
        return True

    def render_access_denied(self):
        """Render permission denied/login UI."""
        self.render_login_form()

    def get_user_role(self) -> str:
        """Return current role."""
        return "admin" if self.is_logged_in() else "viewer"

    def render_user_badge(self) -> str:
        """Return HTML status badge."""
        if self.is_logged_in():
            return (
                "<div style='padding: 6px; background: linear-gradient(135deg, #28a745 0%, #20c997 100%);"
                " color: white; border-radius: 4px; text-align: center; margin-bottom: 6px;'>"
                "<span style='font-size: 11px; font-weight: 500;'>👤 Chế độ Admin</span></div>"
            )
        return (
            "<div style='padding: 6px; background: #fff3cd; color: #856404;"
            " border: 1px solid #ffeaa7; border-radius: 4px; text-align: center;'>"
            "<span style='font-size: 10px;'>🔒 Chế độ chỉ xem</span></div>"
        )


class SessionManager:
    """Manage common Streamlit session state keys."""

    @staticmethod
    def init_session_state():
        """Initialize session defaults."""
        default_values = {
            "logged_in": False,
            "current_page": "👥 Thêm Nhà Đầu Tư",
            "data_changed": False,
            "last_save_time": None,
            "fund_manager": None,
        }
        for key, default_value in default_values.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @staticmethod
    def mark_data_changed():
        """Mark data dirty."""
        st.session_state.data_changed = True

    @staticmethod
    def mark_data_saved():
        """Mark data saved."""
        st.session_state.data_changed = False
        st.session_state.last_save_time = st.session_state.get("current_time")

    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Debug helper for current session."""
        return {
            "logged_in": st.session_state.get("logged_in", False),
            "current_page": st.session_state.get("current_page", "Unknown"),
            "data_changed": st.session_state.get("data_changed", False),
            "session_keys": list(st.session_state.keys()),
        }

    @staticmethod
    def clear_session():
        """Clear all session state except form submit keys."""
        keys_to_clear = [
            key for key in st.session_state.keys() if not key.startswith("FormSubmitter")
        ]
        for key in keys_to_clear:
            del st.session_state[key]


class PermissionManager:
    """Action-level permission helper."""

    PERMISSIONS = {
        "admin": {
            "can_add_investor": True,
            "can_edit_investor": True,
            "can_add_transaction": True,
            "can_edit_transaction": True,
            "can_calculate_fees": True,
            "can_export_data": True,
            "can_view_reports": True,
            "can_manage_nav": True,
            "can_withdraw_funds": True,
        },
        "viewer": {
            "can_add_investor": False,
            "can_edit_investor": False,
            "can_add_transaction": False,
            "can_edit_transaction": False,
            "can_calculate_fees": False,
            "can_export_data": True,
            "can_view_reports": True,
            "can_manage_nav": False,
            "can_withdraw_funds": False,
        },
    }

    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager

    def has_permission(self, action: str) -> bool:
        """Check whether current role can perform action."""
        user_role = self.security_manager.get_user_role()
        return self.PERMISSIONS.get(user_role, {}).get(action, False)

    def require_permission(self, action: str, error_message: str = None) -> bool:
        """Show error and return False if permission is missing."""
        if not self.has_permission(action):
            if error_message:
                st.error(error_message)
            else:
                st.error(f"⚠️ Bạn không có quyền thực hiện: {action}")
            return False
        return True

    def get_allowed_actions(self):
        """Return allowed actions for current role."""
        user_role = self.security_manager.get_user_role()
        permissions = self.PERMISSIONS.get(user_role, {})
        return [action for action, allowed in permissions.items() if allowed]


class AuditLogger:
    """Simple file logger for audit events."""

    def __init__(self):
        self.log_file = "audit.log"

    def log_action(self, user_role: str, action: str, details=None):
        """Append one audit event to file."""
        try:
            timestamp = TimezoneManager.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "user_role": user_role,
                "action": action,
                "details": details or {},
            }
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"{log_entry}\n")
        except Exception:
            pass

    def log_login_attempt(self, success: bool, ip_address: str = None):
        """Record login attempt."""
        self.log_action(
            "system",
            "login_attempt",
            {"success": success, "ip_address": ip_address},
        )

    def log_data_change(self, user_role: str, change_type: str, entity_type: str):
        """Record data change action."""
        self.log_action(
            user_role,
            f"data_{change_type}",
            {"entity_type": entity_type},
        )
