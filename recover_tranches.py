#!/usr/bin/env python3
"""
Standalone Tranche Recovery Script
Khôi phục tranches từ transaction history

Usage:
    python recover_tranches.py --preview    # Xem preview
    python recover_tranches.py --execute    # Thực hiện khôi phục
    python recover_tranches.py --backup     # Tạo backup trước
"""

import os
import sys
import argparse
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Tuple
from collections import defaultdict
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import your models and handlers
from models import Investor, Tranche, Transaction, FeeRecord
from config import *

class StandaloneTrancheRecovery:
    def __init__(self, use_supabase=True):
        self.use_supabase = use_supabase
        self.recovery_log = []
        self.data_handler = None
        self.investors = []
        self.tranches = []
        self.transactions = []
        self.fee_records = []
        
        self._initialize_data_handler()
        self._load_data()
    
    def _initialize_data_handler(self):
        """Initialize data handler"""
        print("Initializing data handler...")
        
        if self.use_supabase:
            try:
                from supabase_data_handler import SupabaseDataHandler
                self.data_handler = SupabaseDataHandler()
                if self.data_handler.connected:
                    print("✓ Connected to Supabase")
                else:
                    raise Exception("Supabase connection failed")
            except Exception as e:
                print(f"Supabase failed: {e}")
                print("Falling back to CSV storage...")
                self.use_supabase = False
        
        if not self.use_supabase:
            from data_handler import EnhancedDataHandler
            self.data_handler = EnhancedDataHandler()
            print("✓ Using CSV storage")
    
    def _load_data(self):
        """Load all data"""
        print("Loading data...")
        
        try:
            self.investors = self.data_handler.load_investors()
            self.tranches = self.data_handler.load_tranches()
            self.transactions = self.data_handler.load_transactions()
            self.fee_records = self.data_handler.load_fee_records()
            
            print(f"Loaded: {len(self.investors)} investors, {len(self.tranches)} tranches, {len(self.transactions)} transactions")
            
        except Exception as e:
            print(f"ERROR loading data: {e}")
            sys.exit(1)
    
    def log(self, message: str, level="INFO"):
        """Enhanced logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        self.recovery_log.append(log_entry)
    
    def create_backup(self) -> str:
        """Create backup of current data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            backup_data = {
                'timestamp': timestamp,
                'investors': [vars(inv) for inv in self.investors],
                'tranches': [vars(t) for t in self.tranches],
                'transactions': [vars(t) for t in self.transactions],
                'fee_records': [vars(f) for f in self.fee_records]
            }
            
            # Convert datetime objects to strings for JSON serialization
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, date):
                    return obj.isoformat()
                return obj
            
            # Deep convert datetime objects
            def convert_datetimes(data):
                if isinstance(data, dict):
                    return {k: convert_datetimes(v) for k, v in data.items()}
                elif isinstance(data, list):
                    return [convert_datetimes(item) for item in data]
                else:
                    return serialize_datetime(data)
            
            backup_data = convert_datetimes(backup_data)
            
            backup_file = backup_dir / f"tranche_backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"Backup created: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            self.log(f"Backup failed: {e}", "ERROR")
            return None
    
    def preview_recovery(self) -> Dict:
        """Preview what recovery would do"""
        self.log("Generating recovery preview...")
        
        try:
            sorted_transactions = sorted(self.transactions, key=lambda x: (x.date, x.id))
            
            preview = {
                'current_state': {
                    'investors': len(self.investors),
                    'tranches': len(self.tranches),
                    'transactions': len(self.transactions),
                    'fee_records': len(self.fee_records)
                },
                'transaction_analysis': {
                    'total': len(sorted_transactions),
                    'by_type': {},
                    'by_investor': {},
                    'date_range': {
                        'start': sorted_transactions[0].date.isoformat() if sorted_transactions else None,
                        'end': sorted_transactions[-1].date.isoformat() if sorted_transactions else None
                    }
                },
                'expected_outcome': {
                    'investors_with_tranches': set(),
                    'estimated_tranches': 0
                }
            }
            
            # Analyze transactions
            for trans in sorted_transactions:
                trans_type = trans.type
                investor_id = trans.investor_id
                
                preview['transaction_analysis']['by_type'][trans_type] = \
                    preview['transaction_analysis']['by_type'].get(trans_type, 0) + 1
                
                preview['transaction_analysis']['by_investor'][investor_id] = \
                    preview['transaction_analysis']['by_investor'].get(investor_id, 0) + 1
                
                if trans_type == 'Nạp':
                    preview['expected_outcome']['investors_with_tranches'].add(investor_id)
                    preview['expected_outcome']['estimated_tranches'] += 1
            
            preview['expected_outcome']['investors_with_tranches'] = \
                len(preview['expected_outcome']['investors_with_tranches'])
            
            return preview
            
        except Exception as e:
            self.log(f"Preview generation failed: {e}", "ERROR")
            return {'error': str(e)}
    
    def execute_recovery(self) -> Dict:
        """Execute the recovery process"""
        self.log("=== STARTING TRANCHE RECOVERY ===")
        
        result = {
            'success': False,
            'original_tranches': len(self.tranches),
            'recovered_tranches': 0,
            'errors': [],
            'warnings': [],
            'summary': {}
        }
        
        try:
            # Step 1: Backup current tranches
            original_tranches = self.tranches.copy()
            self.log(f"Original tranches count: {len(original_tranches)}")
            
            # Step 2: Clear tranches
            self.tranches = []
            self.log("Cleared existing tranches")
            
            # Step 3: Sort transactions chronologically
            sorted_transactions = sorted(self.transactions, key=lambda x: (x.date, x.id))
            self.log(f"Processing {len(sorted_transactions)} transactions...")
            
            # Step 4: Process transactions
            investor_states = defaultdict(lambda: {
                'tranches': [],
                'total_units': 0.0
            })
            
            current_nav = 10000.0  # Default starting NAV
            total_units_in_system = 0.0
            
            for i, transaction in enumerate(sorted_transactions):
                try:
                    if i % 10 == 0:  # Progress update every 10 transactions
                        self.log(f"Progress: {i+1}/{len(sorted_transactions)}")
                    
                    if transaction.type == 'NAV Update':
                        current_nav = transaction.nav
                        self.log(f"NAV updated to: {current_nav:,.0f}")
                        
                    elif transaction.type == 'Nạp':
                        success = self._process_deposit(
                            transaction, investor_states, current_nav, total_units_in_system
                        )
                        if success:
                            total_units_in_system = sum(
                                state['total_units'] for state in investor_states.values()
                            )
                        
                    elif transaction.type == 'Rút':
                        success = self._process_withdrawal(
                            transaction, investor_states, current_nav
                        )
                        if success:
                            total_units_in_system = sum(
                                state['total_units'] for state in investor_states.values()
                            )
                        
                    elif transaction.type in ['Phí', 'Phí Nhận']:
                        success = self._process_fee(
                            transaction, investor_states, current_nav, total_units_in_system
                        )
                        if success:
                            total_units_in_system = sum(
                                state['total_units'] for state in investor_states.values()
                            )
                        
                except Exception as e:
                    error_msg = f"Error processing transaction {transaction.id}: {e}"
                    self.log(error_msg, "ERROR")
                    result['errors'].append(error_msg)
            
            # Step 5: Convert to tranches list
            recovered_tranches = []
            for investor_id, state in investor_states.items():
                for tranche in state['tranches']:
                    if tranche.units > 0.000001:  # Only significant units
                        recovered_tranches.append(tranche)
            
            # Step 6: Validate recovered tranches
            validation = self._validate_tranches(recovered_tranches)
            
            if validation['valid']:
                # Step 7: Apply recovered tranches
                self.tranches = recovered_tranches
                
                # Step 8: Save data
                if self._save_data():
                    result['success'] = True
                    result['recovered_tranches'] = len(recovered_tranches)
                    self.log("✓ Recovery completed successfully!")
                else:
                    result['errors'].append("Failed to save recovered data")
                    self.tranches = original_tranches  # Rollback
                    self.log("✗ Save failed, rolled back", "ERROR")
            else:
                result['errors'].extend(validation['errors'])
                self.tranches = original_tranches  # Rollback
                self.log("✗ Validation failed, rolled back", "ERROR")
            
            # Summary
            result['summary'] = {
                'transactions_processed': len(sorted_transactions),
                'investors_with_tranches': len([s for s in investor_states.values() if s['tranches']]),
                'total_units_recovered': sum(t.units for t in recovered_tranches),
                'total_value_recovered': sum(getattr(t, 'original_invested_value', 0) for t in recovered_tranches)
            }
            
        except Exception as e:
            error_msg = f"Critical error in recovery: {e}"
            self.log(error_msg, "ERROR")
            result['errors'].append(error_msg)
            # Restore original tranches
            self.tranches = original_tranches
        
        return result
    
    def _process_deposit(self, transaction, investor_states, current_nav, total_units) -> bool:
        try:
            investor_id = transaction.investor_id
            amount = transaction.amount
            
                # Dùng units_change có sẵn thay vì tính toán
            if hasattr(transaction, 'units_change') and transaction.units_change > 0:
                units = transaction.units_change
                price_per_unit = amount / units
            else:
                # Fallback calculation
                if total_units > 0:
                    price_per_unit = current_nav / total_units
                else:
                    price_per_unit = 10000.0
                units = amount / price_per_unit
            
            # Create tranche
            tranche = Tranche(
                investor_id=investor_id,
                tranche_id=f"RECOVERED_DEP_{transaction.id}_{int(transaction.date.timestamp())}",
                entry_date=transaction.date,
                entry_nav=price_per_unit,
                units=units,
                hwm=price_per_unit,
                original_entry_date=transaction.date,
                original_entry_nav=price_per_unit,
                original_invested_value=amount,
                cumulative_fees_paid=0.0
            )
            
            investor_states[investor_id]['tranches'].append(tranche)
            investor_states[investor_id]['total_units'] += units
            
            return True
            
        except Exception as e:
            self.log(f"Error processing deposit {transaction.id}: {e}", "ERROR")
            return False
    
    def _process_withdrawal(self, transaction, investor_states, current_nav) -> bool:
        """Process withdrawal transaction"""
        try:
            investor_id = transaction.investor_id
            units_to_remove = abs(transaction.units_change)
            
            investor_state = investor_states[investor_id]
            
            if not investor_state['tranches']:
                return False
            
            total_units = sum(t.units for t in investor_state['tranches'])
            
            if units_to_remove >= total_units:
                # Full withdrawal
                investor_state['tranches'] = []
                investor_state['total_units'] = 0.0
            else:
                # Partial withdrawal
                reduction_ratio = units_to_remove / total_units
                
                for tranche in investor_state['tranches']:
                    tranche.units *= (1 - reduction_ratio)
                
                # Remove negligible units
                investor_state['tranches'] = [
                    t for t in investor_state['tranches'] 
                    if t.units > 0.000001
                ]
                
                investor_state['total_units'] = sum(t.units for t in investor_state['tranches'])
            
            return True
            
        except Exception as e:
            self.log(f"Error processing withdrawal {transaction.id}: {e}", "ERROR")
            return False
    
    def _process_fee(self, transaction, investor_states, current_nav, total_units) -> bool:
        """Process fee transaction"""
        try:
            investor_id = transaction.investor_id
            
            if transaction.type == 'Phí':
                # Fee payment - reduce units
                units_removed = abs(transaction.units_change)
                investor_state = investor_states[investor_id]
                
                if investor_state['tranches'] and units_removed > 0:
                    current_units = sum(t.units for t in investor_state['tranches'])
                    reduction_ratio = units_removed / current_units if current_units > 0 else 0
                    
                    for tranche in investor_state['tranches']:
                        units_reduction = tranche.units * reduction_ratio
                        tranche.units -= units_reduction
                        tranche.cumulative_fees_paid += units_reduction * (current_nav / total_units if total_units > 0 else 0)
                    
                    # Remove negligible units
                    investor_state['tranches'] = [
                        t for t in investor_state['tranches'] 
                        if t.units > 0.000001
                    ]
                    
                    investor_state['total_units'] = sum(t.units for t in investor_state['tranches'])
                
            elif transaction.type == 'Phí Nhận':
                # Fee receipt - create tranche for Fund Manager
                fee_amount = transaction.amount
                units_received = transaction.units_change
                
                if investor_id == 0:  # Fund Manager
                    price_per_unit = current_nav / total_units if total_units > 0 else 10000.0
                    
                    fee_tranche = Tranche(
                        investor_id=investor_id,
                        tranche_id=f"RECOVERED_FEE_{transaction.id}_{int(transaction.date.timestamp())}",
                        entry_date=transaction.date,
                        entry_nav=price_per_unit,
                        units=units_received,
                        hwm=price_per_unit,
                        original_entry_date=transaction.date,
                        original_entry_nav=price_per_unit,
                        original_invested_value=fee_amount,
                        cumulative_fees_paid=0.0
                    )
                    
                    investor_states[investor_id]['tranches'].append(fee_tranche)
                    investor_states[investor_id]['total_units'] += units_received
            
            return True
            
        except Exception as e:
            self.log(f"Error processing fee {transaction.id}: {e}", "ERROR")
            return False
    
    def _validate_tranches(self, tranches) -> Dict:
        """Validate recovered tranches"""
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Check for negative units
            negative_units = [t for t in tranches if t.units < 0]
            if negative_units:
                validation['errors'].append(f"Found {len(negative_units)} tranches with negative units")
                validation['valid'] = False
            
            # Check required fields
            for tranche in tranches:
                if not hasattr(tranche, 'original_invested_value') or tranche.original_invested_value <= 0:
                    validation['errors'].append(f"Invalid original_invested_value in tranche {tranche.tranche_id}")
                    validation['valid'] = False
                
                if tranche.entry_nav <= 0:
                    validation['errors'].append(f"Invalid entry_nav in tranche {tranche.tranche_id}")
                    validation['valid'] = False
            
        except Exception as e:
            validation['valid'] = False
            validation['errors'].append(f"Validation error: {e}")
        
        return validation
    
    def _save_data(self) -> bool:
        """Save recovered data"""
        try:
            self.log("Saving recovered data...")
            return self.data_handler.save_all_data_enhanced(
                self.investors, self.tranches, self.transactions, self.fee_records
            )
        except Exception as e:
            self.log(f"Save failed: {e}", "ERROR")
            return False
    
    def save_recovery_log(self, filename=None):
        """Save recovery log to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recovery_log_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("TRANCHE RECOVERY LOG\n")
                f.write("=" * 50 + "\n\n")
                for log_entry in self.recovery_log:
                    f.write(log_entry + "\n")
            
            print(f"Recovery log saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"Failed to save log: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description='Tranche Recovery Tool')
    parser.add_argument('--preview', action='store_true', help='Preview recovery plan')
    parser.add_argument('--execute', action='store_true', help='Execute recovery')
    parser.add_argument('--backup', action='store_true', help='Create backup only')
    parser.add_argument('--csv', action='store_true', help='Force CSV mode (skip Supabase)')
    
    args = parser.parse_args()
    
    if not any([args.preview, args.execute, args.backup]):
        parser.print_help()
        return
    
    # Initialize recovery service
    print("Initializing Tranche Recovery Service...")
    recovery = StandaloneTrancheRecovery(use_supabase=not args.csv)
    
    try:
        if args.backup:
            print("\nCreating backup...")
            backup_file = recovery.create_backup()
            if backup_file:
                print(f"✓ Backup created: {backup_file}")
            else:
                print("✗ Backup failed")
            return
        
        if args.preview:
            print("\nGenerating recovery preview...")
            preview = recovery.preview_recovery()
            
            if 'error' in preview:
                print(f"✗ Preview failed: {preview['error']}")
                return
            
            print("\n" + "="*60)
            print("RECOVERY PREVIEW")
            print("="*60)
            
            print(f"\nCurrent State:")
            print(f"  Investors: {preview['current_state']['investors']}")
            print(f"  Tranches: {preview['current_state']['tranches']}")
            print(f"  Transactions: {preview['current_state']['transactions']}")
            
            print(f"\nTransaction Analysis:")
            print(f"  Total transactions: {preview['transaction_analysis']['total']}")
            print(f"  Date range: {preview['transaction_analysis']['date_range']['start']} to {preview['transaction_analysis']['date_range']['end']}")
            
            print(f"\n  By type:")
            for trans_type, count in preview['transaction_analysis']['by_type'].items():
                print(f"    {trans_type}: {count}")
            
            print(f"\nExpected Outcome:")
            print(f"  Investors with tranches: {preview['expected_outcome']['investors_with_tranches']}")
            print(f"  Estimated tranches: {preview['expected_outcome']['estimated_tranches']}")
        
        if args.execute:
            print("\n" + "="*60)
            print("EXECUTING RECOVERY")
            print("="*60)
            
            # Create backup first
            print("\nCreating backup before recovery...")
            backup_file = recovery.create_backup()
            if not backup_file:
                print("✗ Backup failed - aborting recovery")
                return
            
            # Confirm execution
            print("\nWARNING: This will DELETE all existing tranches and rebuild from transactions!")
            confirm = input("Type 'CONFIRM' to proceed: ").strip()
            
            if confirm != 'CONFIRM':
                print("Recovery cancelled")
                return
            
            # Execute recovery
            result = recovery.execute_recovery()
            
            print("\n" + "="*60)
            print("RECOVERY RESULTS")
            print("="*60)
            
            if result['success']:
                print("✓ RECOVERY SUCCESSFUL!")
                print(f"  Original tranches: {result['original_tranches']}")
                print(f"  Recovered tranches: {result['recovered_tranches']}")
                print(f"  Transactions processed: {result['summary']['transactions_processed']}")
                print(f"  Investors with tranches: {result['summary']['investors_with_tranches']}")
                print(f"  Total units recovered: {result['summary']['total_units_recovered']:.6f}")
                print(f"  Total value recovered: {result['summary']['total_value_recovered']:,.0f}")
            else:
                print("✗ RECOVERY FAILED!")
                if result['errors']:
                    print("\nErrors:")
                    for error in result['errors']:
                        print(f"  - {error}")
            
            if result.get('warnings'):
                print("\nWarnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
            
            # Save log
            log_file = recovery.save_recovery_log()
            print(f"\nRecovery log saved to: {log_file}")
    
    except KeyboardInterrupt:
        print("\n\nRecovery interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        recovery.save_recovery_log()
    
    finally:
        print("\nRecovery session ended")

if __name__ == "__main__":
    main()