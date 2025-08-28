from copy import copy
import uuid
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Any
import streamlit as st
from config import *
from models import Investor, Tranche, Transaction, FeeRecord

from utils import *
from concurrent.futures import ThreadPoolExecutor

class EnhancedFundManager:
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.investors: List[Investor] = []
        self.tranches: List[Tranche] = []
        self.transactions: List[Transaction] = []
        self.fee_records: List[FeeRecord] = []
        # self.load_data()
        # self._ensure_fund_manager_exists()

    # ================================
    # Load / Save
    # ================================
    def load_data(self):
        if not (self.data_handler and getattr(self.data_handler, "connected", False)):
            print("ERROR: Cannot load data: No database connection.")
            return
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.investors = executor.submit(self.data_handler.load_investors).result()
            self.tranches = executor.submit(self.data_handler.load_tranches).result()
            self.transactions = executor.submit(self.data_handler.load_transactions).result()
            self.fee_records = executor.submit(self.data_handler.load_fee_records).result()

    def save_data(self) -> bool:
        return self.data_handler.save_all_data_enhanced(
            self.investors, self.tranches, self.transactions, self.fee_records
        )

    # ================================
    # Bootstrap / Lookups
    # ================================
    def _ensure_fund_manager_exists(self):
        if not any(inv.is_fund_manager for inv in self.investors):
            fund_manager = Investor(
                id=0, name="Fund Manager", is_fund_manager=True, join_date=date.today()
            )
            self.investors.insert(0, fund_manager)

    def get_fund_manager(self) -> Optional[Investor]:
        return next((inv for inv in self.investors if inv.is_fund_manager), None)

    def get_regular_investors(self) -> List[Investor]:
        return [inv for inv in self.investors if not inv.is_fund_manager]

    def get_investor_options(self) -> Dict[str, int]:
        return {inv.display_name: inv.id for inv in self.get_regular_investors()}

    def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        return next((inv for inv in self.investors if inv.id == investor_id), None)

    # ================================
    # Investor CRUD
    # ================================
    def add_investor(
        self, name: str, phone: str = "", address: str = "", email: str = ""
    ) -> Tuple[bool, str]:
        if not name.strip():
            return False, "Tên không được để trống"

        existing_names = [inv.name.lower().strip() for inv in self.investors]
        if name.lower().strip() in existing_names:
            return False, f"Nhà đầu tư '{name}' đã tồn tại"

        if phone and not validate_phone(phone):
            return False, "SĐT không hợp lệ"
        if email and not validate_email(email):
            return False, "Email không hợp lệ"

        # ID=0 dành cho Fund Manager
        existing_ids = [inv.id for inv in self.investors]
        new_id = 1
        while new_id in existing_ids:
            new_id += 1

        investor = Investor(
            id=new_id,
            name=name.strip(),
            phone=phone.strip(),
            address=address.strip(),
            email=email.strip(),
            is_fund_manager=False,
        )
        self.investors.append(investor)
        return True, f"Đã thêm {investor.display_name}"

    # ================================
    # Portfolio helpers (per investor)
    # ================================
    def get_investor_tranches(self, investor_id: int) -> List[Tranche]:
        return [t for t in self.tranches if t.investor_id == investor_id]

    def get_investor_units(self, investor_id: int) -> float:
        return sum(t.units for t in self.get_investor_tranches(investor_id))

    def get_investor_original_investment(self, investor_id: int) -> float:
        tranches = self.get_investor_tranches(investor_id)
        return sum(getattr(t, "original_invested_value", t.units * t.entry_nav) for t in tranches)

    def get_investor_current_investment(self, investor_id: int) -> float:
        tranches = self.get_investor_tranches(investor_id)
        total = 0.0
        for t in tranches:
            if hasattr(t, "invested_value"):
                total += float(t.invested_value)
            else:
                total += float(t.units * t.entry_nav)
        return total

    def get_investor_fees_paid(self, investor_id: int) -> float:
        return sum(getattr(t, "cumulative_fees_paid", 0.0) for t in self.get_investor_tranches(investor_id))

    def get_investor_balance(self, investor_id: int, total_nav: float) -> Tuple[float, float, float]:
        tranches = self.get_investor_tranches(investor_id)
        if not tranches or total_nav <= 0:
            return 0.0, 0.0, 0.0
        price_per_unit = self.calculate_price_per_unit(total_nav)
        balance = sum(t.units for t in tranches) * price_per_unit
        invested_value = sum(getattr(t, "invested_value", t.units * t.entry_nav) for t in tranches)
        profit = balance - invested_value
        profit_perc = (profit / invested_value) if invested_value > 0 else 0.0
        return balance, profit, profit_perc

    def get_investor_profit(self, investor_id: int, total_nav: float) -> float:
        balance, profit, _ = self.get_investor_balance(investor_id, total_nav)
        return profit

    def get_investor_current_cost_basis(self, investor_id: int) -> float:
        try:
            tranches = self.get_investor_tranches(investor_id)
            if not tranches:
                return 0.0
            total_cost_basis = 0.0
            for tranche in tranches:
                if hasattr(tranche, "invested_value"):
                    total_cost_basis += tranche.invested_value
                else:
                    total_cost_basis += tranche.units * tranche.entry_nav
            return total_cost_basis
        except Exception as e:
            print(f"Error calculating cost basis for investor {investor_id}: {e}")
            return 0.0

    # ================================
    # NAV helpers
    # ================================
    def calculate_price_per_unit(self, total_nav: float) -> float:
        if not self.tranches or total_nav <= 0:
            return DEFAULT_UNIT_PRICE
        total_units = sum(t.units for t in self.tranches)
        return (total_nav / total_units) if total_units > EPSILON else DEFAULT_UNIT_PRICE

    def get_latest_total_nav(self) -> Optional[float]:
        if not self.transactions:
            return None
        nav_transactions = [t for t in self.transactions if (t.nav is not None and t.nav > 0)]
        if not nav_transactions:
            return None
        sorted_transactions = sorted(nav_transactions, key=lambda x: (x.date, x.id), reverse=True)
        return sorted_transactions[0].nav

    # ================================
    # Transactions
    # ================================
    def _get_next_transaction_id(self) -> int:
        return max([t.id for t in self.transactions] or [0]) + 1

    def _add_transaction(
        self, investor_id: int, date: datetime, type: str, amount: float, nav: float, units_change: float
    ):
        self.transactions.append(
            Transaction(
                id=self._get_next_transaction_id(),
                investor_id=investor_id,
                date=date,
                type=type,
                amount=amount,
                nav=nav,
                units_change=units_change,
            )
        )

    def process_deposit(
        self, investor_id: int, amount: float, total_nav_after: float, trans_date: datetime
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Số tiền phải lớn hơn 0"
        old_total_nav = self.get_latest_total_nav() or 0
        price = self.calculate_price_per_unit(old_total_nav) if old_total_nav > 0 else DEFAULT_UNIT_PRICE
        units = amount / price

        tranche = Tranche(
            investor_id=investor_id,
            tranche_id=str(uuid.uuid4()),
            entry_date=trans_date,
            entry_nav=price,
            units=units,
            hwm=price,
            original_entry_date=trans_date,
            original_entry_nav=price,
            original_invested_value=amount,  # set nguồn vốn gốc
            cumulative_fees_paid=0.0,
        )
        # cập nhật invested_value hiện tại
        tranche.invested_value = tranche.units * tranche.entry_nav

        self.tranches.append(tranche)
        self._add_transaction(investor_id, trans_date, "Nạp", amount, total_nav_after, units)
        return True, f"Đã nạp {format_currency(amount)}"

    def _process_unit_reduction_fixed(self, investor_id: int, units_to_remove: float, is_full: bool):
        """
        Giảm units khi rút: full thì xóa hết, partial thì giảm theo tỷ lệ, giữ nguyên original_*.
        """
        if is_full:
            self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
        else:
            tranches = self.get_investor_tranches(investor_id)
            total_units = sum(t.units for t in tranches)
            if total_units > 0:
                reduction_ratio = units_to_remove / total_units
                for tranche in tranches:
                    if tranche.investor_id == investor_id:
                        tranche.units *= (1 - reduction_ratio)
                        tranche.invested_value = tranche.units * tranche.entry_nav
            self.tranches = [t for t in self.tranches if t.units >= EPSILON]
        return True

    def process_withdrawal(
        self, investor_id: int, net_amount: float, total_nav_after: float, trans_date: datetime
    ) -> Tuple[bool, str]:
        """
        Xử lý rút tiền (Net -> Gross):
        - Tính performance fee tương ứng (tỉ lệ rút so với toàn bộ balance)
        - Áp fee (giảm units & tạo FeeRecord + transaction 'Phí' cho investor)
        - Trừ units cho phần rút (tạo transaction 'Rút' chỉ cho phần net)
        - Chuyển fee units cho Fund Manager (tạo transaction 'Phí Nhận' + tranche cho FM)
        """

        # NAV & price trước khi rút
        old_total_nav = self.get_latest_total_nav() or 0
        if old_total_nav <= 0:
            return False, "Không có NAV để thực hiện giao dịch."
        current_price = self.calculate_price_per_unit(old_total_nav)

        tranches = self.get_investor_tranches(investor_id)
        if not tranches:
            return False, "Nhà đầu tư không có vốn."
        balance = sum(t.units for t in tranches) * current_price
        if net_amount > balance + EPSILON:
            return False, f"Số tiền rút ({format_currency(net_amount)}) vượt quá số dư khả dụng ({format_currency(balance)})."

        # 1) Tính fee full (nếu áp cả quỹ)
        fee_info = self.calculate_investor_fee(investor_id, trans_date, old_total_nav)
        perf_fee_full = fee_info.get("total_fee", 0.0)

        # 2) Tỷ lệ phân bổ fee theo net requested
        gross_if_full = balance
        denom = gross_if_full - perf_fee_full if (gross_if_full - perf_fee_full) > EPSILON else gross_if_full
        proportion = net_amount / denom if denom > EPSILON else 1.0
        performance_fee = max(0.0, min(perf_fee_full * proportion, perf_fee_full))

        gross_withdrawal = net_amount + performance_fee
        if gross_withdrawal > balance + EPSILON:
            gross_withdrawal = balance
            performance_fee = max(0.0, gross_withdrawal - net_amount)

        # 3) compute units
        fee_units = round(performance_fee / current_price, 8) if current_price > 0 else 0.0
        
        # Lấy tổng units trước khi làm gì cả
        total_units_before_any_deduction = sum(t.units for t in tranches)
        
        # Nếu net_amount yêu cầu gần bằng toàn bộ số dư (sau khi trừ phí dự kiến), 
        # coi như đây là rút toàn bộ
        balance_after_fee_estimate = balance - performance_fee
        is_intended_full_withdrawal = net_amount >= balance_after_fee_estimate - EPSILON

        if is_intended_full_withdrawal:
            # Nếu rút toàn bộ, units rút ra sẽ bằng toàn bộ units còn lại sau khi trừ phí
            withdrawal_units = total_units_before_any_deduction - fee_units
            # Và số tiền net thực nhận có thể khác một chút do làm tròn
            net_amount = withdrawal_units * current_price
        else:
            withdrawal_units = round(net_amount / current_price, 8) if current_price > 0 else 0.0

        # 4) Apply fee first (reduce units and update cumulative_fees_paid per tranche)
        if performance_fee > EPSILON:
            # units_before for fee_record
            units_before = sum(t.units for t in tranches)

            # Try to apply via existing helper
            fee_applied = self._apply_fee_to_investor_tranches(investor_id, performance_fee, trans_date, old_total_nav)

            # Fallback if helper fails (e.g., extreme edge)
            if not fee_applied:
                total_units = units_before
                if total_units > EPSILON:
                    for tranche in tranches:
                        proportion_tr = tranche.units / total_units
                        units_reduction = fee_units * proportion_tr
                        tranche.units = max(0.0, tranche.units - units_reduction)
                        tranche.cumulative_fees_paid = getattr(tranche, "cumulative_fees_paid", 0.0) + (units_reduction * current_price)
                        tranche.invested_value = tranche.units * tranche.entry_nav
                else:
                    # can't apply fee (no units) -> zero it
                    performance_fee = 0.0
                    fee_units = 0.0

            # record investor-side 'Phí' transaction and FeeRecord (so investor's total_fees_paid is tracked)
            if performance_fee > EPSILON:
                # 4.a Transaction 'Phí' (âm) for investor
                self._add_transaction(investor_id, trans_date, "Phí", -performance_fee, total_nav_after, -fee_units)

                # 4.b FeeRecord for the payer (investor)
                units_after = sum(t.units for t in self.get_investor_tranches(investor_id))
                fee_record = FeeRecord(
                    id=len(self.fee_records) + 1,
                    period=f"Withdrawal {trans_date.strftime('%Y-%m-%d')}",
                    investor_id=investor_id,
                    fee_amount=performance_fee,
                    fee_units=fee_units,
                    calculation_date=trans_date,
                    units_before=units_before,
                    units_after=units_after,
                    nav_per_unit=current_price,
                    description="Performance fee charged on withdrawal",
                )
                self.fee_records.append(fee_record)

        # 5) Remove withdrawal units for net amount (separately)
        # compute current tranches snapshot; is_full if withdraw all remaining units
        tranches_after_fee = self.get_investor_tranches(investor_id)
        total_units_after_fee = sum(t.units for t in tranches_after_fee)
        is_full_withdraw = withdrawal_units >= total_units_after_fee - EPSILON

        # Remove withdrawal units (this will adjust invested_value)
        self._process_unit_reduction_fixed(investor_id, withdrawal_units, is_intended_full_withdrawal)

        # 6) Transaction 'Rút' for investor (net amount) — units_change = -withdrawal_units
        self._add_transaction(investor_id, trans_date, "Rút", -net_amount, total_nav_after, -withdrawal_units)

        # 7) Transfer fee units to Fund Manager (create FM tranche + 'Phí Nhận' transaction)
        if performance_fee > EPSILON and fee_units > EPSILON:
            # _transfer_fee_to_fund_manager will create FM tranche and 'Phí Nhận' transaction
            self._transfer_fee_to_fund_manager(fee_units, current_price, trans_date, total_nav_after, performance_fee)

        # CUỐI HÀM, THÊM BƯỚC KIỂM TRA
        if is_intended_full_withdrawal:
            remaining_units = self.get_investor_units(investor_id)
            if remaining_units > EPSILON:
                print(f"WARNING: Full withdrawal processed, but investor {investor_id} still has {remaining_units} units.")
                # Có thể thêm logic dọn dẹp nốt ở đây nếu cần
                self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
        return True, f"Nhà đầu tư nhận {format_currency(net_amount)} (Gross {format_currency(gross_withdrawal)}, Phí {format_currency(performance_fee)})"


    def process_nav_update(self, total_nav: float, trans_date: datetime) -> Tuple[bool, str]:
        """
        Chỉ cập nhật NAV, KHÔNG tự động cập nhật HWM.
        HWM sẽ được chốt tại thời điểm tính phí.
        """
        if total_nav <= 0:
            return False, "Total NAV phải lớn hơn 0"

        # Vòng lặp cập nhật HWM đã được xóa
        # for tranche in self.tranches:
        #     if price > tranche.hwm:
        #         tranche.hwm = price

        # Ghi transaction NAV Update
        self._add_transaction(0, trans_date, "NAV Update", 0, total_nav, 0)

        return True, f"Đã cập nhật NAV: {format_currency(total_nav)}"

    def crystallize_hwm(self, current_price: float):
        """
        Chốt High Water Mark cho tất cả các tranche tại một mức giá nhất định.
        Hàm này nên được gọi SAU KHI phí đã được tính và áp dụng.
        """
        print(f"💎 Crystallizing HWM at price: {current_price:,.2f}")
        for tranche in self.tranches:
            if current_price > tranche.hwm:
                tranche.hwm = current_price
    # Fees
    # ================================
    def calculate_investor_fee(
        self, investor_id: int, ending_date: datetime, ending_total_nav: float
    ) -> Dict[str, Any]:
        tranches = self.get_investor_tranches(investor_id)
        if not tranches or ending_total_nav <= 0:
            return self._empty_fee_details()

        current_price = self.calculate_price_per_unit(ending_total_nav)
        balance = sum(t.units for t in tranches) * current_price
        invested_value = sum(getattr(t, "invested_value", t.units * t.entry_nav) for t in tranches)
        profit = balance - invested_value
        profit_perc = profit / invested_value if invested_value > 0 else 0.0

        total_fee = 0.0
        hurdle_value = 0.0
        hwm_value = 0.0
        excess_profit = 0.0
        units_before = sum(t.units for t in tranches)

        for tranche in tranches:
            if tranche.units < EPSILON:
                continue

            time_delta_days = (ending_date - tranche.entry_date).days
            if time_delta_days <= 0:
                continue

            time_delta_years = time_delta_days / 365.25
            hurdle_price = tranche.entry_nav * ((1 + HURDLE_RATE_ANNUAL) ** time_delta_years)
            threshold_price = max(hurdle_price, tranche.hwm)

            profit_per_unit = max(0, current_price - threshold_price)
            tranche_excess_profit = profit_per_unit * tranche.units

            total_fee += PERFORMANCE_FEE_RATE * tranche_excess_profit
            hurdle_value += hurdle_price * tranche.units
            hwm_value += tranche.hwm * tranche.units
            excess_profit += tranche_excess_profit

        total_fee = round(total_fee, 0)  # làm tròn tiền phí (VND)
        units_after = units_before - (total_fee / current_price) if current_price > 0 else units_before

        return {
            "total_fee": total_fee,
            "balance": round(balance, 2),
            "invested_value": round(invested_value, 2),
            "profit": round(profit, 2),
            "profit_perc": profit_perc,
            "hurdle_value": round(hurdle_value, 2),
            "hwm_value": round(hwm_value, 2),
            "excess_profit": round(excess_profit, 2),
            "units_before": units_before,
            "units_after": units_after,
        }

    def _apply_fee_to_investor_tranches(
        self, investor_id: int, total_fee: float, fee_date: datetime, total_nav: float
    ) -> bool:
        """
        NÂNG CẤP HOÀN THIỆN: Áp dụng phí một cách an toàn và chính xác.
        - Đảm bảo tính "nguyên tử": Hoặc tất cả thay đổi được áp dụng, hoặc không gì cả.
        - Xử lý sai số làm tròn: Đảm bảo tổng units bị trừ khớp chính xác với tổng phí.
        - Bảo toàn lịch sử: Không reset `entry_date` của tranche.
        - Reset HWM có điều kiện: Chỉ reset HWM/entry_nav cho các tranche thực sự trả phí.
        """
        try:
            # Lấy các tranche gốc của nhà đầu tư
            tranches_original = self.get_investor_tranches(investor_id)
            if not tranches_original or total_fee <= EPSILON:
                return False # Không có gì để làm nếu không có tranche hoặc không có phí

            # 1. TÍNH TOÁN BAN ĐẦU
            current_price = self.calculate_price_per_unit(total_nav)
            if current_price <= 0: return False

            # Xác định các tranche sẽ bị tính phí
            tranches_with_profit = [
                t for t in tranches_original 
                if t.calculate_excess_profit(current_price) > EPSILON
            ]
            
            # Nếu không có tranche nào có lãi, không làm gì cả
            if not tranches_with_profit:
                return False

            total_excess_profit = sum(t.calculate_excess_profit(current_price) for t in tranches_with_profit)
            if total_excess_profit < EPSILON:
                return False

            total_units_to_reduce = round(total_fee / current_price, 8)
            units_reduced_so_far = 0.0

            # 2. THAO TÁC TRÊN BẢN SAO ĐỂ ĐẢM BẢO AN TOÀN (TÍNH NGUYÊN TỬ)
            tranches_copy = copy.deepcopy(tranches_original)
            
            # 3. VÒNG LẶP XỬ LÝ PHÍ
            num_tranches_with_profit = len(tranches_with_profit)

            for i, tranche_id_to_modify in enumerate(t.tranche_id for t in tranches_with_profit):
                # Tìm tranche tương ứng trong bản sao để chỉnh sửa
                tranche = next(t for t in tranches_copy if t.tranche_id == tranche_id_to_modify)
                
                # Xử lý sai số làm tròn cho tranche cuối cùng
                if i == num_tranches_with_profit - 1:
                    units_reduction = total_units_to_reduce - units_reduced_so_far
                else:
                    tranche_excess_profit = tranche.calculate_excess_profit(current_price)
                    fee_proportion = tranche_excess_profit / total_excess_profit
                    fee_for_this_tranche = total_fee * fee_proportion
                    units_reduction = round(fee_for_this_tranche / current_price, 8)

                if units_reduction < EPSILON: continue

                # Cập nhật các giá trị của tranche trong bản sao
                tranche.cumulative_fees_paid += (units_reduction * current_price)
                tranche.units -= units_reduction
                units_reduced_so_far += units_reduction
                
                # CHỐT LÃI VÀ RESET NGƯỠNG TRONG BẢN SAO
                tranche.invested_value = tranche.units * current_price
                tranche.entry_nav = current_price
                # Không reset entry_date để giữ lại lịch sử
                tranche.hwm = current_price

            # 4. SWAP: THAY THẾ DỮ LIỆU GỐC BẰNG BẢN SAO ĐÃ CẬP NHẬT
            # Chỉ thực hiện bước này khi toàn bộ vòng lặp đã chạy thành công
            
            # Xóa các tranche gốc của nhà đầu tư này khỏi danh sách chính
            self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
            
            # Thêm các tranche đã được cập nhật từ bản sao vào
            self.tranches.extend(tranches_copy)
            
            # Dọn dẹp các tranche có thể bị rỗng do làm tròn
            self.tranches = [t for t in self.tranches if t.units >= EPSILON]
            
            return True

        except Exception as e:
            # Nếu có bất kỳ lỗi nào xảy ra, self.tranches gốc không bị ảnh hưởng
            print(f"Error applying fee to investor {investor_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _transfer_fee_to_fund_manager(
        self, fee_units: float, current_price: float, fee_date: datetime, total_nav: float, fee_amount: float
    ):
        """
        Tạo tranche + transaction 'Phí Nhận' cho Fund Manager.
        NOTE: Không tạo FeeRecord cho Fund Manager ở đây — caller (apply fee / withdrawal) sẽ tạo FeeRecord cho payer investor.
        """
        try:
            fund_manager = self.get_fund_manager()
            if not fund_manager:
                print("Cannot transfer fee: Fund Manager not found")
                return False

            fee_tranche = Tranche(
                investor_id=fund_manager.id,
                tranche_id=f"FEE_{str(uuid.uuid4())}",
                entry_date=fee_date,
                entry_nav=current_price,
                units=fee_units,
                hwm=current_price,
                original_entry_date=fee_date,
                original_entry_nav=current_price,
                original_invested_value=fee_amount,
                cumulative_fees_paid=0.0,
            )
            fee_tranche.invested_value = fee_tranche.units * fee_tranche.entry_nav
            self.tranches.append(fee_tranche)

            # Transaction: Fund Manager receives fee (positive amount)
            self._add_transaction(
                fund_manager.id, fee_date, "Phí Nhận", fee_amount, total_nav, fee_units
            )

            print(f"Transferred {fee_units:.6f} units ({fee_amount:,.0f} VND) to Fund Manager")
            return True

        except Exception as e:
            print(f"Error transferring fee to Fund Manager: {str(e)}")
            return False


    def apply_year_end_fees_enhanced(self, fee_date: datetime, total_nav: float) -> Dict[str, Any]:
        """
        Tính & áp phí cuối năm, chuyển units phí sang Fund Manager.
        """
        try:
            results = {
                "success": True,
                "total_fees": 0.0,
                "investors_processed": 0,
                "fee_details": [],
                "errors": [],
                "fund_manager_units_received": 0.0,
            }

            regular_investors = self.get_regular_investors()
            fund_manager = self.get_fund_manager()
            if not fund_manager:
                results["errors"].append("Fund Manager not found")
                results["success"] = False
                return results

            current_price = self.calculate_price_per_unit(total_nav)

            for investor in regular_investors:
                try:
                    fee_calculation = self.calculate_investor_fee(investor.id, fee_date, total_nav)

                    if fee_calculation["total_fee"] > 1:
                        fee_applied = self._apply_fee_to_investor_tranches(
                            investor.id, fee_calculation["total_fee"], fee_date, total_nav
                        )
                        if fee_applied:
                            units_removed = fee_calculation["total_fee"] / current_price

                            # ghi giao dịch phí (âm cho investor)
                            self._add_transaction(
                                investor.id,
                                fee_date,
                                "Phí",
                                -fee_calculation["total_fee"],
                                total_nav,
                                -units_removed,
                            )

                            # chuyển units phí cho FM
                            self._transfer_fee_to_fund_manager(
                                units_removed, current_price, fee_date, total_nav, fee_calculation["total_fee"]
                            )

                            # ghi FeeRecord
                            fee_record = FeeRecord(
                                id=len(self.fee_records) + 1,
                                period=fee_date.strftime("%Y"),
                                investor_id=investor.id,
                                fee_amount=fee_calculation["total_fee"],
                                fee_units=units_removed,
                                calculation_date=fee_date,
                                units_before=fee_calculation.get("units_before", 0.0),
                                units_after=fee_calculation.get("units_after", 0.0),
                                nav_per_unit=current_price,
                                description=f"Performance fee for year {fee_date.year}",
                            )
                            self.fee_records.append(fee_record)

                            results["total_fees"] += fee_calculation["total_fee"]
                            results["investors_processed"] += 1
                            results["fund_manager_units_received"] += units_removed
                            results["fee_details"].append(
                                {
                                    "investor_id": investor.id,
                                    "investor_name": investor.name,
                                    "fee_amount": fee_calculation["total_fee"],
                                    "fee_units": units_removed,
                                    "excess_profit": fee_calculation["excess_profit"],
                                }
                            )
                        else:
                            results["errors"].append(f"Failed to apply fee to investor {investor.name}")
                    else:
                        # Không đủ lớn để áp
                        pass

                except Exception as e:
                    err = f"Error processing investor {investor.name}: {str(e)}"
                    results["errors"].append(err)
                    results["success"] = False

            print(
                f"Fee application completed. Total fees: {results['total_fees']:,.0f} VND, "
                f"FM units received: {results['fund_manager_units_received']:.6f}"
            )
            return results

        except Exception as e:
            error_msg = f"Critical error in apply_year_end_fees_enhanced: {str(e)}"
            print(error_msg)
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": error_msg,
                "total_fees": 0.0,
                "investors_processed": 0,
                "fee_details": [],
                "errors": [error_msg],
                "fund_manager_units_received": 0.0,
            }

    # ================================
    # Lifetime performance & reports
    # ================================
    def get_investor_lifetime_performance(self, investor_id: int, current_nav: float) -> Dict:
        tranches = self.get_investor_tranches(investor_id)
        if not tranches:
            return self._empty_performance_stats()

        current_price = self.calculate_price_per_unit(current_nav)
        total_original_invested = sum(
            getattr(t, "original_invested_value", t.units * t.entry_nav) for t in tranches
        )
        current_value = sum(t.units for t in tranches) * current_price

        # Use fee_records as source of truth for total fees paid by this investor
        total_fees_paid = sum(fr.fee_amount for fr in self.fee_records if fr.investor_id == investor_id)

        gross_profit = current_value + total_fees_paid - total_original_invested
        net_profit = current_value - total_original_invested

        return {
            "original_invested": total_original_invested,
            "current_value": current_value,
            "total_fees_paid": total_fees_paid,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "gross_return": (gross_profit / total_original_invested) if total_original_invested > 0 else 0.0,
            "net_return": (net_profit / total_original_invested) if total_original_invested > 0 else 0.0,
            "current_units": sum(t.units for t in tranches),
        }

    def get_fee_history(self, investor_id: Optional[int] = None) -> List[FeeRecord]:
        if investor_id is None:
            return self.fee_records
        return [record for record in self.fee_records if record.investor_id == investor_id]

    # ================================
    # Undo / Delete transactions
    # ================================
    def undo_last_transaction(self, transaction_id: int) -> bool:
        try:
            transaction = next((t for t in self.transactions if t.id == transaction_id), None)
            if not transaction:
                return False

            recent_transactions = sorted(self.transactions, key=lambda x: x.date, reverse=True)[:5]
            if transaction not in recent_transactions:
                return False

            if transaction.type == "Nạp":
                return self._undo_deposit(transaction)
            elif transaction.type == "Rút":
                return self._undo_withdrawal(transaction)
            elif transaction.type == "NAV Update":
                return self._undo_nav_update(transaction)
            elif transaction.type in ["Phí", "Fund Manager Withdrawal"]:
                return self._simple_transaction_removal(transaction)
            return False

        except Exception as e:
            print(f"Error in undo_last_transaction: {str(e)}")
            return False

    def _undo_deposit(self, original_transaction) -> bool:
        try:
            investor_id = original_transaction.investor_id
            amount = original_transaction.amount
            deposit_date = original_transaction.date

            matching_tranches = [
                t
                for t in self.tranches
                if (t.investor_id == investor_id and abs((t.entry_date - deposit_date).total_seconds()) < 3600)
            ]
            if not matching_tranches:
                return False

            tranche_to_remove = max(matching_tranches, key=lambda x: x.entry_date)

            if abs(tranche_to_remove.units * tranche_to_remove.entry_nav - amount) > 1:
                return False

            self.tranches.remove(tranche_to_remove)
            self.transactions.remove(original_transaction)
            return True

        except Exception as e:
            print(f"Error in _undo_deposit: {str(e)}")
            return False

    def _undo_withdrawal(self, original_transaction) -> bool:
        """
        NÂNG CẤP: Hoàn tác một giao dịch rút tiền.
        Thao tác này phức tạp và chỉ nên dùng cho các giao dịch gần đây.
        Nó sẽ khôi phục trạng thái bằng cách tính toán ngược và thao tác trên bộ nhớ.
        """
        try:
            investor_id = original_transaction.investor_id
            trans_date = original_transaction.date

            # 1. Tìm tất cả các bản ghi liên quan trong bộ nhớ
            fee_txn = next((
                t for t in self.transactions 
                if t.investor_id == investor_id and t.type == "Phí" and 
                abs((t.date - trans_date).total_seconds()) < 1
            ), None)
            
            fm_fee_txns = [
                t for t in self.transactions 
                if t.type == "Phí Nhận" and abs((t.date - trans_date).total_seconds()) < 1
            ]

            fee_record_to_undo = next((
                fr for fr in self.fee_records
                if fr.investor_id == investor_id and fr.period.startswith("Withdrawal") and 
                abs((fr.calculation_date - trans_date).total_seconds()) < 1
            ), None)

            if not fee_record_to_undo and fee_txn:
                print(f"ERROR: Cannot undo withdrawal {original_transaction.id}. Corresponding FeeRecord not found.")
                return False

            # 2. Hoàn tác các thay đổi trên tranche của nhà đầu tư
            # Lấy lại các giá trị từ FeeRecord
            units_before_fee = fee_record_to_undo.units_before if fee_record_to_undo else self.get_investor_units(investor_id) + abs(original_transaction.units_change)
            
            # Xóa các tranche đã bị reset (do _apply_fee_to_investor_tranches)
            # và khôi phục lại trạng thái cũ hơn. Logic này rất phức tạp.
            # Một cách tiếp cận đơn giản và an toàn hơn là không cho phép undo withdrawal.
            # Tuy nhiên, nếu vẫn muốn thực hiện, chúng ta cần một cơ chế snapshot.
            # Vì hiện tại không có, chúng ta sẽ thông báo giới hạn này.
            print("WARNING: 'Undo Withdrawal' is a complex operation and may not perfectly restore state without a snapshot system.")
            print("This feature should be used with caution only for immediate corrections.")
            
            # Vì sự phức tạp và rủi ro, chúng ta sẽ ngăn chặn undo withdrawal phức tạp
            # và chỉ cho phép undo các giao dịch đơn giản
            if fee_txn or fm_fee_txns:
                st.error("Hoàn tác giao dịch rút tiền có tính phí chưa được hỗ trợ vì độ phức tạp cao. Vui lòng xóa và tạo lại giao dịch.")
                return False

            # Nếu là một lần rút tiền đơn giản không có phí
            units_to_restore = abs(original_transaction.units_change)
            tranches = self.get_investor_tranches(investor_id)
            if not tranches:
                # Nếu nhà đầu tư đã rút hết, tạo lại 1 tranche
                price = original_transaction.nav / (sum(t.units for t in self.tranches) + units_to_restore)
                tranche = Tranche(
                    investor_id=investor_id,
                    tranche_id=str(uuid.uuid4()),
                    entry_date=trans_date, entry_nav=price, units=units_to_restore, hwm=price,
                    original_entry_date=trans_date, original_entry_nav=price,
                    original_invested_value=units_to_restore * price, cumulative_fees_paid=0.0
                )
                self.tranches.append(tranche)
            else:
                # Phân bổ lại units
                total_existing_units = self.get_investor_units(investor_id)
                for tranche in tranches:
                    proportion = tranche.units / total_existing_units if total_existing_units > 0 else 1.0/len(tranches)
                    tranche.units += units_to_restore * proportion
                    tranche.invested_value += (units_to_restore * proportion) * tranche.entry_nav

            # Xóa transaction rút tiền
            self.transactions.remove(original_transaction)
            
            return True

        except Exception as e:
            print(f"Error undo withdrawal: {str(e)}")
            import traceback
            traceback.print_exc()
            return False



    def _undo_nav_update(self, original_transaction) -> bool:
        try:
            self.transactions.remove(original_transaction)
            return True
        except Exception:
            return False

    def _simple_transaction_removal(self, transaction) -> bool:
        try:
            self.transactions.remove(transaction)
            return True
        except Exception:
            return False

    def delete_transaction(self, transaction_id: int) -> bool:
        try:
            transaction_to_delete = next((t for t in self.transactions if t.id == transaction_id), None)
            if not transaction_to_delete:
                return False

            self.backup_before_operation(f"Delete transaction {transaction_id}")

            recent_transactions = sorted(self.transactions, key=lambda x: (x.date, x.id), reverse=True)[:10]
            if transaction_to_delete not in recent_transactions:
                print(f"Transaction {transaction_id} is too old to delete safely")
                return False

            if transaction_to_delete.type == "Nạp":
                return self._delete_deposit_transaction(transaction_to_delete)
            elif transaction_to_delete.type == "Rút":
                return self._delete_withdrawal_transaction(transaction_to_delete)
            elif transaction_to_delete.type == "NAV Update":
                return self._delete_nav_update_transaction(transaction_to_delete)
            elif transaction_to_delete.type in ["Phí", "Fund Manager Withdrawal", "Phí Nhận"]:
                return self._delete_complex_transaction(transaction_to_delete)
            else:
                self.transactions.remove(transaction_to_delete)
                return True

        except Exception as e:
            print(f"Error in delete_transaction: {str(e)}")
            return False

    def _delete_deposit_transaction(self, transaction) -> bool:
        try:
            investor_id = transaction.investor_id
            amount = transaction.amount
            transaction_date = transaction.date

            matching_tranches = [
                t
                for t in self.tranches
                if (t.investor_id == investor_id and abs((t.entry_date - transaction_date).total_seconds()) < 3600)
            ]

            best_match = None
            for tranche in matching_tranches:
                calculated_amount = tranche.units * tranche.entry_nav
                if abs(calculated_amount - amount) < 10:
                    best_match = tranche
                    break

            if best_match:
                if getattr(best_match, "cumulative_fees_paid", 0) > 0:
                    print(
                        f"Cannot delete deposit transaction {transaction.id}: tranche has been affected by fees"
                    )
                    return False
                self.tranches.remove(best_match)

            self.transactions.remove(transaction)
            return True

        except Exception as e:
            print(f"Error deleting deposit transaction: {str(e)}")
            return False

    def _delete_withdrawal_transaction(self, transaction) -> bool:
        try:
            investor_id = transaction.investor_id
            investor_transactions = [t for t in self.transactions if t.investor_id == investor_id]
            investor_transactions.sort(key=lambda x: (x.date, x.id), reverse=True)
            if investor_transactions[0].id != transaction.id:
                print(
                    f"Cannot delete withdrawal transaction {transaction.id}: not the latest transaction for investor"
                )
                return False

            amount = abs(transaction.amount)
            units_to_restore = abs(transaction.units_change)
            investor_tranches = self.get_investor_tranches(investor_id)

            if not investor_tranches:
                entry_nav = amount / units_to_restore if units_to_restore > 0 else DEFAULT_UNIT_PRICE
                tranche = Tranche(
                    investor_id=investor_id,
                    tranche_id=str(uuid.uuid4()),
                    entry_date=transaction.date,
                    entry_nav=entry_nav,
                    units=units_to_restore,
                    hwm=entry_nav,
                    original_entry_date=transaction.date,
                    original_entry_nav=entry_nav,
                    original_invested_value=amount,
                    cumulative_fees_paid=0.0,
                )
                tranche.invested_value = tranche.units * tranche.entry_nav
                self.tranches.append(tranche)
            else:
                total_existing_units = sum(t.units for t in investor_tranches)
                for tranche in investor_tranches:
                    if total_existing_units > 0:
                        proportion = tranche.units / total_existing_units
                        tranche.units += units_to_restore * proportion
                        tranche.invested_value = tranche.units * tranche.entry_nav

            self.transactions.remove(transaction)
            return True

        except Exception as e:
            print(f"Error deleting withdrawal transaction: {str(e)}")
            return False

    def _delete_nav_update_transaction(self, transaction) -> bool:
        try:
            latest_nav = self.get_latest_total_nav()
            if latest_nav == transaction.nav:
                print(f"Warning: Deleting NAV update transaction {transaction.id} will change latest NAV")
            self.transactions.remove(transaction)
            return True
        except Exception as e:
            print(f"Error deleting NAV update transaction: {str(e)}")
            return False

    def _delete_complex_transaction(self, transaction) -> bool:
        try:
            if transaction.type in ["Phí", "Phí Nhận"]:
                # mapping theo calculation_date trong FeeRecord
                fee_records_to_check = [
                    f
                    for f in self.fee_records
                    if abs((f.calculation_date - transaction.date).total_seconds()) < 3600
                ]
                if fee_records_to_check:
                    print(
                        f"Cannot delete fee transaction {transaction.id}: has associated fee records. "
                        f"Please delete fee records first."
                    )
                    return False

            self.transactions.remove(transaction)
            return True

        except Exception as e:
            print(f"Error deleting complex transaction: {str(e)}")
            return False

    # ================================
    # Validation / Backup / Cache
    # ================================
    def validate_data_consistency(self) -> Dict[str, Any]:
        results = {"valid": True, "errors": [], "warnings": [], "stats": {}}
        try:
            investor_ids = {inv.id for inv in self.investors}

            for tranche in self.tranches:
                if tranche.investor_id not in investor_ids:
                    results["errors"].append(
                        f"Tranche references non-existent investor ID: {tranche.investor_id}"
                    )
                    results["valid"] = False
                if tranche.units <= 0:
                    results["errors"].append(f"Tranche has non-positive units: {tranche.tranche_id}")
                    results["valid"] = False
                if tranche.hwm < tranche.entry_nav:
                    results["warnings"].append(f"Tranche {tranche.tranche_id} has HWM < entry NAV")

            for trans in self.transactions:
                if trans.investor_id not in investor_ids:
                    results["errors"].append(
                        f"Transaction {trans.id} references non-existent investor ID: {trans.investor_id}"
                    )
                    results["valid"] = False
                if trans.nav <= 0 and trans.type not in ["Phí Nhận"]:
                    results["warnings"].append(f"Transaction {trans.id} has non-positive NAV: {trans.nav}")
                if trans.date > datetime.now():
                    results["warnings"].append(f"Transaction {trans.id} has future date: {trans.date}")

            for fee_record in self.fee_records:
                if fee_record.investor_id not in investor_ids:
                    results["errors"].append(
                        f"Fee record {fee_record.id} references non-existent investor"
                    )
                    results["valid"] = False
                if fee_record.units_after > fee_record.units_before:
                    results["errors"].append(f"Fee record {fee_record.id} has units_after > units_before")
                    results["valid"] = False

            latest_nav = self.get_latest_total_nav()
            if latest_nav:
                total_units = sum(t.units for t in self.tranches)
                if total_units > 0:
                    calculated_price = latest_nav / total_units
                    results["stats"]["latest_nav"] = latest_nav
                    results["stats"]["total_units"] = total_units
                    results["stats"]["price_per_unit"] = calculated_price
                    if calculated_price < 1000 or calculated_price > 10_000_000:
                        results["warnings"].append(
                            f"Price per unit seems unusual: {calculated_price:,.0f} VND"
                        )

            results["stats"]["total_investors"] = len(self.investors)
            results["stats"]["regular_investors"] = len(self.get_regular_investors())
            results["stats"]["total_tranches"] = len(self.tranches)
            results["stats"]["total_transactions"] = len(self.transactions)
            results["stats"]["total_fee_records"] = len(self.fee_records)

            results["valid"] = len(results["errors"]) == 0
            return results

        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Validation error: {str(e)}")
            return results

    def backup_before_operation(self, operation_name: str) -> bool:
        try:
            backup_data = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation_name,
                "investors_count": len(self.investors),
                "tranches_count": len(self.tranches),
                "transactions_count": len(self.transactions),
                "fee_records_count": len(self.fee_records),
            }
            if "operation_backup" not in st.session_state:
                st.session_state.operation_backup = []
            st.session_state.operation_backup.append(backup_data)
            if len(st.session_state.operation_backup) > 5:
                st.session_state.operation_backup = st.session_state.operation_backup[-5:]
            return True
        except Exception as e:
            print(f"Backup failed: {str(e)}")
            return False

    def _clear_nav_cache(self):
        try:
            if hasattr(st, "cache_data"):
                st.cache_data.clear()
            for key in ["cached_nav", "latest_nav", "nav_cache", "nav_large_change_confirmed"]:
                if key in st.session_state:
                    del st.session_state[key]
            print("DEBUG: NAV cache cleared")
        except Exception as e:
            print(f"Warning: Could not clear cache: {e}")

    # ================================
    # Reporting
    # ================================
    def get_investor_individual_report(self, investor_id: int, current_nav: float) -> Dict:
        try:
            if investor_id is None or current_nav <= 0:
                print(f"Invalid inputs: investor_id={investor_id}, current_nav={current_nav}")
                return {}

            investor = self.get_investor_by_id(investor_id)
            if not investor:
                print(f"Investor not found: {investor_id}")
                return {}

            tranches = self.get_investor_tranches(investor_id)
            if not tranches:
                return {
                    "investor": investor,
                    "current_balance": 0.0,
                    "current_profit": 0.0,
                    "current_profit_perc": 0.0,
                    "lifetime_performance": self._empty_performance_stats(),
                    "fee_details": self._empty_fee_details(),
                    "tranches": [],
                    "transactions": [t for t in self.transactions if t.investor_id == investor_id],
                    "fee_history": [f for f in self.fee_records if f.investor_id == investor_id],
                    "report_date": datetime.now(),
                    "current_nav": current_nav,
                    "current_price": self.calculate_price_per_unit(current_nav),
                }

            try:
                balance, profit, profit_perc = self.get_investor_balance(investor_id, current_nav)
            except Exception as e:
                print(f"Error calculating balance for investor {investor_id}: {e}")
                balance = profit = profit_perc = 0.0

            try:
                lifetime_perf = self.get_investor_lifetime_performance(investor_id, current_nav)
            except Exception as e:
                print(f"Error calculating lifetime performance for investor {investor_id}: {e}")
                lifetime_perf = self._empty_performance_stats()

            try:
                fee_details = self.calculate_investor_fee(investor_id, datetime.now(), current_nav)
            except Exception as e:
                print(f"Error calculating fee details for investor {investor_id}: {e}")
                fee_details = self._empty_fee_details()

            investor_transactions = [t for t in self.transactions if t.investor_id == investor_id]
            investor_fees = [f for f in self.fee_records if f.investor_id == investor_id]

            report = {
                "investor": investor,
                "current_balance": balance,
                "current_profit": profit,
                "current_profit_perc": profit_perc,
                "lifetime_performance": lifetime_perf,
                "fee_details": fee_details,
                "tranches": tranches,
                "transactions": investor_transactions,
                "fee_history": investor_fees,
                "report_date": datetime.now(),
                "current_nav": current_nav,
                "current_price": self.calculate_price_per_unit(current_nav),
            }
            print(f"Successfully generated report for investor {investor_id}")
            return report

        except Exception as e:
            print(f"Critical error generating individual report for investor {investor_id}: {str(e)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            return {}

    # ================================
    # Helpers (empty dicts)
    # ================================
    def _empty_fee_details(self) -> Dict[str, Any]:
        return {
            "total_fee": 0.0,
            "balance": 0.0,
            "invested_value": 0.0,
            "profit": 0.0,
            "profit_perc": 0.0,
            "hurdle_value": 0.0,
            "hwm_value": 0.0,
            "excess_profit": 0.0,
            "units_before": 0.0,
            "units_after": 0.0,
        }

    def _empty_performance_stats(self) -> Dict:
        return {
            "original_invested": 0.0,
            "current_value": 0.0,
            "total_fees_paid": 0.0,
            "gross_profit": 0.0,
            "net_profit": 0.0,
            "gross_return": 0.0,
            "net_return": 0.0,
            "current_units": 0.0,
        }
