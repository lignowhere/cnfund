import streamlit as st
import pandas as pd
import altair as alt
import io
from datetime import datetime, date
from helpers import (
    format_currency,
    format_percentage,
    parse_currency,
    highlight_profit_loss,
    display_transaction_type_vi,
)
from ui.chart_utils import safe_altair_chart
from utils.timezone_manager import TimezoneManager

# Performance optimizations
from performance.cache_service_simple import cache_report_data
from performance.skeleton_components import SkeletonLoader, skeleton_chart, skeleton_metric_card, inject_skeleton_css
from performance.performance_monitor import track_performance
from performance.virtual_scroll import render_transaction_table_virtual

# UX enhancements
from ui.ux_enhancements import UXEnhancements

# Color coding for profit/loss
from ui.color_coding import ColorCoding, profit_loss_html, percentage_html, currency_change_html

class EnhancedReportPage:
    """Enhanced Report Page với individual export và professional reports"""

    def __init__(self, fund_manager):
        self.fund_manager = fund_manager

    @cache_report_data
    @track_performance("generate_executive_dashboard")
    def get_dashboard_data(_self):
        """Load dashboard data with caching"""
        return {
            'investors': _self.fund_manager.get_regular_investors(),
            'latest_nav': _self.fund_manager.get_latest_total_nav(),
            'transactions': _self.fund_manager.transactions
        }
    
    def render_reports(self):
        """Render enhanced reports với professional features"""
        st.title("📊 Báo Cáo & Thống Kê")

        # Breadcrumb
        UXEnhancements.breadcrumb([
            ("🏠 Trang chủ", "/"),
            ("📊 Báo cáo", "")
        ])

        # Show loading skeleton
        if 'loading_reports' not in st.session_state:
            st.session_state.loading_reports = True

        if st.session_state.loading_reports:
            UXEnhancements.loading_skeleton(rows=6, columns=3)
            regular_investors = self.fund_manager.get_regular_investors()
            st.session_state.loading_reports = False
            st.rerun()
        else:
            regular_investors = self.fund_manager.get_regular_investors()

        # Empty state
        if not regular_investors:
            UXEnhancements.empty_state(
                icon="📊",
                title="Chưa có dữ liệu báo cáo",
                description="Thêm nhà đầu tư và giao dịch để xem báo cáo chi tiết",
                action_label="➕ Thêm nhà đầu tư",
                action_callback=lambda: st.session_state.update({'menu_selection': "👥 Thêm Nhà Đầu Tư"})
            )
            return
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Bảng Điều Khiển Tổng Quan",
            "👤 Báo Cáo Từng Nhà Đầu Tư", 
            "📈 Hiệu Suất Vòng Đời",
            "💰 Lịch Sử Phí",
            "📋 Lịch Sử Giao Dịch", 
            "🛒 Bảng Điều Khiển Fund Manager"
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
        st.subheader("🎯 Bảng Điều Khiển Điều Hành")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input(
            "📊 NAV Hiện Tại", 
            value=format_currency(latest_nav) if latest_nav else "0đ",
            key="dashboard_nav_input"
        )
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập NAV tổng hợp lệ.")
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
        if st.button("📤 Xuất Tóm Tắt Điều Hành", width='stretch'):
            self._export_executive_summary(current_nav)
    
    def _render_individual_reports(self):
        """Render individual investor reports"""
        st.subheader("👤 Báo Cáo Từng Nhà Đầu Tư")
        
        # Investor selection
        options = self.fund_manager.get_investor_options()
        selected_display = st.selectbox(
            "👤 Chọn Nhà Đầu Tư", 
            list(options.keys()),
            key="individual_report_investor"
        )
        
        if not selected_display:
            return
        
        # Type safety: ensure investor_id is always an integer using safe selectbox handling
        from utils.streamlit_widget_safety import safe_investor_id_from_selectbox
        investor_id = safe_investor_id_from_selectbox(self.fund_manager, selected_display)
        if investor_id is None:
            st.error("❌ Không thể lấy ID nhà đầu tư hợp lệ từ lựa chọn")
            return
        
        # NAV input for calculations
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input(
            "📊 NAV dùng để tính toán", 
            value=format_currency(latest_nav) if latest_nav else "0đ",
            key="individual_report_nav"
        )
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập NAV tổng hợp lệ.")
            return
        
        # Display individual report
        self._render_detailed_individual_report(investor_id, current_nav, selected_display)
        
        # Export options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Xuất Báo Cáo PDF", width='stretch', key="export_pdf"):
                st.info("🚧 Tính năng xuất PDF đang phát triển")
        
        with col2:
            if st.button("📊 Xuất Báo Cáo Excel", width='stretch', key="export_excel_individual"):
                self._export_individual_excel_report(investor_id, current_nav, selected_display)
        
        with col3:
            if st.button("📧 Gửi Email Cho Khách Hàng", width='stretch', key="email_client"):
                st.info("🚧 Tính năng email đang phát triển")
    
    def _render_kpi_section(self, current_nav):
        """Render key performance indicators with color coding"""
        st.markdown("### 🎯 Chỉ Số Hiệu Suất Chính")

        # Add global color classes
        ColorCoding.add_global_color_classes()

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

        # Calculate profit/loss
        total_profit_loss = total_current_value + total_fees_paid - total_original_invested
        gross_return = total_profit_loss / total_original_invested if total_original_invested > 0 else 0

        # Display KPIs with color coding
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("💰 NAV Tổng", format_currency(current_nav))

        with col2:
            st.metric("📈 Giá/đơn vị quỹ", format_currency(current_price))

        with col3:
            # Gross Return with inline color (Dark mode compatible)
            st.markdown(f"""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">📊 Gross Return</div>
                <div class="metric-value">
                    {percentage_html(gross_return)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.metric("💸 Tổng Phí", format_currency(total_fees_paid))

        with col5:
            st.metric("🛒 Giá Trị FM", format_currency(fm_value))

        # Show total profit/loss with color - bigger and clearer (Dark mode compatible)
        st.markdown("---")
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">💹 TỔNG LÃI/LỖ</div>
            <div class="summary-value">
                {profit_loss_html(total_profit_loss)}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Additional insights with color
        st.markdown("---")
        st.markdown("### 📈 Chi Tiết Hiệu Suất")
        insight_col1, insight_col2, insight_col3 = st.columns(3)

        net_return = (total_current_value - total_original_invested) / total_original_invested if total_original_invested > 0 else 0
        fee_rate = total_fees_paid / total_original_invested if total_original_invested > 0 else 0
        aum_growth = (current_nav - total_original_invested) / total_original_invested if total_original_invested > 0 else 0

        with insight_col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📉 Net Return (sau phí)</div>
                <div class="metric-value">
                    {percentage_html(net_return)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with insight_col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">💱 Tỷ lệ phí lũy kế</div>
                <div class="metric-value">
                    {format_percentage(fee_rate)}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with insight_col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🚀 Tăng trưởng AUM</div>
                <div class="metric-value">
                    {percentage_html(aum_growth)}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_portfolio_composition(self, current_nav):
        """Render portfolio composition chart"""
        st.markdown("### 🥧 Cơ Cấu Danh Mục")
        
        composition_data = []
        for investor in self.fund_manager.get_regular_investors():
            balance, _, _ = self.fund_manager.get_investor_balance(investor.id, current_nav)
            if balance > 0:
                composition_data.append({
                    'Nhà Đầu Tư': investor.display_name,
                    'Giá Trị': balance,
                    'Tỷ Trọng': balance / current_nav * 100
                })
        
        # Add Fund Manager
        fund_manager = self.fund_manager.get_fund_manager()
        if fund_manager:
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            fm_units = sum(t.units for t in fm_tranches)
            fm_value = fm_units * self.fund_manager.calculate_price_per_unit(current_nav)
            if fm_value > 0:
                composition_data.append({
                    'Nhà Đầu Tư': '🛒 Fund Manager',
                    'Giá Trị': fm_value,
                    'Tỷ Trọng': fm_value / current_nav * 100
                })
        
        if composition_data:
            df_composition = pd.DataFrame(composition_data)
            
            # =================== THÊM LỚP BẢO VỆ ===================
            if not df_composition.empty:
                # Pie chart
                pie_chart = alt.Chart(df_composition).mark_arc(innerRadius=50).encode(
                    theta='Giá Trị:Q',
                    color=alt.Color('Nhà Đầu Tư:N', scale=alt.Scale(scheme='category20')),
                    tooltip=['Nhà Đầu Tư', 'Giá Trị', 'Tỷ Trọng']
                ).properties(
                    title="Phân Bố Danh Mục",
                    height=300
                )
                safe_altair_chart(pie_chart, use_container_width=True)
            else:
                st.info("ℹ️ Không có dữ liệu để hiển thị biểu đồ phân bổ danh mục.")
    
    def _render_performance_summary(self, current_nav):
        """Render performance summary with color coding"""
        st.markdown("### 📈 Tóm Tắt Hiệu Suất")

        performance_data = []
        for investor in self.fund_manager.get_regular_investors():
            lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, current_nav)
            if lifetime_perf['original_invested'] > 0:
                # Calculate profit/loss
                profit_loss = lifetime_perf['current_value'] + lifetime_perf['total_fees_paid'] - lifetime_perf['original_invested']

                performance_data.append({
                    'Nhà Đầu Tư': investor.display_name,
                    'Vốn Gốc': lifetime_perf['original_invested'],
                    'Giá Trị Hiện Tại': lifetime_perf['current_value'],
                    'Lãi/Lỗ': profit_loss,
                    'Gross Return': lifetime_perf['gross_return'],
                    'Net Return': lifetime_perf['net_return'],
                    'Tổng Phí': lifetime_perf['total_fees_paid']
                })

        if performance_data:
            df_performance = pd.DataFrame(performance_data)

            # Return comparison chart
            chart_data = df_performance.melt(
                id_vars=['Nhà Đầu Tư'],
                value_vars=['Gross Return', 'Net Return'],
                var_name='Loại Lợi Nhuận',
                value_name='Tỷ Lệ'
            )

            bar_chart = alt.Chart(chart_data).mark_bar().encode(
                x='Nhà Đầu Tư:N',
                y='Tỷ Lệ:Q',
                color='Loại Lợi Nhuận:N',
                tooltip=['Nhà Đầu Tư', 'Loại Lợi Nhuận', 'Tỷ Lệ']
            ).properties(
                title="So Sánh Gross và Net Return",
                height=300
            )

            safe_altair_chart(bar_chart, use_container_width=True)
    
    def _render_fund_growth_timeline(self):
        """Render fund growth over time"""
        st.markdown("### 📅 Dòng Thời Gian Tăng Trưởng Quỹ")
        
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
                'Ngày': trans.date,
                'NAV': running_nav,
                'Loại': display_transaction_type_vi(trans.type)
            })
        
        if timeline_data:
            df_timeline = pd.DataFrame(timeline_data)
            
            # =================== THÊM LỚP BẢO VỆ ===================
            if not df_timeline.empty:
                # Line chart
                line_chart = alt.Chart(df_timeline).mark_line(point=True).encode(
                    x='Ngày:T',
                    y='NAV:Q',
                    color=alt.value('steelblue'),
                    tooltip=['Ngày', 'NAV', 'Loại']
                ).properties(
                    title="Dòng thời gian tăng trưởng NAV của quỹ",
                    height=400
                )
                safe_altair_chart(line_chart, use_container_width=True)
                
                # Growth statistics
                if len(timeline_data) > 1:
                    start_nav = timeline_data[0]['NAV']
                    end_nav = timeline_data[-1]['NAV']
                    growth = (end_nav - start_nav) / start_nav if start_nav > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("NAV đầu kỳ", format_currency(start_nav))
                    col2.metric("NAV hiện tại", format_currency(end_nav))
                    col3.metric("Tăng trưởng tổng", format_percentage(growth))
            else:
                st.info("ℹ️ Không có dữ liệu để hiển thị biểu đồ tăng trưởng.")
            # ==========================================================
    
    def _render_detailed_individual_report(self, investor_id, current_nav, investor_name):
        """Render detailed individual investor report"""
        st.markdown(f"### 👤 Báo Cáo Chi Tiết: {investor_name}")
        
        # Get all data for this investor
        report_data = self.fund_manager.get_investor_individual_report(investor_id, current_nav)
        
        if not report_data:
            st.error("❌ Không thể tạo báo cáo cho nhà đầu tư này")
            return
        
        # Summary section with color coding
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">💰 Vốn gốc ban đầu</div>
                <div class="metric-value">
                    {0}
                </div>
            </div>
            """.format(format_currency(report_data['lifetime_performance']['original_invested'])), unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">📊 Giá trị hiện tại</div>
                <div class="metric-value">
                    {0}
                </div>
            </div>
            """.format(format_currency(report_data['current_balance'])), unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">📈 Lãi/Lỗ hiện tại</div>
                <div class="metric-value">
                    {0}
                </div>
            </div>
            """.format(profit_loss_html(report_data['current_profit'])), unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">💸 Tổng phí đã trả</div>
                <div class="metric-value">
                    {0}
                </div>
            </div>
            """.format(format_currency(report_data['lifetime_performance']['total_fees_paid'])), unsafe_allow_html=True)

        # Performance comparison with color coding
        st.markdown("#### 📊 Phân Tích Hiệu Suất")

        perf_col1, perf_col2 = st.columns(2)

        with perf_col1:
            gross_return = report_data['lifetime_performance']['gross_return']
            st.markdown("""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">🚀 Gross Return (trước phí)</div>
                <div class="metric-value">
                    {0}
                </div>
            </div>
            """.format(percentage_html(gross_return)), unsafe_allow_html=True)

        with perf_col2:
            net_return = report_data['lifetime_performance']['net_return']
            st.markdown("""
            <div class="metric-card metric-card-lg">
                <div class="metric-label">💼 Net Return (sau phí)</div>
                <div class="metric-value">
                    {0}
                </div>
            </div>
            """.format(percentage_html(net_return)), unsafe_allow_html=True)
        
        # Tranches detail with color coding
        if report_data['tranches']:
            st.markdown("#### 📋 Các Đợt Vốn Đầu Tư")

            # Header row
            col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1, 1, 1.2, 1.2, 1, 1])
            with col1:
                st.markdown("**Ngày vào**")
            with col2:
                st.markdown("**Giá vào**")
            with col3:
                st.markdown("**Đơn vị quỹ**")
            with col4:
                st.markdown("**Vốn gốc ban đầu**")
            with col5:
                st.markdown("**Giá trị hiện tại**")
            with col6:
                st.markdown("**Lãi/Lỗ**")
            with col7:
                st.markdown("**Phí đã trả**")

            st.divider()

            # Build table with colored P&L
            for tranche in report_data['tranches']:
                current_value = tranche.units * report_data['current_price']
                pnl = current_value - tranche.invested_value

                col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1, 1, 1.2, 1.2, 1, 1])

                with col1:
                    st.text(tranche.entry_date.strftime("%d/%m/%Y"))
                with col2:
                    st.text(format_currency(tranche.entry_nav))
                with col3:
                    st.text(f"{tranche.units:.6f}")
                with col4:
                    st.text(format_currency(tranche.original_invested_value))
                with col5:
                    st.text(format_currency(current_value))
                with col6:
                    st.markdown(profit_loss_html(pnl), unsafe_allow_html=True)
                with col7:
                    st.text(format_currency(tranche.cumulative_fees_paid))

            st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
        
        # Transaction history for this investor
        if report_data['transactions']:
            st.markdown("#### 📝 Lịch Sử Giao Dịch")
            
            trans_data = []
            for trans in sorted(report_data['transactions'], key=lambda x: x.date, reverse=True):
                trans_data.append({
                    'Ngày': trans.date.strftime("%d/%m/%Y"),
                    'Loại': display_transaction_type_vi(trans.type),
                    'Số tiền': format_currency(trans.amount),
                    'NAV tại thời điểm': format_currency(trans.nav),
                    'Biến động đơn vị quỹ': f"{trans.units_change:.6f}"
                })
            
            df_transactions = pd.DataFrame(trans_data)
            st.dataframe(df_transactions, use_container_width=True, hide_index=True)
        
        # Fee history
        if report_data['fee_history']:
            st.markdown("#### 💰 Lịch Sử Thanh Toán Phí")
            
            fee_data = []
            for fee_record in report_data['fee_history']:
                fee_data.append({
                    'Kỳ': fee_record.period,
                    'Ngày': fee_record.calculation_date.strftime("%d/%m/%Y"),
                    'Giá trị phí': format_currency(fee_record.fee_amount),
                    'Đơn vị quỹ phí': f"{fee_record.fee_units:.6f}",
                    'NAV/Unit': format_currency(fee_record.nav_per_unit)
                })
            
            df_fees = pd.DataFrame(fee_data)
            st.dataframe(df_fees, use_container_width=True, hide_index=True)
        
        # Investment insights
        st.markdown("#### 💡 Gợi Ý Đầu Tư")
        
        insights = []
        
        # Time in fund
        if report_data['tranches']:
            # Filter valid tranches with proper datetime objects
            valid_tranches = [
                t for t in report_data['tranches'] 
                if t.original_entry_date is not None 
                and isinstance(t.original_entry_date, datetime)
            ]
            
            if valid_tranches:
                try:
                    oldest_tranche = min(valid_tranches, key=lambda t: t.original_entry_date)
                    current_time = TimezoneManager.now()
                    normalized_entry_date = TimezoneManager.normalize_for_display(oldest_tranche.original_entry_date)
                    
                    days_invested = (current_time - normalized_entry_date).days
                    years_invested = days_invested / 365.25
                    insights.append(f"📅 Đã đầu tư: {years_invested:.1f} năm ({days_invested} ngày)")
                except Exception as e:
                    # Fallback: show basic info without time calculation
                    insights.append("📅 Thời gian đầu tư: Đang tính toán...")
        
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
                insights.append(f"🏆 Xếp hạng: #{rank}/{len(all_returns)} nhà đầu tư theo Net Return")
        
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
            timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Individual_Report_{investor_name.replace(' ', '_')}_{timestamp}.xlsx"
            
            # Offer download
            st.download_button(
                label=f"📥 Tải xuống {filename}",
                data=buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.success(f"✅ Báo cáo cá nhân đã sẵn sàng để tải xuống: {filename}")
            
        except Exception as e:
            st.error(f"❌ Xuất báo cáo thất bại: {str(e)}")
    
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
                        TimezoneManager.now().strftime("%Y-%m-%d %H:%M:%S"),
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
            timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Executive_Summary_{timestamp}.xlsx"
            
            # Offer download
            st.download_button(
                label=f"📥 Tải xuống {filename}",
                data=buffer,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            st.success(f"✅ Tóm tắt điều hành đã sẵn sàng để tải xuống: {filename}")
            
        except Exception as e:
            st.error(f"❌ Xuất báo cáo thất bại: {str(e)}")
    
    def render_lifetime_performance(self):
        """Render lifetime performance"""
        st.subheader("📈 Phân Tích Hiệu Suất Vòng Đời")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input("📊 NAV Hiện Tại", 
                                 value=format_currency(latest_nav) if latest_nav else "0đ",
                                 key="lifetime_performance_nav_input")
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập NAV tổng hợp lệ.")
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
                    'Gross Return': perf['gross_return'],
                    'Net Return': perf['net_return'],
                    'Đơn vị quỹ hiện tại': perf['current_units']
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
            col4.metric("📈 Net Return tổng thể", format_percentage(overall_net_return))
            
            # Format display table
            display_df = df_perf.copy()
            currency_cols = ['Vốn Gốc', 'Giá Trị Hiện Tại', 'Tổng Phí Đã Trả', 
                           'Lợi Nhuận Gross', 'Lợi Nhuận Net']
            for col in currency_cols:
                display_df[col] = display_df[col].apply(format_currency)
            
            display_df['Gross Return'] = display_df['Gross Return'].apply(format_percentage)
            display_df['Net Return'] = display_df['Net Return'].apply(format_percentage)
            display_df['Đơn vị quỹ hiện tại'] = display_df['Đơn vị quỹ hiện tại'].apply(lambda x: f"{x:.6f}")
            
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
                    safe_altair_chart(pie_chart, use_container_width=True)
                
                with col_chart2:
                    st.subheader("📊 So sánh Gross và Net Return")
                    return_data = df_perf[['Nhà Đầu Tư', 'Gross Return', 'Net Return']].copy()
                    return_data_melted = return_data.melt(
                        id_vars=['Nhà Đầu Tư'], 
                        value_vars=['Gross Return', 'Net Return'],
                        var_name='Loại lợi nhuận', 
                        value_name='Tỷ lệ'
                    )
                    
                    bar_chart = alt.Chart(return_data_melted).mark_bar().encode(
                        x='Nhà Đầu Tư:N',
                        y='Tỷ lệ:Q',
                        color='Loại lợi nhuận:N',
                        tooltip=['Nhà Đầu Tư', 'Loại lợi nhuận', 'Tỷ lệ']
                    )
                    safe_altair_chart(bar_chart, use_container_width=True)
                
                # Fee impact analysis
                st.subheader("💰 Phân Tích Tác Động Phí")
                fee_impact_data = df_perf[['Nhà Đầu Tư', 'Tổng Phí Đã Trả']].copy()
                
                fee_chart = alt.Chart(fee_impact_data).mark_bar().encode(
                    x='Nhà Đầu Tư:N',
                    y='Tổng Phí Đã Trả:Q',
                    color=alt.value('orange'),
                    tooltip=['Nhà Đầu Tư', 'Tổng Phí Đã Trả']
                )
                safe_altair_chart(fee_chart, use_container_width=True)
        
        else:
            st.info("📄 Chưa có dữ liệu hiệu suất.")
    
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
            # Type safety: ensure all selected IDs are integers using safe conversion
            from utils.streamlit_widget_safety import safe_selectbox_int_value
            selected_ids = []
            for name in selected_investors:
                try:
                    investor_id = safe_selectbox_int_value(investor_options, name)
                    if investor_id is not None and investor_id >= 0:
                        selected_ids.append(investor_id)
                except Exception as e:
                    print(f"Warning: Skipping invalid investor ID for {name}: {e}")
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
                    'Phí (Đơn vị quỹ)': f"{record.fee_units:.6f}",
                    'NAV/Unit': record.nav_per_unit,
                    'Đơn vị quỹ trước': f"{record.units_before:.6f}",
                    'Đơn vị quỹ sau': f"{record.units_after:.6f}",
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
            col2.metric("📊 Tổng đơn vị quỹ chuyển", f"{total_fee_units:.6f}")
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
                    'Tổng đơn vị quỹ': f"{data['units']:.6f}",
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
                ).properties(title="Phí hiệu suất theo kỳ")
                
                safe_altair_chart(chart, use_container_width=True)
        
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
            investor_name = investor.display_name if investor else "Hệ thống"
            
            data.append({
                'ID': trans.id,
                'Nhà Đầu Tư': investor_name,
                'Ngày': trans.date.strftime("%d/%m/%Y %H:%M"),
                'Loại': display_transaction_type_vi(trans.type),
                'Số Tiền': format_currency(trans.amount),
                'NAV': format_currency(trans.nav),
                'Biến động đơn vị quỹ': f"{trans.units_change:.6f}"
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
        st.subheader("🛒 Bảng Điều Khiển Fund Manager")
        
        fund_manager = self.fund_manager.get_fund_manager()
        if not fund_manager:
            st.error("❌ Không tìm thấy Fund Manager")
            return
        
        fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
        
        if not fm_tranches:
            st.info("📄 Fund Manager chưa có đơn vị quỹ")
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
        col1.metric("📊 Tổng đơn vị quỹ", f"{total_units:.6f}")
        col2.metric("💰 Tổng giá trị", format_currency(total_value))
        col3.metric("📈 Giá hiện tại", format_currency(current_price))
        col4.metric("🎯 Giá vào trung bình", format_currency(avg_entry_price))
        
        # Fund Manager tranches detail
        st.subheader("📋 Danh Sách Đợt Vốn Fund Manager")
        
        fm_data = []
        for tranche in fm_tranches:
            current_value = tranche.units * current_price
            profit_loss = current_value - tranche.invested_value
            
            fm_data.append({
                'Ngày Nhận': tranche.entry_date.strftime("%d/%m/%Y"),
                'Giá vào': format_currency(tranche.entry_nav),
                'Đơn vị quỹ': f"{tranche.units:.6f}",
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
            st.subheader("📈 Dòng thời gian phí nhận")
            
            fee_timeline = []
            cumulative_fee = 0
            
            for trans in sorted(fee_transactions, key=lambda x: x.date):
                cumulative_fee += trans.amount
                fee_timeline.append({
                    'Ngày': trans.date,
                    'Phí nhận': trans.amount,
                    'Phí lũy kế': cumulative_fee
                })
            
            df_timeline = pd.DataFrame(fee_timeline)
            
            chart = alt.Chart(df_timeline).mark_line(point=True).encode(
                x='Ngày:T',
                y='Phí lũy kế:Q',
                tooltip=['Ngày', 'Phí nhận', 'Phí lũy kế']
            ).properties(title="Lũy kế phí nhận")
            
            safe_altair_chart(chart, use_container_width=True)
            
            total_fee_income = sum(t.amount for t in fee_transactions)
            st.success(f"💰 **Tổng phí nhận:** {format_currency(total_fee_income)}")
        
        else:
            st.info("📄 Fund Manager chưa nhận khoản phí nào")
