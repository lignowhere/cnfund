import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils import format_currency, parse_currency, format_percentage, highlight_profit_loss

class EnhancedFeePage:
    """Enhanced Fee Page với fund manager tracking"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_enhanced_fee_calculation(self):
        """Enhanced fee calculation với fund manager tracking"""
        st.title("🧮 Tính Toán Phí Cuối Năm (Enhanced)")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
            st.warning("⚠️ Chưa có nhà đầu tư nào.")
            return
        
        # Input parameters
        col1, col2, col3 = st.columns(3)
        
        year = col1.number_input("📅 Năm", value=2025, min_value=2020, max_value=2030)
        ending_date = col2.date_input("📅 Ngày Kết Thúc", value=date(2025, 12, 31))
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = col3.text_input("📊 Total NAV Kết Thúc", 
                                   value=format_currency(latest_nav) if latest_nav else "0đ",
                                   key="enhanced_fee_nav_input")
        ending_nav = parse_currency(nav_input)
        
        # Show fund manager current status
        fund_manager = self.fund_manager.get_fund_manager()
        if fund_manager:
            with st.expander("🏛️ Fund Manager Status"):
                fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
                if fm_tranches:
                    fm_units = sum(t.units for t in fm_tranches)
                    if ending_nav > 0:
                        fm_value = fm_units * self.fund_manager.calculate_price_per_unit(ending_nav)
                        col_fm1, col_fm2 = st.columns(2)
                        col_fm1.metric("Units hiện tại", f"{fm_units:.6f}")
                        col_fm2.metric("Giá trị hiện tại", format_currency(fm_value))
                else:
                    st.info("Fund Manager chưa có units")
        
        tab1, tab2, tab3 = st.tabs(["🧮 Tính Phí Enhanced", "📋 Phí Chi Tiết", "📊 Chi Tiết Tranches"])
        
        with tab1:
            st.subheader("🚀 Enhanced Fee Calculation")
            
            if st.button("🧮 Tính Toán Phí Enhanced", use_container_width=True, type="primary"):
                if ending_nav <= 0:
                    st.error("❌ Total NAV kết thúc phải lớn hơn 0")
                else:
                    self._show_enhanced_fee_preview(year, ending_date, ending_nav)
            
            # Enhanced fee application
            st.markdown("---")
            st.subheader("⚡ Áp Dụng Phí Enhanced")
            
            st.info("""
            🎯 **Enhanced Features:**
            - ✅ Units được chuyển cho Fund Manager (không biến mất)
            - ✅ Giữ nguyên original entry data cho lifetime tracking
            - ✅ Lưu chi tiết fee history
            - ✅ Track cumulative fees paid
            """)
            
            confirm_enhanced = st.checkbox("✅ Tôi chắc chắn muốn áp dụng phí Enhanced")
            
            if confirm_enhanced and st.button("🚀 Áp Dụng Phí Enhanced", type="primary"):
                if ending_nav <= 0:
                    st.error("❌ Total NAV kết thúc phải lớn hơn 0")
                else:
                    success, message = self.fund_manager.apply_year_end_fees_enhanced(year, ending_date, ending_nav)
                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.data_changed = True
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        with tab2:
            if st.button("📋 Tính Phí Chi Tiết", use_container_width=True):
                if ending_nav <= 0:
                    st.error("❌ Total NAV kết thúc phải lớn hơn 0")
                else:
                    self._show_detailed_fee_calculation(ending_date, ending_nav)
        
        with tab3:
            self._show_tranches_detail(ending_nav)
        
        # Comparison with old system
        with st.expander("⚖️ So Sánh: Enhanced vs Old System"):
            self._show_system_comparison()
    
    def render_individual_fee(self):
        """Tính phí riêng cho nhà đầu tư"""
        st.title("🔍 Tính Phí Riêng Cho Nhà Đầu Tư")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
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
        nav_input = col2.text_input("📊 Total NAV", 
                                   value=format_currency(latest_nav) if latest_nav else "0đ",
                                   key="individual_fee_nav_input")
        calc_nav = parse_currency(nav_input)
        
        if st.button("🧮 Tính Toán", use_container_width=True):
            if calc_nav <= 0:
                st.error("❌ Total NAV phải lớn hơn 0")
            else:
                calc_date_dt = datetime.combine(calc_date, datetime.min.time())
                details = self.fund_manager.calculate_investor_fee(investor_id, calc_date_dt, calc_nav)
                
                # Show current vs lifetime performance
                lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor_id, calc_nav)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Current Performance")
                    st.metric("💰 Vốn Đầu Tư Hiện Tại", format_currency(details['invested_value']))
                    st.metric("📊 Số Dư Hiện Tại", format_currency(details['balance']))
                    profit_color = "normal" if details['profit'] >= 0 else "inverse"
                    st.metric("📈 Lãi/Lỗ Hiện Tại", format_currency(details['profit']), delta_color=profit_color)
                    perc_color = "normal" if details['profit_perc'] >= 0 else "inverse"
                    st.metric("📊 Tỷ Lệ L/L Hiện Tại", format_percentage(details['profit_perc']), delta_color=perc_color)
                
                with col2:
                    st.subheader("🎯 Lifetime Performance")
                    st.metric("💰 Vốn Gốc (Original)", format_currency(lifetime_perf['original_invested']))
                    st.metric("💸 Tổng Phí Đã Trả", format_currency(lifetime_perf['total_fees_paid']))
                    gross_color = "normal" if lifetime_perf['gross_return'] >= 0 else "inverse"
                    st.metric("📈 Gross Return", format_percentage(lifetime_perf['gross_return']), delta_color=gross_color)
                    net_color = "normal" if lifetime_perf['net_return'] >= 0 else "inverse"
                    st.metric("📊 Net Return", format_percentage(lifetime_perf['net_return']), delta_color=net_color)
                
                # Fee calculation details
                st.markdown("---")
                st.subheader("💰 Chi Tiết Tính Phí")
                
                fee_col1, fee_col2, fee_col3 = st.columns(3)
                fee_col1.metric("🎯 Hurdle Value (6%)", format_currency(details['hurdle_value']))
                fee_col2.metric("🏔️ HWM Value", format_currency(details['hwm_value']))
                fee_col3.metric("💎 Lợi Nhuận Vượt Ngưỡng", format_currency(details['excess_profit']))
                
                if details['total_fee'] > 0:
                    st.success(f"💸 **Phí Performance (20%):** {format_currency(details['total_fee'])}")
                else:
                    st.info("ℹ️ Không có phí performance")
        
        st.info("💡 Chỉ tính toán preview, không áp dụng. Dùng để xem trước khi rút giữa năm.")
    
    def _show_enhanced_fee_preview(self, year: int, ending_date: date, ending_nav: float):
        """Show preview của enhanced fee calculation"""
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        
        results = []
        total_fees = 0.0
        total_units_transfer = 0.0
        
        ending_price = self.fund_manager.calculate_price_per_unit(ending_nav)
        
        for investor in self.fund_manager.get_regular_investors():
            details = self.fund_manager.calculate_investor_fee(investor.id, ending_date_dt, ending_nav)
            lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, ending_nav)
            
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            total_units = sum(t.units for t in tranches) if tranches else 0
            units_fee = details['total_fee'] / ending_price if details['total_fee'] > 0 else 0
            
            results.append({
                'Nhà Đầu Tư': investor.display_name,
                'Units Hiện Tại': f"{total_units:.6f}",
                'Vốn Gốc': lifetime_perf['original_invested'],
                'Phí Đã Trả': lifetime_perf['total_fees_paid'],
                'Số Dư': details['balance'],
                'Lãi/Lỗ': details['profit'],
                'Phí Mới': details['total_fee'],
                'Units Chuyển': f"{units_fee:.6f}",
                'Units Còn Lại': f"{total_units - units_fee:.6f}"
            })
            
            total_fees += details['total_fee']
            total_units_transfer += units_fee
        
        if results:
            df_results = pd.DataFrame(results)
            
            # Format DataFrame
            currency_cols = ['Vốn Gốc', 'Phí Đã Trả', 'Số Dư', 'Lãi/Lỗ', 'Phí Mới']
            for col in currency_cols:
                df_results[col] = df_results[col].apply(format_currency)
            
            st.dataframe(df_results, use_container_width=True)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            col1.success(f"💰 **Tổng phí:** {format_currency(total_fees)}")
            col2.info(f"📊 **Units chuyển:** {total_units_transfer:.6f}")
            col3.warning(f"🏛️ **Về Fund Manager:** {format_currency(total_fees)}")
    
    def _show_detailed_fee_calculation(self, ending_date, ending_nav):
        """Hiển thị kết quả tính phí chi tiết"""
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        results = []
        
        for investor in self.fund_manager.get_regular_investors():
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
                           for inv in self.fund_manager.get_regular_investors())
            
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
                'Ngày Vào': tranche.entry_date.strftime("%d/%m/%Y"),
                'Entry NAV': format_currency(tranche.entry_nav),
                'Original NAV': format_currency(tranche.original_entry_nav),
                'Units': f"{tranche.units:.6f}",
                'HWM': format_currency(tranche.hwm),
                'Phí Đã Trả': format_currency(tranche.cumulative_fees_paid),
                'Vốn': format_currency(tranche.invested_value),
                'Giá Trị Hiện Tại': format_currency(current_value),
                'L/L': format_currency(profit_loss)
            })
        
        if data:
            df_tranches = pd.DataFrame(data)
            st.dataframe(df_tranches, use_container_width=True)
    
    def _show_system_comparison(self):
        """So sánh Enhanced vs Old system"""
        comparison_data = {
            'Khía Cạnh': [
                'Units Flow',
                'Transparency', 
                'History Preservation',
                'Fee Tracking',
                'Performance Reporting',
                'Data Reset'
            ],
            'Old System': [
                '❌ Units biến mất',
                '❌ Không rõ phí đi đâu',
                '❌ Mất lịch sử sau reset',
                '❌ Chỉ có transaction log',
                '❌ Chỉ current performance',
                '❌ Reset hoàn toàn'
            ],
            'Enhanced System': [
                '✅ Units chuyển Fund Manager',
                '✅ Minh bạch 100%',
                '✅ Giữ nguyên original data',
                '✅ Chi tiết fee records',
                '✅ Gross vs Net return',
                '✅ Giữ history, chỉ reset base'
            ]
        }
        
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)