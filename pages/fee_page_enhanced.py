import streamlit as st
import pandas as pd
from datetime import date, datetime
from helpers import format_currency, parse_currency, format_percentage, highlight_profit_loss

# Performance optimizations
from performance.cache_service_simple import cache_report_data
from performance.performance_monitor import track_performance

# UX enhancements
from ui.ux_enhancements import UXEnhancements

# Add comprehensive error handling for integer conversion issues
def safe_operation(operation_name, func, *args, **kwargs):
    """Safely execute operations that might have integer conversion issues"""
    try:
        return func(*args, **kwargs)
    except TypeError as e:
        if "'str' object cannot be interpreted as an integer" in str(e):
            st.error(f"🚨 Integer conversion error in {operation_name}")
            st.error(f"Error details: {str(e)}")
            # Log debug info
            st.write("**Debug info:**")
            for i, arg in enumerate(args):
                st.write(f"  Arg {i}: {type(arg).__name__} = {repr(arg)}")
            for k, v in kwargs.items():
                st.write(f"  {k}: {type(v).__name__} = {repr(v)}")
            raise e
        else:
            raise e

class SafeFeePage:
    """Enhanced Fee Page với comprehensive safety features - COMPLETE VERSION"""

    def __init__(self, fund_manager):
        self.fund_manager = fund_manager

    @cache_report_data
    @track_performance("calculate_fees")
    def calculate_fees_cached(_self, investor_id, start_date, end_date, current_nav):
        """Calculate fees with caching"""
        return _self.fund_manager.calculate_performance_fee(investor_id, start_date, end_date, current_nav)
    
    def render_enhanced_fee_calculation(self):
        """Enhanced fee calculation với comprehensive safety"""
        try:
            self._render_enhanced_fee_calculation_impl()
        except TypeError as e:
            if "'str' object cannot be interpreted as an integer" in str(e):
                st.error("🚨 Integer conversion error detected in fee calculation!")
                st.error(f"Error: {str(e)}")
                st.write("**Please report this error with the following details:**")
                st.code(f"Function: render_enhanced_fee_calculation\nError: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
            else:
                raise e
        except Exception as e:
            st.error(f"❌ Unexpected error in fee calculation: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            
    def _render_enhanced_fee_calculation_impl(self):
        """Implementation of enhanced fee calculation"""
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
            with st.expander("🛡️ Fund Manager Status", expanded=False):
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
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🧮 Preview & Safety Check", 
            "📋 Phí Chi Tiết", 
            "📊 Chi Tiết Tranches",
            "💰 Performance Analysis",
            "⚡ Apply Phí"
        ])
        
        with tab1:
            self._render_fee_preview_with_safety(year, ending_date, ending_nav)
        
        with tab2:
            self._render_detailed_fee_calculation(ending_date, ending_nav)
        
        with tab3:
            self._render_tranches_detail(ending_nav)
        
        with tab4:
            self._render_performance_analysis(ending_nav)
        
        with tab5:
            self._render_safe_fee_application(year, ending_date, ending_nav)
            
    def render_individual_fee(self):
        """Tính phí riêng cho nhà đầu tư với enhanced display"""
        try:
            st.title("📋 Tính Phí Riêng Cho Nhà Đầu Tư")
            
            regular_investors = self.fund_manager.get_regular_investors()
            if not regular_investors:
                st.info("📄 Chưa có nhà đầu tư nào.")
                return
            
            options = self.fund_manager.get_investor_options()
            selected_display = st.selectbox("👤 Chọn Nhà Đầu Tư", list(options.keys()))
            
            if not selected_display:
                return
            
            # Type safety: ensure investor_id is always an integer using safe selectbox handling
            from utils.streamlit_widget_safety import safe_investor_id_from_selectbox
            investor_id = safe_investor_id_from_selectbox(self.fund_manager, selected_display)
            if investor_id is None:
                st.error("❌ Could not get valid investor ID from selection")
                return
            
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
                    safe_operation("individual_fee_analysis", self._render_individual_fee_analysis, investor_id, calc_date, calc_nav, selected_display)
                
                st.info("💡 Chỉ tính toán preview, không áp dụng. Dùng để xem trước khi rút giữa năm.")
                
        except TypeError as e:
            if "'str' object cannot be interpreted as an integer" in str(e):
                st.error("🚨 Integer conversion error detected in individual fee calculation!")
                st.error(f"Error: {str(e)}")
                st.write("**Debug Information:**")
                
                # Debug all variables that might be causing the issue
                debug_info = []
                try:
                    if 'regular_investors' in locals():
                        debug_info.append(f"regular_investors count: {len(regular_investors)}")
                        if regular_investors:
                            debug_info.append(f"First investor type: {type(regular_investors[0])}")
                            debug_info.append(f"First investor ID: {repr(regular_investors[0].id)} (type: {type(regular_investors[0].id).__name__})")
                    
                    if 'options' in locals():
                        debug_info.append(f"options count: {len(options)}")
                        for name, inv_id in list(options.items())[:3]:  # First 3
                            debug_info.append(f"  {name}: {repr(inv_id)} (type: {type(inv_id).__name__})")
                    
                    if 'selected_display' in locals():
                        debug_info.append(f"selected_display: {repr(selected_display)} (type: {type(selected_display).__name__})")
                    
                    if 'investor_id' in locals():
                        debug_info.append(f"investor_id: {repr(investor_id)} (type: {type(investor_id).__name__})")
                        
                    # Check transaction types
                    debug_info.append("Sample transaction investor_id types:")
                    for i, tx in enumerate(self.fund_manager.transactions[:3]):
                        debug_info.append(f"  TX{i}: investor_id={repr(tx.investor_id)} (type: {type(tx.investor_id).__name__})")
                        
                except Exception as debug_e:
                    debug_info.append(f"Debug info collection failed: {debug_e}")
                
                st.code("\n".join(debug_info))
                
                import traceback
                st.code(traceback.format_exc())
            else:
                raise e
        except Exception as e:
            st.error(f"❌ Unexpected error in individual fee calculation: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
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
            
            # FIXED: Tính current cost basis chính xác
            current_cost_basis = self.fund_manager.get_investor_current_cost_basis(investor.id)
            original_investment = self.fund_manager.get_investor_original_investment(investor.id)
            
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            total_units = sum(t.units for t in tranches) if tranches else 0
            units_fee = details['total_fee'] / ending_price if details['total_fee'] > 0 and ending_price > 0 else 0
            
            # FIXED: Hiển thị cả current và original investment
            results.append({
                'Nhà Đầu Tư': investor.display_name,
                'Units Hiện Tại': f"{total_units:.6f}",
                'Vốn Gốc Ban Đầu': original_investment,
                'Vốn Hiện Tại': current_cost_basis,
                'Phí Đã Trả': lifetime_perf['total_fees_paid'],
                'Số Dư': details['balance'],
                'L/L vs Current': details['profit'],
                'L/L vs Original': lifetime_perf['gross_profit'],
                'Phí Mới': details['total_fee'],
                'Units Chuyển': f"{units_fee:.6f}",
                'Units Còn Lại': f"{total_units - units_fee:.6f}",
                '% Portfolio': f"{(details['balance'] / ending_nav * 100):.1f}%" if ending_nav > 0 else "0%"
            })
            total_fees += details['total_fee']
            total_units_transfer += units_fee
        
        if results:
            df_results = pd.DataFrame(results)
            currency_cols = ['Vốn Gốc Ban Đầu', 'Vốn Hiện Tại', 'Phí Đã Trả', 'Số Dư', 'L/L vs Current', 'L/L vs Original', 'Phí Mới']
            for col in currency_cols:
                df_results[col] = df_results[col].apply(format_currency)
            
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            # Summary với color coding
            col1, col2, col3, col4 = st.columns(4)
            col1.success(f"💰 **Tổng phí:** {format_currency(total_fees)}")
            col2.info(f"📊 **Units chuyển:** {total_units_transfer:,.6f}")
            col3.warning(f"🛡️ **Về Fund Manager:** {format_currency(total_fees)}")
            col4.metric("📈 **Fee Rate**", f"{(total_fees/ending_nav*100):.2f}%" if ending_nav > 0 else "0%")
            
            # Additional insights
            if total_fees > 0:
                total_portfolio_value = sum(
                    self.fund_manager.get_investor_balance(inv.id, ending_nav)[0] 
                    for inv in self.fund_manager.get_regular_investors()
                )
                
                st.info(f"""
                📈 **Phân tích fee chi tiết:**
                - Fee rate: {(total_fees/ending_nav*100):.2f}% of total NAV
                - Fee vs portfolio: {(total_fees/total_portfolio_value*100):.2f}% of investor portfolio
                - Units transfer: {(total_units_transfer/sum(t.units for t in self.fund_manager.tranches)*100):.1f}% of total units
                - FM units sau fee: {sum(t.units for t in self.fund_manager.get_investor_tranches(self.fund_manager.get_fund_manager().id)) + total_units_transfer:.6f}
                """)
    
    def _render_performance_analysis(self, ending_nav: float):
        """FIXED: Render comprehensive performance analysis"""
        st.subheader("📊 Phân Tích Performance Chi Tiết")
        
        if ending_nav <= 0:
            st.warning("ℹ️ Vui lòng nhập Total NAV để xem phân tích.")
            return
        
        # Overall fund performance
        st.markdown("### 🏆 Performance Tổng Quát")
        
        total_original = sum(
            self.fund_manager.get_investor_original_investment(inv.id) 
            for inv in self.fund_manager.get_regular_investors()
        )
        total_current_value = sum(
            self.fund_manager.get_investor_balance(inv.id, ending_nav)[0]
            for inv in self.fund_manager.get_regular_investors()
        )
        total_fees_paid = sum(
            sum(t.cumulative_fees_paid for t in self.fund_manager.get_investor_tranches(inv.id))
            for inv in self.fund_manager.get_regular_investors()
        )
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Tổng Vốn Gốc", format_currency(total_original))
        col2.metric("📊 Giá Trị Hiện Tại", format_currency(total_current_value))
        col3.metric("💸 Tổng Phí Đã Trả", format_currency(total_fees_paid))
        
        gross_return = (total_current_value + total_fees_paid - total_original) / total_original if total_original > 0 else 0
        col4.metric("📈 Gross Return", format_percentage(gross_return))
        
        # Individual investor performance breakdown
        st.markdown("### 👥 Performance Từng Nhà Đầu Tư")
        
        performance_data = []
        for investor in self.fund_manager.get_regular_investors():
            lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, ending_nav)
            balance, current_profit, current_profit_perc = self.fund_manager.get_investor_balance(investor.id, ending_nav)
            
            # FIXED: Tính toán performance metrics chính xác
            original_investment = lifetime_perf['original_invested']
            current_cost_basis = self.fund_manager.get_investor_current_cost_basis(investor.id)
            
            performance_data.append({
                'Nhà Đầu Tư': investor.display_name,
                'Vốn Gốc': original_investment,
                'Cost Basis Hiện Tại': current_cost_basis,
                'Giá Trị Hiện Tại': balance,
                'Gross Profit': lifetime_perf['gross_profit'],
                'Gross Return': lifetime_perf['gross_return'],
                'Phí Đã Trả': lifetime_perf['total_fees_paid'],
                'Net Profit': lifetime_perf['net_profit'],
                'Net Return': lifetime_perf['net_return'],
                'Fee Impact': lifetime_perf['total_fees_paid'] / original_investment if original_investment > 0 else 0
            })
        
        if performance_data:
            df_performance = pd.DataFrame(performance_data)
            
            # Format currency columns
            currency_cols = ['Vốn Gốc', 'Cost Basis Hiện Tại', 'Giá Trị Hiện Tại', 'Gross Profit', 'Phí Đã Trả', 'Net Profit']
            for col in currency_cols:
                df_performance[col] = df_performance[col].apply(format_currency)
            
            # Format percentage columns
            percentage_cols = ['Gross Return', 'Net Return', 'Fee Impact']
            for col in percentage_cols:
                df_performance[col] = df_performance[col].apply(format_percentage)
            
            st.dataframe(df_performance, use_container_width=True, hide_index=True)
    
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
        st.markdown("### 🔐 Xác Nhận Áp Dụng Phí (3 bước)")
        
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
                # 1. Tạo backup trước khi thao tác
                self.fund_manager.backup_before_operation(f"Fee Application {year}")
                st.info("💾 Đã tạo backup trước khi áp dụng phí.")

                # 2. Gọi hàm logic nghiệp vụ để áp dụng phí (chỉ thay đổi trong bộ nhớ)
                # Lưu ý: Hàm này bây giờ trả về một dictionary
                ending_date_dt = datetime.combine(ending_date, datetime.min.time())
                results = self.fund_manager.apply_year_end_fees_enhanced(ending_date_dt, ending_nav)
                
                # 3. Kiểm tra kết quả và thực hiện các bước tiếp theo
                if results.get('success'):
                    # ✅✅✅ BƯỚC QUAN TRỌNG NHẤT ✅✅✅
                    # Sau khi áp dụng phí thành công, chốt HWM mới cho toàn quỹ
                    current_price = self.fund_manager.calculate_price_per_unit(ending_nav)
                    # self.fund_manager.crystallize_hwm(current_price)
                    
                    # 4. Thông báo, bật cờ và làm mới giao diện
                    st.balloons()
                    st.success(f"✅ Đã áp dụng phí thành công cho {results['investors_processed']} nhà đầu tư.")
                    
                    # Bật cờ để app.py biết cần phải lưu
                    st.session_state.data_changed = True
                    
                    # Xóa các state của checkbox để lần sau phải xác nhận lại
                    for key in ['step1', 'step2', 'step3']:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    # Yêu cầu làm mới giao diện, app.py sẽ bắt cờ và lưu dữ liệu
                    st.rerun()
                else:
                    st.error(f"❌ Áp dụng phí thất bại: {results.get('errors')}")
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
        """FIXED: Render comprehensive individual fee analysis"""
        calc_date_dt = datetime.combine(calc_date, datetime.min.time())
        details = self.fund_manager.calculate_investor_fee(investor_id, calc_date_dt, calc_nav)
        lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor_id, calc_nav)
        
        st.markdown(f"## 📊 Phân Tích Chi Tiết: {investor_name}")
        
        # FIXED: Current vs Lifetime Performance với dữ liệu chính xác
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Current Performance")
            current_cost = self.fund_manager.get_investor_current_cost_basis(investor_id)
            st.metric("💰 Vốn Đầu Tư Hiện Tại", format_currency(current_cost))
            st.metric("📊 Số Dư Hiện Tại", format_currency(details['balance']))
            profit_color = "normal" if details['profit'] >= 0 else "inverse"
            st.metric("📈 L/L vs Current Cost", format_currency(details['profit']), delta_color=profit_color)
            perc_color = "normal" if details['profit_perc'] >= 0 else "inverse"
            st.metric("📊 Tỷ Lệ L/L vs Current", format_percentage(details['profit_perc']), delta_color=perc_color)
        
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
        fee_col2.metric("🔝 HWM Value", format_currency(details['hwm_value']))
        fee_col3.metric("💎 Lợi Nhuận Vượt Ngưỡng", format_currency(details['excess_profit']))
        fee_col4.metric("💸 Phí Performance (20%)", format_currency(details['total_fee']))
        
        # Performance insights với thông tin chính xác hơn
        if details['total_fee'] > 0:
            st.success(f"🎉 Investor có performance vượt ngưỡng! Phí: {format_currency(details['total_fee'])}")
            
            # Show fee impact chi tiết
            current_fee_rate = details['total_fee'] / lifetime_perf['original_invested'] * 100 if lifetime_perf['original_invested'] > 0 else 0
            total_fees_after = lifetime_perf['total_fees_paid'] + details['total_fee']
            cumulative_fee_rate = total_fees_after / lifetime_perf['original_invested'] * 100 if lifetime_perf['original_invested'] > 0 else 0
            
            st.info(f"""
            📊 **Phân tích impact của phí:**
            - Phí này: {format_currency(details['total_fee'])} ({current_fee_rate:.1f}% của vốn gốc)
            - Tổng phí cumulative: {format_currency(total_fees_after)} ({cumulative_fee_rate:.1f}% của vốn gốc)
            - Net return sau phí: {format_percentage((lifetime_perf['current_value'] - details['total_fee'] - lifetime_perf['original_invested']) / lifetime_perf['original_invested'])}
            """)
        else:
            st.info("ℹ️ Không có phí performance (chưa vượt hurdle rate hoặc HWM)")
            
            # Show why no fee
            current_price = self.fund_manager.calculate_price_per_unit(calc_nav)
            tranches = self.fund_manager.get_investor_tranches(investor_id)
            
            if tranches:
                st.markdown("**Lý do không có phí:**")
                for i, tranche in enumerate(tranches):
                    from utils.datetime_utils import safe_days_between
                    time_delta_days = safe_days_between(calc_date_dt, tranche.entry_date)
                    if time_delta_days > 0:
                        time_delta_years = time_delta_days / 365.25
                        hurdle_price = tranche.entry_nav * ((1 + 0.06) ** time_delta_years)
                        threshold_price = max(hurdle_price, tranche.hwm)
                        
                        st.write(f"- Tranche {i+1}: Current price {format_currency(current_price)} ≤ Threshold {format_currency(threshold_price)}")
        
        # Tranches breakdown
        tranches = self.fund_manager.get_investor_tranches(investor_id)
        if tranches:
            st.markdown("---")
            st.subheader("📋 Chi Tiết Từng Tranche")
            
            tranche_data = []
            current_price = self.fund_manager.calculate_price_per_unit(calc_nav)
            
            for tranche in tranches:
                # Calculate fee for this specific tranche
                from utils.datetime_utils import safe_days_between
                time_delta_days = safe_days_between(calc_date_dt, tranche.entry_date)
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
                    'Original NAV': format_currency(tranche.original_entry_nav),
                    'Units': f"{tranche.units:.6f}",
                    'Days Held': time_delta_days,
                    'Hurdle Price': format_currency(hurdle_price),
                    'HWM': format_currency(tranche.hwm),
                    'Threshold': format_currency(threshold_price),
                    'Current Value': format_currency(tranche.units * current_price),
                    'Fees Paid': format_currency(tranche.cumulative_fees_paid),
                    'Excess Profit': format_currency(tranche_excess),
                    'New Fee': format_currency(tranche_fee)
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
        
        # Check 6: FIXED - Check for unrealistic fee amounts
        total_fees = sum(
            self.fund_manager.calculate_investor_fee(inv.id, datetime.combine(ending_date, datetime.min.time()), ending_nav)['total_fee']
            for inv in self.fund_manager.get_regular_investors()
        )
        
        if total_fees > ending_nav * 0.1:  # More than 10% of NAV
            checks['warnings'].append(f"Phí rất cao: {format_currency(total_fees)} ({total_fees/ending_nav*100:.1f}% of NAV)")
        
        checks['checks'].append(f"Fee amount check: {format_currency(total_fees)}")
        
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
        """FIXED: Hiển thị kết quả tính phí chi tiết với thông tin chính xác"""
        st.subheader("📋 Chi Tiết Tính Phí Từng Nhà Đầu Tư")
        
        if ending_nav <= 0:
            st.warning("ℹ️ Vui lòng nhập Total NAV để xem chi tiết.")
            return
            
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        results = []
        
        for investor in self.fund_manager.get_regular_investors():
            details = self.fund_manager.calculate_investor_fee(investor.id, ending_date_dt, ending_nav)
            lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, ending_nav)
            
            # FIXED: Lấy thông tin chính xác
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            total_units = sum(t.units for t in tranches) if tranches else 0
            original_investment = lifetime_perf['original_invested']
            current_cost_basis = self.fund_manager.get_investor_current_cost_basis(investor.id)
            
            results.append({
                'Nhà Đầu Tư': investor.display_name, 
                'Tổng Units': f"{total_units:.6f}",
                'Vốn Gốc': original_investment,
                'Vốn Hiện Tại': current_cost_basis,
                'Số Dư': details['balance'],
                'L/L vs Gốc': lifetime_perf['gross_profit'],
                'L/L vs Hiện Tại': details['profit'], 
                'Tỷ Lệ L/L': details['profit_perc'],
                'Hurdle Value': details['hurdle_value'], 
                'HWM Value': details['hwm_value'],
                'Lợi Nhuận Vượt': details['excess_profit'], 
                'Phí Mới': details['total_fee'],
                'Phí Đã Trả': lifetime_perf['total_fees_paid']
            })
        
        if results:
            df_results = pd.DataFrame(results)
            currency_cols = ['Vốn Gốc', 'Vốn Hiện Tại', 'Số Dư', 'L/L vs Gốc', 'L/L vs Hiện Tại', 
                           'Hurdle Value', 'HWM Value', 'Lợi Nhuận Vượt', 'Phí Mới', 'Phí Đã Trả']
            for col in currency_cols:
                df_results[col] = df_results[col].apply(format_currency)
            df_results['Tỷ Lệ L/L'] = df_results['Tỷ Lệ L/L'].apply(format_percentage)
            
            st.dataframe(df_results, use_container_width=True, hide_index=True)
            
            total_fee = sum(
                self.fund_manager.calculate_investor_fee(inv.id, ending_date_dt, ending_nav)['total_fee'] 
                for inv in self.fund_manager.get_regular_investors()
            )
            
            if total_fee > 0:
                st.success(f"💰 **Tổng phí performance:** {format_currency(total_fee)}")
                
                # Additional statistics
                eligible_investors = sum(1 for inv in self.fund_manager.get_regular_investors() 
                                       if self.fund_manager.calculate_investor_fee(inv.id, ending_date_dt, ending_nav)['total_fee'] > 0)
                
                st.info(f"""
                📊 **Thống kê phí:**
                - Số investor phải trả phí: {eligible_investors}/{len(self.fund_manager.get_regular_investors())}
                - Phí trung bình: {format_currency(total_fee / eligible_investors) if eligible_investors > 0 else 'N/A'}
                - Tỷ lệ phí/NAV: {total_fee/ending_nav*100:.2f}%
                """)
            else:
                st.info("ℹ️ Không có phí performance được tính.")
    
    def _render_tranches_detail(self, ending_nav):
        """FIXED: Hiển thị chi tiết tranches với thông tin chính xác"""
        st.subheader("📊 Chi Tiết Tất Cả Tranches")
        
        if not self.fund_manager.tranches:
            st.info("📄 Chưa có tranches nào.")
            return
        
        data = []
        current_price = self.fund_manager.calculate_price_per_unit(ending_nav) if ending_nav > 0 else 0
        
        for tranche in self.fund_manager.tranches:
            investor = self.fund_manager.get_investor_by_id(tranche.investor_id)
            investor_name = investor.display_name if investor else f"ID {tranche.investor_id}"
            
            current_value = tranche.units * current_price if current_price > 0 else 0
            
            # FIXED: Tính profit/loss chính xác
            current_cost = tranche.units * tranche.entry_nav
            original_cost = tranche.units * tranche.original_entry_nav
            current_profit_loss = current_value - current_cost
            lifetime_profit_loss = current_value - original_cost
            
            data.append({
                'Investor': investor_name,
                'Ngày Vào': tranche.entry_date.strftime("%d/%m/%Y"),
                'Entry NAV': format_currency(tranche.entry_nav),
                'Original NAV': format_currency(tranche.original_entry_nav),
                'Units': f"{tranche.units:.6f}",
                'HWM': format_currency(tranche.hwm),
                'Phí Đã Trả': format_currency(tranche.cumulative_fees_paid),
                'Vốn Hiện Tại': format_currency(current_cost),
                'Vốn Gốc': format_currency(original_cost),
                'Giá Trị Hiện Tại': format_currency(current_value),
                'L/L vs Current': format_currency(current_profit_loss),
                'L/L vs Original': format_currency(lifetime_profit_loss)
            })
        
        if data:
            df_tranches = pd.DataFrame(data)
            st.dataframe(df_tranches, use_container_width=True)
            
            # Summary statistics
            total_current_value = sum(t.units * current_price for t in self.fund_manager.tranches if current_price > 0)
            total_fees_paid = sum(t.cumulative_fees_paid for t in self.fund_manager.tranches)
            total_units = sum(t.units for t in self.fund_manager.tranches)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Tổng Giá Trị", format_currency(total_current_value))
            col2.metric("💸 Tổng Phí Đã Trả", format_currency(total_fees_paid))
            col3.metric("📊 Tổng Units", f"{total_units:.6f}")