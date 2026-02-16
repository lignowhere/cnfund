import copy as cp
import uuid
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Any
from config import *
from .models import Investor, Tranche, Transaction, FeeRecord
import logging # Sá»­ dá»¥ng logging chuyÃªn nghiá»‡p hÆ¡n

# Thiáº¿t láº­p logging (cÃ³ thá»ƒ Ä‘áº·t á»Ÿ Ä‘áº§u file)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from concurrent.futures import ThreadPoolExecutor
from utils.timezone_manager import TimezoneManager
from utils.datetime_utils import safe_total_seconds_between
from helpers import validate_phone, validate_email, format_currency

class EnhancedFundManager:
    def __init__(self, data_handler, enable_snapshots: bool = True):
        self.data_handler = data_handler
        self.investors: List[Investor] = []
        self.tranches: List[Tranche] = []
        self.transactions: List[Transaction] = []
        self.fee_records: List[FeeRecord] = []
        self._operation_backups: List[Dict[str, Any]] = []
        
        # Backup handled by APIBackupFlow (integrated via legacy UI)
        if enable_snapshots:
            print("ðŸš€ Backup system: APIBackupFlow (via backend API)")
            # Old backup managers removed - now handled by backend backup service
            self.snapshot_manager = None
        else:
            print("ðŸš« Backup system disabled (enable_snapshots=False)")
            self.snapshot_manager = None

        # DO NOT set backup_manager attribute - it's now handled by api_backup service
            
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
    
    def _auto_backup_if_enabled(self, operation_type: str, description: str = None):
        """
        ULTRA OPTIMIZED: Deferred backup - maximum UI responsiveness
        """
        # Backup operations are handled by backend API services.
        pass
    
    def _should_skip_frequent_backup(self) -> bool:
        """Check if we should skip backup due to frequency limits"""
        # backup_manager removed - always return False
        return False

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
        """Get investor options with type safety guarantees"""
        from utils.type_safety_fixes import safe_int_conversion
        options = {}
        for inv in self.get_regular_investors():
            try:
                # Ensure investor ID is always an integer
                investor_id = safe_int_conversion(inv.id)
                if investor_id >= 0:  # Valid ID
                    options[inv.display_name] = investor_id
            except Exception as e:
                print(f"Warning: Skipping investor {getattr(inv, 'name', 'unknown')} due to ID conversion error: {e}")
                continue
        return options

    def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        return next((inv for inv in self.investors if inv.id == investor_id), None)

    # ================================
    # Investor CRUD
    # ================================
    def add_investor(
        self, name: str, phone: str = "", address: str = "", email: str = ""
    ) -> Tuple[bool, str]:
        if not name.strip():
            return False, "TÃªn khÃ´ng Ä‘Æ°á»£c Ä‘á»ƒ trá»‘ng"

        existing_names = [inv.name.lower().strip() for inv in self.investors]
        if name.lower().strip() in existing_names:
            return False, f"NhÃ  Ä‘áº§u tÆ° '{name}' Ä‘Ã£ tá»“n táº¡i"

        if phone and not validate_phone(phone):
            return False, "SÄT khÃ´ng há»£p lá»‡"
        if email and not validate_email(email):
            return False, "Email khÃ´ng há»£p lá»‡"

        # ID=0 dÃ nh cho Fund Manager
        existing_ids = [inv.id for inv in self.investors]
        new_id = 1
        while new_id in existing_ids:
            new_id += 1

        investor = Investor(
            id=new_id,
            name=name.strip(),
            phone=phone.strip(),
            address=address.strip(),
            address_line=address.strip(),
            email=email.strip(),
            is_fund_manager=False,
        )
        self.investors.append(investor)
        
        # Auto-backup after adding investor
        self._auto_backup_if_enabled("ADD_INVESTOR", f"Added investor: {investor.display_name}")
        
        return True, f"ÄÃ£ thÃªm {investor.display_name}"

    # ================================
    # Portfolio helpers (per investor)
    # ================================
    def get_investor_tranches(self, investor_id: int) -> List[Tranche]:
        return [t for t in self.tranches if t.investor_id == investor_id]

    def get_investor_units(self, investor_id: int) -> float:
        return sum(t.units for t in self.get_investor_tranches(investor_id))

    def get_investor_original_investment(self, investor_id: int) -> float:
        deposits = sum(
            t.amount
            for t in self.transactions
            if t.investor_id == investor_id and t.type == "Náº¡p" and t.amount > 0
        )
        if deposits > EPSILON:
            return deposits
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
        if not self.tranches:
            return DEFAULT_UNIT_PRICE
        total_units = sum(t.units for t in self.tranches)
        if total_units <= EPSILON:
            return DEFAULT_UNIT_PRICE
        if total_nav == 0:
            return 0.0
        if total_nav < 0:
            return DEFAULT_UNIT_PRICE
        return total_nav / total_units

    def _sort_transaction_datetime(self, transaction: Transaction) -> datetime:
        """Normalize transaction datetime for deterministic sorting/comparison."""
        return TimezoneManager.normalize_for_display(transaction.date)

    def get_latest_total_nav(self, include_zero_nav: bool = True) -> Optional[float]:
        """
        Get the latest Total NAV from the most recent transaction (any type).

        Returns NAV from the most recent transaction by datetime and ID,
        regardless of transaction type (NAV Update, Náº¡p, RÃºt, etc.).
        This ensures we always use the most up-to-date NAV value.
        """
        if not self.transactions:
            return None

        nav_transactions = [
            t for t in self.transactions
            if t.nav is not None and (t.nav >= 0 if include_zero_nav else t.nav > 0)
        ]
        if not nav_transactions:
            return None

        sorted_transactions = sorted(
            nav_transactions,
            key=lambda tx: (self._sort_transaction_datetime(tx), tx.id),
            reverse=True,
        )
        latest_transaction = sorted_transactions[0]

        # Debug: Show which transaction was used for NAV
        tx_date = self._sort_transaction_datetime(latest_transaction)
        print(f"ðŸ“Š Latest NAV: {latest_transaction.nav:,.0f} from transaction:")
        print(f"   Type: {latest_transaction.type}")
        print(f"   Date: {tx_date}")
        print(f"   ID: {latest_transaction.id}")

        return latest_transaction.nav

    def get_nav_for_date(self, target_date, include_zero_nav: bool = True) -> Optional[float]:
        """Get NAV for a specific date (most recent NAV on or before that date)"""
        if not self.transactions:
            return None

        if isinstance(target_date, datetime):
            target_dt = target_date
        else:
            target_dt = datetime.combine(target_date, datetime.max.time())
        target_dt = TimezoneManager.normalize_for_display(target_dt)

        nav_transactions = [
            t for t in self.transactions
            if t.nav is not None and (t.nav >= 0 if include_zero_nav else t.nav > 0)
        ]
        relevant_transactions = [
            t for t in nav_transactions
            if self._sort_transaction_datetime(t) <= target_dt
        ]

        if not relevant_transactions:
            return None

        sorted_transactions = sorted(
            relevant_transactions,
            key=lambda tx: (self._sort_transaction_datetime(tx), tx.id),
            reverse=True,
        )
        selected = sorted_transactions[0]

        print(
            f"ðŸŽ¯ get_nav_for_date({target_date}): "
            f"Using transaction ID:{selected.id}, Date:{selected.date}, NAV:{selected.nav}"
        )
        return selected.nav

    def get_nav_history(self) -> List[Dict[str, Any]]:
        """Compatibility helper for UI pages that need NAV timeline data."""
        nav_transactions = [
            t for t in self.transactions if t.nav is not None and t.nav >= 0
        ]
        nav_transactions.sort(key=lambda tx: (self._sort_transaction_datetime(tx), tx.id))
        return [
            {
                "id": t.id,
                "date": t.date,
                "type": t.type,
                "nav": t.nav,
            }
            for t in nav_transactions
        ]

    # ================================
    # Transactions
    # ================================
    def _get_next_transaction_id(self) -> int:
        return max([t.id for t in self.transactions] or [0]) + 1

    def _add_transaction(
        self, investor_id: int, date: datetime, type: str, amount: float, nav: float, units_change: float
    ):
        transaction_id = self._get_next_transaction_id()
        
        # OPTIMIZED: Minimal logging for better performance
        if type == "NAV Update":
            print(f"ðŸŽ¯ NAV UPDATE: ID={transaction_id}, NAV={nav:,.0f}")
        
        # Use naive datetime for local operations (Excel compatible)
        normalized_date = date.replace(tzinfo=None) if hasattr(date, 'tzinfo') and date.tzinfo else date
        
        transaction = Transaction(
            id=transaction_id,
            investor_id=investor_id,
            date=normalized_date,
            type=type,
            amount=amount,
            nav=nav,
            units_change=units_change,
        )
        
        # OPTIMIZED: Remove excessive verification logging
        self.transactions.append(transaction)

    def process_deposit(
        self, investor_id: int, amount: float, total_nav_after: float, trans_date: datetime
    ) -> Tuple[bool, str]:
        if amount <= 0:
            return False, "Sá»‘ tiá»n pháº£i lá»›n hÆ¡n 0"
        if total_nav_after < 0:
            return False, "NAV tá»•ng sau giao dá»‹ch khÃ´ng thá»ƒ Ã¢m"

        # NAV trÆ°á»›c náº¡p luÃ´n Ä‘Æ°á»£c suy ra tá»« NAV sau vÃ  sá»‘ tiá»n náº¡p.
        inferred_nav_before = total_nav_after - amount
        if inferred_nav_before < -EPSILON:
            return False, "NAV trÆ°á»›c giao dá»‹ch suy ra bá»‹ Ã¢m. Vui lÃ²ng kiá»ƒm tra NAV sau giao dá»‹ch."

        old_total_nav = max(0.0, inferred_nav_before)
        price = self.calculate_price_per_unit(old_total_nav) if old_total_nav > EPSILON else DEFAULT_UNIT_PRICE
        if price <= EPSILON:
            return False, "KhÃ´ng thá»ƒ xÃ¡c Ä‘á»‹nh giÃ¡ Ä‘Æ¡n vá»‹ quá»¹ tá»« NAV hiá»‡n táº¡i."
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
            original_invested_value=amount,  # set nguá»“n vá»‘n gá»‘c
            cumulative_fees_paid=0.0,
        )
        # cáº­p nháº­t invested_value hiá»‡n táº¡i
        tranche.invested_value = tranche.units * tranche.entry_nav

        self.tranches.append(tranche)
        self._add_transaction(investor_id, trans_date, "Náº¡p", amount, round(total_nav_after, 2), units)
        
        # Auto-backup after deposit transaction
        investor = self.get_investor_by_id(investor_id)
        investor_name = investor.display_name if investor else f"ID-{investor_id}"
        self._auto_backup_if_enabled("DEPOSIT", f"Deposit: {format_currency(amount)} by {investor_name}")
        
        return True, f"ÄÃ£ náº¡p {format_currency(amount)}"

    def _process_unit_reduction_fixed(self, investor_id: int, units_to_remove: float, is_full: bool):
        """
        Giáº£m units khi rÃºt: full thÃ¬ xÃ³a háº¿t, partial thÃ¬ giáº£m theo tá»· lá»‡, giá»¯ nguyÃªn original_*.
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

    # +++++ THAY THáº¾ TOÃ€N Bá»˜ HÃ€M process_withdrawal Báº°NG PHIÃŠN Báº¢N HOÃ€N THIá»†N NÃ€Y +++++
    def process_withdrawal(
        self, investor_id: int, net_amount: float, total_nav_after: float, trans_date: datetime
    ) -> Tuple[bool, str]:
        """Xá»­ lÃ½ rÃºt tiá»n vá»›i logic rÃµ rÃ ng vÃ  chÃ­nh xÃ¡c cho má»i trÆ°á»ng há»£p."""
        if net_amount <= 0:
            return False, "Sá»‘ tiá»n rÃºt pháº£i lá»›n hÆ¡n 0"
        if total_nav_after < 0:
            return False, "NAV tá»•ng sau giao dá»‹ch khÃ´ng thá»ƒ Ã¢m"

        # 1. Suy ra NAV trÆ°á»›c rÃºt tá»« NAV sau vÃ  sá»‘ tiá»n rÃºt thá»±c nháº­n.
        inferred_nav_before = total_nav_after + net_amount
        if inferred_nav_before <= EPSILON:
            return False, "NAV trÆ°á»›c giao dá»‹ch khÃ´ng há»£p lá»‡. Vui lÃ²ng kiá»ƒm tra NAV sau giao dá»‹ch."
        old_total_nav = inferred_nav_before
        current_price = self.calculate_price_per_unit(old_total_nav)
        if current_price <= EPSILON:
            return False, "KhÃ´ng thá»ƒ xÃ¡c Ä‘á»‹nh giÃ¡ Ä‘Æ¡n vá»‹ quá»¹ tá»« NAV trÆ°á»›c giao dá»‹ch."
        
        tranches = self.get_investor_tranches(investor_id)
        if not tranches: return False, "NhÃ  Ä‘áº§u tÆ° khÃ´ng cÃ³ vá»‘n."
        
        balance = sum(t.units for t in tranches) * current_price

        # 2. TÃ­nh toÃ¡n phÃ­ vÃ  sá»‘ dÆ° thá»±c nháº­n
        fee_info = self.calculate_investor_fee(investor_id, trans_date, old_total_nav)
        fee_on_full_balance = fee_info.get("total_fee", 0.0)
        net_balance = balance - fee_on_full_balance
        if net_balance < -EPSILON:
            return False, "Lá»—i dá»¯ liá»‡u: phÃ­ lá»›n hÆ¡n sá»‘ dÆ° nhÃ  Ä‘áº§u tÆ°."

        # 3. PhÃ¢n loáº¡i yÃªu cáº§u vÃ  Ä‘iá»u chá»‰nh
        is_full_withdrawal = False
        if net_amount >= net_balance - EPSILON:
            is_full_withdrawal = True
            performance_fee = fee_on_full_balance
            net_amount = net_balance # Tá»± Äá»˜NG ÄIá»€U CHá»ˆNH
        else:
            proportion = net_amount / net_balance if net_balance > EPSILON else 1.0
            performance_fee = fee_on_full_balance * proportion
        
        gross_withdrawal = net_amount + performance_fee
        
        # Kiá»ƒm tra cuá»‘i cÃ¹ng Ä‘á»ƒ Ä‘áº£m báº£o khÃ´ng cÃ³ lá»—i logic nÃ o
        if gross_withdrawal > balance + EPSILON:
            error_msg = f"Lá»—i logic: GiÃ¡ trá»‹ rÃºt gá»™p ({format_currency(gross_withdrawal)}) > Sá»‘ dÆ° ({format_currency(balance)})"
            logging.error(error_msg)
            return False, error_msg

        # NAV sau rÃºt pháº£i Ä‘Æ°á»£c tÃ­nh authoritative tá»« backend.
        authoritative_nav_after = max(0.0, old_total_nav - net_amount)
        if abs(total_nav_after - authoritative_nav_after) > 1.0:
            logging.warning(
                "NAV sau rÃºt do UI gá»­i (%s) khÃ´ng khá»›p NAV backend tÃ­nh toÃ¡n (%s). "
                "Sáº½ dÃ¹ng NAV backend.",
                total_nav_after,
                authoritative_nav_after,
            )
        authoritative_nav_after = round(authoritative_nav_after, 2)

        fee_units = round(performance_fee / current_price, 8) if current_price > 0 else 0.0
        withdrawal_units = round(net_amount / current_price, 8) if current_price > 0 else 0.0

        # 4. Ghi nháº­n giao dá»‹ch
        units_before = sum(t.units for t in tranches)
        if performance_fee > EPSILON:
            self._add_transaction(
                investor_id, trans_date, "PhÃ­", -performance_fee, authoritative_nav_after, -fee_units
            )
            self.fee_records.append(FeeRecord(
                id=len(self.fee_records) + 1,
                period=f"Withdrawal {trans_date.strftime('%Y-%m-%d')}", investor_id=investor_id,
                fee_amount=performance_fee, fee_units=fee_units, calculation_date=trans_date,
                units_before=units_before, units_after=units_before - fee_units - withdrawal_units, 
                nav_per_unit=current_price, description="Performance fee charged on withdrawal"
            ))
            self._transfer_fee_to_fund_manager(
                fee_units, current_price, trans_date, authoritative_nav_after, performance_fee
            )

        self._add_transaction(
            investor_id, trans_date, "RÃºt", -net_amount, authoritative_nav_after, -withdrawal_units
        )

        # 5. Cáº­p nháº­t tranches
        if is_full_withdrawal:
            self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
            logging.info(f"Investor {investor_id} performed a full withdrawal. All tranches removed.")
        else:
            if performance_fee > EPSILON:
                fee_details = {"total_fee": performance_fee, "current_price": current_price}
                self._apply_fee_to_investor_tranches(investor_id, fee_details, trans_date, crystallize=False)
            self._process_unit_reduction_fixed(investor_id, withdrawal_units, is_full=False)
                
        # Auto-backup after withdrawal transaction
        investor = self.get_investor_by_id(investor_id)
        investor_name = investor.display_name if investor else f"ID-{investor_id}"
        withdrawal_type = "FULL_WITHDRAWAL" if is_full_withdrawal else "PARTIAL_WITHDRAWAL"
        self._auto_backup_if_enabled(withdrawal_type, f"Withdrawal: {format_currency(net_amount)} by {investor_name}")
        
        return True, f"NhÃ  Ä‘áº§u tÆ° nháº­n {format_currency(net_amount)} (Gá»™p {format_currency(gross_withdrawal)}, PhÃ­ {format_currency(performance_fee)})"


    def process_nav_update(self, total_nav: float, trans_date: datetime) -> Tuple[bool, str]:
        """
        OPTIMIZED NAV Update - Ultra fast processing
        Chá»‰ cáº­p nháº­t NAV, KHÃ”NG tá»± Ä‘á»™ng cáº­p nháº­t HWM.
        """
        # Fast input validation
        if total_nav < 0:
            return False, "NAV tá»•ng khÃ´ng thá»ƒ Ã¢m"

        # Use naive datetime for local operations (Excel compatible)
        normalized_date = trans_date.replace(tzinfo=None) if hasattr(trans_date, 'tzinfo') and trans_date.tzinfo else trans_date
        
        # ULTRA FAST: Add transaction directly without debug logging
        self._add_transaction(0, normalized_date, "NAV Update", 0, total_nav, 0)
        
        # ULTRA FAST: Minimal save operation
        try:
            if hasattr(self, 'save_data'):
                self.save_data()  # Just save, no status checking
        except Exception:
            pass  # Don't let save errors slow down the UI
        
        # ULTRA FAST: Skip backup for immediate response
        # Auto-backup will be handled by background process
        
        return True, f"ÄÃ£ cáº­p nháº­t NAV: {format_currency(total_nav)}"

    # def crystallize_hwm(self, current_price: float):
    #     """
    #     Chá»‘t High Water Mark cho táº¥t cáº£ cÃ¡c tranche táº¡i má»™t má»©c giÃ¡ nháº¥t Ä‘á»‹nh.
    #     HÃ m nÃ y nÃªn Ä‘Æ°á»£c gá»i SAU KHI phÃ­ Ä‘Ã£ Ä‘Æ°á»£c tÃ­nh vÃ  Ã¡p dá»¥ng.
    #     """
    #     print(f"ðŸ’Ž Crystallizing HWM at price: {current_price:,.2f}")
    #     for tranche in self.tranches:
    #         if current_price > tranche.hwm:
    #             tranche.hwm = current_price
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
        profit_perc = (profit / invested_value) if invested_value > 0 else 0.0

        total_fee = 0.0
        hurdle_value = 0.0
        hwm_value = 0.0
        excess_profit = 0.0
        units_before = sum(t.units for t in tranches)

        for tranche in tranches:
            if tranche.units < EPSILON:
                continue
            
            # Sá»­a Ä‘á»•i: Truyá»n ending_date vÃ o hÃ m tÃ­nh toÃ¡n
            tranche_excess_profit = tranche.calculate_excess_profit(current_price, ending_date)
            hurdle_price = tranche.calculate_hurdle_price(ending_date)

            total_fee += PERFORMANCE_FEE_RATE * tranche_excess_profit
            hurdle_value += hurdle_price * tranche.units
            hwm_value += tranche.hwm * tranche.units
            excess_profit += tranche_excess_profit

        total_fee = round(total_fee, 0)
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
        self, 
        investor_id: int, 
        fee_details: Dict[str, Any],
        fee_date: datetime,
        crystallize: bool
    ) -> bool:
        try:
            total_fee = fee_details.get("total_fee", 0.0)
            current_price = fee_details.get("current_price")
            
            tranches_original = self.get_investor_tranches(investor_id)
            if not tranches_original or total_fee <= EPSILON or not current_price:
                return False

            tranches_with_profit = [
                t for t in tranches_original 
                if t.calculate_excess_profit(current_price, fee_date) > EPSILON
            ]
            if not tranches_with_profit:
                logging.warning(f"Investor {investor_id} has a total fee but no tranches with excess profit. Skipping fee application.")
                return False

            total_excess_profit_for_allocation = sum(
                t.calculate_excess_profit(current_price, fee_date) for t in tranches_with_profit
            )
            if total_excess_profit_for_allocation < EPSILON: return False

            tranches_copy = cp.deepcopy(tranches_original)
            total_units_to_reduce = round(total_fee / current_price, 8)
            units_reduced_so_far = 0.0
            
            for i, original_tranche in enumerate(tranches_with_profit):
                tranche = next(t for t in tranches_copy if t.tranche_id == original_tranche.tranche_id)
                
                if i == len(tranches_with_profit) - 1:
                    units_reduction = total_units_to_reduce - units_reduced_so_far
                else:
                    tranche_excess_profit = tranche.calculate_excess_profit(current_price, fee_date)
                    fee_proportion = tranche_excess_profit / total_excess_profit_for_allocation
                    fee_for_this_tranche = total_fee * fee_proportion
                    units_reduction = round(fee_for_this_tranche / current_price, 8)

                if units_reduction < EPSILON: continue
                units_reduction = min(units_reduction, tranche.units)

                fee_amount_for_tranche = units_reduction * current_price
                tranche.cumulative_fees_paid += fee_amount_for_tranche
                tranche.units -= units_reduction
                units_reduced_so_far += units_reduction
                
                if not crystallize:
                    tranche.invested_value = tranche.units * tranche.entry_nav

                if crystallize:
                    logging.info(f"Crystallizing tranche {tranche.tranche_id} for investor {investor_id}")
                    tranche.invested_value = tranche.units * current_price
                    tranche.entry_nav = current_price
                    tranche.hwm = current_price

            self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
            self.tranches.extend(tranches_copy)
            self.tranches = [t for t in self.tranches if t.units >= EPSILON]
            
            return True
        except Exception as e:
            logging.error(f"Error in _apply_fee_to_investor_tranches for investor {investor_id}: {e}", exc_info=True)
            return False
    def _transfer_fee_to_fund_manager(
        self, fee_units: float, current_price: float, fee_date: datetime, total_nav: float, fee_amount: float
    ):
        """
        Táº¡o tranche + transaction 'PhÃ­ Nháº­n' cho Fund Manager.
        NOTE: KhÃ´ng táº¡o FeeRecord cho Fund Manager á»Ÿ Ä‘Ã¢y â€” caller (apply fee / withdrawal) sáº½ táº¡o FeeRecord cho payer investor.
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
                fund_manager.id, fee_date, "PhÃ­ Nháº­n", fee_amount, total_nav, fee_units
            )

            print(f"Transferred {fee_units:.6f} units ({fee_amount:,.0f} VND) to Fund Manager")
            return True

        except Exception as e:
            print(f"Error transferring fee to Fund Manager: {str(e)}")
            return False


    def apply_year_end_fees_enhanced(self, fee_date: datetime, total_nav: float) -> Dict[str, Any]:
        """
        TÃ­nh & Ã¡p phÃ­ cuá»‘i nÄƒm, chuyá»ƒn units phÃ­ sang Fund Manager.
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
            if not regular_investors: return results # Tráº£ vá» success=True náº¿u khÃ´ng cÃ³ NÄT

            fund_manager = self.get_fund_manager()
            if not fund_manager:
                results["errors"].append("KhÃ´ng tÃ¬m tháº¥y Fund Manager")
                results["success"] = False
                return results

            current_price = self.calculate_price_per_unit(total_nav)

            for investor in regular_investors:
                try:
                    # TÃ­nh toÃ¡n chi tiáº¿t phÃ­ Má»˜T Láº¦N
                    fee_calculation = self.calculate_investor_fee(investor.id, fee_date, total_nav)
                    
                    if fee_calculation["total_fee"] > 1:
                        # ThÃªm giÃ¡ vÃ o dictionary Ä‘á»ƒ truyá»n Ä‘i
                        fee_calculation["current_price"] = current_price
                        
                        # Gá»i vá»›i crystallize=True
                        fee_applied = self._apply_fee_to_investor_tranches(
                            investor.id, fee_calculation, fee_date, crystallize=True
                        )
                        
                        if fee_applied:
                            units_removed = round(fee_calculation["total_fee"] / current_price, 8)

                            self._add_transaction(
                                investor.id, fee_date, "PhÃ­",
                                -fee_calculation["total_fee"], total_nav, -units_removed,
                            )
                            self._transfer_fee_to_fund_manager(
                                units_removed, current_price, fee_date, total_nav, fee_calculation["total_fee"]
                            )
                            
                            fee_record = FeeRecord(
                                id=len(self.fee_records) + 1,
                                period=fee_date.strftime("%Y"),
                                investor_id=investor.id,
                                fee_amount=fee_calculation["total_fee"],
                                fee_units=units_removed,
                                calculation_date=fee_date,
                                units_before=fee_calculation.get("units_before", 0.0),
                                units_after=fee_calculation.get("units_before", 0.0) - units_removed,
                                nav_per_unit=current_price,
                                description=f"Performance fee for year {fee_date.year}",
                            )
                            self.fee_records.append(fee_record)

                            # Cáº­p nháº­t káº¿t quáº£
                            results["total_fees"] += fee_calculation["total_fee"]
                            results["investors_processed"] += 1
                            results["fund_manager_units_received"] += units_removed
                            results["fee_details"].append({
                                "investor_id": investor.id, "investor_name": investor.name,
                                "fee_amount": fee_calculation["total_fee"], "fee_units": units_removed,
                                "excess_profit": fee_calculation["excess_profit"],
                            })
                        else:
                            results["errors"].append(f"KhÃ´ng thá»ƒ Ã¡p dá»¥ng phÃ­ cho nhÃ  Ä‘áº§u tÆ° {investor.name}")
                except Exception as e:
                    err = f"Lá»—i xá»­ lÃ½ nhÃ  Ä‘áº§u tÆ° {investor.name}: {str(e)}"
                    results["errors"].append(err)
                    results["success"] = False

            print(f"Fee application completed. Total fees: {results['total_fees']:,.0f} VND, "
                f"FM units received: {results['fund_manager_units_received']:.6f}")
            
            # Auto-backup after fee calculation
            if results['total_fees'] > 0:
                self._auto_backup_if_enabled("FEE_CALCULATION", f"Year-end fees applied: {format_currency(results['total_fees'])}")
            
            return results

        except Exception as e:
            error_msg = f"Critical error in apply_year_end_fees_enhanced: {str(e)}"
            logging.error(error_msg, exc_info=True)
            return {
                "success": False, "error": error_msg, "total_fees": 0.0,
                "investors_processed": 0, "fee_details": [], "errors": [error_msg],
                "fund_manager_units_received": 0.0,
            }

    # ================================
    # Lifetime performance & reports
    # ================================
    def calculate_investor_performance_cashflow(self, investor_id: int, current_nav: float) -> Dict[str, float]:
        """
        Cashflow-based performance:
        total_wealth = current_value + cash_out
        pnl = total_wealth - cash_in
        """
        investor_transactions = [t for t in self.transactions if t.investor_id == investor_id]

        cash_in = sum(t.amount for t in investor_transactions if t.type == "Náº¡p" and t.amount > 0)
        cash_out = sum(-t.amount for t in investor_transactions if t.type in ["RÃºt", "Fund Manager Withdrawal"] and t.amount < 0)
        fees_paid = sum(-t.amount for t in investor_transactions if t.type == "PhÃ­" and t.amount < 0)

        current_units = self.get_investor_units(investor_id)
        current_price = self.calculate_price_per_unit(current_nav)
        current_value = current_units * current_price

        net_profit = current_value + cash_out - cash_in
        gross_profit = net_profit + fees_paid

        gross_return = (gross_profit / cash_in) if cash_in > EPSILON else 0.0
        net_return = (net_profit / cash_in) if cash_in > EPSILON else 0.0

        return {
            "cash_in": cash_in,
            "cash_out": cash_out,
            "fees_paid": fees_paid,
            "current_units": current_units,
            "current_value": current_value,
            "gross_profit": gross_profit,
            "net_profit": net_profit,
            "gross_return": gross_return,
            "net_return": net_return,
        }

    def calculate_performance_fee(
        self, investor_id: int, start_date: datetime, end_date: datetime, current_nav: float
    ) -> Dict[str, Any]:
        """Backward-compatible wrapper used by some UI paths."""
        if not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.min.time())
        return self.calculate_investor_fee(investor_id, end_date, current_nav)

    def get_investor_lifetime_performance(self, investor_id: int, current_nav: float) -> Dict:
        performance = self.calculate_investor_performance_cashflow(investor_id, current_nav)

        # Fallback for legacy datasets that have tranches but no historical transactions.
        if performance["cash_in"] <= EPSILON and self.get_investor_tranches(investor_id):
            total_original_invested = sum(
                getattr(t, "original_invested_value", t.units * t.entry_nav)
                for t in self.get_investor_tranches(investor_id)
            )
            total_fees_paid = sum(fr.fee_amount for fr in self.fee_records if fr.investor_id == investor_id)
            current_value = performance["current_value"]
            gross_profit = current_value + total_fees_paid - total_original_invested
            net_profit = current_value - total_original_invested
            return {
                "original_invested": total_original_invested,
                "current_value": current_value,
                "total_fees_paid": total_fees_paid,
                "gross_profit": gross_profit,
                "net_profit": net_profit,
                "gross_return": (gross_profit / total_original_invested) if total_original_invested > EPSILON else 0.0,
                "net_return": (net_profit / total_original_invested) if total_original_invested > EPSILON else 0.0,
                "current_units": performance["current_units"],
            }

        return {
            "original_invested": performance["cash_in"],
            "current_value": performance["current_value"],
            "total_fees_paid": performance["fees_paid"],
            "gross_profit": performance["gross_profit"],
            "net_profit": performance["net_profit"],
            "gross_return": performance["gross_return"],
            "net_return": performance["net_return"],
            "current_units": performance["current_units"],
        }

    def get_fee_history(self, investor_id: Optional[int] = None) -> List[FeeRecord]:
        if investor_id is None:
            return self.fee_records
        return [record for record in self.fee_records if record.investor_id == investor_id]

    # ================================
    # Undo / Delete transactions
    # ================================
    def undo_last_transaction(self, transaction_id: int) -> bool:
        """
        ENHANCED: Undo transaction with snapshot support
        """
        # Create operation snapshot before attempting undo
        snapshot_id = None
        # backup_manager removed - snapshots disabled
        # snapshot_id = self.backup_manager.create_operation_snapshot(
        #     self, "UNDO_TRANSACTION", f"Before undo transaction {transaction_id}"
        # )
        
        try:
            transaction = next((t for t in self.transactions if t.id == transaction_id), None)
            if not transaction:
                print(f"âŒ Transaction {transaction_id} not found")
                return False

            # Allow undo for more recent transactions (increased from 5 to 10)
            recent_transactions = sorted(self.transactions, key=lambda x: x.date, reverse=True)[:10]
            if transaction not in recent_transactions:
                print(f"âŒ Transaction {transaction_id} is too old to undo (only last 10 allowed)")
                return False

            print(f"ðŸ”„ Attempting to undo {transaction.type} transaction {transaction_id}")
            
            success = False
            if transaction.type == "Náº¡p":
                success = self._undo_deposit_enhanced(transaction)
            elif transaction.type == "RÃºt":
                success = self._undo_withdrawal_enhanced(transaction)
            elif transaction.type == "NAV Update":
                success = self._undo_nav_update_enhanced(transaction)
            elif transaction.type in ["PhÃ­", "Fund Manager Withdrawal"]:
                success = self._simple_transaction_removal_enhanced(transaction)
            else:
                print(f"âŒ Unknown transaction type: {transaction.type}")
                return False
            
            if success:
                print(f"âœ… Successfully undone transaction {transaction_id}")
                # Auto-backup after successful undo
                self._auto_backup_if_enabled("UNDO_TRANSACTION", f"Undone transaction {transaction_id} ({transaction.type})")
                return True
            else:
                print(f"âŒ Failed to undo transaction {transaction_id}")
                # Restore snapshot if undo failed (backup_manager removed)
                # print(f"ðŸ”„ Restoring snapshot {snapshot_id}")
                return False

        except Exception as e:
            print(f"âŒ Error in undo_last_transaction: {str(e)}")
            # Restore snapshot on exception (backup_manager removed)
            # print(f"ðŸ”„ Restoring snapshot {snapshot_id} due to error")
            return False

    def _undo_deposit_enhanced(self, original_transaction) -> bool:
        """
        ENHANCED: Undo deposit transaction with better validation
        """
        try:
            investor_id = original_transaction.investor_id
            amount = original_transaction.amount
            deposit_date = original_transaction.date

            print(f"  ðŸ” Looking for tranche created on {deposit_date} with amount {amount:,}")

            # More flexible time window for matching (6 hours instead of 1)
            matching_tranches = [
                t for t in self.tranches
                if (t.investor_id == investor_id and 
                    abs((t.entry_date - deposit_date).total_seconds()) < 21600)  # 6 hours
            ]
            
            if not matching_tranches:
                print(f"  âŒ No matching tranches found for investor {investor_id}")
                return False

            tranche_to_remove = max(matching_tranches, key=lambda x: x.entry_date)
            expected_amount = tranche_to_remove.units * tranche_to_remove.entry_nav
            
            print(f"  ðŸ“Š Tranche to remove: {tranche_to_remove.tranche_id}")
            print(f"  ðŸ“Š Expected amount: {expected_amount:,}, Transaction amount: {amount:,}")

            # More lenient amount checking (allow 1% difference)
            if abs(expected_amount - amount) > max(1, amount * 0.01):
                print(f"  âŒ Amount mismatch too large")
                return False

            # Validate investor still has other tranches or will have 0 units
            remaining_units = self.get_investor_units(investor_id) - tranche_to_remove.units
            print(f"  ðŸ“Š Investor units after removal: {remaining_units:.6f}")

            self.tranches.remove(tranche_to_remove)
            self.transactions.remove(original_transaction)
            
            print(f"  âœ… Removed tranche {tranche_to_remove.tranche_id}")
            return True

        except Exception as e:
            print(f"  âŒ Error in _undo_deposit_enhanced: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _undo_withdrawal(self, original_transaction) -> bool:
        """
        NÃ‚NG Cáº¤P: HoÃ n tÃ¡c má»™t giao dá»‹ch rÃºt tiá»n.
        Thao tÃ¡c nÃ y phá»©c táº¡p vÃ  chá»‰ nÃªn dÃ¹ng cho cÃ¡c giao dá»‹ch gáº§n Ä‘Ã¢y.
        NÃ³ sáº½ khÃ´i phá»¥c tráº¡ng thÃ¡i báº±ng cÃ¡ch tÃ­nh toÃ¡n ngÆ°á»£c vÃ  thao tÃ¡c trÃªn bá»™ nhá»›.
        """
        try:
            investor_id = original_transaction.investor_id
            trans_date = original_transaction.date

            # 1. TÃ¬m táº¥t cáº£ cÃ¡c báº£n ghi liÃªn quan trong bá»™ nhá»›
            fee_txn = next((
                t for t in self.transactions 
                if t.investor_id == investor_id and t.type == "PhÃ­" and 
                abs(safe_total_seconds_between(t.date, trans_date)) < 1
            ), None)
            
            fm_fee_txns = [
                t for t in self.transactions 
                if t.type == "PhÃ­ Nháº­n" and abs(safe_total_seconds_between(t.date, trans_date)) < 1
            ]

            fee_record_to_undo = next((
                fr for fr in self.fee_records
                if fr.investor_id == investor_id and fr.period.startswith("Withdrawal") and 
                abs((fr.calculation_date - trans_date).total_seconds()) < 1
            ), None)

            if not fee_record_to_undo and fee_txn:
                print(f"ERROR: Cannot undo withdrawal {original_transaction.id}. Corresponding FeeRecord not found.")
                return False

            # 2. HoÃ n tÃ¡c cÃ¡c thay Ä‘á»•i trÃªn tranche cá»§a nhÃ  Ä‘áº§u tÆ°
            # Láº¥y láº¡i cÃ¡c giÃ¡ trá»‹ tá»« FeeRecord
            units_before_fee = fee_record_to_undo.units_before if fee_record_to_undo else self.get_investor_units(investor_id) + abs(original_transaction.units_change)
            
            # XÃ³a cÃ¡c tranche Ä‘Ã£ bá»‹ reset (do _apply_fee_to_investor_tranches)
            # vÃ  khÃ´i phá»¥c láº¡i tráº¡ng thÃ¡i cÅ© hÆ¡n. Logic nÃ y ráº¥t phá»©c táº¡p.
            # Má»™t cÃ¡ch tiáº¿p cáº­n Ä‘Æ¡n giáº£n vÃ  an toÃ n hÆ¡n lÃ  khÃ´ng cho phÃ©p undo withdrawal.
            # Tuy nhiÃªn, náº¿u váº«n muá»‘n thá»±c hiá»‡n, chÃºng ta cáº§n má»™t cÆ¡ cháº¿ snapshot.
            # VÃ¬ hiá»‡n táº¡i khÃ´ng cÃ³, chÃºng ta sáº½ thÃ´ng bÃ¡o giá»›i háº¡n nÃ y.
            print("WARNING: 'Undo Withdrawal' is a complex operation and may not perfectly restore state without a snapshot system.")
            print("This feature should be used with caution only for immediate corrections.")
            
            # VÃ¬ sá»± phá»©c táº¡p vÃ  rá»§i ro, chÃºng ta sáº½ ngÄƒn cháº·n undo withdrawal phá»©c táº¡p
            # vÃ  chá»‰ cho phÃ©p undo cÃ¡c giao dá»‹ch Ä‘Æ¡n giáº£n
            if fee_txn or fm_fee_txns:
                print("âŒ HoÃ n tÃ¡c giao dá»‹ch rÃºt tiá»n cÃ³ tÃ­nh phÃ­ chÆ°a Ä‘Æ°á»£c há»— trá»£ vÃ¬ Ä‘á»™ phá»©c táº¡p cao. Vui lÃ²ng xÃ³a vÃ  táº¡o láº¡i giao dá»‹ch.")
                return False

            # Náº¿u lÃ  má»™t láº§n rÃºt tiá»n Ä‘Æ¡n giáº£n khÃ´ng cÃ³ phÃ­
            units_to_restore = abs(original_transaction.units_change)
            tranches = self.get_investor_tranches(investor_id)
            if not tranches:
                # Náº¿u nhÃ  Ä‘áº§u tÆ° Ä‘Ã£ rÃºt háº¿t, táº¡o láº¡i 1 tranche
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
                # PhÃ¢n bá»• láº¡i units
                total_existing_units = self.get_investor_units(investor_id)
                for tranche in tranches:
                    proportion = tranche.units / total_existing_units if total_existing_units > 0 else 1.0/len(tranches)
                    tranche.units += units_to_restore * proportion
                    tranche.invested_value += (units_to_restore * proportion) * tranche.entry_nav

            # XÃ³a transaction rÃºt tiá»n
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
    
    def _undo_withdrawal_enhanced(self, original_transaction) -> bool:
        """
        ENHANCED: Improved withdrawal undo with snapshot system
        """
        try:
            investor_id = original_transaction.investor_id
            trans_date = original_transaction.date
            
            print(f"  ðŸ” Analyzing withdrawal transaction for investor {investor_id}")

            # Find related transactions within larger time window (1 hour)
            fee_txn = next((
                t for t in self.transactions 
                if t.investor_id == investor_id and t.type == "PhÃ­" and 
                abs(safe_total_seconds_between(t.date, trans_date)) < 3600
            ), None)
            
            fm_fee_txns = [
                t for t in self.transactions 
                if t.type == "PhÃ­ Nháº­n" and abs(safe_total_seconds_between(t.date, trans_date)) < 3600
            ]

            fee_record_to_undo = next((
                fr for fr in self.fee_records
                if fr.investor_id == investor_id and fr.period.startswith("Withdrawal") and 
                abs((fr.calculation_date - trans_date).total_seconds()) < 3600
            ), None)

            # Check if this is a complex withdrawal with fees
            if fee_txn or fm_fee_txns or fee_record_to_undo:
                print("  âš ï¸  Complex withdrawal with fees detected")
                if self.snapshot_manager:
                    print("  âœ… Using snapshot system to handle complex withdrawal undo")
                    # For complex withdrawals, we rely on snapshot restore
                    # Just remove the main withdrawal transaction and let snapshot handle the rest
                    try:
                        self.transactions.remove(original_transaction)
                        if fee_txn:
                            self.transactions.remove(fee_txn)
                        for fm_fee_txn in fm_fee_txns:
                            self.transactions.remove(fm_fee_txn)
                        if fee_record_to_undo:
                            self.fee_records.remove(fee_record_to_undo)
                        print("  âœ… Removed complex withdrawal transactions and fee records")
                        print("  ðŸ’¡ Note: Snapshot system will restore full state if any issues occur")
                        return True
                    except Exception as e:
                        print(f"  âŒ Error removing complex withdrawal components: {e}")
                        return False
                else:
                    print("  â„¹ï¸  Snapshot khÃ´ng kháº£ dá»¥ng, chuyá»ƒn sang luá»“ng hoÃ n tÃ¡c atomic.")
                    return self._delete_withdrawal_transaction(original_transaction)

            # Simple withdrawal without fees - safe to undo
            print(f"  âœ… Simple withdrawal detected, safe to undo")
            
            units_to_restore = abs(original_transaction.units_change)
            tranches = self.get_investor_tranches(investor_id)
            
            print(f"  ðŸ“Š Units to restore: {units_to_restore:.6f}")
            print(f"  ðŸ“Š Current tranches: {len(tranches)}")
            
            if not tranches:
                # Investor has no tranches - create new one
                print(f"  ðŸ”„ Creating new tranche for units restoration")
                price = abs(original_transaction.amount / original_transaction.units_change)
                
                import uuid
                from .models import Tranche
                tranche = Tranche(
                    investor_id=investor_id,
                    tranche_id=str(uuid.uuid4()),
                    entry_date=trans_date, 
                    entry_nav=price, 
                    units=units_to_restore,
                    original_invested_value=units_to_restore * price,
                    hwm=price,
                    original_entry_date=trans_date, 
                    original_entry_nav=price,
                    cumulative_fees_paid=0.0
                )
                self.tranches.append(tranche)
                print(f"  âœ… Created tranche {tranche.tranche_id}")
            else:
                # Restore units proportionally to existing tranches
                print(f"  ðŸ”„ Restoring units proportionally to existing tranches")
                total_existing_units = self.get_investor_units(investor_id)
                
                for tranche in tranches:
                    proportion = tranche.units / total_existing_units if total_existing_units > 0 else 1.0/len(tranches)
                    units_to_add = units_to_restore * proportion
                    value_to_add = units_to_add * tranche.entry_nav
                    
                    tranche.units += units_to_add
                    tranche.invested_value += value_to_add
                    
                    print(f"    ðŸ”„ Tranche {tranche.tranche_id}: +{units_to_add:.6f} units")

            # Remove the withdrawal transaction
            self.transactions.remove(original_transaction)
            print(f"  âœ… Removed withdrawal transaction {original_transaction.id}")
            
            return True

        except Exception as e:
            print(f"  âŒ Error in _undo_withdrawal_enhanced: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _undo_nav_update_enhanced(self, original_transaction) -> bool:
        """
        ENHANCED: Undo NAV update with validation
        """
        try:
            print(f"  ðŸ”„ Removing NAV Update transaction {original_transaction.id}")
            self.transactions.remove(original_transaction)
            print(f"  âœ… NAV Update removed successfully")
            return True
        except Exception as e:
            print(f"  âŒ Error in _undo_nav_update_enhanced: {str(e)}")
            return False
    
    def _simple_transaction_removal_enhanced(self, transaction) -> bool:
        """
        ENHANCED: Remove simple transactions with validation
        """
        try:
            print(f"  ðŸ”„ Removing {transaction.type} transaction {transaction.id}")
            
            # Additional validation for fee transactions
            if transaction.type == "PhÃ­":
                # Check if there are related fee records
                related_fee_records = [
                    fr for fr in self.fee_records
                    if (fr.investor_id == transaction.investor_id and 
                        abs((fr.calculation_date - transaction.date).total_seconds()) < 3600)
                ]
                if related_fee_records:
                    print(f"  âš ï¸  Found {len(related_fee_records)} related fee records")
                    # Remove related fee records as well
                    for fee_record in related_fee_records:
                        self.fee_records.remove(fee_record)
                        print(f"    ðŸ—‘ï¸  Removed fee record {fee_record.id}")
            
            self.transactions.remove(transaction)
            print(f"  âœ… Transaction removed successfully")
            return True
        except Exception as e:
            print(f"  âŒ Error in _simple_transaction_removal_enhanced: {str(e)}")
            return False

    # ================================
    # Data Integrity Validation
    # ================================
    def validate_data_integrity(self, detailed: bool = True) -> Dict[str, Any]:
        """
        ENHANCED: Comprehensive data integrity validation
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'summary': {},
            'details': {} if detailed else None
        }
        
        try:
            print("ðŸ” Starting data integrity validation...")
            
            # 1. Validate Investors
            investor_issues = self._validate_investors()
            validation_results['summary']['investors'] = investor_issues
            if investor_issues['errors']:
                validation_results['errors'].extend(investor_issues['errors'])
                validation_results['is_valid'] = False
            if investor_issues['warnings']:
                validation_results['warnings'].extend(investor_issues['warnings'])
            
            # 2. Validate Tranches
            tranche_issues = self._validate_tranches()
            validation_results['summary']['tranches'] = tranche_issues
            if tranche_issues['errors']:
                validation_results['errors'].extend(tranche_issues['errors'])
                validation_results['is_valid'] = False
            if tranche_issues['warnings']:
                validation_results['warnings'].extend(tranche_issues['warnings'])
            
            # 3. Validate Transactions
            transaction_issues = self._validate_transactions()
            validation_results['summary']['transactions'] = transaction_issues
            if transaction_issues['errors']:
                validation_results['errors'].extend(transaction_issues['errors'])
                validation_results['is_valid'] = False
            if transaction_issues['warnings']:
                validation_results['warnings'].extend(transaction_issues['warnings'])
            
            # 4. Validate Fee Records
            fee_issues = self._validate_fee_records()
            validation_results['summary']['fee_records'] = fee_issues
            if fee_issues['errors']:
                validation_results['errors'].extend(fee_issues['errors'])
                validation_results['is_valid'] = False
            if fee_issues['warnings']:
                validation_results['warnings'].extend(fee_issues['warnings'])
            
            # 5. Cross-validation between different data types
            cross_issues = self._validate_cross_references()
            validation_results['summary']['cross_references'] = cross_issues
            if cross_issues['errors']:
                validation_results['errors'].extend(cross_issues['errors'])
                validation_results['is_valid'] = False
            if cross_issues['warnings']:
                validation_results['warnings'].extend(cross_issues['warnings'])
            
            # Summary
            total_errors = len(validation_results['errors'])
            total_warnings = len(validation_results['warnings'])
            
            if validation_results['is_valid']:
                print(f"âœ… Data integrity validation PASSED")
            else:
                print(f"âŒ Data integrity validation FAILED")
            
            print(f"ðŸ“Š Found {total_errors} errors, {total_warnings} warnings")
            
            validation_results['summary']['total_errors'] = total_errors
            validation_results['summary']['total_warnings'] = total_warnings
            
            return validation_results
            
        except Exception as e:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Quy trÃ¬nh kiá»ƒm tra dá»¯ liá»‡u tháº¥t báº¡i: {str(e)}")
            print(f"âŒ Data validation error: {str(e)}")
            return validation_results
    
    def _validate_investors(self) -> Dict[str, Any]:
        """Validate investor data"""
        issues = {'errors': [], 'warnings': [], 'count': len(self.investors)}
        
        investor_ids = set()
        fund_managers = []
        
        for investor in self.investors:
            # Check for duplicate IDs
            if investor.id in investor_ids:
                issues['errors'].append(f"TrÃ¹ng ID nhÃ  Ä‘áº§u tÆ°: {investor.id}")
            investor_ids.add(investor.id)
            
            # Check for fund managers
            if investor.is_fund_manager:
                fund_managers.append(investor.id)
            
            # Basic data validation
            if not investor.name or not investor.name.strip():
                issues['errors'].append(f"NhÃ  Ä‘áº§u tÆ° {investor.id} cÃ³ tÃªn trá»‘ng")
            
            if investor.id < 0 or (investor.id == 0 and not investor.is_fund_manager):
                issues['errors'].append(f"ID nhÃ  Ä‘áº§u tÆ° khÃ´ng há»£p lá»‡: {investor.id}")
        
        # Check fund manager count
        if len(fund_managers) == 0:
            issues['warnings'].append("KhÃ´ng tÃ¬m tháº¥y Fund Manager")
        elif len(fund_managers) > 1:
            issues['warnings'].append(f"TÃ¬m tháº¥y nhiá»u Fund Manager: {fund_managers}")
        
        return issues
    
    def _validate_tranches(self) -> Dict[str, Any]:
        """Validate tranche data"""
        issues = {'errors': [], 'warnings': [], 'count': len(self.tranches)}
        
        tranche_ids = set()
        
        for tranche in self.tranches:
            # Check for duplicate tranche IDs
            if tranche.tranche_id in tranche_ids:
                issues['errors'].append(f"TrÃ¹ng ID tranche: {tranche.tranche_id}")
            tranche_ids.add(tranche.tranche_id)
            
            # Validate using model validation
            from .models import validate_tranche
            is_valid, errors = validate_tranche(tranche)
            if not is_valid:
                for error in errors:
                    issues['errors'].append(f"Tranche {tranche.tranche_id}: {error}")
            
            # Check if investor exists
            investor_exists = any(inv.id == tranche.investor_id for inv in self.investors)
            if not investor_exists:
                issues['errors'].append(f"Tranche {tranche.tranche_id} tham chiáº¿u nhÃ  Ä‘áº§u tÆ° khÃ´ng tá»“n táº¡i: {tranche.investor_id}")
            
            # Check for negative units
            if tranche.units < 0:
                issues['errors'].append(f"Tranche {tranche.tranche_id} cÃ³ Ä‘Æ¡n vá»‹ quá»¹ Ã¢m: {tranche.units}")
            
            # Check for zero units (warning)
            if abs(tranche.units) < 0.000001:
                issues['warnings'].append(f"Tranche {tranche.tranche_id} cÃ³ Ä‘Æ¡n vá»‹ quá»¹ gáº§n báº±ng 0: {tranche.units}")
        
        return issues
    
    def _validate_transactions(self) -> Dict[str, Any]:
        """Validate transaction data"""
        issues = {'errors': [], 'warnings': [], 'count': len(self.transactions)}
        
        transaction_ids = set()
        
        for transaction in self.transactions:
            # Check for duplicate transaction IDs
            if transaction.id in transaction_ids:
                issues['errors'].append(f"TrÃ¹ng ID giao dá»‹ch: {transaction.id}")
            transaction_ids.add(transaction.id)
            
            # Validate using model validation
            from .models import validate_transaction
            is_valid, errors = validate_transaction(transaction)
            if not is_valid:
                for error in errors:
                    issues['errors'].append(f"Giao dá»‹ch {transaction.id}: {error}")
            
            # Check if investor exists
            investor_exists = any(inv.id == transaction.investor_id for inv in self.investors)
            if not investor_exists:
                issues['errors'].append(f"Giao dá»‹ch {transaction.id} tham chiáº¿u nhÃ  Ä‘áº§u tÆ° khÃ´ng tá»“n táº¡i: {transaction.investor_id}")
        
        return issues
    
    def _validate_fee_records(self) -> Dict[str, Any]:
        """Validate fee record data"""
        issues = {'errors': [], 'warnings': [], 'count': len(self.fee_records)}
        
        fee_record_ids = set()
        
        for fee_record in self.fee_records:
            # Check for duplicate fee record IDs
            if fee_record.id in fee_record_ids:
                issues['errors'].append(f"TrÃ¹ng ID báº£n ghi phÃ­: {fee_record.id}")
            fee_record_ids.add(fee_record.id)
            
            # Validate using model validation
            from .models import validate_fee_record
            is_valid, errors = validate_fee_record(fee_record)
            if not is_valid:
                for error in errors:
                    issues['errors'].append(f"Báº£n ghi phÃ­ {fee_record.id}: {error}")
            
            # Check if investor exists
            investor_exists = any(inv.id == fee_record.investor_id for inv in self.investors)
            if not investor_exists:
                issues['errors'].append(f"Báº£n ghi phÃ­ {fee_record.id} tham chiáº¿u nhÃ  Ä‘áº§u tÆ° khÃ´ng tá»“n táº¡i: {fee_record.investor_id}")
        
        return issues
    
    def _validate_cross_references(self) -> Dict[str, Any]:
        """Validate cross-references between different data types"""
        issues = {'errors': [], 'warnings': []}
        
        # Check consistency between transactions and tranches
        for investor in self.investors:
            investor_tranches = self.get_investor_tranches(investor.id)
            investor_transactions = [t for t in self.transactions if t.investor_id == investor.id]
            
            # Check if investor has transactions but no tranches
            deposit_txns = [t for t in investor_transactions if t.type == "Náº¡p"]
            if deposit_txns and not investor_tranches:
                issues['warnings'].append(f"NhÃ  Ä‘áº§u tÆ° {investor.id} cÃ³ giao dá»‹ch náº¡p nhÆ°ng khÃ´ng cÃ³ tranche")
            
            # Check if investor has tranches but no deposit transactions  
            if investor_tranches and not deposit_txns:
                issues['warnings'].append(f"NhÃ  Ä‘áº§u tÆ° {investor.id} cÃ³ tranche nhÆ°ng khÃ´ng cÃ³ giao dá»‹ch náº¡p")
        
        # Check total units consistency
        try:
            total_units = sum(t.units for t in self.tranches)
            if total_units <= 0:
                issues['warnings'].append(f"Tá»•ng Ä‘Æ¡n vá»‹ quá»¹ hiá»‡n lÃ  {total_units}")
        except Exception as e:
            issues['errors'].append(f"Lá»—i tÃ­nh tá»•ng Ä‘Æ¡n vá»‹ quá»¹: {str(e)}")
        
        return issues

    # ================================
    # Backup & Recovery Management
    # ================================
    def create_manual_backup(self, backup_type: str = "MANUAL") -> str:
        """
        Táº¡o manual backup
        Note: backup_manager removed - backups handled by api_backup service
        """
        print("â„¹ï¸ Viá»‡c táº¡o sao lÆ°u thá»§ cÃ´ng hiá»‡n do dá»‹ch vá»¥ api_backup xá»­ lÃ½")
        return None
    
    def restore_from_backup(self, backup_id: str = None, backup_date: str = None) -> bool:
        """
        Restore tá»« backup
        Note: backup_manager removed - backups handled by api_backup service
        """
        print("â„¹ï¸ Viá»‡c khÃ´i phá»¥c sao lÆ°u hiá»‡n do dá»‹ch vá»¥ api_backup xá»­ lÃ½")
        return False
    
    def get_backup_status(self) -> Dict[str, Any]:
        """
        Get backup system status
        Note: backup_manager removed - backups handled by api_backup service
        """
        return {'enabled': True, 'message': 'Sao lÆ°u Ä‘Æ°á»£c xá»­ lÃ½ bá»Ÿi dá»‹ch vá»¥ api_backup'}
    
    def list_available_backups(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        List available backups
        Note: backup_manager removed - backups handled by api_backup service
        """
        return []
    
    def trigger_auto_backup_if_needed(self) -> bool:
        """
        Trigger auto backup náº¿u cáº§n (called from main application)
        Note: backup_manager removed - backups handled by api_backup service
        """
        return True  # Auto backup service runs independently
    
    def create_emergency_backup(self) -> str:
        """
        Create emergency backup (immediate, high priority)
        Note: backup_manager removed - return empty string
        """
        # backup_manager removed - emergency backup disabled
        return ""

    def delete_transaction(self, transaction_id: int) -> bool:
        try:
            transaction_to_delete = next((t for t in self.transactions if t.id == transaction_id), None)
            if not transaction_to_delete:
                return False

            self.backup_before_operation(f"Delete transaction {transaction_id}")

            recent_transactions = sorted(self.transactions, key=lambda x: (x.date, x.id), reverse=True)[:10]
            if transaction_to_delete not in recent_transactions:
                print(f"Giao dá»‹ch {transaction_id} Ä‘Ã£ quÃ¡ cÅ© Ä‘á»ƒ xÃ³a an toÃ n")
                return False

            if transaction_to_delete.type == "Náº¡p":
                return self._delete_deposit_transaction(transaction_to_delete)
            elif transaction_to_delete.type == "RÃºt":
                return self._delete_withdrawal_transaction(transaction_to_delete)
            elif transaction_to_delete.type == "NAV Update":
                return self._delete_nav_update_transaction(transaction_to_delete)
            elif transaction_to_delete.type in ["PhÃ­", "Fund Manager Withdrawal", "PhÃ­ Nháº­n"]:
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
                        f"KhÃ´ng thá»ƒ xÃ³a giao dá»‹ch náº¡p {transaction.id}: tranche Ä‘Ã£ bá»‹ áº£nh hÆ°á»Ÿng bá»Ÿi phÃ­"
                    )
                    return False
                self.tranches.remove(best_match)

            self.transactions.remove(transaction)
            return True

        except Exception as e:
            print(f"Error deleting deposit transaction: {str(e)}")
            return False

    def _remove_units_from_fund_manager(self, units_to_remove: float, reference_date: datetime) -> bool:
        """Remove units from Fund Manager tranches when reverting fee transfer."""
        if units_to_remove <= EPSILON:
            return True

        fund_manager = self.get_fund_manager()
        if not fund_manager:
            return False

        original_state = cp.deepcopy(self.tranches)
        remaining_units = units_to_remove

        fm_tranches = [t for t in self.tranches if t.investor_id == fund_manager.id and t.units > EPSILON]
        fm_tranches.sort(
            key=lambda t: (
                abs(safe_total_seconds_between(t.entry_date, reference_date)),
                abs(t.units - units_to_remove),
            )
        )

        for tranche in fm_tranches:
            if remaining_units <= EPSILON:
                break
            units_delta = min(tranche.units, remaining_units)
            tranche.units -= units_delta
            tranche.invested_value = tranche.units * tranche.entry_nav
            remaining_units -= units_delta

        self.tranches = [t for t in self.tranches if t.units >= EPSILON]
        if remaining_units > 1e-8:
            self.tranches = original_state
            return False

        return True

    def _rollback_cumulative_fee_on_tranches(self, investor_id: int, fee_amount: float) -> bool:
        """
        Roll back cumulative fee counters on investor tranches when undoing/deleting
        a withdrawal fee transaction.
        """
        if fee_amount <= EPSILON:
            return True

        investor_tranches = [
            t for t in self.get_investor_tranches(investor_id)
            if getattr(t, "cumulative_fees_paid", 0.0) > EPSILON
        ]
        if not investor_tranches:
            return True

        total_cumulative_paid = sum(max(0.0, getattr(t, "cumulative_fees_paid", 0.0)) for t in investor_tranches)
        if total_cumulative_paid <= EPSILON:
            return True

        rollback_target = min(fee_amount, total_cumulative_paid)
        rollback_remaining = rollback_target

        for idx, tranche in enumerate(investor_tranches):
            current_paid = max(0.0, getattr(tranche, "cumulative_fees_paid", 0.0))
            if current_paid <= EPSILON:
                continue

            if idx == len(investor_tranches) - 1:
                deduction = min(current_paid, rollback_remaining)
            else:
                proportional = rollback_target * (current_paid / total_cumulative_paid)
                deduction = min(current_paid, proportional, rollback_remaining)

            tranche.cumulative_fees_paid = max(0.0, current_paid - deduction)
            rollback_remaining -= deduction
            if rollback_remaining <= EPSILON:
                break

        # Numerical tolerance to avoid rollback failures from floating-point dust.
        return rollback_remaining <= 0.01

    def _delete_withdrawal_transaction(self, transaction) -> bool:
        snapshot = {
            "tranches": cp.deepcopy(self.tranches),
            "transactions": cp.deepcopy(self.transactions),
            "fee_records": cp.deepcopy(self.fee_records),
        }

        try:
            investor_id = transaction.investor_id
            investor_transactions = [t for t in self.transactions if t.investor_id == investor_id]
            investor_transactions.sort(key=lambda x: (x.date, x.id), reverse=True)
            if investor_transactions[0].id != transaction.id:
                print(
                    f"KhÃ´ng thá»ƒ xÃ³a giao dá»‹ch rÃºt {transaction.id}: Ä‘Ã¢y khÃ´ng pháº£i giao dá»‹ch má»›i nháº¥t cá»§a nhÃ  Ä‘áº§u tÆ°"
                )
                return False

            related_fee_txn = next(
                (
                    t
                    for t in self.transactions
                    if t.investor_id == investor_id
                    and t.type == "PhÃ­"
                    and abs(safe_total_seconds_between(t.date, transaction.date)) < 3600
                ),
                None,
            )
            related_fm_fee_txns = [
                t
                for t in self.transactions
                if t.type == "PhÃ­ Nháº­n"
                and abs(safe_total_seconds_between(t.date, transaction.date)) < 3600
            ]
            related_fee_records = [
                f
                for f in self.fee_records
                if f.investor_id == investor_id
                and f.period.startswith("Withdrawal")
                and abs(safe_total_seconds_between(f.calculation_date, transaction.date)) < 3600
            ]

            gross_amount = abs(transaction.amount)
            units_to_restore = abs(transaction.units_change)
            if related_fee_txn:
                gross_amount += abs(related_fee_txn.amount)
                units_to_restore += abs(related_fee_txn.units_change)

            investor_tranches = self.get_investor_tranches(investor_id)

            if not investor_tranches:
                entry_nav = gross_amount / units_to_restore if units_to_restore > EPSILON else DEFAULT_UNIT_PRICE
                tranche = Tranche(
                    investor_id=investor_id,
                    tranche_id=str(uuid.uuid4()),
                    entry_date=transaction.date,
                    entry_nav=entry_nav,
                    units=units_to_restore,
                    hwm=entry_nav,
                    original_entry_date=transaction.date,
                    original_entry_nav=entry_nav,
                    original_invested_value=gross_amount,
                    cumulative_fees_paid=0.0,
                )
                tranche.invested_value = tranche.units * tranche.entry_nav
                self.tranches.append(tranche)
            else:
                total_existing_units = sum(t.units for t in investor_tranches)
                for tranche in investor_tranches:
                    if total_existing_units > EPSILON:
                        proportion = tranche.units / total_existing_units
                        tranche.units += units_to_restore * proportion
                        tranche.invested_value = tranche.units * tranche.entry_nav

            if related_fee_txn:
                fee_amount_to_rollback = abs(related_fee_txn.amount)
                if not self._rollback_cumulative_fee_on_tranches(investor_id, fee_amount_to_rollback):
                    raise ValueError("KhÃ´ng thá»ƒ hoÃ n nguyÃªn cumulative_fees_paid trÃªn tranche nhÃ  Ä‘áº§u tÆ°")

            fm_units_to_remove = sum(abs(t.units_change) for t in related_fm_fee_txns)
            if not self._remove_units_from_fund_manager(fm_units_to_remove, transaction.date):
                raise ValueError("KhÃ´ng thá»ƒ hoÃ n nguyÃªn Ä‘Æ¡n vá»‹ quá»¹ cá»§a Fund Manager")

            tx_ids_to_remove = {transaction.id}
            if related_fee_txn:
                tx_ids_to_remove.add(related_fee_txn.id)
            tx_ids_to_remove.update(t.id for t in related_fm_fee_txns)

            self.transactions = [t for t in self.transactions if t.id not in tx_ids_to_remove]
            self.fee_records = [f for f in self.fee_records if f not in related_fee_records]
            return True

        except Exception as e:
            self.tranches = snapshot["tranches"]
            self.transactions = snapshot["transactions"]
            self.fee_records = snapshot["fee_records"]
            print(f"Error deleting withdrawal transaction: {str(e)}")
            return False

    def _delete_nav_update_transaction(self, transaction) -> bool:
        try:
            latest_nav = self.get_latest_total_nav()
            if latest_nav == transaction.nav:
                print(f"Cáº£nh bÃ¡o: XÃ³a giao dá»‹ch cáº­p nháº­t NAV {transaction.id} sáº½ lÃ m thay Ä‘á»•i NAV má»›i nháº¥t")
            self.transactions.remove(transaction)
            return True
        except Exception as e:
            print(f"Error deleting NAV update transaction: {str(e)}")
            return False

    def _delete_complex_transaction(self, transaction) -> bool:
        try:
            if transaction.type in ["PhÃ­", "PhÃ­ Nháº­n"]:
                # mapping theo calculation_date trong FeeRecord
                fee_records_to_check = [
                    f
                    for f in self.fee_records
                    if abs((f.calculation_date - transaction.date).total_seconds()) < 3600
                ]
                if fee_records_to_check:
                    print(
                        f"KhÃ´ng thá»ƒ xÃ³a giao dá»‹ch phÃ­ {transaction.id}: cÃ²n báº£n ghi phÃ­ liÃªn quan. "
                        f"Vui lÃ²ng xÃ³a báº£n ghi phÃ­ trÆ°á»›c."
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
                        f"Tranche tham chiáº¿u tá»›i ID nhÃ  Ä‘áº§u tÆ° khÃ´ng tá»“n táº¡i: {tranche.investor_id}"
                    )
                    results["valid"] = False
                if tranche.units <= 0:
                    results["errors"].append(f"Tranche cÃ³ Ä‘Æ¡n vá»‹ quá»¹ khÃ´ng dÆ°Æ¡ng: {tranche.tranche_id}")
                    results["valid"] = False
                if tranche.hwm < tranche.entry_nav:
                    results["warnings"].append(f"Tranche {tranche.tranche_id} cÃ³ HWM < entry NAV")

            for trans in self.transactions:
                if trans.investor_id not in investor_ids:
                    results["errors"].append(
                        f"Giao dá»‹ch {trans.id} tham chiáº¿u tá»›i ID nhÃ  Ä‘áº§u tÆ° khÃ´ng tá»“n táº¡i: {trans.investor_id}"
                    )
                    results["valid"] = False
                if trans.nav < 0:
                    results["warnings"].append(f"Giao dá»‹ch {trans.id} cÃ³ NAV Ã¢m: {trans.nav}")
                if trans.date > datetime.now():
                    results["warnings"].append(f"Giao dá»‹ch {trans.id} cÃ³ ngÃ y trong tÆ°Æ¡ng lai: {trans.date}")

            for fee_record in self.fee_records:
                if fee_record.investor_id not in investor_ids:
                    results["errors"].append(
                        f"Báº£n ghi phÃ­ {fee_record.id} tham chiáº¿u tá»›i nhÃ  Ä‘áº§u tÆ° khÃ´ng tá»“n táº¡i"
                    )
                    results["valid"] = False
                if fee_record.units_after > fee_record.units_before:
                    results["errors"].append(f"Báº£n ghi phÃ­ {fee_record.id} cÃ³ sá»‘ Ä‘Æ¡n vá»‹ quá»¹ sau phÃ­ lá»›n hÆ¡n trÆ°á»›c phÃ­")
                    results["valid"] = False

            latest_nav = self.get_latest_total_nav()
            if latest_nav is not None:
                total_units = sum(t.units for t in self.tranches)
                if total_units > 0:
                    calculated_price = latest_nav / total_units
                    results["stats"]["latest_nav"] = latest_nav
                    results["stats"]["total_units"] = total_units
                    results["stats"]["price_per_unit"] = calculated_price
                    if calculated_price < 1000 or calculated_price > 10_000_000:
                        results["warnings"].append(
                            f"GiÃ¡ má»—i unit cÃ³ váº» báº¥t thÆ°á»ng: {calculated_price:,.0f} VND"
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
            results["errors"].append(f"Lá»—i kiá»ƒm tra dá»¯ liá»‡u: {str(e)}")
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
            self._operation_backups.append(backup_data)
            if len(self._operation_backups) > 5:
                self._operation_backups = self._operation_backups[-5:]
            return True
        except Exception as e:
            print(f"Backup failed: {str(e)}")
            return False

    def _clear_nav_cache(self):
        # Legacy Streamlit cache hook removed.
        return None

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


