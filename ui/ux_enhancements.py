"""
Phase 3: User Experience Enhancements
Real-time feedback, better forms, and helpful empty states
"""

import streamlit as st
from typing import Optional, Callable, Any

class UXEnhancements:
    """User experience enhancement utilities"""

    @staticmethod
    def loading_skeleton(rows: int = 3, columns: int = 1):
        """Show loading skeleton for tables/content"""
        css = """
        <style>
        .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: skeleton-loading 1.5s ease-in-out infinite;
            border-radius: 4px;
            margin-bottom: 8px;
        }

        @keyframes skeleton-loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .skeleton-row {
            display: flex;
            gap: 12px;
            margin-bottom: 12px;
        }

        .skeleton-col {
            flex: 1;
            height: 20px;
        }
        </style>
        """

        st.markdown(css, unsafe_allow_html=True)

        skeleton_html = ""
        for _ in range(rows):
            skeleton_html += '<div class="skeleton-row">'
            for _ in range(columns):
                skeleton_html += '<div class="skeleton skeleton-col"></div>'
            skeleton_html += '</div>'

        st.markdown(f'<div>{skeleton_html}</div>', unsafe_allow_html=True)

    @staticmethod
    def empty_state(
        icon: str,
        title: str,
        description: str,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable] = None
    ):
        """Show helpful empty state when no data"""
        html = f"""
        <div style="
            text-align: center;
            padding: 4rem 2rem;
            background: #f9fafb;
            border-radius: 12px;
            border: 2px dashed #e5e7eb;
        ">
            <div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
            <h3 style="color: #1f2937; margin-bottom: 0.5rem;">{title}</h3>
            <p style="color: #6b7280; margin-bottom: 1.5rem;">{description}</p>
        </div>
        """

        st.markdown(html, unsafe_allow_html=True)

        if action_label and action_callback:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(action_label, use_container_width=True):
                    action_callback()

    @staticmethod
    def inline_validation(
        field_value: Any,
        validation_func: Callable[[Any], tuple[bool, str]],
        field_name: str
    ) -> bool:
        """Show inline validation feedback"""
        is_valid, message = validation_func(field_value)

        if not is_valid and field_value:  # Only show if user has typed something
            st.markdown(f"""
            <div style="
                color: #dc2626;
                font-size: 0.875rem;
                margin-top: -0.5rem;
                margin-bottom: 1rem;
            ">
                ⚠️ {message}
            </div>
            """, unsafe_allow_html=True)

        return is_valid

    @staticmethod
    def success_animation():
        """Show success animation"""
        css = """
        <style>
        @keyframes checkmark {
            0% {
                stroke-dashoffset: 100;
                opacity: 0;
            }
            50% {
                stroke-dashoffset: 0;
                opacity: 1;
            }
            100% {
                stroke-dashoffset: 0;
                opacity: 1;
            }
        }

        .success-checkmark {
            width: 80px;
            height: 80px;
            margin: 0 auto;
        }

        .success-checkmark path {
            stroke-dasharray: 100;
            stroke-dashoffset: 100;
            animation: checkmark 0.6s ease-in-out forwards;
        }
        </style>
        """

        svg = """
        <svg class="success-checkmark" viewBox="0 0 52 52">
            <circle cx="26" cy="26" r="25" fill="none" stroke="#28a745" stroke-width="2"/>
            <path fill="none" stroke="#28a745" stroke-width="3" stroke-linecap="round"
                  d="M14 27l7 7 16-16"/>
        </svg>
        """

        st.markdown(css + svg, unsafe_allow_html=True)

    @staticmethod
    def progress_stepper(steps: list[str], current_step: int):
        """Show progress stepper for multi-step forms"""
        css = """
        <style>
        .stepper {
            display: flex;
            justify-content: space-between;
            margin-bottom: 2rem;
            position: relative;
        }

        .stepper::before {
            content: '';
            position: absolute;
            top: 20px;
            left: 0;
            right: 0;
            height: 2px;
            background: #e5e7eb;
            z-index: 0;
        }

        .step {
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            z-index: 1;
            flex: 1;
        }

        .step-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e5e7eb;
            color: #6b7280;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 600;
            margin-bottom: 0.5rem;
            transition: all 0.3s ease;
        }

        .step-circle.active {
            background: #667eea;
            color: white;
            box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
        }

        .step-circle.completed {
            background: #28a745;
            color: white;
        }

        .step-label {
            font-size: 0.875rem;
            color: #6b7280;
            text-align: center;
        }

        .step-label.active {
            color: #667eea;
            font-weight: 600;
        }
        </style>
        """

        html = '<div class="stepper">'

        for i, step in enumerate(steps):
            circle_class = "step-circle"
            label_class = "step-label"

            if i < current_step:
                circle_class += " completed"
            elif i == current_step:
                circle_class += " active"
                label_class += " active"

            icon = "✓" if i < current_step else str(i + 1)

            html += f"""
            <div class="step">
                <div class="{circle_class}">{icon}</div>
                <div class="{label_class}">{step}</div>
            </div>
            """

        html += '</div>'

        st.markdown(css + html, unsafe_allow_html=True)

    @staticmethod
    def quick_actions_bar(actions: list[dict]):
        """Show floating quick actions bar"""
        css = """
        <style>
        .quick-actions {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            display: flex;
            gap: 0.5rem;
            z-index: 1000;
        }

        .quick-action-btn {
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: #667eea;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            cursor: pointer;
            transition: all 0.2s ease;
            border: none;
        }

        .quick-action-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        }

        @media (max-width: 768px) {
            .quick-actions {
                bottom: 1rem;
                right: 1rem;
            }

            .quick-action-btn {
                width: 48px;
                height: 48px;
                font-size: 1.25rem;
            }
        }
        </style>
        """

        st.markdown(css, unsafe_allow_html=True)

    @staticmethod
    def breadcrumb(items: list[tuple[str, str]]):
        """Show breadcrumb navigation"""
        css = """
        <style>
        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            font-size: 0.875rem;
            color: #6b7280;
        }

        .breadcrumb-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .breadcrumb-item a {
            color: #667eea;
            text-decoration: none;
            transition: color 0.2s ease;
        }

        .breadcrumb-item a:hover {
            color: #5568d3;
            text-decoration: underline;
        }

        .breadcrumb-item.active {
            color: #1f2937;
            font-weight: 600;
        }

        .breadcrumb-separator {
            color: #d1d5db;
        }
        </style>
        """

        html = '<div class="breadcrumb">'

        for i, (label, url) in enumerate(items):
            if i > 0:
                html += '<span class="breadcrumb-separator">›</span>'

            if i == len(items) - 1:  # Last item (current page)
                html += f'<span class="breadcrumb-item active">{label}</span>'
            else:
                html += f'<span class="breadcrumb-item"><a href="{url}">{label}</a></span>'

        html += '</div>'

        st.markdown(css + html, unsafe_allow_html=True)

    @staticmethod
    def auto_save_indicator(is_saving: bool = False, last_saved: Optional[str] = None):
        """Show auto-save status indicator"""
        if is_saving:
            status = "💾 Đang lưu..."
            color = "#667eea"
        elif last_saved:
            status = f"✅ Đã lưu {last_saved}"
            color = "#28a745"
        else:
            status = "⚪ Chưa lưu"
            color = "#6b7280"

        st.markdown(f"""
        <div style="
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-size: 0.875rem;
            color: {color};
            z-index: 1000;
        ">
            {status}
        </div>
        """, unsafe_allow_html=True)

    @staticmethod
    def confirmation_dialog(
        title: str,
        message: str,
        confirm_label: str = "Xác nhận",
        cancel_label: str = "Hủy"
    ) -> Optional[bool]:
        """Show confirmation dialog"""
        with st.container():
            st.markdown(f"""
            <div style="
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
            ">
                <h4 style="color: #1f2937; margin-top: 0;">{title}</h4>
                <p style="color: #6b7280;">{message}</p>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if st.button(cancel_label, use_container_width=True, key="cancel"):
                    return False

            with col2:
                if st.button(confirm_label, use_container_width=True, type="primary", key="confirm"):
                    return True

        return None