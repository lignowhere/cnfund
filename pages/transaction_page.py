import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
try:
    from utils import format_currency, parse_currency, format_percentage, EPSILON
except ImportError:
    from data_utils import format_currency_safe as format_currency
    
    def parse_currency(text):
        if not text:
            return 0.0
        clean_text = str(text).replace('đ', '').replace(',', '').replace(' ', '')
        try:
            return float(clean_text)
        except:
            return 0.0
    
    def format_percentage(value):
        return f"{float(value) * 100:.2f}%" if value else "0%"
    
    EPSILON = 1e-6

class EnhancedTransactionPage:
    """Enhanced Transaction Page với validation & undo features"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_transaction_form(self):
        """Enhanced form thêm giao dịch với validation"""
        st.title("💸 Thêm Giao Dịch")
        
        if not self.fund_manager.investors:
            st.warning("⚠️ Chưa có nhà đầu tư nào. Hãy thêm nhà đầu tư trước.")
            return
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        if not latest_nav and not self.fund_manager.transactions:
            st.info("🆕 Quỹ mới, hãy bắt đầu bằng giao dịch Nạp tiền.")
        
        # Show current NAV and validation warnings
        self._render_current_status(latest_nav)
        
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
            
            # Ngày giao dịch với validation
            trans_date = st.date_input(
                "📅 Ngày Giao Dịch", 
                value=date.today(),
                max_value=date.today(),
                help="Không được chọn ngày tương lai"
            )
            
            # Số tiền với smart defaults
            default_amount = self._get_smart_default_amount(investor_id, trans_type)
            amount_input = st.text_input(
                "💰 Số Tiền", 
                value=default_amount,
                help="Nhập số tiền giao dịch",
                key="transaction_amount_input"
            )
            amount = parse_currency(amount_input)
            
            # Real-time validation display
            validation_results = self._validate_transaction_inputs(
                investor_id, trans_type, amount, trans_date, latest_nav
            )
            self._display_validation_results(validation_results)
            
            # Total NAV calculation
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
                    help="Nhập Total NAV sau khi thực hiện giao dịch",
                    key="transaction_nav_input"
                )
                total_nav = parse_currency(nav_input)
            
            # NAV change validation
            if latest_nav and total_nav > 0:
                nav_change_pct = abs(total_nav - latest_nav) / latest_nav * 100
                if nav_change_pct > 10:
                    st.warning(f"⚠️ NAV thay đổi {nav_change_pct:.1f}% - Kiểm tra lại!")
            
            submitted = st.form_submit_button(
                "✅ Thực hiện giao dịch", 
                use_container_width=True,
                disabled=not validation_results.get('valid', False)
            )
            
            if submitted:
                if validation_results.get('valid', False):
                    success = self._process_validated_transaction(
                        investor_id, trans_type, amount, total_nav, trans_date
                    )
                    if success:
                        st.balloons()
                        st.rerun()
                else:
                    st.error("❌ Vui lòng sửa các lỗi validation trước khi tiếp tục")
        
        # === PHẦN HOÀN TÁC Ở CUỐI TRANG ===
        st.markdown("---")
        self._render_undo_section()
    
    def render_nav_update(self):
        """Enhanced NAV update với validation"""
        st.title("📈 Cập Nhật Total NAV")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        
        if latest_nav:
            st.info(f"📊 Total NAV hiện tại: {format_currency(latest_nav)}")
        
        with st.form("nav_form"):
            trans_date = st.date_input(
                "📅 Ngày", 
                value=date.today(),
                max_value=date.today()
            )
            
            default_nav = format_currency(latest_nav) if latest_nav else "0đ"
            nav_input = st.text_input(
                "📊 Total NAV mới", 
                value=default_nav,
                help="Nhập Total NAV mới của quỹ",
                key="nav_update_input"
            )
            total_nav = parse_currency(nav_input)
            
            # NAV change validation
            if latest_nav and total_nav > 0:
                change_amount = total_nav - latest_nav
                change_pct = change_amount / latest_nav * 100
                
                col1, col2 = st.columns(2)
                col1.metric("Thay đổi", format_currency(change_amount))
                col2.metric("Tỷ lệ thay đổi", f"{change_pct:.2f}%")
                
                if abs(change_pct) > 15:
                    st.warning(f"⚠️ NAV thay đổi {abs(change_pct):.1f}% - Rất lớn!")
                elif abs(change_pct) > 5:
                    st.info(f"ℹ️ NAV thay đổi {abs(change_pct):.1f}%")
            
            submitted = st.form_submit_button("✅ Cập nhật NAV", use_container_width=True)
            
            if submitted:
                if total_nav <= 0:
                    st.error("❌ Total NAV phải lớn hơn 0")
                else:
                    # Confirmation for large changes
                    if latest_nav and abs((total_nav - latest_nav) / latest_nav) > 0.1:
                        if not st.session_state.get('nav_large_change_confirmed', False):
                            st.warning("⚠️ Thay đổi NAV lớn! Xác nhận bằng cách tick checkbox dưới:")
                            if st.checkbox("✅ Tôi xác nhận thay đổi NAV này đúng"):
                                st.session_state.nav_large_change_confirmed = True
                                st.rerun()
                            return
                    
                    trans_date_dt = datetime.combine(trans_date, datetime.min.time())
                    success, message = self.fund_manager.process_nav_update(total_nav, trans_date_dt)
                    
                    if success:
                        st.success(message)
                        st.session_state.data_changed = True
                        if 'nav_large_change_confirmed' in st.session_state:
                            del st.session_state.nav_large_change_confirmed
                        st.rerun()
                    else:
                        st.error(message)
    
    def render_fund_manager_withdrawal(self):
        """Fund Manager Withdrawal với enhanced safety"""
        st.title("🛒 Fund Manager Withdrawal")
        
        fund_manager = self.fund_manager.get_fund_manager()
        if not fund_manager:
            st.error("❌ Fund Manager not found")
            return
        
        # Show Fund Manager status
        fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
        if not fm_tranches:
            st.info("📄 Fund Manager chưa có units để rút")
            return
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        if not latest_nav:
            st.error("❌ Chưa có NAV để tính giá trị")
            return
        
        # Calculate Fund Manager balance
        fm_units = sum(t.units for t in fm_tranches)
        current_price = self.fund_manager.calculate_price_per_unit(latest_nav)
        fm_balance = fm_units * current_price
        
        # Display current status
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total Units", f"{fm_units:.6f}")
        col2.metric("💰 Total Value", format_currency(fm_balance))
        col3.metric("📈 Current Price", format_currency(current_price))
        
        # Show earning history
        with st.expander("💰 Fee Income History"):
            fee_transactions = [t for t in self.fund_manager.transactions 
                              if t.investor_id == fund_manager.id and t.type == 'Phí Nhận']
            
            if fee_transactions:
                fee_data = []
                for trans in fee_transactions:
                    fee_data.append({
                        'Ngày': trans.date.strftime("%d/%m/%Y"),
                        'Số Tiền': format_currency(trans.amount),
                        'Units Nhận': f"{trans.units_change:.6f}"
                    })
                
                st.dataframe(pd.DataFrame(fee_data), use_container_width=True)
                
                total_fee_income = sum(t.amount for t in fee_transactions)
                st.success(f"💰 **Tổng Fee Income:** {format_currency(total_fee_income)}")
            else:
                st.info("📄 Chưa có fee income")
        
        # Withdrawal form với enhanced validation
        st.markdown("---")
        st.subheader("💸 Fund Manager Withdrawal")
        
        with st.form("fm_withdrawal_form"):
            col1, col2 = st.columns(2)
            
            withdrawal_date = col1.date_input("📅 Ngày Rút", value=date.today())
            
            # Withdrawal options
            withdrawal_type = col2.selectbox(
                "📝 Loại Rút",
                ["Rút một phần", "Rút toàn bộ"]
            )
            
            if withdrawal_type == "Rút một phần":
                # Provide suggested amounts
                suggested_amounts = [
                    fm_balance * 0.1,  # 10%
                    fm_balance * 0.25, # 25%
                    fm_balance * 0.5,  # 50%
                ]
                
                col_sug1, col_sug2, col_sug3 = st.columns(3)
                with col_sug1:
                    if st.form_submit_button(f"10% ({format_currency(suggested_amounts[0])})"):
                        st.session_state.fm_withdrawal_amount = suggested_amounts[0]
                with col_sug2:
                    if st.form_submit_button(f"25% ({format_currency(suggested_amounts[1])})"):
                        st.session_state.fm_withdrawal_amount = suggested_amounts[1]
                with col_sug3:
                    if st.form_submit_button(f"50% ({format_currency(suggested_amounts[2])})"):
                        st.session_state.fm_withdrawal_amount = suggested_amounts[2]
                
                default_amount = format_currency(st.session_state.get('fm_withdrawal_amount', 0))
                amount_input = st.text_input(
                    "💰 Số Tiền Rút", 
                    value=default_amount,
                    help="Nhập số tiền muốn rút",
                    key="fm_withdrawal_amount_input"
                )
                withdrawal_amount = parse_currency(amount_input)
                
                if withdrawal_amount > fm_balance:
                    st.error(f"❌ Số tiền rút ({format_currency(withdrawal_amount)}) > Balance ({format_currency(fm_balance)})")
                    withdrawal_amount = 0
                
            else:  # Rút toàn bộ
                withdrawal_amount = fm_balance
                st.info(f"💰 Rút toàn bộ: {format_currency(withdrawal_amount)}")
            
            # Calculate units to be removed
            if withdrawal_amount > 0:
                units_to_remove = withdrawal_amount / current_price
                remaining_units = fm_units - units_to_remove
                remaining_value = remaining_units * current_price
                
                st.markdown("---")
                st.subheader("📋 Preview Withdrawal")
                
                preview_col1, preview_col2 = st.columns(2)
                preview_col1.metric("Units Rút", f"{units_to_remove:.6f}")
                preview_col1.metric("Số Tiền", format_currency(withdrawal_amount))
                
                preview_col2.metric("Units Còn Lại", f"{remaining_units:.6f}")
                preview_col2.metric("Giá Trị Còn Lại", format_currency(remaining_value))
            
            # NAV after withdrawal
            st.markdown("---")
            st.subheader("📊 NAV Sau Withdrawal")
            
            nav_after_withdrawal = latest_nav - withdrawal_amount
            st.info(f"📊 NAV sau withdrawal: {format_currency(latest_nav)} - {format_currency(withdrawal_amount)} = **{format_currency(nav_after_withdrawal)}**")
            
            # Confirmation checkbox
            confirmed = st.checkbox("✅ Tôi xác nhận Fund Manager withdrawal này đúng")
            
            submitted = st.form_submit_button(
                "💸 Xác Nhận Fund Manager Withdrawal", 
                use_container_width=True,
                disabled=not confirmed or withdrawal_amount <= 0
            )
            
            if submitted and withdrawal_amount > 0 and confirmed:
                success = self._process_fund_manager_withdrawal(
                    withdrawal_amount, nav_after_withdrawal, withdrawal_date
                )
                
                if success:
                    st.success(f"✅ Fund Manager đã rút {format_currency(withdrawal_amount)}")
                    st.session_state.data_changed = True
                    st.rerun()
    
    def render_transaction_management(self):
        """Render trang quản lý giao dịch"""
        st.title("🔧 Quản Lý Giao Dịch")
        
        if not hasattr(self.fund_manager, 'transactions') or not self.fund_manager.transactions:
            st.info("ℹ️ Chưa có giao dịch nào.")
            return
        
        # Hiển thị danh sách giao dịch
        st.subheader("📋 Danh Sách Giao Dịch")
        
        # Tạo DataFrame để hiển thị
        transactions_data = []
        for trans in sorted(self.fund_manager.transactions, key=lambda x: x.date, reverse=True):
            investor = next((inv for inv in self.fund_manager.investors if inv.id == trans.investor_id), None)
            
            transactions_data.append({
                "ID": trans.id,
                "Nhà Đầu Tư": investor.name if investor else "Unknown",
                "Loại": trans.type,
                "Số Tiền": format_currency(trans.amount),
                "Ngày": trans.date.strftime("%d/%m/%Y %H:%M"),
                "NAV": format_currency(trans.nav),
                "Units Change": f"{trans.units_change:.6f}"
            })
        
        if transactions_data:
            df = pd.DataFrame(transactions_data)
            st.dataframe(df, use_container_width=True)
            
            # Export to Excel
            if st.button("📊 Xuất Excel"):
                try:
                    # Create buffer for Excel file
                    import io
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df.to_excel(writer, sheet_name='Transactions', index=False)
                    
                    buffer.seek(0)
                    
                    st.download_button(
                        label="💾 Tải File Excel",
                        data=buffer,
                        file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"❌ Lỗi xuất Excel: {str(e)}")
        
        # Summary statistics
        st.subheader("📊 Thống Kê Giao Dịch")
        
        total_deposits = sum(t.amount for t in self.fund_manager.transactions if t.type == 'Nạp')
        total_withdrawals = abs(sum(t.amount for t in self.fund_manager.transactions if t.type == 'Rút'))
        total_fees = abs(sum(t.amount for t in self.fund_manager.transactions if t.type == 'Phí'))
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Tổng Nạp", format_currency(total_deposits))
        col2.metric("💸 Tổng Rút", format_currency(total_withdrawals))
        col3.metric("🧮 Tổng Phí", format_currency(total_fees))
        
        # Form xóa giao dịch (nếu cần)
        st.subheader("🗑️ Xóa Giao Dịch")
        st.warning("⚠️ Chức năng này cần được thực hiện cẩn thận")
        
        if st.checkbox("Hiển thị form xóa giao dịch"):
            transaction_ids = [trans.id for trans in self.fund_manager.transactions]
            if transaction_ids:
                selected_id = st.selectbox("Chọn ID giao dịch cần xóa", transaction_ids)
                
                if st.button("🗑️ Xóa Giao Dịch", type="secondary"):
                    if st.session_state.get('confirm_delete'):
                        try:
                            success = self.fund_manager.delete_transaction(selected_id)
                            if success:
                                st.success("✅ Đã xóa giao dịch!")
                                st.session_state.data_changed = True
                                st.rerun()
                            else:
                                st.error("❌ Không thể xóa giao dịch")
                        except Exception as e:
                            st.error(f"❌ Lỗi: {str(e)}")
                    else:
                        st.session_state.confirm_delete = True
                        st.warning("⚠️ Nhấn lại để xác nhận xóa")
    
    def _render_undo_section(self):
        """Render undo section for recent transactions"""
        st.subheader("🔄 Hoàn Tác Giao Dịch")
        
        recent_transactions = sorted(
            self.fund_manager.transactions, 
            key=lambda x: x.date, 
            reverse=True
        )[:3]  # Show last 3 transactions
        
        if not recent_transactions:
            st.info("📄 Chưa có giao dịch nào để hoàn tác")
            return
        
        st.write("**Giao dịch gần nhất:**")
        for i, trans in enumerate(recent_transactions):
            investor = self.fund_manager.get_investor_by_id(trans.investor_id)
            investor_name = investor.display_name if investor else f"ID {trans.investor_id}"
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{trans.date.strftime('%d/%m/%Y %H:%M')}** - {investor_name}")
                st.write(f"{trans.type}: {format_currency(trans.amount)}")
            
            with col2:
                st.write(f"NAV: {format_currency(trans.nav)}")
                st.write(f"Units: {trans.units_change:.6f}")
            
            with col3:
                if st.button(f"🔄 Undo", key=f"undo_{trans.id}"):
                    if self._confirm_undo_transaction(trans):
                        success = self.fund_manager.undo_last_transaction(trans.id)
                        if success:
                            st.success("✅ Đã hoàn tác giao dịch")
                            st.session_state.data_changed = True
                            st.rerun()
                        else:
                            st.error("❌ Không thể hoàn tác giao dịch này")
    
    def _render_current_status(self, latest_nav):
        """Render current fund status"""
        if latest_nav:
            col1, col2, col3 = st.columns(3)
            
            total_units = sum(t.units for t in self.fund_manager.tranches)
            price_per_unit = self.fund_manager.calculate_price_per_unit(latest_nav)
            regular_investors = len(self.fund_manager.get_regular_investors())
            
            col1.metric("Total NAV", format_currency(latest_nav))
            col2.metric("Price/Unit", format_currency(price_per_unit))
            col3.metric("Investors", regular_investors)
    
    def _get_smart_default_amount(self, investor_id, trans_type):
        """Get smart default amount based on history"""
        if not investor_id:
            return "0đ"
        
        # Get recent transactions for this investor
        investor_transactions = [
            t for t in self.fund_manager.transactions 
            if t.investor_id == investor_id and t.type == trans_type
        ]
        
        if investor_transactions:
            # Use most recent transaction amount
            recent_trans = max(investor_transactions, key=lambda x: x.date)
            return format_currency(abs(recent_trans.amount))
        
        return "0đ"
    
    def _validate_transaction_inputs(self, investor_id, trans_type, amount, trans_date, latest_nav):
        """Comprehensive validation for transaction inputs"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Basic validation
        if not investor_id:
            results['errors'].append("Chưa chọn nhà đầu tư")
            results['valid'] = False
        
        if amount <= 0:
            results['errors'].append("Số tiền phải lớn hơn 0")
            results['valid'] = False
        
        if trans_date > date.today():
            results['errors'].append("Không được chọn ngày tương lai")
            results['valid'] = False
        
        # Business logic validation
        if investor_id and trans_type == "Rút":
            investor_tranches = self.fund_manager.get_investor_tranches(investor_id)
            if not investor_tranches:
                results['errors'].append("Nhà đầu tư chưa có vốn để rút")
                results['valid'] = False
            elif latest_nav:
                balance, _, _ = self.fund_manager.get_investor_balance(investor_id, latest_nav)
                if amount > balance * 1.01:  # Allow 1% tolerance
                    results['errors'].append(f"Số tiền rút vượt quá balance: {format_currency(balance)}")
                    results['valid'] = False
                elif amount > balance * 0.9:
                    results['warnings'].append("Rút gần hết vốn - kiểm tra lại")
        
        # Amount size validation
        if amount > 50_000_000:  # 50M VND
            results['warnings'].append("Giao dịch lớn - kiểm tra kỹ")
        
        # Date validation
        if trans_date < date.today() - timedelta(days=30):
            results['warnings'].append("Giao dịch cũ hơn 30 ngày")
        
        return results
    
    def _display_validation_results(self, results):
        """Display validation results to user"""
        if results['errors']:
            for error in results['errors']:
                st.error(f"❌ {error}")
        
        if results['warnings']:
            for warning in results['warnings']:
                st.warning(f"⚠️ {warning}")
        
        if results['valid'] and not results['warnings']:
            st.success("✅ Dữ liệu hợp lệ")
    
    def _process_validated_transaction(self, investor_id, trans_type, amount, total_nav, trans_date):
        """Process transaction after validation"""
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
            st.success(f"✅ {message}")
            st.session_state.data_changed = True
            return True
        else:
            st.error(f"❌ {message}")
            return False
    
    def _confirm_undo_transaction(self, transaction):
        """Confirm undo transaction"""
        return st.checkbox(
            f"✅ Xác nhận hoàn tác: {transaction.type} {format_currency(transaction.amount)}",
            key=f"confirm_undo_{transaction.id}"
        )
    
    def _process_fund_manager_withdrawal(self, amount, nav_after, withdrawal_date):
        """Process Fund Manager withdrawal với enhanced safety"""
        try:
            fund_manager = self.fund_manager.get_fund_manager()
            if not fund_manager:
                st.error("❌ Fund Manager not found")
                return False
            
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            if not fm_tranches:
                st.error("❌ Fund Manager has no units")
                return False
            
            current_price = self.fund_manager.calculate_price_per_unit(nav_after + amount)
            units_to_remove = amount / current_price
            total_fm_units = sum(t.units for t in fm_tranches)
            
            if units_to_remove > total_fm_units:
                st.error("❌ Insufficient units for withdrawal")
                return False
            
            withdrawal_date_dt = datetime.combine(withdrawal_date, datetime.min.time())
            
            # Remove units proportionally from tranches
            removal_ratio = units_to_remove / total_fm_units
            
            for tranche in fm_tranches:
                if tranche.investor_id == fund_manager.id:
                    tranche.units *= (1 - removal_ratio)
            
            # Clean up zero tranches
            self.fund_manager.tranches = [t for t in self.fund_manager.tranches if t.units >= EPSILON]
            
            # Add withdrawal transaction for Fund Manager
            self.fund_manager._add_transaction(
                fund_manager.id, 
                withdrawal_date_dt, 
                'Fund Manager Withdrawal', 
                -amount, 
                nav_after, 
                -units_to_remove
            )
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error processing Fund Manager withdrawal: {str(e)}")
            return False