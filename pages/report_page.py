import streamlit as st
import pandas as pd
import altair as alt
from utils import format_currency, format_percentage, parse_currency, highlight_profit_loss

class ReportPage:
    """Page báo cáo và thống kê"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_reports(self):
        """Render trang báo cáo"""
        st.title("📊 Báo Cáo & Thống Kê")
        
        if not self.fund_manager.investors:
            st.info("📝 Chưa có nhà đầu tư nào.")
            return
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Thống Kê Giá Trị", 
            "📋 Lịch Sử Giao Dịch", 
            "🔍 Chi Tiết Tranches",
            "📈 Hiệu Suất Quỹ"
        ])
        
        with tab1:
            self._render_value_statistics()
        
        with tab2:
            self._render_transaction_history()
        
        with tab3:
            self._render_tranches_detail()
        
        with tab4:
            self._render_fund_performance()
    
    def _render_value_statistics(self):
        """Thống kê giá trị"""
        st.subheader("📊 Thống Kê Giá Trị")
        
        # Filter investors
        options = self.fund_manager.get_investor_options()
        selected_investors = st.multiselect(
            "👥 Lọc theo Nhà Đầu Tư",
            list(options.keys()),
            default=[]
        )
        
        selected_ids = [options[name] for name in selected_investors] if selected_investors else [inv.id for inv in self.fund_manager.investors]
        
        # Current NAV input
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = st.text_input("📊 Total NAV Hiện Tại", value=format_currency(latest_nav) if latest_nav else "0đ")
        current_nav = parse_currency(nav_input)
        
        if current_nav <= 0:
            st.warning("⚠️ Vui lòng nhập Total NAV hợp lệ.")
            return
        
        # Calculate balances
        balances = []
        chart_data = []
        
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
            
            # Data for charts
            for tranche in tranches:
                chart_data.append({
                    'Investor': investor.display_name,
                    'Date': tranche.entry_date,
                    'EntryPrice': tranche.entry_nav,
                    'InvestedValue': tranche.invested_value
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
            
            # Charts
            if chart_data:
                df_chart = pd.DataFrame(chart_data)
                
                # Pie chart for balance distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🥧 Phân Bố NAV")
                    pie_data = df_balances[['Nhà Đầu Tư', 'Số Dư']].copy()
                    
                    pie_chart = alt.Chart(pie_data).mark_arc().encode(
                        theta='Số Dư:Q',
                        color='Nhà Đầu Tư:N',
                        tooltip=['Nhà Đầu Tư', 'Số Dư']
                    )
                    st.altair_chart(pie_chart, use_container_width=True)
                
                with col2:
                    st.subheader("📈 Lãi/Lỗ theo NĐT")
                    profit_data = df_balances[['Nhà Đầu Tư', 'Lãi/Lỗ']].copy()
                    
                    bar_chart = alt.Chart(profit_data).mark_bar().encode(
                        x='Nhà Đầu Tư:N',
                        y='Lãi/Lỗ:Q',
                        color=alt.condition(
                            alt.datum['Lãi/Lỗ'] > 0,
                            alt.value('green'),
                            alt.value('red')
                        ),
                        tooltip=['Nhà Đầu Tư', 'Lãi/Lỗ']
                    )
                    st.altair_chart(bar_chart, use_container_width=True)
                
                # Investment timeline
                st.subheader("📅 Timeline Đầu Tư")
                line_chart = alt.Chart(df_chart).mark_line(point=True).encode(
                    x='Date:T',
                    y='InvestedValue:Q',
                    color='Investor:N',
                    tooltip=['Investor', 'Date', 'InvestedValue', 'EntryPrice']
                ).properties(height=400)
                st.altair_chart(line_chart, use_container_width=True)
        
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
        col1, col2, col3 = st.columns(3)
        
        total_deposits = sum(t.amount for t in self.fund_manager.transactions if t.type == 'Nạp')
        total_withdrawals = abs(sum(t.amount for t in self.fund_manager.transactions if t.type == 'Rút'))
        total_fees = abs(sum(t.amount for t in self.fund_manager.transactions if t.type == 'Phí'))
        
        col1.metric("💰 Tổng Nạp", format_currency(total_deposits))
        col2.metric("💸 Tổng Rút", format_currency(total_withdrawals))
        col3.metric("🧮 Tổng Phí", format_currency(total_fees))
    
    def _render_tranches_detail(self):
        """Chi tiết tranches"""
        st.subheader("🔍 Chi Tiết Tranches")
        
        if not self.fund_manager.tranches:
            st.info("📝 Chưa có tranches nào.")
            return
        
        # Current NAV for calculations
        latest_nav = self.fund_manager.get_latest_total_nav()
        if latest_nav:
            current_price = self.fund_manager.calculate_price_per_unit(latest_nav)
            
            data = []
            for tranche in self.fund_manager.tranches:
                investor = self.fund_manager.get_investor_by_id(tranche.investor_id)
                investor_name = investor.display_name if investor else f"ID {tranche.investor_id}"
                
                current_value = tranche.units * current_price
                profit_loss = current_value - tranche.invested_value
                
                data.append({
                    'Nhà Đầu Tư': investor_name,
                    'Ngày Vào': tranche.entry_date.strftime("%d/%m/%Y"),
                    'Entry NAV': format_currency(tranche.entry_nav),
                    'Units': f"{tranche.units:.6f}",
                    'HWM': format_currency(tranche.hwm),
                    'Vốn Đầu Tư': format_currency(tranche.invested_value),
                    'Giá Trị Hiện Tại': format_currency(current_value),
                    'Lãi/Lỗ': format_currency(profit_loss)
                })
            
            df_tranches = pd.DataFrame(data)
            st.dataframe(df_tranches, use_container_width=True)
            
            st.info(f"💡 Tính toán dựa trên giá hiện tại: {format_currency(current_price)} per unit")
        
        else:
            # No NAV data - just show basic info
            data = []
            for tranche in self.fund_manager.tranches:
                investor = self.fund_manager.get_investor_by_id(tranche.investor_id)
                investor_name = investor.display_name if investor else f"ID {tranche.investor_id}"
                
                data.append({
                    'Nhà Đầu Tư': investor_name,
                    'Ngày Vào': tranche.entry_date.strftime("%d/%m/%Y"),
                    'Entry NAV': format_currency(tranche.entry_nav),
                    'Units': f"{tranche.units:.6f}",
                    'HWM': format_currency(tranche.hwm),
                    'Vốn Đầu Tư': format_currency(tranche.invested_value)
                })
            
            df_tranches = pd.DataFrame(data)
            st.dataframe(df_tranches, use_container_width=True)
    
    def _render_fund_performance(self):
        """Hiệu suất quỹ"""
        st.subheader("📈 Hiệu Suất Quỹ")
        
        if not self.fund_manager.transactions:
            st.info("📝 Chưa có dữ liệu giao dịch để tính hiệu suất.")
            return
        
        # Calculate performance metrics
        performance = self._calculate_performance_metrics()
        
        if not performance:
            st.warning("⚠️ Không đủ dữ liệu để tính hiệu suất.")
            return
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("📊 Time-Weighted Return", format_percentage(performance.get('twr', 0)))
        col2.metric("📉 Max Drawdown", format_percentage(performance.get('max_drawdown', 0)))
        col3.metric("📈 Volatility", f"{performance.get('volatility', 0) * 100:.2f}%")
        col4.metric("🔍 Sharpe Ratio", f"{performance.get('sharpe_ratio', 0):.3f}")
        
        # Price history chart
        if 'price_history' in performance and not performance['price_history'].empty:
            st.subheader("📈 Biểu Đồ Giá NAV per Unit")
            
            df_hist = performance['price_history']
            
            price_chart = alt.Chart(df_hist).mark_line(point=True).encode(
                x='date:T',
                y='price:Q',
                tooltip=['date', 'price', 'nav', 'units']
            ).properties(height=400)
            
            st.altair_chart(price_chart, use_container_width=True)
        
        # Performance summary
        st.subheader("📋 Tóm Tắt Hiệu Suất")
        
        summary_data = {
            'Chỉ Số': [
                'Time-Weighted Return',
                'Max Drawdown', 
                'Volatility (Annualized)',
                'Sharpe Ratio',
                'Tổng Số Ngày',
                'Số Giao Dịch'
            ],
            'Giá Trị': [
                format_percentage(performance.get('twr', 0)),
                format_percentage(performance.get('max_drawdown', 0)),
                f"{performance.get('annualized_volatility', 0) * 100:.2f}%",
                f"{performance.get('sharpe_ratio', 0):.3f}",
                f"{performance.get('total_days', 0)} ngày",
                f"{performance.get('total_transactions', 0)} giao dịch"
            ]
        }
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    def _calculate_performance_metrics(self):
        """Tính các chỉ số performance"""
        if not self.fund_manager.transactions:
            return {}
        
        # Build price history
        price_history = []
        total_units = 0.0
        
        for trans in sorted(self.fund_manager.transactions, key=lambda x: x.date):
            if trans.type in ['Nạp', 'Rút', 'Phí']:
                total_units += trans.units_change
                total_units = max(0, total_units)
            
            if trans.nav > 0 and total_units > 1e-6:
                price = trans.nav / total_units
                price_history.append({
                    'date': trans.date,
                    'price': price,
                    'nav': trans.nav,
                    'units': total_units
                })
        
        if len(price_history) < 2:
            return {}
        
        df_hist = pd.DataFrame(price_history)
        df_hist['return'] = df_hist['price'].pct_change().fillna(0)
        
        # Remove extreme outliers
        df_hist = df_hist[abs(df_hist['return']) < 5.0]
        
        if df_hist.empty or len(df_hist) < 2:
            return {}
        
        import numpy as np
        
        returns = df_hist['return'].dropna()
        
        # Time-weighted return
        twr = np.prod(1 + returns) - 1 if len(returns) > 0 else 0
        
        # Volatility
        volatility = returns.std() if len(returns) > 1 else 0
        
        # Max drawdown
        running_max = df_hist['price'].expanding().max()
        drawdown = (df_hist['price'] - running_max) / running_max
        max_drawdown = drawdown.min() if not drawdown.empty else 0
        
        # Sharpe ratio (assuming 0% risk-free rate)
        avg_return = returns.mean() if len(returns) > 0 else 0
        sharpe_ratio = avg_return / volatility if volatility > 0 else 0
        
        # Annualized metrics
        total_days = (df_hist['date'].max() - df_hist['date'].min()).days
        annualized_volatility = volatility * np.sqrt(252) if volatility > 0 else 0
        
        return {
            'twr': twr,
            'volatility': volatility,
            'annualized_volatility': annualized_volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_days': total_days,
            'total_transactions': len(self.fund_manager.transactions),
            'price_history': df_hist
        }
