import streamlit as st
import pandas as pd
from datetime import date
from helpers import format_currency, format_phone, format_percentage, parse_currency

# Performance optimizations
from performance.cache_service_simple import cache_investor_data, invalidate_investor_cache
from performance.skeleton_components import SkeletonLoader, skeleton_investor_card, inject_skeleton_css
from performance.performance_monitor import track_performance
from performance.virtual_scroll import InfiniteScrollList

# UX enhancements
from ui.ux_enhancements import UXEnhancements

class InvestorPage:
    """Page quản lý nhà đầu tư"""

    def __init__(self, fund_manager):
        self.fund_manager = fund_manager

    @cache_investor_data
    @track_performance("load_investors")
    def get_investors(_self):
        """Load investors with caching"""
        return _self.fund_manager.get_regular_investors()
    
    def render_add_form(self):
        """Form thêm nhà đầu tư"""
        st.title("👥 Thêm Nhà Đầu Tư")

        # Breadcrumb
        UXEnhancements.breadcrumb([
            ("🏠 Trang chủ", "/"),
            ("👥 Thêm NĐT", "")
        ])

        with st.form("investor_form"):
            col1, col2 = st.columns(2)
            name = col1.text_input("Tên *", help="Tên nhà đầu tư (bắt buộc)")
            phone = col2.text_input("SĐT", help="Số điện thoại (tùy chọn)")

            col3, col4 = st.columns(2)
            address = col3.text_input("Địa chỉ", help="Địa chỉ (tùy chọn)")
            email = col4.text_input("Email", help="Email (tùy chọn)")

            # Inline validation for name
            if name:
                is_valid = len(name.strip()) > 0
                if not is_valid:
                    st.markdown('<div style="color: #dc2626; font-size: 0.875rem; margin-top: -0.5rem;">⚠️ Tên là bắt buộc</div>', unsafe_allow_html=True)

            submitted = st.form_submit_button("➕ Thêm Nhà Đầu Tư", use_container_width=True)

            if submitted:
                # Validation
                if not name or not name.strip():
                    st.error("❌ Vui lòng nhập tên nhà đầu tư")
                    return

                with st.spinner("Đang thêm nhà đầu tư..."):
                    success, message = self.fund_manager.add_investor(name, phone, address, email)

                if success:
                    UXEnhancements.success_animation()
                    st.success(message)
                    st.session_state.data_changed = True
                    invalidate_investor_cache()
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
    
    def render_edit_page(self):
        """Page sửa thông tin nhà đầu tư"""
        st.title("✏️ Sửa Thông Tin Nhà Đầu Tư")

        # Breadcrumb
        UXEnhancements.breadcrumb([
            ("🏠 Trang chủ", "/"),
            ("✏️ Sửa NĐT", "")
        ])

        # Show loading skeleton
        if 'loading_investors' not in st.session_state:
            st.session_state.loading_investors = True

        if st.session_state.loading_investors:
            UXEnhancements.loading_skeleton(rows=5, columns=6)
            investors = self.get_investors()
            st.session_state.loading_investors = False
            st.rerun()
        else:
            investors = self.get_investors()

        # Empty state
        if not investors:
            UXEnhancements.empty_state(
                icon="👥",
                title="Chưa có nhà đầu tư nào",
                description="Thêm nhà đầu tư đầu tiên để bắt đầu quản lý quỹ của bạn",
                action_label="➕ Thêm nhà đầu tư",
                action_callback=lambda: st.session_state.update({'menu_selection': "👥 Thêm Nhà Đầu Tư"})
            )
            return

        # Tạo DataFrame để edit
        data = []
        for inv in investors:
            data.append({
                'ID': inv.id,
                'Name': inv.name,
                'Phone': format_phone(inv.phone),
                'Address': inv.address,
                'Email': inv.email,
                'JoinDate': inv.join_date
            })

        df_display = pd.DataFrame(data)
        
        st.info("💡 Sửa trực tiếp trên bảng bên dưới và bấm 'Lưu' để cập nhật.")
        
        # Data editor
        column_config = {
            "ID": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "Name": st.column_config.TextColumn("Tên", required=True, width="medium"),
            "Phone": st.column_config.TextColumn("SĐT", help="Số điện thoại", width="medium"),
            "Address": st.column_config.TextColumn("Địa chỉ", width="large"),
            "Email": st.column_config.TextColumn("Email", width="medium"),
            "JoinDate": st.column_config.DateColumn("Ngày tham gia", width="medium")
        }
        
        edited_df = st.data_editor(
            df_display,
            column_config=column_config,
            use_container_width=True,
            key="investor_editor"
        )
        
        col1, col2 = st.columns([1, 4])
        
        if col1.button("💾 Lưu Thay Đổi", use_container_width=True):
            with st.spinner("Đang lưu thay đổi..."):
                # Cập nhật fund_manager
                self.fund_manager.investors.clear()

                for _, row in edited_df.iterrows():
                    from core.models import Investor
                    investor = Investor(
                        id=int(row['ID']),
                        name=str(row['Name']),
                        phone=str(row['Phone']) if pd.notna(row['Phone']) else "",
                        address=str(row['Address']) if pd.notna(row['Address']) else "",
                        email=str(row['Email']) if pd.notna(row['Email']) else "",
                        join_date=row['JoinDate'] if pd.notna(row['JoinDate']) else date.today()
                    )
                    self.fund_manager.investors.append(investor)

                st.session_state.data_changed = True
                invalidate_investor_cache()

            # Success feedback
            UXEnhancements.success_animation()
            st.success("✅ Đã lưu thay đổi")
            import time
            time.sleep(1)
            st.rerun()
        
        # Phần xem tình trạng investor
        st.markdown("---")
        self.render_investor_status()
    
    def render_investor_status(self):
        """Xem tình trạng nhà đầu tư"""
        st.subheader("🔍 Xem Tình Trạng Nhà Đầu Tư")
        
        if not self.fund_manager.investors:
            st.info("📝 Chưa có nhà đầu tư nào.")
            return
        
        options = self.fund_manager.get_investor_options()
        selected_display = st.selectbox("Chọn Nhà Đầu Tư", list(options.keys()), key="status_select")
        
        if not selected_display:
            return
        
        # Type safety: ensure investor_id is always an integer using safe selectbox handling
        from utils.streamlit_widget_safety import safe_investor_id_from_selectbox
        investor_id = safe_investor_id_from_selectbox(self.fund_manager, selected_display)
        if investor_id is None:
            st.error("❌ Không thể lấy ID nhà đầu tư hợp lệ từ lựa chọn")
            return
        
        # Input Total NAV
        latest_nav = self.fund_manager.get_latest_total_nav()
        default_nav = format_currency(latest_nav) if latest_nav else "0đ"
        nav_input = st.text_input("NAV hiện tại", value=default_nav, key="status_nav")
        
        current_nav = parse_currency(nav_input)
        
        if current_nav > 0:
            tranches = self.fund_manager.get_investor_tranches(investor_id)
            if tranches:
                balance, profit, profit_perc = self.fund_manager.get_investor_balance(investor_id, current_nav)
                
                col1, col2, col3 = st.columns(3)
                
                col1.metric("💰 Số dư hiện tại", format_currency(balance))
                
                profit_color = "normal" if profit >= 0 else "inverse"
                col2.metric("📈 Lãi/Lỗ hiện tại", format_currency(profit), delta_color=profit_color)
                
                perc_color = "normal" if profit_perc >= 0 else "inverse"
                col3.metric("📊 Tỷ lệ Lãi/Lỗ", format_percentage(profit_perc), delta_color=perc_color)
                
                # Chi tiết tranches
                if len(tranches) > 1:
                    with st.expander("📋 Chi tiết các đợt vốn"):
                        tranche_data = []
                        current_price = self.fund_manager.calculate_price_per_unit(current_nav)
                        
                        for t in tranches:
                            tranche_data.append({
                                'Ngày vào': t.entry_date.strftime("%d/%m/%Y"),
                                'Giá vào': format_currency(t.entry_nav),
                                'Đơn vị quỹ': f"{t.units:.6f}",
                                'Vốn': format_currency(t.invested_value),
                                'Giá trị hiện tại': format_currency(t.units * current_price),
                                'L/L': format_currency((current_price - t.entry_nav) * t.units),
                                'HWM': format_currency(t.hwm)
                            })
                        
                        st.dataframe(pd.DataFrame(tranche_data), use_container_width=True)
            else:
                st.info("📝 Nhà đầu tư chưa có giao dịch nào.")
