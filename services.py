import uuid
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict
import streamlit as st

from config import *
from models import Investor, Tranche, Transaction
from data_handler import DataHandler
from utils import *

class FundManager:
    """Class chính quản lý quỹ"""
    
    def __init__(self):
        self.investors: List[Investor] = []
        self.tranches: List[Tranche] = []
        self.transactions: List[Transaction] = []
        self.load_data()
    
    def load_data(self):
        """Load tất cả dữ liệu"""
        self.investors = DataHandler.load_investors()
        self.tranches = DataHandler.load_tranches()
        self.transactions = DataHandler.load_transactions()
    
    def save_data(self) -> bool:
        """Save tất cả dữ liệu"""
        return DataHandler.save_all_data(self.investors, self.tranches, self.transactions)
    
    # === INVESTOR MANAGEMENT ===
    
    def add_investor(self, name: str, phone: str = "", address: str = "", email: str = "") -> Tuple[bool, str]:
        """Thêm investor mới"""
        # Validate
        if not name.strip():
            return False, "Tên không được để trống"
        
        # Check duplicate
        existing_names = [inv.name.lower().strip() for inv in self.investors]
        if name.lower().strip() in existing_names:
            return False, f"Nhà đầu tư '{name}' đã tồn tại"
        
        if phone and not validate_phone(phone):
            return False, "SĐT không hợp lệ"
        
        if email and not validate_email(email):
            return False, "Email không hợp lệ"
        
        # Create new investor
        new_id = max([inv.id for inv in self.investors]) + 1 if self.investors else 1
        investor = Investor(
            id=new_id, name=name.strip(), phone=phone.strip(),
            address=address.strip(), email=email.strip()
        )
        
        self.investors.append(investor)
        return True, f"Đã thêm {investor.display_name}"
    
    def get_investor_options(self) -> Dict[str, int]:
        """Get options cho selectbox"""
        return {inv.display_name: inv.id for inv in self.investors}
    
    def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        """Get investor by ID"""
        for inv in self.investors:
            if inv.id == investor_id:
                return inv
        return None
    
    # === FUND CALCULATIONS ===
    
    def calculate_price_per_unit(self, total_nav: float) -> float:
        """Tính giá per unit"""
        if not self.tranches or total_nav <= 0:
            return DEFAULT_UNIT_PRICE
        
        total_units = sum(t.units for t in self.tranches)
        if total_units <= EPSILON:
            return DEFAULT_UNIT_PRICE
        
        return total_nav / total_units
    
    def get_latest_total_nav(self) -> Optional[float]:
        """Lấy Total NAV mới nhất"""
        nav_transactions = [t for t in self.transactions if t.nav > 0 and t.type != 'Phí']
        if not nav_transactions:
            return None
        
        latest = max(nav_transactions, key=lambda x: x.date)
        return latest.nav
    
    def get_investor_tranches(self, investor_id: int) -> List[Tranche]:
        """Get tranches của investor"""
        return [t for t in self.tranches if t.investor_id == investor_id]
    
    def get_investor_balance(self, investor_id: int, total_nav: float) -> Tuple[float, float, float]:
        """Tính balance, profit, profit% cho investor"""
        tranches = self.get_investor_tranches(investor_id)
        if not tranches or total_nav <= 0:
            return 0.0, 0.0, 0.0
        
        price_per_unit = self.calculate_price_per_unit(total_nav)
        total_units = sum(t.units for t in tranches)
        balance = total_units * price_per_unit
        
        invested_value = sum(t.invested_value for t in tranches)
        profit = balance - invested_value
        profit_perc = profit / invested_value if invested_value > 0 else 0.0
        
        return balance, profit, profit_perc
    
    # === TRANSACTION PROCESSING ===
    
    def process_deposit(self, investor_id: int, amount: float, total_nav_after: float, 
                       trans_date: Optional[datetime] = None) -> Tuple[bool, str]:
        """Xử lý nạp tiền"""
        if trans_date is None:
            trans_date = datetime.now()
        
        if amount <= 0:
            return False, "Số tiền phải lớn hơn 0"
        
        # Tính entry price
        old_total_nav = total_nav_after - amount
        old_price_per_unit = self.calculate_price_per_unit(old_total_nav)
        units_change = amount / old_price_per_unit
        
        # Tạo tranche mới
        tranche = Tranche(
            investor_id=investor_id,
            tranche_id=str(uuid.uuid4()),
            entry_date=trans_date,
            entry_nav=old_price_per_unit,
            units=units_change,
            hwm=old_price_per_unit
        )
        
        # Tạo transaction
        transaction = Transaction(
            id=self._get_next_transaction_id(),
            investor_id=investor_id,
            date=trans_date,
            type='Nạp',
            amount=amount,
            nav=total_nav_after,
            units_change=units_change
        )
        
        self.tranches.append(tranche)
        self.transactions.append(transaction)
        
        return True, f"Đã nạp {format_currency(amount)} ({units_change:.6f} units tại giá {format_currency(old_price_per_unit)})"
    
    def process_withdrawal(self, investor_id: int, amount: float, total_nav_after: float,
                          trans_date: Optional[datetime] = None) -> Tuple[bool, str]:
        """Xử lý rút tiền"""
        if trans_date is None:
            trans_date = datetime.now()
        
        investor_tranches = self.get_investor_tranches(investor_id)
        if not investor_tranches:
            return False, "Nhà đầu tư chưa có tranche nào"
        
        # Tính balance trước khi rút
        old_total_nav = total_nav_after + amount
        old_price_per_unit = self.calculate_price_per_unit(old_total_nav)
        
        investor_units = sum(t.units for t in investor_tranches)
        balance_before = investor_units * old_price_per_unit
        
        if amount > balance_before + EPSILON:
            return False, f"Số tiền rút ({format_currency(amount)}) vượt balance ({format_currency(balance_before)})"
        
        # Tính phí nếu không phải cuối năm
        is_end_year = (trans_date.month == 12 and trans_date.day == 31)
        fee = 0.0
        
        if not is_end_year:
            fee_details = self.calculate_investor_fee(investor_id, trans_date, old_total_nav)
            fee = fee_details['total_fee']
            
            # Pro-rata fee nếu rút một phần
            if amount < balance_before - EPSILON:
                fee *= (amount / balance_before)
        
        effective_amount = amount - fee
        if effective_amount <= 0:
            return False, "Số tiền rút không đủ để trả phí"
        
        # Xử lý rút
        success = self._process_unit_reduction(investor_id, effective_amount / old_price_per_unit, 
                                              amount >= balance_before - EPSILON, trans_date, total_nav_after)
        
        if not success:
            return False, "Lỗi khi xử lý rút tiền"
        
        # Ghi transactions
        self._add_transaction(investor_id, trans_date, 'Rút', -effective_amount, total_nav_after, -(effective_amount / old_price_per_unit))
        
        if fee > 0:
            self._add_transaction(investor_id, trans_date, 'Phí', -fee, total_nav_after, -(fee / old_price_per_unit))
        
        message = f"Đã rút {format_currency(effective_amount)}"
        if fee > 0:
            message += f" (phí: {format_currency(fee)})"
        
        return True, message
    
    def process_nav_update(self, total_nav: float, trans_date: Optional[datetime] = None) -> Tuple[bool, str]:
        """Cập nhật NAV"""
        if trans_date is None:
            trans_date = datetime.now()
        
        if total_nav <= 0:
            return False, "Total NAV phải lớn hơn 0"
        
        # Update HWM
        self.update_hwm_if_higher(total_nav)
        
        # Add transaction
        self._add_transaction(0, trans_date, 'NAV Update', 0, total_nav, 0)
        
        return True, f"Đã cập nhật NAV: {format_currency(total_nav)}"
    
    # === FEE CALCULATION ===
    
    def calculate_investor_fee(self, investor_id: int, ending_date: datetime, ending_total_nav: float) -> Dict[str, float]:
        """Tính phí chi tiết cho investor"""
        tranches = self.get_investor_tranches(investor_id)
        if not tranches or ending_total_nav <= 0:
            return self._empty_fee_details()
        
        current_price = self.calculate_price_per_unit(ending_total_nav)
        total_units = sum(t.units for t in tranches)
        balance = total_units * current_price
        invested_value = sum(t.invested_value for t in tranches)
        profit = balance - invested_value
        profit_perc = profit / invested_value if invested_value > 0 else 0
        
        total_fee = 0.0
        hurdle_value = 0.0
        hwm_value = 0.0
        excess_profit = 0.0
        
        # Tính phí cho từng tranche
        for tranche in tranches:
            if tranche.units < EPSILON:
                continue
            
            # Tính thời gian nắm giữ
            time_delta_days = (ending_date - tranche.entry_date).days
            if time_delta_days <= 0:
                continue
            
            time_delta_years = time_delta_days / 365.25
            
            # Hurdle price với compound interest
            hurdle_multiplier = (1 + HURDLE_RATE_ANNUAL) ** time_delta_years
            hurdle_price = tranche.entry_nav * hurdle_multiplier
            
            # Threshold = MAX(hurdle, HWM)
            threshold_price = max(hurdle_price, tranche.hwm)
            
            # Lợi nhuận vượt ngưỡng
            profit_per_unit = max(0, current_price - threshold_price)
            tranche_excess = profit_per_unit * tranche.units
            tranche_fee = PERFORMANCE_FEE_RATE * tranche_excess
            
            total_fee += tranche_fee
            hurdle_value += hurdle_price * tranche.units
            hwm_value += tranche.hwm * tranche.units
            excess_profit += tranche_excess
        
        return {
            'total_fee': round(total_fee, 2),
            'hurdle_value': round(hurdle_value, 2),
            'hwm_value': round(hwm_value, 2),
            'excess_profit': round(excess_profit, 2),
            'invested_value': round(invested_value, 2),
            'balance': round(balance, 2),
            'profit': round(profit, 2),
            'profit_perc': profit_perc
        }
    
    def apply_year_end_fees(self, year: int, ending_date: date, ending_total_nav: float) -> Tuple[bool, str]:
        """Áp dụng phí cuối năm"""
        if ending_total_nav <= 0:
            return False, "Total NAV phải lớn hơn 0"
        
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        ending_price = self.calculate_price_per_unit(ending_total_nav)
        
        total_fees_applied = 0.0
        
        for investor in self.investors:
            inv_tranches = self.get_investor_tranches(investor.id)
            if not inv_tranches:
                continue
            
            fee_details = self.calculate_investor_fee(investor.id, ending_date_dt, ending_total_nav)
            total_fee = fee_details['total_fee']
            
            if total_fee > 0:
                # Giảm units theo phí
                units_fee = total_fee / ending_price
                investor_units = sum(t.units for t in inv_tranches)
                
                if investor_units < units_fee:
                    return False, f"Không đủ đơn vị cho phí của investor {investor.id}"
                
                ratio = units_fee / investor_units
                for tranche in inv_tranches:
                    if tranche.investor_id == investor.id:
                        tranche.units *= (1 - ratio)
                
                # Add fee transaction
                self._add_transaction(investor.id, ending_date_dt, 'Phí', -total_fee, ending_total_nav, -units_fee)
                
                # Reset entry data và HWM
                for tranche in inv_tranches:
                    if tranche.investor_id == investor.id:
                        tranche.entry_date = ending_date_dt
                        tranche.entry_nav = ending_price
                        tranche.hwm = ending_price
                
                total_fees_applied += total_fee
        
        # Clean up zero tranches
        self.tranches = [t for t in self.tranches if t.units >= EPSILON]
        
        return True, f"Đã áp dụng phí tổng cộng: {format_currency(total_fees_applied)}"
    
    # === HELPER METHODS ===
    
    def update_hwm_if_higher(self, total_nav: float):
        """Cập nhật HWM nếu giá cao hơn"""
        if not self.tranches or total_nav <= 0:
            return
        
        current_price = self.calculate_price_per_unit(total_nav)
        for tranche in self.tranches:
            if tranche.hwm < current_price:
                tranche.hwm = current_price
    
    def _get_next_transaction_id(self) -> int:
        """Get ID transaction tiếp theo"""
        if not self.transactions:
            return 1
        return max(t.id for t in self.transactions) + 1
    
    def _add_transaction(self, investor_id: int, date: datetime, type: str, amount: float, nav: float, units_change: float):
        """Add transaction"""
        transaction = Transaction(
            id=self._get_next_transaction_id(),
            investor_id=investor_id,
            date=date,
            type=type,
            amount=amount,
            nav=nav,
            units_change=units_change
        )
        self.transactions.append(transaction)
    
    def _process_unit_reduction(self, investor_id: int, units_to_remove: float, is_full: bool, 
                               trans_date: datetime, total_nav_after: float) -> bool:
        """Xử lý giảm units"""
        try:
            investor_tranches = self.get_investor_tranches(investor_id)
            total_units = sum(t.units for t in investor_tranches)
            
            if is_full:
                # Rút hết
                self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
            else:
                # Rút một phần
                ratio = units_to_remove / total_units
                current_price = self.calculate_price_per_unit(total_nav_after)
                
                for tranche in investor_tranches:
                    tranche.units *= (1 - ratio)
                    tranche.entry_date = trans_date
                    tranche.entry_nav = current_price
                    if tranche.hwm < current_price:
                        tranche.hwm = current_price
                
                # Clean up
                self.tranches = [t for t in self.tranches if t.units >= EPSILON]
            
            return True
        except Exception:
            return False
    
    def _empty_fee_details(self) -> Dict[str, float]:
        """Empty fee details"""
        return {
            'total_fee': 0.0, 'hurdle_value': 0.0, 'hwm_value': 0.0,
            'excess_profit': 0.0, 'invested_value': 0.0, 'balance': 0.0,
            'profit': 0.0, 'profit_perc': 0.0
        }
