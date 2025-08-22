import streamlit as st
import pandas as pd
from datetime import date, datetime
from utils import format_currency, parse_currency, format_percentage, highlight_profit_loss

class SafeFeePage:
    """Enhanced Fee Page với comprehensive safety features"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_enhanced_fee_calculation(self):
        """Enhanced fee calculation với comprehensive safety"""
        st.title("🧮 Tính Toán Phí Cuối Năm")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
            st.warning("⚠️ Chưa có nhà đầu tư nào.")
            return
        
        # Data consistency check first
        self._render_data_consistency_check()
        
        # Input parameters
        col1, col2, col3 = st.columns(3)
        
        year = col1.number_input("📅 Năm", value=2025, min_value=2020, max_value=2030)
        ending_date = col2.date_input("📅 Ngày Kết Thúc", value=date(2025, 12, 31))
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        nav_input = col3.text_input("📊 Total NAV Kết Thúc", 
                                   value=format_currency(latest_nav) if latest_nav else "0đ",
                                   key="enhanced_fee_nav_input")
        ending_nav = parse_currency(nav_input)
        
        # NAV change validation
        if latest_nav and ending_nav > 0:
            nav_change_pct = abs(ending_nav - latest_nav) / latest_nav * 100
            if nav_change_pct > 5:
                st.warning(f"⚠️ NAV thay đổi {nav_change_pct:.1f}% so với NAV hiện tại")
        
        # Show fund manager current status
        fund_manager = self.fund_manager.get_fund_manager()
        if fund_manager:
            with st.expander("🛒 Fund Manager Status", expanded=False):
                fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
                if fm_tranches:
                    fm_units = sum(t.units for t in fm_tranches)
                    if ending_nav > 0:
                        fm_value = fm_units * self.fund_manager.calculate_price_per_unit(ending_nav)
                        col_fm1, col_fm2 = st.columns(2)
                        col_fm1.metric("Units hiện tại", f"{fm_units:,.6f}")
                        col_fm2.metric("Giá trị hiện tại", format_currency(fm_value))
                else:
                    st.info("Fund Manager chưa có units")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "🧮 Preview & Safety Check", 
            "📋 Phí Chi Tiết", 
            "📊 Chi Tiết Tranches",
            "⚡ Apply Phí"
        ])
        
        with tab1:
            self._render_fee_preview_with_safety(year, ending_date, ending_nav)
        
        with tab2:
            self._render_detailed_fee_calculation(ending_date, ending_nav)
        
        with tab3:
            self._render_tranches_detail(ending_nav)
        
        with tab4:
            self._render_safe_fee_application(year, ending_date, ending_nav)
    
    def render_individual_fee(self):
        """Tính phí riêng cho nhà đầu tư với enhanced display"""
        st.title("📋 Tính Phí Riêng Cho Nhà Đầu Tư")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
            st.info("📄 Chưa có nhà đầu tư nào.")
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
                self._render_individual_fee_analysis(investor_id, calc_date, calc_nav, selected_display)
        
        st.info("💡 Chỉ tính toán preview, không áp dụng. Dùng để xem trước khi rút giữa năm.")
    
    def _render_data_consistency_check(self):
        """Render data consistency check"""
        with st.expander("🔍 Kiểm Tra Tính Nhất Quán Dữ Liệu", expanded=False):
            if st.button("🔍 Chạy Kiểm Tra", use_container_width=True):
                validation_results = self.fund_manager.validate_data_consistency()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if validation_results['valid']:
                        st.success("✅ Dữ liệu nhất quán")
                    else:
                        st.error("❌ Phát hiện lỗi trong dữ liệu")
                    
                    if validation_results['errors']:
                        st.subheader("❌ Lỗi:")
                        for error in validation_results['errors']:
                            st.error(error)
                
                with col2:
                    if validation_results['warnings']:
                        st.subheader("⚠️ Cảnh báo:")
                        for warning in validation_results['warnings']:
                            st.warning(warning)
                    
                    if validation_results['stats']:
                        st.subheader("📊 Thống kê:")
                        stats = validation_results['stats']
                        for key, value in stats.items():
                            if isinstance(value, float):
                                st.write(f"**{key}:** {value:,.2f}")
                            else:
                                st.write(f"**{key}:** {value}")
    
    def _render_fee_preview_with_safety(self, year: int, ending_date: date, ending_nav: float):
        """Show comprehensive fee preview với safety checks"""
        st.subheader("🚀 Bảng tính phí Preview (Enhanced Safety)")
        
        if ending_nav <= 0:
            st.warning("ℹ️ Vui lòng nhập Total NAV kết thúc lớn hơn 0 để xem tính toán.")
            return
        
        # Safety checks first
        safety_results = self._perform_safety_checks(year, ending_date, ending_nav)
        self._display_safety_results(safety_results)
        
        if not safety_results['safe_to_proceed']:
            st.error("❌ Không thể tiếp tục do có vấn đề về an toàn dữ liệu")
            return
        
        # Fee calculation preview
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
            units_fee = details['total_fee'] / ending_price if details['total_fee'] > 0 and ending_price > 0 else 0
            
            results.append({
                'Nhà Đầu Tư': investor.display_name,
                'Units Hiện Tại': f"{total_units:.6f}",
                'Vốn Gốc': lifetime_perf['original_invested'],
                'Phí Đã Trả': lifetime_perf['total_fees_paid'],
                'Số Dư': details['balance'],
                'Lãi/Lỗ': details['profit'],
                'Phí Mới': details['total_fee'],
                'Units Chuyển': f"{units_fee:.6f}",
                'Units Còn Lại': f"{total_units - units_fee:.6f}",
                '% Portfolio': f"{(details['balance'] / ending_nav * 100):.1f}%" if ending_nav > 0 else "0%"
            })
            total_fees += details['total_fee']
            total_units_transfer += units_fee
        
        if results:
            df_results = pd.DataFrame(results)
            currency_cols = ['Vốn Gốc', 'Phí Đã Trả', 'Số Dư', 'Lãi/Lỗ', 'Phí Mới']
            for col in currency_cols:
                df_results[col] = df_results[col].apply(format_currency)
            
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            # Summary với color coding
            col1, col2, col3, col4 = st.columns(4)
            col1.success(f"💰 **Tổng phí:** {format_currency(total_fees)}")
            col2.info(f"📊 **Units chuyển:** {total_units_transfer:,.6f}")
            col3.warning(f"🛒 **Về Fund Manager:** {format_currency(total_fees)}")
            col4.metric("📈 **Fee Rate**", f"{(total_fees/ending_nav*100):.2f}%" if ending_nav > 0 else "0%")
            
            # Additional insights
            if total_fees > 0:
                st.info(f"""
                📈 **Phân tích fee:**
                - Fee rate: {(total_fees/ending_nav*100):.2f}% of total NAV
                - Units transfer: {(total_units_transfer/sum(t.units for t in self.fund_manager.tranches)*100):.1f}% of total units
                - Estimated FM units after: {sum(t.units for t in self.fund_manager.get_investor_tranches(self.fund_manager.get_fund_manager().id)) + total_units_transfer:.6f}
                """)
    
    def _render_safe_fee_application(self, year: int, ending_date: date, ending_nav: float):
        """Render safe fee application với multiple confirmations"""
        st.subheader("⚡ Áp Dụng Phí (Safe Mode)")
        
        if ending_nav <= 0:
            st.warning("ℹ️ Vui lòng nhập Total NAV để tiếp tục.")
            return
        
        # Final safety check
        safety_results = self._perform_safety_checks(year, ending_date, ending_nav)
        
        if not safety_results['safe_to_proceed']:
            st.error("❌ Không thể áp dụng phí do có vấn đề về an toàn dữ liệu")
            return
        
        # Multi-step confirmation
        st.markdown("### 🔒 Xác Nhận Áp Dụng Phí (3 bước)")
        
        # Step 1: Acknowledge risks
        step1 = st.checkbox("1️⃣ Tôi hiểu rằng việc áp dụng phí sẽ thay đổi dữ liệu vĩnh viễn")
        
        # Step 2: Confirm calculations
        step2 = False
        if step1:
            st.info("✅ Bước 1 hoàn thành")
            step2 = st.checkbox("2️⃣ Tôi đã kiểm tra kỹ các tính toán phí ở tab Preview")
        
        # Step 3: Final confirmation
        step3 = False
        if step2:
            st.info("✅ Bước 2 hoàn thành")
            
            # Show summary again
            total_fees = sum(
                self.fund_manager.calculate_investor_fee(inv.id, datetime.combine(ending_date, datetime.min.time()), ending_nav)['total_fee']
                for inv in self.fund_manager.get_regular_investors()
            )
            
            st.warning(f"""
            🚨 **Xác nhận cuối cùng:**
            - Năm: {year}
            - Ngày: {ending_date.strftime('%d/%m/%Y')}
            - Total NAV: {format_currency(ending_nav)}
            - Tổng phí áp dụng: {format_currency(total_fees)}
            """)
            
            step3 = st.checkbox("3️⃣ Tôi xác nhận áp dụng phí với các thông số trên")
        
        # Apply button
        if step1 and step2 and step3:
            st.success("✅ Tất cả xác nhận hoàn thành")
            
            if st.button("🚀 ÁP DỤNG PHÍ CUỐI NĂM", type="primary", use_container_width=True):
                # Create backup first
                backup_success = self.fund_manager.backup_before_operation(f"Fee Application {year}")
                
                if backup_success:
                    st.info("💾 Đã tạo backup trước khi áp dụng phí")
                
                # Apply fees
                success, message = self.fund_manager.apply_year_end_fees_enhanced(year, ending_date, ending_nav)
                
                if success:
                    st.balloons()
                    st.success(f"✅ {message}")
                    st.session_state.data_changed = True
                    
                    # Clear confirmation states
                    for key in list(st.session_state.keys()):
                        if key.startswith(('step1', 'step2', 'step3')):
                            del st.session_state[key]
                    
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        else:
            remaining_steps = []
            if not step1:
                remaining_steps.append("Bước 1")
            if not step2:
                remaining_steps.append("Bước 2") 
            if not step3:
                remaining_steps.append("Bước 3")
            
            st.info(f"ℹ️ Cần hoàn thành: {', '.join(remaining_steps)}")
    
    def _render_individual_fee_analysis(self, investor_id, calc_date, calc_nav, investor_name):
        """Render comprehensive individual fee analysis"""
        calc_date_dt = datetime.combine(calc_date, datetime.min.time())
        details = self.fund_manager.calculate_investor_fee(investor_id, calc_date_dt, calc_nav)
        lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor_id, calc_nav)
        
        st.markdown(f"## 📊 Phân Tích Chi Tiết: {investor_name}")
        
        # Current vs Lifetime Performance
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
        
        # Fee calculation breakdown
        st.markdown("---")
        st.subheader("💰 Chi Tiết Tính Phí")
        
        fee_col1, fee_col2, fee_col3, fee_col4 = st.columns(4)
        fee_col1.metric("🎯 Hurdle Value (6%)", format_currency(details['hurdle_value']))
        fee_col2.metric("🏔️ HWM Value", format_currency(details['hwm_value']))
        fee_col3.metric("💎 Lợi Nhuận Vượt Ngưỡng", format_currency(details['excess_profit']))
        fee_col4.metric("💸 Phí Performance (20%)", format_currency(details['total_fee']))
        
        # Performance insights
        if details['total_fee'] > 0:
            st.success(f"🎉 Investor có performance vượt ngưỡng! Phí: {format_currency(details['total_fee'])}")
            
            # Show fee impact
            if lifetime_perf['total_fees_paid'] > 0:
                total_fees_after = lifetime_perf['total_fees_paid'] + details['total_fee']
                fee_impact = total_fees_after / lifetime_perf['original_invested'] * 100
                st.info(f"📊 Tổng phí cumulative sẽ là: {format_currency(total_fees_after)} ({fee_impact:.1f}% của vốn gốc)")
        else:
            st.info("ℹ️ Không có phí performance (chưa vượt hurdle rate hoặc HWM)")
        
        # Tranches breakdown
        tranches = self.fund_manager.get_investor_tranches(investor_id)
        if tranches:
            st.markdown("---")
            st.subheader("📋 Chi Tiết Từng Tranche")
            
            tranche_data = []
            current_price = self.fund_manager.calculate_price_per_unit(calc_nav)
            
            for tranche in tranches:
                # Calculate fee for this specific tranche
                time_delta_days = (calc_date_dt - tranche.entry_date).days
                time_delta_years = time_delta_days / 365.25 if time_delta_days > 0 else 0
                
                hurdle_multiplier = (1 + 0.06) ** time_delta_years  # 6% hurdle
                hurdle_price = tranche.entry_nav * hurdle_multiplier
                threshold_price = max(hurdle_price, tranche.hwm)
                profit_per_unit = max(0, current_price - threshold_price)
                tranche_excess = profit_per_unit * tranche.units
                tranche_fee = 0.20 * tranche_excess  # 20% performance fee
                
                tranche_data.append({
                    'Entry Date': tranche.entry_date.strftime("%d/%m/%Y"),
                    'Entry NAV': format_currency(tranche.entry_nav),
                    'Units': f"{tranche.units:.6f}",
                    'Days Held': time_delta_days,
                    'Hurdle Price': format_currency(hurdle_price),
                    'HWM': format_currency(tranche.hwm),
                    'Threshold': format_currency(threshold_price),
                    'Current Value': format_currency(tranche.units * current_price),
                    'Excess Profit': format_currency(tranche_excess),
                    'Fee': format_currency(tranche_fee)
                })
            
            df_tranches = pd.DataFrame(tranche_data)
            st.dataframe(df_tranches, use_container_width=True)
    
    def _perform_safety_checks(self, year: int, ending_date: date, ending_nav: float) -> dict:
        """Perform comprehensive safety checks before fee application"""
        checks = {
            'safe_to_proceed': True,
            'checks': [],
            'warnings': [],
            'errors': []
        }
        
        # Check 1: Data consistency
        validation = self.fund_manager.validate_data_consistency()
        if not validation['valid']:
            checks['safe_to_proceed'] = False
            checks['errors'].extend(validation['errors'])
        checks['checks'].append(f"Data consistency: {'✅ Pass' if validation['valid'] else '❌ Fail'}")
        
        # Check 2: NAV reasonableness
        latest_nav = self.fund_manager.get_latest_total_nav()
        if latest_nav:
            nav_change = abs(ending_nav - latest_nav) / latest_nav * 100
            if nav_change > 20:
                checks['safe_to_proceed'] = False
                checks['errors'].append(f"NAV thay đổi quá lớn: {nav_change:.1f}%")
            elif nav_change > 10:
                checks['warnings'].append(f"NAV thay đổi lớn: {nav_change:.1f}%")
        checks['checks'].append(f"NAV change check: {'✅ Pass' if ending_nav > 0 else '❌ Fail'}")
        
        # Check 3: Fee period check
        last_fee_records = [f for f in self.fund_manager.fee_records if f.period == str(year)]
        if last_fee_records:
            checks['warnings'].append(f"Đã có {len(last_fee_records)} fee records cho năm {year}")
        checks['checks'].append(f"Fee period check: ℹ️ {len(last_fee_records)} existing records for {year}")
        
        # Check 4: All investors have positive balance
        problem_investors = []
        for investor in self.fund_manager.get_regular_investors():
            balance, _, _ = self.fund_manager.get_investor_balance(investor.id, ending_nav)
            if balance <= 0:
                problem_investors.append(investor.display_name)
        
        if problem_investors:
            checks['warnings'].append(f"Investors with zero/negative balance: {', '.join(problem_investors)}")
        checks['checks'].append(f"Investor balances: {'✅ All positive' if not problem_investors else f'⚠️ {len(problem_investors)} with issues'}")
        
        # Check 5: Total units vs NAV consistency
        total_units = sum(t.units for t in self.fund_manager.tranches)
        if total_units > 0:
            price_per_unit = ending_nav / total_units
            if price_per_unit < 1000 or price_per_unit > 10_000_000:
                checks['warnings'].append(f"Unusual price per unit: {format_currency(price_per_unit)}")
        checks['checks'].append(f"Price per unit: {format_currency(price_per_unit) if total_units > 0 else 'N/A'}")
        
        return checks
    
    def _display_safety_results(self, safety_results):
        """Display safety check results"""
        if safety_results['safe_to_proceed']:
            st.success("✅ Safety checks passed - Safe to proceed")
        else:
            st.error("❌ Safety checks failed - Do NOT proceed")
        
        with st.expander("🔍 Chi Tiết Safety Checks", expanded=not safety_results['safe_to_proceed']):
            # Show all checks
            for check in safety_results['checks']:
                st.write(f"• {check}")
            
            # Show errors
            if safety_results['errors']:
                st.subheader("❌ Errors (Must Fix):")
                for error in safety_results['errors']:
                    st.error(error)
            
            # Show warnings
            if safety_results['warnings']:
                st.subheader("⚠️ Warnings (Review):")
                for warning in safety_results['warnings']:
                    st.warning(warning)
    
    def _render_detailed_fee_calculation(self, ending_date, ending_nav):
        """Hiển thị kết quả tính phí chi tiết (unchanged from original)"""
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        results = []
        for investor in self.fund_manager.get_regular_investors():
            details = self.fund_manager.calculate_investor_fee(investor.id, ending_date_dt, ending_nav)
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            total_units = sum(t.units for t in tranches) if tranches else 0
            results.append({
                'Nhà Đầu Tư': investor.display_name, 'Tổng Units': f"{total_units:.6f}",
                'Vốn Đầu Tư': details['invested_value'], 'Số Dư': details['balance'],
                'Lãi/Lỗ': details['profit'], 'Tỷ Lệ L/L': details['profit_perc'],
                'Hurdle Value': details['hurdle_value'], 'HWM Value': details['hwm_value'],
                'Lợi Nhuận Vượt': details['excess_profit'], 'Phí': details['total_fee']
            })
        
        if results:
            df_results = pd.DataFrame(results)
            currency_cols = ['Vốn Đầu Tư', 'Số Dư', 'Lãi/Lỗ', 'Hurdle Value', 'HWM Value', 'Lợi Nhuận Vượt', 'Phí']
            for col in currency_cols:
                df_results[col] = df_results[col].apply(format_currency)
            df_results['Tỷ Lệ L/L'] = df_results['Tỷ Lệ L/L'].apply(format_percentage)
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            total_fee = sum(self.fund_manager.calculate_investor_fee(inv.id, ending_date_dt, ending_nav)['total_fee'] 
                           for inv in self.fund_manager.get_regular_investors())
            if total_fee > 0:
                st.success(f"💰 **Tổng phí performance:** {format_currency(total_fee)}")
            else:
                st.info("ℹ️ Không có phí performance được tính.")
    
    def _render_tranches_detail(self, ending_nav):
        """Hiển thị chi tiết tranches (unchanged from original)"""
        if not self.fund_manager.tranches:
            st.info("📄 Chưa có tranches nào.")
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