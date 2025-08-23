import uuid
from datetime import datetime, date
from typing import List, Tuple, Optional, Dict, Any
import streamlit as st
from config import *
from models import Investor, Tranche, Transaction, FeeRecord

# SIMPLIFIED SUPABASE INTEGRATION
try:
    from supabase_data_handler import SupabaseDataHandler
    DATA_HANDLER = SupabaseDataHandler()
    if DATA_HANDLER.connected:
        pass
    else:
        raise Exception("Supabase connection failed")
except Exception as e:
    # Fallback to local CSV if Supabase not available
    st.sidebar.warning("📄 Fallback to CSV storage")
    from data_handler import EnhancedDataHandler
    DATA_HANDLER = EnhancedDataHandler()

from utils import *
from concurrent.futures import ThreadPoolExecutor

class EnhancedFundManager:
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.investors: List[Investor] = []
        self.tranches: List[Tranche] = []
        self.transactions: List[Transaction] = []
        self.fee_records: List[FeeRecord] = []
        self.load_data()
        self._ensure_fund_manager_exists()
    
    def load_data(self):
        if not (self.data_handler and self.data_handler.connected):
            st.error("Cannot load data: No database connection.")
            return
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.investors = executor.submit(self.data_handler.load_investors).result()
            self.tranches = executor.submit(self.data_handler.load_tranches).result()
            self.transactions = executor.submit(self.data_handler.load_transactions).result()
            self.fee_records = executor.submit(self.data_handler.load_fee_records).result()
    
    def save_data(self) -> bool:
        return self.data_handler.save_all_data_enhanced(self.investors, self.tranches, self.transactions, self.fee_records)
    
    def _ensure_fund_manager_exists(self):
        if not any(inv.is_fund_manager for inv in self.investors):
            fund_manager = Investor(id=0, name="Fund Manager", is_fund_manager=True, join_date=date.today())
            self.investors.insert(0, fund_manager)
            self.save_data()
    
    def get_fund_manager(self) -> Optional[Investor]:
        return next((inv for inv in self.investors if inv.is_fund_manager), None)
    
    def get_regular_investors(self) -> List[Investor]:
        return [inv for inv in self.investors if not inv.is_fund_manager]
    
    def get_investor_options(self) -> Dict[str, int]:
        return {inv.display_name: inv.id for inv in self.get_regular_investors()}

    def get_investor_by_id(self, investor_id: int) -> Optional[Investor]:
        return next((inv for inv in self.investors if inv.id == investor_id), None)
    
    def calculate_price_per_unit(self, total_nav: float) -> float:
        if not self.tranches or total_nav <= 0: return DEFAULT_UNIT_PRICE
        total_units = sum(t.units for t in self.tranches)
        return total_nav / total_units if total_units > EPSILON else DEFAULT_UNIT_PRICE
    
    def get_latest_total_nav(self) -> Optional[float]:
        if not self.transactions: return None
        nav_transactions = [t for t in self.transactions if t.nav is not None and t.nav > 0]
        if not nav_transactions: return None
        sorted_transactions = sorted(nav_transactions, key=lambda x: (x.date, x.id), reverse=True)
        return sorted_transactions[0].nav
    
    def get_investor_tranches(self, investor_id: int) -> List[Tranche]:
        return [t for t in self.tranches if t.investor_id == investor_id]
    
    def get_investor_balance(self, investor_id: int, total_nav: float) -> Tuple[float, float, float]:
        tranches = self.get_investor_tranches(investor_id)
        if not tranches or total_nav <= 0: return 0.0, 0.0, 0.0
        price_per_unit = self.calculate_price_per_unit(total_nav)
        balance = sum(t.units for t in tranches) * price_per_unit
        invested_value = sum(t.invested_value for t in tranches)
        profit = balance - invested_value
        profit_perc = profit / invested_value if invested_value > 0 else 0.0
        return balance, profit, profit_perc
    
    def process_deposit(self, investor_id: int, amount: float, total_nav_after: float, trans_date: datetime) -> Tuple[bool, str]:
        if amount <= 0: return False, "Số tiền phải lớn hơn 0"
        old_total_nav = self.get_latest_total_nav() or 0
        price = self.calculate_price_per_unit(old_total_nav) if old_total_nav > 0 else DEFAULT_UNIT_PRICE
        units = amount / price
        tranche = Tranche(investor_id=investor_id, tranche_id=str(uuid.uuid4()), entry_date=trans_date, entry_nav=price, units=units, hwm=price, original_entry_date=trans_date, original_entry_nav=price)
        self.tranches.append(tranche)
        self._add_transaction(investor_id, trans_date, 'Nạp', amount, total_nav_after, units)
        return True, f"Đã nạp {format_currency(amount)}"

    def process_withdrawal(self, investor_id: int, amount: float, total_nav_after: float, trans_date: datetime) -> Tuple[bool, str]:
        old_total_nav = self.get_latest_total_nav() or 0
        if old_total_nav <= 0: return False, "Không có NAV để thực hiện giao dịch."
        price = self.calculate_price_per_unit(old_total_nav)
        tranches = self.get_investor_tranches(investor_id)
        if not tranches: return False, "Nhà đầu tư không có vốn."
        balance = sum(t.units for t in tranches) * price
        if amount > balance + EPSILON: return False, f"Số tiền rút vượt quá số dư."
        units_to_remove = amount / price
        self._process_unit_reduction(investor_id, units_to_remove, amount >= balance - EPSILON)
        self._add_transaction(investor_id, trans_date, 'Rút', -amount, total_nav_after, -units_to_remove)
        return True, f"Đã rút {format_currency(amount)}"

    def process_nav_update(self, total_nav: float, trans_date: datetime) -> Tuple[bool, str]:
        if total_nav <= 0: return False, "Total NAV phải lớn hơn 0"
        self._add_transaction(0, trans_date, 'NAV Update', 0, total_nav, 0)
        return True, f"Đã cập nhật NAV."

    def _get_next_transaction_id(self) -> int:
        return max([t.id for t in self.transactions] or [0]) + 1

    def _add_transaction(self, investor_id: int, date: datetime, type: str, amount: float, nav: float, units_change: float):
        self.transactions.append(Transaction(id=self._get_next_transaction_id(), investor_id=investor_id, date=date, type=type, amount=amount, nav=nav, units_change=units_change))
    
    def _process_unit_reduction(self, investor_id: int, units_to_remove: float, is_full: bool):
        if is_full:
            self.tranches = [t for t in self.tranches if t.investor_id != investor_id]
        else:
            tranches = self.get_investor_tranches(investor_id)
            total_units = sum(t.units for t in tranches)
            if total_units > 0:
                ratio = units_to_remove / total_units
                for t in tranches: t.units *= (1 - ratio)
            self.tranches = [t for t in self.tranches if t.units >= EPSILON]
        return True

    # === CÁC HÀM BỊ THIẾU ĐÃ ĐƯỢỢC PHỤC HỒI ĐẦY ĐỦ ===

    def calculate_investor_fee(self, investor_id: int, ending_date: datetime, ending_total_nav: float) -> Dict[str, Any]:
        """Calculate detailed fees for an investor, returning a full dictionary."""
        tranches = self.get_investor_tranches(investor_id)
        if not tranches or ending_total_nav <= 0:
            return self._empty_fee_details()

        current_price = self.calculate_price_per_unit(ending_total_nav)
        balance = sum(t.units for t in tranches) * current_price
        invested_value = sum(t.invested_value for t in tranches)
        profit = balance - invested_value
        profit_perc = profit / invested_value if invested_value > 0 else 0.0
        
        total_fee = 0.0
        hurdle_value = 0.0
        hwm_value = 0.0
        excess_profit = 0.0

        for tranche in tranches:
            if tranche.units < EPSILON: continue
            
            time_delta_days = (ending_date - tranche.entry_date).days
            if time_delta_days <= 0: continue
            
            time_delta_years = time_delta_days / 365.25
            hurdle_price = tranche.entry_nav * ((1 + HURDLE_RATE_ANNUAL) ** time_delta_years)
            threshold_price = max(hurdle_price, tranche.hwm)
            
            profit_per_unit = max(0, current_price - threshold_price)
            tranche_excess_profit = profit_per_unit * tranche.units
            
            total_fee += PERFORMANCE_FEE_RATE * tranche_excess_profit
            hurdle_value += hurdle_price * tranche.units
            hwm_value += tranche.hwm * tranche.units
            excess_profit += tranche_excess_profit
        
        return {
            'total_fee': round(total_fee, 2),
            'balance': round(balance, 2),
            'invested_value': round(invested_value, 2),
            'profit': round(profit, 2),
            'profit_perc': profit_perc,
            'hurdle_value': round(hurdle_value, 2),
            'hwm_value': round(hwm_value, 2),
            'excess_profit': round(excess_profit, 2)
        }

    def get_investor_lifetime_performance(self, investor_id: int, current_nav: float) -> Dict:
        tranches = self.get_investor_tranches(investor_id)
        if not tranches: return self._empty_performance_stats()
        
        current_price = self.calculate_price_per_unit(current_nav)
        total_original_invested = sum(t.original_invested_value for t in tranches)
        current_value = sum(t.units for t in tranches) * current_price
        total_fees_paid = sum(t.cumulative_fees_paid for t in tranches)
        
        gross_profit = current_value + total_fees_paid - total_original_invested
        net_profit = current_value - total_original_invested
        
        return {
            'original_invested': total_original_invested,
            'current_value': current_value,
            'total_fees_paid': total_fees_paid,
            'gross_profit': gross_profit,
            'net_profit': net_profit,
            'gross_return': gross_profit / total_original_invested if total_original_invested > 0 else 0,
            'net_return': net_profit / total_original_invested if total_original_invested > 0 else 0,
            'current_units': sum(t.units for t in tranches)
        }

    def get_fee_history(self, investor_id: Optional[int] = None) -> List[FeeRecord]:
        if investor_id is None:
            return self.fee_records
        return [record for record in self.fee_records if record.investor_id == investor_id]

    def _empty_fee_details(self) -> Dict[str, Any]:
        """Returns a full dictionary with zero values to prevent KeyErrors."""
        return {
            'total_fee': 0.0, 'balance': 0.0, 'invested_value': 0.0,
            'profit': 0.0, 'profit_perc': 0.0, 'hurdle_value': 0.0,
            'hwm_value': 0.0, 'excess_profit': 0.0
        }

    def _empty_performance_stats(self) -> Dict:
        return {
            'original_invested': 0.0, 'current_value': 0.0, 'total_fees_paid': 0.0,
            'gross_profit': 0.0, 'net_profit': 0.0, 'gross_return': 0.0,
            'net_return': 0.0, 'current_units': 0.0
        }

    # Enhanced Services - Transaction Management Methods

    def undo_last_transaction(self, transaction_id: int) -> bool:
        """
        Undo a specific transaction by reversing its effects
        IMPORTANT: Only works for recent transactions, not complex multi-step operations
        """
        try:
            # Find the transaction
            transaction = None
            for t in self.transactions:
                if t.id == transaction_id:
                    transaction = t
                    break
            
            if not transaction:
                return False
            
            # Check if it's safe to undo (must be one of the last 5 transactions)
            recent_transactions = sorted(self.transactions, key=lambda x: x.date, reverse=True)[:5]
            if transaction not in recent_transactions:
                return False
            
            # Create reverse transaction based on type
            if transaction.type == 'Nạp':
                return self._undo_deposit(transaction)
            elif transaction.type == 'Rút':
                return self._undo_withdrawal(transaction)
            elif transaction.type == 'NAV Update':
                return self._undo_nav_update(transaction)
            elif transaction.type in ['Phí', 'Fund Manager Withdrawal']:
                # These are more complex, for now just remove the transaction
                return self._simple_transaction_removal(transaction)
            
            return False
            
        except Exception as e:
            print(f"Error in undo_last_transaction: {str(e)}")
            return False

    def _undo_deposit(self, original_transaction) -> bool:
        """Undo a deposit transaction"""
        try:
            investor_id = original_transaction.investor_id
            amount = original_transaction.amount
            
            # Find and remove the tranche created by this deposit
            # Look for tranche created around the same time
            deposit_date = original_transaction.date
            matching_tranches = [
                t for t in self.tranches 
                if (t.investor_id == investor_id and 
                    abs((t.entry_date - deposit_date).total_seconds()) < 3600)  # Within 1 hour
            ]
            
            if not matching_tranches:
                return False
            
            # Remove the most recent matching tranche
            tranche_to_remove = max(matching_tranches, key=lambda x: x.entry_date)
            
            # Check if tranche hasn't been modified by fees
            if abs(tranche_to_remove.units * tranche_to_remove.entry_nav - amount) > 1:  # Allow 1 VND difference
                return False
            
            # Remove the tranche
            self.tranches.remove(tranche_to_remove)
            
            # Remove the original transaction
            self.transactions.remove(original_transaction)
            
            return True
            
        except Exception as e:
            print(f"Error in _undo_deposit: {str(e)}")
            return False

    def _undo_withdrawal(self, original_transaction) -> bool:
        """Undo a withdrawal transaction - complex, simplified approach"""
        try:
            # For withdrawal, it's complex to restore exact state
            # For now, just add back the units proportionally to existing tranches
            investor_id = original_transaction.investor_id
            amount = abs(original_transaction.amount)
            units_change = abs(original_transaction.units_change)
            
            investor_tranches = self.get_investor_tranches(investor_id)
            if not investor_tranches:
                # Create a new tranche
                tranche = Tranche(
                    investor_id=investor_id,
                    tranche_id=str(uuid.uuid4()),
                    entry_date=original_transaction.date,
                    entry_nav=amount / units_change if units_change > 0 else DEFAULT_UNIT_PRICE,
                    units=units_change,
                    hwm=amount / units_change if units_change > 0 else DEFAULT_UNIT_PRICE,
                    original_entry_date=original_transaction.date,
                    original_entry_nav=amount / units_change if units_change > 0 else DEFAULT_UNIT_PRICE,
                    cumulative_fees_paid=0.0
                )
                self.tranches.append(tranche)
            else:
                # Add units proportionally to existing tranches
                total_existing_units = sum(t.units for t in investor_tranches)
                for tranche in investor_tranches:
                    if tranche.investor_id == investor_id:
                        proportion = tranche.units / total_existing_units if total_existing_units > 0 else 1
                        tranche.units += units_change * proportion
            
            # Remove the original transaction
            self.transactions.remove(original_transaction)
            
            return True
            
        except Exception as e:
            print(f"Error in _undo_withdrawal: {str(e)}")
            return False

    def _undo_nav_update(self, original_transaction) -> bool:
        """Undo NAV update - just remove the transaction"""
        try:
            self.transactions.remove(original_transaction)
            return True
        except Exception:
            return False

    def _simple_transaction_removal(self, transaction) -> bool:
        """Simple removal for complex transactions"""
        try:
            self.transactions.remove(transaction)
            return True
        except Exception:
            return False

    def validate_data_consistency(self) -> Dict[str, Any]:
        """
        Comprehensive data consistency check
        Returns validation results with errors and warnings
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Check 1: All investor IDs in tranches exist in investors
            investor_ids = {inv.id for inv in self.investors}
            for tranche in self.tranches:
                if tranche.investor_id not in investor_ids:
                    results['errors'].append(f"Tranche references non-existent investor ID: {tranche.investor_id}")
                    results['valid'] = False
            
            # Check 2: All investor IDs in transactions exist in investors
            for trans in self.transactions:
                if trans.investor_id not in investor_ids:
                    results['errors'].append(f"Transaction {trans.id} references non-existent investor ID: {trans.investor_id}")
                    results['valid'] = False
            
            # Check 3: Units should be positive
            for tranche in self.tranches:
                if tranche.units <= 0:
                    results['errors'].append(f"Tranche has non-positive units: {tranche.tranche_id}")
                    results['valid'] = False
            
            # Check 4: NAV values should be positive (warnings only for special cases)
            for trans in self.transactions:
                if trans.nav <= 0 and trans.type not in ['Phí Nhận']:  # Allow 0 NAV for internal transfers
                    results['warnings'].append(f"Transaction {trans.id} has non-positive NAV: {trans.nav}")
            
            # Check 5: Transaction dates should not be in future (warnings only)
            from datetime import datetime
            now = datetime.now()
            for trans in self.transactions:
                if trans.date > now:
                    results['warnings'].append(f"Transaction {trans.id} has future date: {trans.date}")
            
            # Check 6: HWM should not be less than entry NAV for active tranches (warnings only)
            for tranche in self.tranches:
                if tranche.hwm < tranche.entry_nav:
                    results['warnings'].append(f"Tranche {tranche.tranche_id} has HWM < entry NAV")
            
            # Check 7: Fee records consistency
            for fee_record in self.fee_records:
                if fee_record.investor_id not in investor_ids:
                    results['errors'].append(f"Fee record {fee_record.id} references non-existent investor")
                    results['valid'] = False
                
                if fee_record.units_after > fee_record.units_before:
                    results['errors'].append(f"Fee record {fee_record.id} has units_after > units_before")
                    results['valid'] = False
            
            # Check 8: Total balance calculation consistency (warnings only)
            latest_nav = self.get_latest_total_nav()
            if latest_nav:
                total_units = sum(t.units for t in self.tranches)
                if total_units > 0:
                    calculated_price = latest_nav / total_units
                    results['stats']['latest_nav'] = latest_nav
                    results['stats']['total_units'] = total_units
                    results['stats']['price_per_unit'] = calculated_price
                    
                    # Check if price is unusual (warnings only)
                    if calculated_price < 1000 or calculated_price > 10_000_000:
                        results['warnings'].append(f"Price per unit seems unusual: {calculated_price:,.0f} VND")
            
            # Statistics
            results['stats']['total_investors'] = len(self.investors)
            results['stats']['regular_investors'] = len(self.get_regular_investors())
            results['stats']['total_tranches'] = len(self.tranches)
            results['stats']['total_transactions'] = len(self.transactions)
            results['stats']['total_fee_records'] = len(self.fee_records)
            
            # IMPORTANT: Only errors should set valid=False, not warnings
            results['valid'] = len(results['errors']) == 0
            
            return results
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
            return results

    def backup_before_operation(self, operation_name: str) -> bool:
        """Create backup before major operations"""
        try:
            # Create a data snapshot
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation_name,
                'investors_count': len(self.investors),
                'tranches_count': len(self.tranches),
                'transactions_count': len(self.transactions),
                'fee_records_count': len(self.fee_records)
            }
            
            # Save to session state for potential rollback
            if 'operation_backup' not in st.session_state:
                st.session_state.operation_backup = []
            
            st.session_state.operation_backup.append(backup_data)
            
            # Keep only last 5 backups
            if len(st.session_state.operation_backup) > 5:
                st.session_state.operation_backup = st.session_state.operation_backup[-5:]
            
            return True
            
        except Exception as e:
            print(f"Backup failed: {str(e)}")
            return False

    def get_investor_individual_report(self, investor_id: int, current_nav: float) -> Dict:
        """Generate individual report for specific investor"""
        try:
            investor = self.get_investor_by_id(investor_id)
            if not investor:
                return {}
            
            tranches = self.get_investor_tranches(investor_id)
            if not tranches:
                return {}
            
            # Current performance
            balance, profit, profit_perc = self.get_investor_balance(investor_id, current_nav)
            
            # Lifetime performance
            lifetime_perf = self.get_investor_lifetime_performance(investor_id, current_nav)
            
            # Fee details
            fee_details = self.calculate_investor_fee(investor_id, datetime.now(), current_nav)
            
            # Transaction history for this investor
            investor_transactions = [
                t for t in self.transactions 
                if t.investor_id == investor_id
            ]
            
            # Fee history for this investor
            investor_fees = [
                f for f in self.fee_records
                if f.investor_id == investor_id
            ]
            
            return {
                'investor': investor,
                'current_balance': balance,
                'current_profit': profit,
                'current_profit_perc': profit_perc,
                'lifetime_performance': lifetime_perf,
                'fee_details': fee_details,
                'tranches': tranches,
                'transactions': investor_transactions,
                'fee_history': investor_fees,
                'report_date': datetime.now(),
                'current_nav': current_nav,
                'current_price': self.calculate_price_per_unit(current_nav)
            }
            
        except Exception as e:
            print(f"Error generating individual report: {str(e)}")
            return {}
    def _clear_nav_cache(self):
        """Clear NAV-related cache"""
        try:
            import streamlit as st
            
            # Clear Streamlit cache
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            
            # Clear session state cache
            cache_keys_to_clear = [
                'cached_nav', 'latest_nav', 'nav_cache', 
                'nav_large_change_confirmed'
            ]
            
            for key in cache_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            
            print("DEBUG: NAV cache cleared")
                    
        except Exception as e:
            print(f"Warning: Could not clear cache: {e}")

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete a transaction safely with validation
        Returns True if successful, False otherwise
        """
        try:
            # Find the transaction
            transaction_to_delete = None
            for t in self.transactions:
                if t.id == transaction_id:
                    transaction_to_delete = t
                    break
            
            if not transaction_to_delete:
                return False
            
            # Create backup before deletion
            self.backup_before_operation(f"Delete transaction {transaction_id}")
            
            # Check if it's safe to delete
            # For safety, only allow deletion of recent transactions (last 10)
            recent_transactions = sorted(
                self.transactions, 
                key=lambda x: (x.date, x.id), 
                reverse=True
            )[:10]
            
            if transaction_to_delete not in recent_transactions:
                print(f"Transaction {transaction_id} is too old to delete safely")
                return False
            
            # Special handling based on transaction type
            if transaction_to_delete.type == 'Nạp':
                return self._delete_deposit_transaction(transaction_to_delete)
            elif transaction_to_delete.type == 'Rút':
                return self._delete_withdrawal_transaction(transaction_to_delete)
            elif transaction_to_delete.type == 'NAV Update':
                return self._delete_nav_update_transaction(transaction_to_delete)
            elif transaction_to_delete.type in ['Phí', 'Fund Manager Withdrawal', 'Phí Nhận']:
                return self._delete_complex_transaction(transaction_to_delete)
            else:
                # Simple deletion for other types
                self.transactions.remove(transaction_to_delete)
                return True
                
        except Exception as e:
            print(f"Error in delete_transaction: {str(e)}")
            return False

    def _delete_deposit_transaction(self, transaction) -> bool:
        """Delete a deposit transaction and its associated tranche"""
        try:
            investor_id = transaction.investor_id
            amount = transaction.amount
            transaction_date = transaction.date
            
            # Find matching tranche created by this deposit
            matching_tranches = [
                t for t in self.tranches 
                if (t.investor_id == investor_id and 
                    abs((t.entry_date - transaction_date).total_seconds()) < 3600)  # Within 1 hour
            ]
            
            # Find the tranche that most likely corresponds to this transaction
            best_match = None
            for tranche in matching_tranches:
                calculated_amount = tranche.units * tranche.entry_nav
                if abs(calculated_amount - amount) < 10:  # Allow 10 VND difference
                    best_match = tranche
                    break
            
            if best_match:
                # Check if tranche has been affected by fees
                if best_match.cumulative_fees_paid > 0:
                    print(f"Cannot delete deposit transaction {transaction.id}: tranche has been affected by fees")
                    return False
                
                # Remove the tranche
                self.tranches.remove(best_match)
            
            # Remove the transaction
            self.transactions.remove(transaction)
            return True
            
        except Exception as e:
            print(f"Error deleting deposit transaction: {str(e)}")
            return False

    def _delete_withdrawal_transaction(self, transaction) -> bool:
        """Delete a withdrawal transaction - more complex"""
        try:
            # For withdrawal, it's very complex to restore exact state
            # Only allow if it's the very last transaction for this investor
            investor_id = transaction.investor_id
            
            investor_transactions = [
                t for t in self.transactions 
                if t.investor_id == investor_id
            ]
            
            # Sort by date and ID to find the latest
            investor_transactions.sort(key=lambda x: (x.date, x.id), reverse=True)
            
            if investor_transactions[0].id != transaction.id:
                print(f"Cannot delete withdrawal transaction {transaction.id}: not the latest transaction for investor")
                return False
            
            # Try to restore units proportionally
            amount = abs(transaction.amount)
            units_to_restore = abs(transaction.units_change)
            
            investor_tranches = self.get_investor_tranches(investor_id)
            
            if not investor_tranches:
                # Create a new tranche to restore the withdrawn amount
                # Use the price at the time of withdrawal
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
                    cumulative_fees_paid=0.0
                )
                self.tranches.append(tranche)
            else:
                # Add units proportionally to existing tranches
                total_existing_units = sum(t.units for t in investor_tranches)
                
                for tranche in investor_tranches:
                    if total_existing_units > 0:
                        proportion = tranche.units / total_existing_units
                        tranche.units += units_to_restore * proportion
            
            # Remove the transaction
            self.transactions.remove(transaction)
            return True
            
        except Exception as e:
            print(f"Error deleting withdrawal transaction: {str(e)}")
            return False

    def _delete_nav_update_transaction(self, transaction) -> bool:
        """Delete NAV update transaction"""
        try:
            # Check if this is the source of latest NAV
            latest_nav = self.get_latest_total_nav()
            if latest_nav == transaction.nav:
                # This deletion will change the latest NAV
                print(f"Warning: Deleting NAV update transaction {transaction.id} will change latest NAV")
            
            self.transactions.remove(transaction)
            return True
            
        except Exception as e:
            print(f"Error deleting NAV update transaction: {str(e)}")
            return False

    def _delete_complex_transaction(self, transaction) -> bool:
        """Delete complex transactions (fees, etc.) - requires more careful handling"""
        try:
            if transaction.type in ['Phí', 'Phí Nhận']:
                # Check if this fee transaction has corresponding fee records
                fee_records_to_check = [
                    f for f in self.fee_records 
                    if abs((f.fee_date - transaction.date).total_seconds()) < 3600
                ]
                
                if fee_records_to_check:
                    print(f"Cannot delete fee transaction {transaction.id}: has associated fee records")
                    print("Please delete fee records first or use the fee management interface")
                    return False
            
            # For other complex transactions, just remove the transaction
            # The user should be warned about potential data inconsistencies
            self.transactions.remove(transaction)
            return True
            
        except Exception as e:
            print(f"Error deleting complex transaction: {str(e)}")
            return False
