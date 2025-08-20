import uuid
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict
import streamlit as st

from config import *
from models import Investor, Tranche, Transaction, FeeRecord
from data_handler import EnhancedDataHandler
from utils import *

class EnhancedFundManager:
    """Enhanced Fund Manager với fund manager tracking và fee history"""
    
    def __init__(self):
        self.investors: List[Investor] = []
        self.tranches: List[Tranche] = []
        self.transactions: List[Transaction] = []
        self.fee_records: List[FeeRecord] = []
        self.load_data()
        self._ensure_fund_manager_exists()
    
    def load_data(self):
        """Load tất cả dữ liệu"""
        self.investors = EnhancedDataHandler.load_investors()
        self.tranches = EnhancedDataHandler.load_tranches()
        self.transactions = EnhancedDataHandler.load_transactions()
        self.fee_records = EnhancedDataHandler.load_fee_records()
    
    def save_data(self) -> bool:
        """Save tất cả dữ liệu including fee records"""
        return EnhancedDataHandler.save_all_data_enhanced(
            self.investors, self.tranches, self.transactions, self.fee_records
        )
    
    def _ensure_fund_manager_exists(self):
        """Đảm bảo có fund manager investor"""
        fund_manager = self.get_fund_manager()
        if not fund_manager:
            # Tạo fund manager với ID = 0
            fund_manager = Investor(
                id=0,
                name="Fund Manager",
                is_fund_manager=True,
                join_date=date.today()
            )
            self.investors.insert(0, fund_manager)  # Đặt đầu list
            print("✅ Created Fund Manager investor")
    
    def get_fund_manager(self) -> Optional[Investor]:
        """Lấy fund manager investor"""
        for inv in self.investors:
            if inv.is_fund_manager:
                return inv
        return None
    
    def get_regular_investors(self) -> List[Investor]:
        """Lấy danh sách investors thường (không phải fund manager)"""
        return [inv for inv in self.investors if not inv.is_fund_manager]
    
    # === INVESTOR MANAGEMENT (từ FundManager cũ) ===
    
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
        
        # Create new investor (skip ID=0 reserved for fund manager)
        existing_ids = [inv.id for inv in self.investors]
        new_id = 1
        while new_id in existing_ids:
            new_id += 1
        
        investor = Investor(
            id=new_id, name=name.strip(), phone=phone.strip(),
            address=address.strip(), email=email.strip(),
            is_fund_manager=False
        )
        
        self.investors.append(investor)
        return True, f"Đã thêm {investor.display_name}"
    
    def get_investor_options(self) -> Dict[str, int]:
        """Get options cho selectbox (chỉ regular investors)"""
        regular_investors = self.get_regular_investors()
        return {inv.display_name: inv.id for inv in regular_investors}
    
    def get_all_investor_options(self) -> Dict[str, int]:
        """Get ALL investor options (bao gồm fund manager)"""
        return {inv.display_name: inv.id for inv in self.investors}
    
    def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        """Get investor by ID"""
        for inv in self.investors:
            if inv.id == investor_id:
                return inv
        return None
    
    # === FUND CALCULATIONS (từ FundManager cũ) ===
    
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
    
    # === TRANSACTION PROCESSING (từ FundManager cũ với nhỏ sửa đổi) ===
    
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
            hwm=old_price_per_unit,
            original_entry_date=trans_date,
            original_entry_nav=old_price_per_unit,
            cumulative_fees_paid=0.0
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
    
    # === ENHANCED FEE CALCULATION ===
    
    def calculate_investor_fee(self, investor_id: int, ending_date: datetime, ending_total_nav: float) -> Dict[str, float]:
        """Tính phí chi tiết cho investor (giống như cũ)"""
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
    
    def apply_year_end_fees_enhanced(self, year: int, ending_date: date, 
                                   ending_total_nav: float) -> Tuple[bool, str]:
        """ENHANCED fee application với fund manager tracking"""
        if ending_total_nav <= 0:
            return False, "Total NAV phải lớn hơn 0"
        
        ending_date_dt = datetime.combine(ending_date, datetime.min.time())
        ending_price = self.calculate_price_per_unit(ending_total_nav)
        
        fund_manager = self.get_fund_manager()
        if not fund_manager:
            return False, "Không tìm thấy fund manager"
        
        total_fees_applied = 0.0
        total_units_transferred = 0.0
        new_fee_records = []
        
        # Xử lý phí cho từng regular investor
        for investor in self.get_regular_investors():
            inv_tranches = self.get_investor_tranches(investor.id)
            if not inv_tranches:
                continue
            
            fee_details = self.calculate_investor_fee(investor.id, ending_date_dt, ending_total_nav)
            total_fee = fee_details['total_fee']
            
            if total_fee > 0:
                units_before = sum(t.units for t in inv_tranches)
                units_fee = total_fee / ending_price
                
                if units_before < units_fee:
                    return False, f"Không đủ đơn vị cho phí của investor {investor.id}"
                
                # Giảm units của investor
                ratio = units_fee / units_before
                for tranche in inv_tranches:
                    if tranche.investor_id == investor.id:
                        # Cập nhật cumulative fees (QUAN TRỌNG: giữ history)
                        tranche.cumulative_fees_paid += total_fee
                        # Giảm units
                        old_units = tranche.units
                        tranche.units *= (1 - ratio)
                        
                        # KHÔNG reset entry data - giữ nguyên để track performance dài hạn
                        # Chỉ reset current base sau khi thu phí
                        tranche.entry_date = ending_date_dt
                        tranche.entry_nav = ending_price
                        if tranche.hwm < ending_price:
                            tranche.hwm = ending_price
                
                # Tạo fee record
                fee_record = FeeRecord(
                    id=len(self.fee_records) + len(new_fee_records) + 1,
                    period=str(year),
                    investor_id=investor.id,
                    fee_amount=total_fee,
                    fee_units=units_fee,
                    calculation_date=ending_date_dt,
                    units_before=units_before,
                    units_after=units_before - units_fee,
                    nav_per_unit=ending_price,
                    description=f"Year-end fee for {year}"
                )
                new_fee_records.append(fee_record)
                
                # Chuyển units cho fund manager
                self._transfer_units_to_fund_manager(units_fee, ending_price, ending_date_dt)
                
                # Ghi transaction
                self._add_transaction(investor.id, ending_date_dt, 'Phí', -total_fee, 
                                    ending_total_nav, -units_fee)
                
                total_fees_applied += total_fee
                total_units_transferred += units_fee
        
        # Lưu fee records
        self.fee_records.extend(new_fee_records)
        
        # Clean up zero tranches
        self.tranches = [t for t in self.tranches if t.units >= EPSILON]
        
        message = f"Đã áp dụng phí tổng cộng: {format_currency(total_fees_applied)}"
        message += f"\nĐã chuyển {total_units_transferred:.6f} units cho Fund Manager"
        
        return True, message
    
    def _transfer_units_to_fund_manager(self, units: float, price: float, date: datetime):
        """Chuyển units cho fund manager"""
        fund_manager = self.get_fund_manager()
        if not fund_manager:
            return
        
        # Tìm hoặc tạo tranche cho fund manager
        fm_tranches = self.get_investor_tranches(fund_manager.id)
        
        if fm_tranches:
            # Thêm vào tranche hiện có (latest)
            latest_tranche = max(fm_tranches, key=lambda t: t.entry_date)
            # Recalculate weighted average
            total_value = latest_tranche.units * latest_tranche.entry_nav + units * price
            total_units = latest_tranche.units + units
            
            if total_units > 0:
                latest_tranche.entry_nav = total_value / total_units
                latest_tranche.units = total_units
                if latest_tranche.hwm < price:
                    latest_tranche.hwm = price
        else:
            # Tạo tranche mới cho fund manager
            fm_tranche = Tranche(
                investor_id=fund_manager.id,
                tranche_id=str(uuid.uuid4()),
                entry_date=date,
                entry_nav=price,
                units=units,
                hwm=price,
                original_entry_date=date,
                original_entry_nav=price,
                cumulative_fees_paid=0.0
            )
            self.tranches.append(fm_tranche)
        
        # Ghi transaction cho fund manager
        self._add_transaction(fund_manager.id, date, 'Phí Nhận', units * price, 
                            0, units)  # NAV = 0 vì đây là internal transfer
    
    # === NEW: LIFETIME PERFORMANCE TRACKING ===
    
    def get_investor_lifetime_performance(self, investor_id: int, current_nav: float) -> Dict:
        """Tính performance từ đầu (bao gồm cả phí đã trả)"""
        tranches = self.get_investor_tranches(investor_id)
        if not tranches:
            return self._empty_performance_stats()
        
        current_price = self.calculate_price_per_unit(current_nav)
        
        # Tính từ original values
        total_original_invested = sum(t.original_invested_value for t in tranches)
        total_current_units = sum(t.units for t in tranches)
        current_value = total_current_units * current_price
        total_fees_paid = sum(t.cumulative_fees_paid for t in tranches)
        
        # Performance = current value + fees paid - original invested
        gross_profit = current_value + total_fees_paid - total_original_invested
        net_profit = current_value - total_original_invested
        
        gross_return = gross_profit / total_original_invested if total_original_invested > 0 else 0
        net_return = net_profit / total_original_invested if total_original_invested > 0 else 0
        
        return {
            'original_invested': total_original_invested,
            'current_value': current_value,
            'total_fees_paid': total_fees_paid,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'gross_return': gross_return,
            'net_return': net_return,
            'current_units': total_current_units
        }
    
    def get_fee_history(self, investor_id: Optional[int] = None) -> List[FeeRecord]:
        """Lấy lịch sử phí"""
        if investor_id is None:
            return self.fee_records
        return [record for record in self.fee_records if record.investor_id == investor_id]
    
    # === HELPER METHODS (từ FundManager cũ) ===
    
    def update_hwm_if_higher(self, total_nav: float):
        """Cập nhật HWM nếu giá cao hơn - CHỈ CHO FUND MANAGER"""
        if not self.tranches or total_nav <= 0:
            return
        
        current_price = self.calculate_price_per_unit(total_nav)
        
        # CHỈ update HWM cho Fund Manager tranches
        # Regular investor HWM chỉ update sau khi thu phí trong apply_year_end_fees_enhanced
        fund_manager = self.get_fund_manager()
        if fund_manager:
            for tranche in self.tranches:
                if tranche.investor_id == fund_manager.id and tranche.hwm < current_price:
                    tranche.hwm = current_price
    
    def _get_next_transaction_id(self) -> int:
        """Get ID transaction tiếp theo"""
        if not self.transactions:
            return 1
        return max(t.id for t in self.transactions) + 1
    
    def _get_next_fee_record_id(self) -> int:
        """Get ID fee record tiếp theo"""
        if not self.fee_records:
            return 1
        return max(f.id for f in self.fee_records) + 1
    
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
    
    def _empty_performance_stats(self) -> Dict:
        """Empty performance stats"""
        return {
            'original_invested': 0.0, 'current_value': 0.0, 'total_fees_paid': 0.0,
            'gross_profit': 0.0, 'net_profit': 0.0, 'gross_return': 0.0,
            'net_return': 0.0, 'current_units': 0.0
        }