import streamlit as st
import pandas as pd
import altair as alt
import io
from datetime import datetime, date
from utils import format_currency, format_percentage, parse_currency, highlight_profit_loss

class EnhancedReportPage:
    """Enhanced Report Page với individual export và professional reports"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_reports(self):
        """Render enhanced reports với professional features"""
        st.title("📊 Báo Cáo & Thống Kê")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
            st.info("📄 Chưa có nhà đầu tư nào.")
            return
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Dashboard Tổng Quan",
            "👤 Individual Reports", 
            "📈 Lifetime Performance",
            "💰 Lịch Sử Phí",
            "📋 Transaction History", 
            "🛒 Fund Manager Dashboard"
        ])
        
        with tab1:
            self._render_executive_dashboard()
        
        with tab2:
            self._render_individual_reports()
        
        with tab3:
            self.render_lifetime_performance()
        
        with tab4:
            self.render_fee_history()
        
        with tab5:
            self._render_transaction_history()
        
        with tab6:
            self._render_fund_manager_dashboard()
    
    def _render_executive_dashboard(self):
        """Render executive dashboard với key metrics"""
        st.subheader("🎯 Executive Dashboard")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input(
            "📊 Total NAV Hiện Tại", 
            value=format_currency(latest_nav) if latest_nav else "0đ",
            key="dashboard_nav_input"
        )
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập Total NAV hợp lệ.")
            return
        
        # Key Performance Metrics
        self._render_kpi_section(current_nav)
        
        # Portfolio Overview
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_portfolio_composition(current_nav)
        
        with col2:
            self._render_performance_summary(current_nav)
        
        # Fund Growth Timeline
        self._render_fund_growth_timeline()
        
        # Export full dashboard
        if st.button("📤 Export Executive Summary", use_container_width=True):
            self._export_executive_summary(current_nav)
    
    def _render_individual_reports(self):
        """Render individual investor reports"""
        st.subheader("👤 Individual Investor Reports")
        
        # Investor selection
        options = self.fund_manager.get_investor_options()
        selected_display = st.selectbox(
            "👤 Chọn Nhà Đầu Tư", 
            list(options.keys()),
            key="individual_report_investor"
        )
        
        if not selected_display:
            return
        
        investor_id = options[selected_display]
        
        # NAV input for calculations
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input(
            "📊 Total NAV cho tính toán", 
            value=format_currency(latest_nav) if latest_nav else "0đ",
            key="individual_report_nav"
        )
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập Total NAV hợp lệ.")
            return
        
        # Display individual report
        self._render_detailed_individual_report(investor_id, current_nav, selected_display)
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Export PDF Report", use_container_width=True, key="export_pdf"):
                st.info("🚧 PDF export đang phát triển")
        
        with col2:
            if st.button("📊 Export Excel Report", use_container_width=True, key="export_excel_individual"):
                self._export_individual_excel_report(investor_id, current_nav, selected_display)
        
        with col3:
            if st.button("📧 Email to Client", use_container_width=True, key="email_client"):
                st.info("🚧 Email feature đang phát triển")
    
    def _render_kpi_section(self, current_nav):
        """Render key performance indicators"""
        st.markdown("### 🎯 Key Performance Indicators")
        
        # Calculate metrics
        total_units = sum(t.units for t in self.fund_manager.tranches)
        current_price = self.fund_manager.calculate_price_per_unit(current_nav)
        regular_investors = self.fund_manager.get_regular_investors()
        
        # Total invested vs current value
        total_original_invested = 0
        total_current_value = 0
        total_fees_paid = 0
        
        for investor in regular_investors:
            lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, current_nav)
            total_original_invested += lifetime_perf['original_invested']
            total_current_value += lifetime_perf['current_value']
            total_fees_paid += lifetime_perf['total_fees_paid']
        
        # Fund Manager value
        fund_manager = self.fund_manager.get_fund_manager()
        fm_value = 0
        if fund_manager:
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            fm_units = sum(t.units for t in fm_tranches)
            fm_value = fm_units * current_price
        
        # Display KPIs
        col1, col2, col3, col4, col5 = st.columns(5)
        
        col1.metric(
            "💰 Total NAV",
            format_currency(current_nav)
        )
        
        col2.metric(
            "📈 Price/Unit",
            format_currency(current_price)
        )
        
        gross_return = (total_current_value + total_fees_paid - total_original_invested) / total_original_invested if total_original_invested > 0 else 0
        col3.metric(
            "📊 Gross Return",
            format_percentage(gross_return),
            delta_color="normal" if gross_return >= 0 else "inverse"
        )
        
        col4.metric(
            "💸 Total Fees Collected",
            format_currency(total_fees_paid)
        )
        
        col5.metric(
            "🛒 Fund Manager Value",
            format_currency(fm_value)
        )
        
        # Additional insights
        st.markdown("---")
        insight_col1, insight_col2, insight_col3 = st.columns(3)
        
        with insight_col1:
            net_return = (total_current_value - total_original_invested) / total_original_invested if total_original_invested > 0 else 0
            st.metric("📉 Net Return (After Fees)", format_percentage(net_return))
        
        with insight_col2:
            fee_rate = total_fees_paid / total_original_invested if total_original_invested > 0 else 0
            st.metric("💱 Cumulative Fee Rate", format_percentage(fee_rate))
        
        with insight_col3:
            aum_growth = (current_nav - total_original_invested) / total_original_invested if total_original_invested > 0 else 0
            st.metric("🚀 AUM Growth", format_percentage(aum_growth))
    
    def _render_portfolio_composition(self, current_nav):
        """Render portfolio composition chart"""
        st.markdown("### 🥧 Portfolio Composition")
        
        composition_data = []
        for investor in self.fund_manager.get_regular_investors():
            balance, _, _ = self.fund_manager.get_investor_balance(investor.id, current_nav)
            if balance > 0:
                composition_data.append({
                    'Investor': investor.display_name,
                    'Value': balance,
                    'Percentage': balance / current_nav * 100
                })
        
        # Add Fund Manager
        fund_manager = self.fund_manager.get_fund_manager()
        if fund_manager:
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            fm_units = sum(t.units for t in fm_tranches)
            fm_value = fm_units * self.fund_manager.calculate_price_per_unit(current_nav)
            if fm_value > 0:
                composition_data.append({
                    'Investor': '🛒 Fund Manager',
                    'Value': fm_value,
                    'Percentage': fm_value / current_nav * 100
                })
        
        if composition_data:
            df_composition = pd.DataFrame(composition_data)
            
            # =================== THÊM LỚP BẢO VỆ ===================
            if not df_composition.empty:
                # Pie chart
                pie_chart = alt.Chart(df_composition).mark_arc(innerRadius=50).encode(
                    theta='Value:Q',
                    color=alt.Color('Investor:N', scale=alt.Scale(scheme='category20')),
                    tooltip=['Investor', 'Value', 'Percentage']
                ).properties(
                    title="Portfolio Distribution",
                    height=300
                )
                st.altair_chart(pie_chart, use_container_width=True)
                
                # Table
                display_df = df_composition.copy()
                display_df['Value'] = display_df['Value'].apply(format_currency)
                display_df['Percentage'] = display_df['Percentage'].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Không có dữ liệu để hiển thị biểu đồ phân bổ danh mục.")
    
    def _render_performance_summary(self, current_nav):
        """Render performance summary"""
        st.markdown("### 📈 Performance Summary")
        
        performance_data = []
        for investor in self.fund_manager.get_regular_investors():
            lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, current_nav)
            if lifetime_perf['original_invested'] > 0:
                performance_data.append({
                    'Investor': investor.display_name,
                    'Gross Return': lifetime_perf['gross_return'],
                    'Net Return': lifetime_perf['net_return'],
                    'Total Fees': lifetime_perf['total_fees_paid']
                })
        
        if performance_data:
            df_performance = pd.DataFrame(performance_data)
            
            # Return comparison chart
            chart_data = df_performance.melt(
                id_vars=['Investor'], 
                value_vars=['Gross Return', 'Net Return'],
                var_name='Return Type',
                value_name='Return'
            )
            
            bar_chart = alt.Chart(chart_data).mark_bar().encode(
                x='Investor:N',
                y='Return:Q',
                color='Return Type:N',
                tooltip=['Investor', 'Return Type', 'Return']
            ).properties(
                title="Gross vs Net Returns",
                height=300
            )
            
            st.altair_chart(bar_chart, use_container_width=True)
            
            # Summary table
            display_df = df_performance.copy()
            display_df['Gross Return'] = display_df['Gross Return'].apply(format_percentage)
            display_df['Net Return'] = display_df['Net Return'].apply(format_percentage)
            display_df['Total Fees'] = display_df['Total Fees'].apply(format_currency)
            st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    def _render_fund_growth_timeline(self):
        """Render fund growth over time"""
        st.markdown("### 📅 Fund Growth Timeline")
        
        if not self.fund_manager.transactions:
            st.info("📄 Chưa có dữ liệu giao dịch.")
            return
        
        # Build timeline data
        timeline_data = []
        running_nav = 0
        
        nav_transactions = [t for t in self.fund_manager.transactions if t.nav > 0]
        nav_transactions.sort(key=lambda x: x.date)
        
        for trans in nav_transactions:
            if trans.type == 'NAV Update':
                running_nav = trans.nav
            elif trans.type in ['Nạp', 'Rút']:
                running_nav = trans.nav
            
            timeline_data.append({
                'Date': trans.date,
                'NAV': running_nav,
                'Type': trans.type
            })
        
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)
            
            # =================== THÊM LỚP BẢO VỆ ===================
            if not df_timeline.empty:
                # Line chart
                line_chart = alt.Chart(df_timeline).mark_line(point=True).encode(
                    x='Date:T',
                    y='NAV:Q',
                    color=alt.value('steelblue'),
                    tooltip=['Date', 'NAV', 'Type']
                ).properties(
                    title="Fund NAV Growth Over Time",
                    height=400
                )
                st.altair_chart(line_chart, use_container_width=True)
                
                # Growth statistics
                if len(timeline_data) > 1:
                    start_nav = timeline_data[0]['NAV']
                    end_nav = timeline_data[-1]['NAV']
                    growth = (end_nav - start_nav) / start_nav if start_nav > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Starting NAV", format_currency(start_nav))
                    col2.metric("Current NAV", format_currency(end_nav))
                    col3.metric("Total Growth", format_percentage(growth))
            else:
                st.info("ℹ️ Không có dữ liệu để hiển thị biểu đồ tăng trưởng.")
            # ==========================================================
    
    def _render_detailed_individual_report(self, investor_id, current_nav, investor_name):
        """Render detailed individual investor report"""
        st.markdown(f"### 👤 Detailed Report: {investor_name}")
        
        # Get all data for this investor
        report_data = self.fund_manager.get_investor_individual_report(investor_id, current_nav)
        
        if not report_data:
            st.error("❌ Không thể tạo báo cáo cho investor này")
            return
        
        # Summary section
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric(
            "💰 Original Investment",
            format_currency(report_data['lifetime_performance']['original_invested'])
        )
        
        col2.metric(
            "📊 Current Value", 
            format_currency(report_data['current_balance'])
        )
        
        profit_color = "normal" if report_data['current_profit'] >= 0 else "inverse"
        col3.metric(
            "📈 Current P&L",
            format_currency(report_data['current_profit']),
            delta_color=profit_color
        )
        
        col4.metric(
            "💸 Total Fees Paid",
            format_currency(report_data['lifetime_performance']['total_fees_paid'])
        )
        
        # Performance comparison
        st.markdown("#### 📊 Performance Analysis")
        
        perf_col1, perf_col2 = st.columns(2)
        
        with perf_col1:
            gross_return = report_data['lifetime_performance']['gross_return']
            st.metric(
                "🚀 Gross Return (Before Fees)",
                format_percentage(gross_return),
                delta_color="normal" if gross_return >= 0 else "inverse"
            )
        
        with perf_col2:
            net_return = report_data['lifetime_performance']['net_return']
            st.metric(
                "💼 Net Return (After Fees)",
                format_percentage(net_return),
                delta_color="normal" if net_return >= 0 else "inverse"
            )
        
        # Tranches detail
        if report_data['tranches']:
            st.markdown("#### 📋 Investment Tranches")
            
            tranche_data = []
            for tranche in report_data['tranches']:
                current_value = tranche.units * report_data['current_price']
                
                tranche_data.append({
                    'Entry Date': tranche.entry_date.strftime("%d/%m/%Y"),
                    'Entry Price': format_currency(tranche.entry_nav),
                    'Units': f"{tranche.units:.6f}",
                    'Original Investment': format_currency(tranche.original_invested_value),
                    'Current Value': format_currency(current_value),
                    'P&L': format_currency(current_value - tranche.invested_value),
                    'Fees Paid': format_currency(tranche.cumulative_fees_paid)
                })
            
            df_tranches = pd.DataFrame(tranche_data)
            st.dataframe(df_tranches, use_container_width=True, hide_index=True)
        
        # Transaction history for this investor
        if report_data['transactions']:
            st.markdown("#### 📝 Transaction History")
            
            trans_data = []
            for trans in sorted(report_data['transactions'], key=lambda x: x.date, reverse=True):
                trans_data.append({
                    'Date': trans.date.strftime("%d/%m/%Y"),
                    'Type': trans.type,
                    'Amount': format_currency(trans.amount),
                    'NAV at Time': format_currency(trans.nav),
                    'Units Change': f"{trans.units_change:.6f}"
                })
            
            df_transactions = pd.DataFrame(trans_data)
            st.dataframe(df_transactions, use_container_width=True, hide_index=True)
        
        # Fee history
        if report_data['fee_history']:
            st.markdown("#### 💰 Fee Payment History")
            
            fee_data = []
            for fee_record in report_data['fee_history']:
                fee_data.append({
                    'Period': fee_record.period,
                    'Date': fee_record.calculation_date.strftime("%d/%m/%Y"),
                    'Fee Amount': format_currency(fee_record.fee_amount),
                    'Fee Units': f"{fee_record.fee_units:.6f}",
                    'NAV/Unit': format_currency(fee_record.nav_per_unit)
                })
            
            df_fees = pd.DataFrame(fee_data)
            st.dataframe(df_fees, use_container_width=True, hide_index=True)
        
        # Investment insights
        st.markdown("#### 💡 Investment Insights")
        
        insights = []
        
        # Time in fund
        if report_data['tranches']:
            oldest_tranche = min(report_data['tranches'], key=lambda t: t.original_entry_date)
            days_invested = (datetime.now() - oldest_tranche.original_entry_date).days
            years_invested = days_invested / 365.25
            insights.append(f"📅 Đã đầu tư: {years_invested:.1f} năm ({days_invested} ngày)")
        
        # Fee impact
        original_invested = report_data['lifetime_performance']['original_invested']
        total_fees = report_data['lifetime_performance']['total_fees_paid']
        if original_invested > 0:
            fee_rate = total_fees / original_invested * 100
            insights.append(f"💸 Tổng phí: {fee_rate:.1f}% của vốn gốc")
        
        # Performance ranking (if multiple investors)
        regular_investors = self.fund_manager.get_regular_investors()
        if len(regular_investors) > 1:
            all_returns = []
            for inv in regular_investors:
                perf = self.fund_manager.get_investor_lifetime_performance(inv.id, current_nav)
                if perf['original_invested'] > 0:
                    all_returns.append(perf['net_return'])
            
            if all_returns:
                current_return = report_data['lifetime_performance']['net_return']
                rank = sum(1 for r in all_returns if r > current_return) + 1
                insights.append(f"🏆 Xếp hạng: #{rank}/{len(all_returns)} investors theo net return")
        
        for insight in insights:
            st.info(insight)
    
    def _export_individual_excel_report(self, investor_id, current_nav, investor_name):
        """Export individual investor report to Excel"""
        try:
            # Get report data
            report_data = self.fund_manager.get_investor_individual_report(investor_id, current_nav)
            
            if not report_data:
                st.error("❌ Không thể tạo báo cáo")
                return
            
            # Create Excel buffer
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = {
                    'Metric': [
                        'Report Date',
                        'Investor Name',
                        'Original Investment',
                        'Current Value',
                        'Current Profit/Loss',
                        'Current P&L %',
                        'Total Fees Paid',
                        'Gross Return %',
                        'Net Return %',
                        'Current Units',
                        'Current NAV/Unit'
                    ],
                    'Value': [
                        report_data['report_date'].strftime("%Y-%m-%d %H:%M:%S"),
                        investor_name,
                        format_currency(report_data['lifetime_performance']['original_invested']),
                        format_currency(report_data['current_balance']),
                        format_currency(report_data['current_profit']),
                        format_percentage(report_data['current_profit_perc']),
                        format_currency(report_data['lifetime_performance']['total_fees_paid']),
                        format_percentage(report_data['lifetime_performance']['gross_return']),
                        format_percentage(report_data['lifetime_performance']['net_return']),
                        f"{report_data['lifetime_performance']['current_units']:.6f}",
                        format_currency(report_data['current_price'])
                    ]
                }
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Tranches sheet
                if report_data['tranches']:
                    tranche_data = []
                    for tranche in report_data['tranches']:
                        current_value = tranche.units * report_data['current_price']
                        tranche_data.append({
                            'Entry Date': tranche.entry_date,
                            'Original Entry Date': tranche.original_entry_date,
                            'Entry NAV': tranche.entry_nav,
                            'Original Entry NAV': tranche.original_entry_nav,
                            'Units': tranche.units,
                            'HWM': tranche.hwm,
                            'Cumulative Fees Paid': tranche.cumulative_fees_paid,
                            'Current Value': current_value,
                            'Profit/Loss': current_value - tranche.invested_value
                        })
                    
                    df_tranches = pd.DataFrame(tranche_data)
                    df_tranches.to_excel(writer, sheet_name='Tranches', index=False)
                
                # Transactions sheet
                if report_data['transactions']:
                    trans_data = []
                    for trans in report_data['transactions']:
                        trans_data.append({
                            'Date': trans.date,
                            'Type': trans.type,
                            'Amount': trans.amount,
                            'NAV': trans.nav,
                            'Units Change': trans.units_change
                        })
                    
                    df_transactions = pd.DataFrame(trans_data)
                    df_transactions.to_excel(writer, sheet_name='Transactions', index=False)
                
                # Fee history sheet
                if report_data['fee_history']:
                    fee_data = []
                    for fee_record in report_data['fee_history']:
                        fee_data.append({
                            'Period': fee_record.period,
                            'Calculation Date': fee_record.calculation_date,
                            'Fee Amount': fee_record.fee_amount,
                            'Fee Units': fee_record.fee_units,
                            'Units Before': fee_record.units_before,
                            'Units After': fee_record.units_after,
                            'NAV per Unit': fee_record.nav_per_unit,
                            'Description': fee_record.description
                        })
                    
                    df_fees = pd.DataFrame(fee_data)
                    df_fees.to_excel(writer, sheet_name='Fee History', index=False)
            
            buffer.seek(0)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Individual_Report_{investor_name.replace(' ', '_')}_{timestamp}.xlsx"
            
            # Offer download
            st.download_button(
                label=f"📥 Download {filename}",
                data=buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.success(f"✅ Individual report ready for download: {filename}")
            
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
    def _export_executive_summary(self, current_nav):
        """Export executive summary to Excel"""
        try:
            # Create Excel buffer
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Executive Summary sheet
                total_original = sum(
                    self.fund_manager.get_investor_lifetime_performance(inv.id, current_nav)['original_invested']
                    for inv in self.fund_manager.get_regular_investors()
                )
                
                total_current = sum(
                    self.fund_manager.get_investor_lifetime_performance(inv.id, current_nav)['current_value']
                    for inv in self.fund_manager.get_regular_investors()
                )
                
                total_fees = sum(
                    self.fund_manager.get_investor_lifetime_performance(inv.id, current_nav)['total_fees_paid']
                    for inv in self.fund_manager.get_regular_investors()
                )
                
                exec_data = {
                    'Metric': [
                        'Report Date',
                        'Total NAV',
                        'Total Original Investment',
                        'Total Current Value',
                        'Total Fees Collected',
                        'Gross Fund Return',
                        'Net Fund Return',
                        'Total Investors',
                        'Total Tranches',
                        'Total Transactions'
                    ],
                    'Value': [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        format_currency(current_nav),
                        format_currency(total_original),
                        format_currency(total_current),
                        format_currency(total_fees),
                        format_percentage((total_current + total_fees - total_original) / total_original if total_original > 0 else 0),
                        format_percentage((total_current - total_original) / total_original if total_original > 0 else 0),
                        len(self.fund_manager.get_regular_investors()),
                        len(self.fund_manager.tranches),
                        len(self.fund_manager.transactions)
                    ]
                }
                
                df_exec = pd.DataFrame(exec_data)
                df_exec.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            buffer.seek(0)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Executive_Summary_{timestamp}.xlsx"
            
            # Offer download
            st.download_button(
                label=f"📥 Download {filename}",
                data=buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.success(f"✅ Executive summary ready for download: {filename}")
            
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
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
            st.info("📄 Chưa có dữ liệu performance.")
    
    def render_fee_history(self):
        """Render fee history"""
        st.subheader("💰 Lịch Sử Phí Chi Tiết")
        
        fee_records = self.fund_manager.get_fee_history()
        
        if not fee_records:
            st.info("📄 Chưa có lịch sử phí nào.")
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
            st.info("📄 Không có dữ liệu phí với bộ lọc hiện tại.")
    
    def _render_transaction_history(self):
        """Lịch sử giao dịch"""
        st.subheader("📋 Lịch Sử Giao Dịch")
        
        if not self.fund_manager.transactions:
            st.info("📄 Chưa có giao dịch nào.")
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
        col4.metric("🛒 Phí Nhận (FM)", format_currency(total_fee_received))
    
    def _render_fund_manager_dashboard(self):
        """Dashboard cho fund manager"""
        st.subheader("🛒 Fund Manager Dashboard")
        
        fund_manager = self.fund_manager.get_fund_manager()
        if not fund_manager:
            st.error("❌ Không tìm thấy Fund Manager")
            return
        
        fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
        
        if not fm_tranches:
            st.info("📄 Fund Manager chưa có units")
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
            st.info("📄 Fund Manager chưa nhận fee nào")