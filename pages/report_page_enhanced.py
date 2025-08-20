import streamlit as st
import pandas as pd
import altair as alt
from utils import format_currency, format_percentage, parse_currency, highlight_profit_loss

class EnhancedReportPage:
    """Enhanced Report Page với lifetime performance và fee tracking"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_reports(self):
        """Render trang báo cáo enhanced"""
        st.title("📊 Enhanced Báo Cáo & Thống Kê")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
            st.info("📝 Chưa có nhà đầu tư nào.")
            return
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Thống Kê Giá Trị", 
            "📈 Lifetime Performance",
            "💰 Lịch Sử Phí",
            "📋 Lịch Sử Giao Dịch", 
            "🏛️ Fund Manager Dashboard"
        ])
        
        with tab1:
            self._render_value_statistics()
        
        with tab2:
            self.render_lifetime_performance()
        
        with tab3:
            self.render_fee_history()
        
        with tab4:
            self._render_transaction_history()
        
        with tab5:
            self._render_fund_manager_dashboard()
    
    def render_lifetime_performance(self):
        """Render lifetime performance"""
        st.subheader("📈 Lifetime Performance Analysis")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input("📊 Total NAV Hiện Tại", 
                                 value=format_currency(latest_nav) if latest_nav else "0đ",
                                 key="lifetime_performance_nav_input")
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập Total NAV hợp lệ.")
            return
        
        # Performance table
        performance_data = []
        regular_investors = self.fund_manager.get_regular_investors()
        
        for investor in regular_investors:
            perf = self.fund_manager.get_investor_lifetime_performance(investor.id, current_nav)
            
            if perf['original_invested'] > 0:  # Only show investors with investments
                performance_data.append({
                    'Nhà Đầu Tư': investor.display_name,
                    'Vốn Gốc': perf['original_invested'],
                    'Giá Trị Hiện Tại': perf['current_value'],
                    'Tổng Phí Đã Trả': perf['total_fees_paid'],
                    'Lợi Nhuận Gross': perf['gross_profit'],
                    'Lợi Nhuận Net': perf['net_profit'],
                    'Return Gross': perf['gross_return'],
                    'Return Net': perf['net_return'],
                    'Units Hiện Tại': perf['current_units']
                })
        
        if performance_data:
            df_perf = pd.DataFrame(performance_data)
            
            # Display metrics overview
            col1, col2, col3, col4 = st.columns(4)
            
            total_invested = sum(item['Vốn Gốc'] for item in performance_data)
            total_current = sum(item['Giá Trị Hiện Tại'] for item in performance_data)
            total_fees = sum(item['Tổng Phí Đã Trả'] for item in performance_data)
            overall_gross_return = (total_current + total_fees - total_invested) / total_invested if total_invested > 0 else 0
            overall_net_return = (total_current - total_invested) / total_invested if total_invested > 0 else 0
            
            col1.metric("💰 Tổng Vốn Gốc", format_currency(total_invested))
            col2.metric("📊 Tổng Giá Trị Hiện Tại", format_currency(total_current))
            col3.metric("💸 Tổng Phí Đã Thu", format_currency(total_fees))
            col4.metric("📈 Overall Net Return", format_percentage(overall_net_return))
            
            # Format display table
            display_df = df_perf.copy()
            currency_cols = ['Vốn Gốc', 'Giá Trị Hiện Tại', 'Tổng Phí Đã Trả', 
                           'Lợi Nhuận Gross', 'Lợi Nhuận Net']
            for col in currency_cols:
                display_df[col] = display_df[col].apply(format_currency)
            
            display_df['Return Gross'] = display_df['Return Gross'].apply(format_percentage)
            display_df['Return Net'] = display_df['Return Net'].apply(format_percentage)
            display_df['Units Hiện Tại'] = display_df['Units Hiện Tại'].apply(lambda x: f"{x:.6f}")
            
            st.dataframe(display_df, use_container_width=True)
            
            # Charts
            if len(performance_data) > 1:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.subheader("🥧 Phân Bố Giá Trị")
                    pie_data = df_perf[['Nhà Đầu Tư', 'Giá Trị Hiện Tại']].copy()
                    
                    pie_chart = alt.Chart(pie_data).mark_arc().encode(
                        theta='Giá Trị Hiện Tại:Q',
                        color='Nhà Đầu Tư:N',
                        tooltip=['Nhà Đầu Tư', 'Giá Trị Hiện Tại']
                    )
                    st.altair_chart(pie_chart, use_container_width=True)
                
                with col_chart2:
                    st.subheader("📊 Gross vs Net Return")
                    return_data = df_perf[['Nhà Đầu Tư', 'Return Gross', 'Return Net']].copy()
                    return_data_melted = return_data.melt(
                        id_vars=['Nhà Đầu Tư'], 
                        value_vars=['Return Gross', 'Return Net'],
                        var_name='Return Type', 
                        value_name='Return'
                    )
                    
                    bar_chart = alt.Chart(return_data_melted).mark_bar().encode(
                        x='Nhà Đầu Tư:N',
                        y='Return:Q',
                        color='Return Type:N',
                        tooltip=['Nhà Đầu Tư', 'Return Type', 'Return']
                    )
                    st.altair_chart(bar_chart, use_container_width=True)
                
                # Fee impact analysis
                st.subheader("💰 Phân Tích Tác Động Phí")
                fee_impact_data = df_perf[['Nhà Đầu Tư', 'Tổng Phí Đã Trả']].copy()
                
                fee_chart = alt.Chart(fee_impact_data).mark_bar().encode(
                    x='Nhà Đầu Tư:N',
                    y='Tổng Phí Đã Trả:Q',
                    color=alt.value('orange'),
                    tooltip=['Nhà Đầu Tư', 'Tổng Phí Đã Trả']
                )
                st.altair_chart(fee_chart, use_container_width=True)
        
        else:
            st.info("📝 Chưa có dữ liệu performance.")
    
    def render_fee_history(self):
        """Render fee history"""
        st.subheader("💰 Lịch Sử Phí Chi Tiết")
        
        fee_records = self.fund_manager.get_fee_history()
        
        if not fee_records:
            st.info("📝 Chưa có lịch sử phí nào.")
            return
        
        # Filter options
        col1, col2 = st.columns(2)
        
        # Period filter
        available_periods = list(set(record.period for record in fee_records))
        selected_periods = col1.multiselect("📅 Lọc theo kỳ", available_periods, 
                                           default=available_periods,
                                           key="fee_history_period_filter")
        
        # Investor filter
        investor_options = self.fund_manager.get_investor_options()
        selected_investors = col2.multiselect("👤 Lọc theo nhà đầu tư", list(investor_options.keys()),
                                             key="fee_history_investor_filter")
        
        # Filter data
        filtered_records = fee_records
        if selected_periods:
            filtered_records = [r for r in filtered_records if r.period in selected_periods]
        if selected_investors:
            selected_ids = [investor_options[name] for name in selected_investors]
            filtered_records = [r for r in filtered_records if r.investor_id in selected_ids]
        
        if filtered_records:
            # Fee history table
            fee_data = []
            for record in filtered_records:
                investor = self.fund_manager.get_investor_by_id(record.investor_id)
                investor_name = investor.display_name if investor else f"ID {record.investor_id}"
                
                fee_data.append({
                    'Kỳ': record.period,
                    'Nhà Đầu Tư': investor_name,
                    'Ngày Tính': record.calculation_date.strftime("%d/%m/%Y"),
                    'Phí (VND)': record.fee_amount,
                    'Phí (Units)': f"{record.fee_units:.6f}",
                    'NAV/Unit': record.nav_per_unit,
                    'Units Trước': f"{record.units_before:.6f}",
                    'Units Sau': f"{record.units_after:.6f}",
                    'Mô tả': record.description
                })
            
            df_fees = pd.DataFrame(fee_data)
            
            # Format display
            display_df = df_fees.copy()
            display_df['Phí (VND)'] = display_df['Phí (VND)'].apply(format_currency)
            display_df['NAV/Unit'] = display_df['NAV/Unit'].apply(format_currency)
            
            st.dataframe(display_df, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            total_fee_amount = sum(record.fee_amount for record in filtered_records)
            total_fee_units = sum(record.fee_units for record in filtered_records)
            avg_nav_price = sum(record.nav_per_unit for record in filtered_records) / len(filtered_records)
            
            col1.metric("💰 Tổng Phí (VND)", format_currency(total_fee_amount))
            col2.metric("📊 Tổng Units Chuyển", f"{total_fee_units:.6f}")
            col3.metric("📈 NAV Trung Bình", format_currency(avg_nav_price))
            
            # Fee summary by period
            st.subheader("📊 Tổng Kết Phí Theo Kỳ")
            
            fee_by_period = {}
            for record in filtered_records:
                period = record.period
                if period not in fee_by_period:
                    fee_by_period[period] = {'amount': 0, 'units': 0, 'count': 0}
                fee_by_period[period]['amount'] += record.fee_amount
                fee_by_period[period]['units'] += record.fee_units
                fee_by_period[period]['count'] += 1
            
            summary_data = []
            for period, data in fee_by_period.items():
                summary_data.append({
                    'Kỳ': period,
                    'Tổng Phí': format_currency(data['amount']),
                    'Tổng Units': f"{data['units']:.6f}",
                    'Số Lần Tính': data['count']
                })
            
            st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
            
            # Chart: Fee by period
            if len(fee_by_period) > 1:
                chart_data = pd.DataFrame([
                    {'Kỳ': period, 'Tổng Phí': data['amount']} 
                    for period, data in fee_by_period.items()
                ])
                
                chart = alt.Chart(chart_data).mark_bar().encode(
                    x='Kỳ:N',
                    y='Tổng Phí:Q',
                    color=alt.value('steelblue'),
                    tooltip=['Kỳ', 'Tổng Phí']
                ).properties(title="Phí Performance Theo Kỳ")
                
                st.altair_chart(chart, use_container_width=True)
        
        else:
            st.info("📝 Không có dữ liệu phí với bộ lọc hiện tại.")
    
    def _render_value_statistics(self):
        """Thống kê giá trị"""
        st.subheader("📊 Thống Kê Giá Trị")
        
        # Filter investors
        options = self.fund_manager.get_investor_options()
        selected_investors = st.multiselect(
            "👥 Lọc theo Nhà Đầu Tư",
            list(options.keys()),
            default=[],
            key="value_statistics_investor_filter"
        )
        
        selected_ids = [options[name] for name in selected_investors] if selected_investors else [inv.id for inv in self.fund_manager.get_regular_investors()]
        
        # Current NAV input
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input("📊 Total NAV Hiện Tại", 
                                 value=format_currency(latest_nav) if latest_nav else "0đ",
                                 key="value_statistics_nav_input")
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập Total NAV hợp lệ.")
            return
        
        # Calculate balances
        balances = []
        
        for inv_id in selected_ids:
            investor = self.fund_manager.get_investor_by_id(inv_id)
            if not investor:
                continue
            
            tranches = self.fund_manager.get_investor_tranches(inv_id)
            if not tranches:
                continue
            
            balance, profit, profit_perc = self.fund_manager.get_investor_balance(inv_id, current_nav)
            total_units = sum(t.units for t in tranches)
            invested = sum(t.invested_value for t in tranches)
            
            balances.append({
                'Nhà Đầu Tư': investor.display_name,
                'Tổng Units': f"{total_units:.6f}",
                'Số Dư': balance,
                'Vốn Đầu Tư': invested,
                'Lãi/Lỗ': profit,
                'Tỷ Lệ L/L': profit_perc
            })
        
        if balances:
            # Display table
            df_balances = pd.DataFrame(balances)
            
            # Format table
            display_df = df_balances.copy()
            display_df['Số Dư'] = display_df['Số Dư'].apply(format_currency)
            display_df['Vốn Đầu Tư'] = display_df['Vốn Đầu Tư'].apply(format_currency)
            display_df['Lãi/Lỗ'] = display_df['Lãi/Lỗ'].apply(format_currency)
            display_df['Tỷ Lệ L/L'] = display_df['Tỷ Lệ L/L'].apply(format_percentage)
            
            st.dataframe(display_df, use_container_width=True)
        
        else:
            st.info("📝 Không có dữ liệu để hiển thị.")
    
    def _render_transaction_history(self):
        """Lịch sử giao dịch"""
        st.subheader("📋 Lịch Sử Giao Dịch")
        
        if not self.fund_manager.transactions:
            st.info("📝 Chưa có giao dịch nào.")
            return
        
        # Prepare data
        data = []
        for trans in sorted(self.fund_manager.transactions, key=lambda x: x.date, reverse=True):
            investor = self.fund_manager.get_investor_by_id(trans.investor_id)
            investor_name = investor.display_name if investor else "System"
            
            data.append({
                'ID': trans.id,
                'Nhà Đầu Tư': investor_name,
                'Ngày': trans.date.strftime("%d/%m/%Y %H:%M"),
                'Loại': trans.type,
                'Số Tiền': format_currency(trans.amount),
                'NAV': format_currency(trans.nav),
                'Units Change': f"{trans.units_change:.6f}"
            })
        
        df_trans = pd.DataFrame(data)
        st.dataframe(df_trans, use_container_width=True)
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        total_deposits = sum(t.amount for t in self.fund_manager.transactions if t.type == 'Nạp')
        total_withdrawals = abs(sum(t.amount for t in self.fund_manager.transactions if t.type == 'Rút'))
        total_fees = abs(sum(t.amount for t in self.fund_manager.transactions if t.type == 'Phí'))
        total_fee_received = sum(t.amount for t in self.fund_manager.transactions if t.type == 'Phí Nhận')
        
        col1.metric("💰 Tổng Nạp", format_currency(total_deposits))
        col2.metric("💸 Tổng Rút", format_currency(total_withdrawals))
        col3.metric("🧮 Tổng Phí Trừ", format_currency(total_fees))
        col4.metric("🏛️ Phí Nhận (FM)", format_currency(total_fee_received))
    
    def _render_fund_manager_dashboard(self):
        """Dashboard cho fund manager"""
        st.subheader("🏛️ Fund Manager Dashboard")
        
        fund_manager = self.fund_manager.get_fund_manager()
        if not fund_manager:
            st.error("❌ Không tìm thấy Fund Manager")
            return
        
        fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
        
        if not fm_tranches:
            st.info("📝 Fund Manager chưa có units")
            return
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        if not latest_nav:
            st.warning("⚠️ Chưa có NAV để tính giá trị")
            return
        
        # Fund Manager metrics
        total_units = sum(t.units for t in fm_tranches)
        current_price = self.fund_manager.calculate_price_per_unit(latest_nav)
        total_value = total_units * current_price
        
        # Calculate average entry price
        total_invested = sum(t.invested_value for t in fm_tranches)
        avg_entry_price = total_invested / total_units if total_units > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Total Units", f"{total_units:.6f}")
        col2.metric("💰 Total Value", format_currency(total_value))
        col3.metric("📈 Current Price", format_currency(current_price))
        col4.metric("🎯 Avg Entry Price", format_currency(avg_entry_price))
        
        # Fund Manager tranches detail
        st.subheader("📋 Fund Manager Tranches")
        
        fm_data = []
        for tranche in fm_tranches:
            current_value = tranche.units * current_price
            profit_loss = current_value - tranche.invested_value
            
            fm_data.append({
                'Ngày Nhận': tranche.entry_date.strftime("%d/%m/%Y"),
                'Entry Price': format_currency(tranche.entry_nav),
                'Units': f"{tranche.units:.6f}",
                'Vốn Đầu Tư': format_currency(tranche.invested_value),
                'Giá Trị Hiện Tại': format_currency(current_value),
                'L/L': format_currency(profit_loss),
                'L/L %': format_percentage(profit_loss / tranche.invested_value if tranche.invested_value > 0 else 0)
            })
        
        df_fm = pd.DataFrame(fm_data)
        st.dataframe(df_fm, use_container_width=True)
        
        # Fund Manager fee income over time
        fee_transactions = [t for t in self.fund_manager.transactions if t.investor_id == fund_manager.id and t.type == 'Phí Nhận']
        
        if fee_transactions:
            st.subheader("📈 Fee Income Timeline")
            
            fee_timeline = []
            cumulative_fee = 0
            
            for trans in sorted(fee_transactions, key=lambda x: x.date):
                cumulative_fee += trans.amount
                fee_timeline.append({
                    'Date': trans.date,
                    'Fee Amount': trans.amount,
                    'Cumulative Fee': cumulative_fee
                })
            
            df_timeline = pd.DataFrame(fee_timeline)
            
            chart = alt.Chart(df_timeline).mark_line(point=True).encode(
                x='Date:T',
                y='Cumulative Fee:Q',
                tooltip=['Date', 'Fee Amount', 'Cumulative Fee']
            ).properties(title="Cumulative Fee Income")
            
            st.altair_chart(chart, use_container_width=True)
            
            total_fee_income = sum(t.amount for t in fee_transactions)
            st.success(f"💰 **Tổng Fee Income:** {format_currency(total_fee_income)}")
        
        else:
            st.info("📝 Fund Manager chưa nhận fee nào")