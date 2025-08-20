import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils import format_currency, parse_currency, format_percentage, highlight_profit_loss

class FeePage:
    """Page tính toán phí"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_fee_calculation(self):
        """Tính toán phí cuối năm"""
        st.title("🧮 Tính Toán Phí Cuối Năm")
        
        if not self.fund_manager.investors:
            st.warning("⚠️ Chưa có nhà đầu tư nào.")
            return
        
        # Input parameters
        col1, col2, col3 = st.columns(3)
        
        year = col1.number_input("📅 Năm", value=2025, min_value=2020, max_value=2030)
        ending_date = col2.date_input("📅 Ngày Kết Thúc", value=date(2025, 12, 31))
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = col3.text_input("📊 Total NAV Kết Thúc", value=format_currency(latest_nav) if latest_nav else "0đ")
        ending_nav = parse_currency(nav_input)
        
        tab1, tab2 = st.tabs(["📋 Phí Chi Tiết", "🔍 Chi Tiết Tranches"])
        
        with tab1:
            if st.button("🧮 Tính Toán Phí", use_container_width=True):
                if ending_nav <= 0:
                    st.error("❌ Total NAV kết thúc phải lớn hơn 0")
                else:
                    self._show_fee_calculation(ending_date, ending_nav)
        
        with tab2:
            self._show_tranches_detail(ending_nav)
        
        # Apply fees section
        st.markdown("---")
        st.subheader("⚠️ Áp Dụng Phí")
        st.warning("🚨 Áp dụng phí sẽ thay đổi dữ liệu vĩnh viễn. Hãy chắc chắn trước khi tiếp tục.")
        
        confirm_apply = st.checkbox("✅ Tôi chắc chắn muốn áp dụng phí và reset base.")
        
        if confirm_apply and st.button("🔥 Xác Nhận và Áp Dụng Phí", type="primary"):
            if ending_nav <= 0:
                st.error("❌ Total NAV kết thúc phải lớn hơn 0")
            else:
                success, message = self.fund_manager.apply_year_end_fees(year, ending_date, ending_nav)
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.data_changed = True
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    def render_individual_fee(self):
        """Tính phí riêng cho nhà đầu tư"""
        st.title("🔍 Tính Phí Riêng Cho Nhà Đầu Tư")
        
        if not self.fund_manager.investors:
            st.info("📝 Chưa có nhà đầu tư nào.")
            return
        
        options = self.fund_manager.get_investor_options()
        selected_display = st.selectbox("👤 Chọn Nhà Đầu Tư", list(options.keys()))
        
        if not selected_display:
            return
        
        investor_id = options[selected_display]
        
        col1, col2 = st.columns(2)
        calc_date = col1.date_input("📅 Ngày Tính Phí", value=date.today())
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = col2.text_input("📊 Total NAV", value=format_currency(latest_nav) if latest_nav else "0đ")
        calc_nav = parse_currency(nav_input)
        
        if st.button("🧮 Tính Toán", use_container_width=True):
            if calc_nav <= 0:
                st.error("❌ Total NAV phải lớn hơn 0")
            else:
                calc_date_dt = datetime.combine(calc_date, datetime.min.time())
                details = self.fund_manager.calculate_investor_fee(investor_id, calc_date_dt, calc_nav)
                
                st.markdown(f"**👤 Nhà Đầu Tư:** {selected_display}")
                
                tranches = self.fund_manager.get_investor_tranches(investor_id)
                total_units = sum(t.units for t in tranches)
                st.markdown(f"**📊 Total Units:** {total_units:.6f}")
                
                # Display metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("💰 Vốn Đầu Tư", format_currency(details['invested_value']))
                    st.metric("📊 Số Dư Hiện Tại", format_currency(details['balance']))
                    
                    profit_color = "normal" if details['profit'] >= 0 else "inverse"
                    st.metric("📈 Lãi/Lỗ", format_currency(details['profit']), delta_color=profit_color)
                
                with col2:
                    perc_color = "normal" if details['profit_perc'] >= 0 else "inverse"
                    st.metric("📊 Tỷ Lệ L/L", format_percentage(details['profit_perc']), delta_color=perc_color)
                    
                    st.metric("🎯 Hurdle Value (6%)", format_currency(details['hurdle_value']))
                    st.metric("🏔️ HWM Value", format_currency(details['hwm_value']))
                
                st.markdown(f"**💎 Lợi Nhuận Vượt Ngưỡng:** {format_currency(details['excess_profit'])}")
                st.markdown(f"**💸 Phí Performance (20%):** {format_currency(details['total_fee'])}")
        
        st.info("💡 Chỉ tính toán, không áp dụng. Dùng để xem trước khi rút giữa năm.")
    
    def _show_fee_calculation(self, ending_date, ending_nav):
        """Hiển thị kết quả tính phí"""
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        results = []
        
        for investor in self.fund_manager.investors:
            details = self.fund_manager.calculate_investor_fee(investor.id, ending_date_dt, ending_nav)
            
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            total_units = sum(t.units for t in tranches) if tranches else 0
            
            results.append({
                'Nhà Đầu Tư': investor.display_name,
                'Tổng Units': f"{total_units:.6f}",
                'Vốn Đầu Tư': details['invested_value'],
                'Số Dư': details['balance'],
                'Lãi/Lỗ': details['profit'],
                'Tỷ Lệ L/L': details['profit_perc'],
                'Hurdle Value': details['hurdle_value'],
                'HWM Value': details['hwm_value'],
                'Lợi Nhuận Vượt': details['excess_profit'],
                'Phí': details['total_fee']
            })
        
        if results:
            df_results = pd.DataFrame(results)
            
            # Format DataFrame
            currency_cols = ['Vốn Đầu Tư', 'Số Dư', 'Lãi/Lỗ', 'Hurdle Value', 'HWM Value', 'Lợi Nhuận Vượt', 'Phí']
            for col in currency_cols:
                df_results[col] = df_results[col].apply(format_currency)
            
            df_results['Tỷ Lệ L/L'] = df_results['Tỷ Lệ L/L'].apply(format_percentage)
            
            st.dataframe(df_results, use_container_width=True)
            
            # Tổng kết
            total_fee = sum(self.fund_manager.calculate_investor_fee(inv.id, ending_date_dt, ending_nav)['total_fee'] 
                           for inv in self.fund_manager.investors)
            
            if total_fee > 0:
                st.success(f"💰 **Tổng phí performance:** {format_currency(total_fee)}")
            else:
                st.info("ℹ️ Không có phí performance được tính.")
    
    def _show_tranches_detail(self, ending_nav):
        """Hiển thị chi tiết tranches"""
        if not self.fund_manager.tranches:
            st.info("📝 Chưa có tranches nào.")
            return
        
        data = []
        current_price = self.fund_manager.calculate_price_per_unit(ending_nav) if ending_nav > 0 else 0
        
        for tranche in self.fund_manager.tranches:
            investor = self.fund_manager.get_investor_by_id(tranche.investor_id)
            investor_name = investor.display_name if investor else f"ID {tranche.investor_id}"
            
            current_value = tranche.units * current_price if current_price > 0 else 0
            profit_loss = current_value - tranche.invested_value
            
            data.append({
                'Investor': investor_name,
                'Tranche ID': tranche.tranche_id[:8] + "...",
                'Ngày Vào': tranche.entry_date.strftime("%d/%m/%Y"),
                'Entry NAV': format_currency(tranche.entry_nav),
                'Units': f"{tranche.units:.6f}",
                'HWM': format_currency(tranche.hwm),
                'Vốn': format_currency(tranche.invested_value),
                'Giá Trị Hiện Tại': format_currency(current_value),
                'L/L': format_currency(profit_loss)
            })
        
        if data:
            df_tranches = pd.DataFrame(data)
            st.dataframe(df_tranches, use_container_width=True)