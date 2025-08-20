import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from utils import format_currency, parse_currency, format_percentage, EPSILON

class TransactionPage:
    """Page xử lý giao dịch với enhanced features"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
    
    def render_transaction_form(self):
        """Form thêm giao dịch (original)"""
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
            amount_input = st.text_input("💰 Số Tiền", value="0đ", 
                                       help="Nhập số tiền giao dịch",
                                       key="transaction_amount_input")
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
                    help="Nhập Total NAV sau khi thực hiện giao dịch",
                    key="transaction_nav_input"
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
        """Form cập nhật NAV (original)"""
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
                help="Nhập Total NAV mới của quỹ",
                key="nav_update_input"
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
    
    # NEW METHODS
    
    def render_fund_manager_withdrawal(self):
        """Fund Manager Withdrawal"""
        st.title("🏛️ Fund Manager Withdrawal")
        
        fund_manager = self.fund_manager.get_fund_manager()
        if not fund_manager:
            st.error("❌ Fund Manager not found")
            return
        
        # Show Fund Manager status
        fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
        if not fm_tranches:
            st.info("📝 Fund Manager chưa có units để rút")
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
                st.info("📝 Chưa có fee income")
        
        # Withdrawal form
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
                amount_input = st.text_input(
                    "💰 Số Tiền Rút", 
                    value="0đ",
                    help="Nhập số tiền muốn rút",
                    key="fm_withdrawal_amount"
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
                st.subheader("🔍 Preview Withdrawal")
                
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
            
            submitted = st.form_submit_button("💸 Xác Nhận Fund Manager Withdrawal", use_container_width=True)
            
            if submitted and withdrawal_amount > 0:
                success = self._process_fund_manager_withdrawal(
                    withdrawal_amount, nav_after_withdrawal, withdrawal_date
                )
                
                if success:
                    st.success(f"✅ Fund Manager đã rút {format_currency(withdrawal_amount)}")
                    st.session_state.data_changed = True
                    st.rerun()
    
    def render_transaction_management(self):
        """Transaction Management Center"""
        st.title("🔧 Quản Lý Giao Dịch")
        
        if not self.fund_manager.transactions:
            st.info("📝 Chưa có giao dịch nào để quản lý")
            return
        
        st.warning("⚠️ **Cảnh báo:** Sửa/xóa giao dịch có thể ảnh hưởng đến tính toán phí và báo cáo. Hãy cẩn thận!")
        
        tab1, tab2, tab3 = st.tabs(["📋 Danh Sách Giao Dịch", "✏️ Sửa Giao Dịch", "🗑️ Xóa Giao Dịch"])
        
        with tab1:
            self._render_transaction_list()
        
        with tab2:
            self._render_edit_transaction()
        
        with tab3:
            self._render_delete_transaction()
    
    # HELPER METHODS
    
    def _process_fund_manager_withdrawal(self, amount: float, nav_after: float, withdrawal_date):
        """Process Fund Manager withdrawal - NO FEES"""
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
            
            # Add withdrawal transaction for Fund Manager (NO FEES)
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
    
    def _render_transaction_list(self):
        """Hiển thị danh sách giao dịch"""
        st.subheader("📋 Danh Sách Giao Dịch")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        # Transaction type filter
        all_types = list(set(t.type for t in self.fund_manager.transactions))
        selected_types = col1.multiselect("📝 Lọc theo loại", all_types, default=all_types, key="tx_type_filter")
        
        # Investor filter
        investor_options = self.fund_manager.get_all_investor_options()  # Include Fund Manager
        selected_investors = col2.multiselect("👤 Lọc theo investor", list(investor_options.keys()), key="tx_investor_filter")
        
        # Date range
        from_date = col3.date_input("📅 Từ ngày", value=date.today() - timedelta(days=30), key="tx_from_date")
        to_date = col3.date_input("📅 Đến ngày", value=date.today(), key="tx_to_date")
        
        # Filter transactions
        filtered_transactions = []
        selected_investor_ids = [investor_options[name] for name in selected_investors] if selected_investors else None
        
        for trans in self.fund_manager.transactions:
            # Type filter
            if trans.type not in selected_types:
                continue
            
            # Investor filter
            if selected_investor_ids and trans.investor_id not in selected_investor_ids:
                continue
            
            # Date filter
            trans_date = trans.date.date()
            if trans_date < from_date or trans_date > to_date:
                continue
            
            filtered_transactions.append(trans)
        
        # Display transactions
        if filtered_transactions:
            data = []
            for trans in sorted(filtered_transactions, key=lambda x: x.date, reverse=True):
                investor = self.fund_manager.get_investor_by_id(trans.investor_id)
                investor_name = investor.display_name if investor else f"ID {trans.investor_id}"
                
                data.append({
                    'ID': trans.id,
                    'Ngày': trans.date.strftime("%d/%m/%Y %H:%M"),
                    'Investor': investor_name,
                    'Loại': trans.type,
                    'Số Tiền': format_currency(trans.amount),
                    'NAV': format_currency(trans.nav),
                    'Units Change': f"{trans.units_change:.6f}"
                })
            
            df_trans = pd.DataFrame(data)
            st.dataframe(df_trans, use_container_width=True)
            st.success(f"📊 Hiển thị {len(filtered_transactions)} giao dịch")
        else:
            st.info("📝 Không có giao dịch nào thỏa mãn bộ lọc")
    
    def _render_edit_transaction(self):
        """Sửa giao dịch - Basic implementation"""
        st.subheader("✏️ Sửa Giao Dịch")
        st.info("🚧 Tính năng này đang được phát triển. Hiện tại hãy sử dụng 'Xóa' và tạo lại giao dịch mới.")
    
    def _render_delete_transaction(self):
        """Xóa giao dịch"""
        st.subheader("🗑️ Xóa Giao Dịch")
        
        # Warning
        st.error("🚨 **NGUY HIỂM:** Xóa giao dịch có thể làm mất dữ liệu và ảnh hưởng nghiêm trọng đến tính toán!")
        
        # Select transaction to delete
        transaction_options = {}
        recent_transactions = sorted(self.fund_manager.transactions, key=lambda x: x.date, reverse=True)[:20]  # Show recent 20
        
        for trans in recent_transactions:
            investor = self.fund_manager.get_investor_by_id(trans.investor_id)
            investor_name = investor.display_name if investor else f"ID {trans.investor_id}"
            
            display_name = f"ID {trans.id} - {trans.date.strftime('%d/%m/%Y')} - {investor_name} - {trans.type} - {format_currency(trans.amount)}"
            transaction_options[display_name] = trans.id
        
        if not transaction_options:
            st.info("📝 Không có giao dịch nào để xóa")
            return
        
        selected_trans_display = st.selectbox("🔍 Chọn giao dịch cần xóa (20 gần nhất)", list(transaction_options.keys()), key="delete_trans_select")
        
        if selected_trans_display:
            trans_id = transaction_options[selected_trans_display]
            transaction = next((t for t in self.fund_manager.transactions if t.id == trans_id), None)
            
            if transaction:
                # Show transaction details
                st.markdown("---")
                st.subheader("🔍 Giao Dịch Sẽ Bị Xóa")
                
                col1, col2 = st.columns(2)
                col1.write(f"**ID:** {transaction.id}")
                col1.write(f"**Ngày:** {transaction.date.strftime('%d/%m/%Y %H:%M')}")
                col1.write(f"**Loại:** {transaction.type}")
                
                col2.write(f"**Số tiền:** {format_currency(transaction.amount)}")
                col2.write(f"**NAV:** {format_currency(transaction.nav)}")
                col2.write(f"**Units change:** {transaction.units_change:.6f}")
                
                # Confirmation
                st.markdown("---")
                confirm_delete = st.checkbox("✅ Tôi hiểu rủi ro và muốn xóa giao dịch này", key="confirm_delete")
                
                if confirm_delete:
                    if st.button("🗑️ XÓA GIAO DỊCH", type="primary", use_container_width=True):
                        success = self._delete_transaction(transaction.id)
                        if success:
                            st.success("✅ Đã xóa giao dịch")
                            st.session_state.data_changed = True
                            st.rerun()
    
    def _delete_transaction(self, trans_id: int) -> bool:
        """Delete transaction"""
        try:
            # Find and remove transaction
            original_count = len(self.fund_manager.transactions)
            self.fund_manager.transactions = [t for t in self.fund_manager.transactions if t.id != trans_id]
            
            if len(self.fund_manager.transactions) == original_count:
                st.error("❌ Không tìm thấy giao dịch để xóa")
                return False
            
            st.warning("⚠️ Lưu ý: Có thể cần rebuild tranches manually nếu xóa giao dịch Nạp/Rút")
            return True
            
        except Exception as e:
            st.error(f"❌ Lỗi xóa giao dịch: {str(e)}")
            return False