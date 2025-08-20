import streamlit as st
from datetime import date, datetime
from utils import format_currency, parse_currency

class TransactionPage:
    """Page xử lý giao dịch"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_transaction_form(self):
        """Form thêm giao dịch"""
        st.title("💸 Thêm Giao Dịch")
        
        if not self.fund_manager.investors:
            st.warning("⚠️ Chưa có nhà đầu tư nào. Hãy thêm nhà đầu tư trước.")
            return
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        if not latest_nav and not self.fund_manager.transactions:
            st.info("🆕 Quỹ mới, hãy bắt đầu bằng giao dịch Nạp tiền.")
        
        # NAV option
        nav_option = st.radio(
            "📊 Cách nhập Total NAV",
            ["Dùng Total NAV mới nhất", "Nhập thủ công"],
            help="Chọn cách xác định Total NAV sau giao dịch"
        )
        
        with st.form("transaction_form"):
            col1, col2 = st.columns(2)
            
            # Chọn investor
            options = self.fund_manager.get_investor_options()
            selected_display = col1.selectbox("👤 Chọn Nhà Đầu Tư", list(options.keys()))
            investor_id = options.get(selected_display, None) if selected_display else None
            
            # Loại giao dịch  
            trans_type = col2.selectbox("📝 Loại Giao Dịch", ["Nạp", "Rút"])
            
            # Ngày giao dịch
            trans_date = st.date_input("📅 Ngày Giao Dịch", value=date.today())
            
            # Số tiền
            amount_input = st.text_input("💰 Số Tiền", value="0đ", help="Nhập số tiền giao dịch")
            amount = parse_currency(amount_input)
            
            # Total NAV
            if nav_option == "Dùng Total NAV mới nhất":
                if trans_type == "Nạp":
                    total_nav = (latest_nav or 0) + amount
                else:  # Rút
                    total_nav = (latest_nav or 0) - amount
                st.write(f"📊 Total NAV sau giao dịch: {format_currency(total_nav)}")
            else:
                default_nav = format_currency(latest_nav) if latest_nav else "0đ"
                nav_input = st.text_input(
                    "📊 Total NAV sau giao dịch", 
                    value=default_nav,
                    help="Nhập Total NAV sau khi thực hiện giao dịch"
                )
                total_nav = parse_currency(nav_input)
            
            submitted = st.form_submit_button("✅ Thực hiện giao dịch", use_container_width=True)
            
            if submitted:
                # Validation
                if not investor_id:
                    st.error("❌ Vui lòng chọn nhà đầu tư")
                elif amount <= 0:
                    st.error("❌ Số tiền phải lớn hơn 0")
                elif total_nav <= 0:
                    st.error("❌ Total NAV phải lớn hơn 0")
                else:
                    # Xử lý giao dịch
                    trans_date_dt = datetime.combine(trans_date, datetime.min.time())
                    
                    if trans_type == "Nạp":
                        success, message = self.fund_manager.process_deposit(
                            investor_id, amount, total_nav, trans_date_dt
                        )
                    else:  # Rút
                        success, message = self.fund_manager.process_withdrawal(
                            investor_id, amount, total_nav, trans_date_dt
                        )
                    
                    if success:
                        st.success(message)
                        st.session_state.data_changed = True
                        st.rerun()
                    else:
                        st.error(message)
    
    def render_nav_update(self):
        """Form cập nhật NAV"""
        st.title("📈 Cập Nhật Total NAV")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        
        if latest_nav:
            st.info(f"📊 Total NAV hiện tại: {format_currency(latest_nav)}")
        
        with st.form("nav_form"):
            trans_date = st.date_input("📅 Ngày", value=date.today())
            
            default_nav = format_currency(latest_nav) if latest_nav else "0đ"
            nav_input = st.text_input(
                "📊 Total NAV mới", 
                value=default_nav,
                help="Nhập Total NAV mới của quỹ"
            )
            total_nav = parse_currency(nav_input)
            
            submitted = st.form_submit_button("✅ Cập nhật NAV", use_container_width=True)
            
            if submitted:
                if total_nav <= 0:
                    st.error("❌ Total NAV phải lớn hơn 0")
                else:
                    trans_date_dt = datetime.combine(trans_date, datetime.min.time())
                    success, message = self.fund_manager.process_nav_update(total_nav, trans_date_dt)
                    
                    if success:
                        st.success(message)
                        st.session_state.data_changed = True
                        st.rerun()
                    else:
                        st.error(message)
