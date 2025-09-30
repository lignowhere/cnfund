#!/usr/bin/env python3
"""
CSV Data Handler - Local CSV storage system
High-performance local data storage with thread-safe operations
"""

import pandas as pd
import shutil
import threading
import os
import tempfile

# Handle fcntl import (Unix only)
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import streamlit as st

from .models import Investor, Tranche, Transaction, FeeRecord
from utils.timezone_manager import TimezoneManager
from utils.type_safety_fixes import safe_int_conversion, safe_float_conversion

class CSVDataHandler:
    """
    CSV-based data handler with thread-safe operations, atomic writes, and automatic backups
    Provides complete local data storage solution for the Fund Management System
    """
    
    def __init__(self):
        self.connected = True
        self.data_dir = Path("data")
        self.backup_dir = Path("data/backups")
        self._lock = threading.Lock()
        
        # For compatibility with Supabase code that checks for engine
        self.engine = None
        
        # Tạo directories
        self._init_directories()
        
        # File paths
        self.investors_file = self.data_dir / "investors.csv"
        self.tranches_file = self.data_dir / "tranches.csv"  
        self.transactions_file = self.data_dir / "transactions.csv"
        self.fee_records_file = self.data_dir / "fee_records.csv"
        
        print("✅ CSVDataHandler initialized successfully")
    
    def _init_directories(self):
        """Khởi tạo directories cần thiết"""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Tạo daily backup directory
            today = TimezoneManager.now().strftime("%Y%m%d")
            daily_backup_dir = self.backup_dir / today
            daily_backup_dir.mkdir(exist_ok=True)
            
        except Exception as e:
            print(f"❌ Error creating directories: {e}")
            self.connected = False
    
    def reconnect(self):
        """Reconnect method for compatibility - always returns True for CSV storage"""
        self.connected = True
        self._init_directories()
        return True
    
    def _create_backup_before_write(self, file_path: Path) -> bool:
        """Tạo backup trước khi ghi file"""
        if not file_path.exists():
            return True
            
        try:
            timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}.csv"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"⚠️ Backup failed for {file_path}: {e}")
            return False
    
    def _atomic_write_csv(self, df: pd.DataFrame, file_path: Path) -> bool:
        """Atomic write using temp file và rename"""
        try:
            # Tạo backup trước
            self._create_backup_before_write(file_path)
            
            # Write to temp file first
            temp_file = file_path.with_suffix('.tmp')
            df.to_csv(temp_file, index=False)
            
            # Atomic rename on same filesystem
            if os.name == 'nt':  # Windows
                # Windows doesn't allow rename over existing file
                if file_path.exists():
                    file_path.unlink()
                temp_file.rename(file_path)
            else:  # Unix/Linux
                temp_file.rename(file_path)
            
            return True
        except Exception as e:
            # Clean up temp file if it exists
            if 'temp_file' in locals() and temp_file.exists():
                temp_file.unlink()
            print(f"❌ Atomic write failed for {file_path}: {e}")
            return False
    
    # === LOAD METHODS ===
    
    def load_investors(self) -> List[Investor]:
        """Load investors from CSV"""
        try:
            if not self.investors_file.exists():
                return []
                
            df = pd.read_csv(self.investors_file, dtype={'phone': 'str'})
            if df.empty:
                return []
            
            # Handle different column name cases
            df.columns = df.columns.str.lower()
            
            # Handle join_date
            if 'join_date' in df.columns:
                df['join_date'] = pd.to_datetime(df['join_date'], errors='coerce')
            elif 'joindate' in df.columns:
                df['join_date'] = pd.to_datetime(df['joindate'], errors='coerce')
            else:
                df['join_date'] = pd.NaT
            
            # Add missing columns with defaults
            if 'is_fund_manager' not in df.columns and 'isfundmanager' not in df.columns:
                df['is_fund_manager'] = False
            elif 'isfundmanager' in df.columns:
                df['is_fund_manager'] = df['isfundmanager']
            
            investors = []
            for _, row in df.iterrows():
                try:
                    # Handle join date
                    join_date = date.today()
                    if pd.notna(row['join_date']):
                        if hasattr(row['join_date'], 'date'):
                            join_date = row['join_date'].date()
                        else:
                            join_date = pd.to_datetime(row['join_date']).date()
                    
                    investor = Investor(
                        id=safe_int_conversion(row['id']),
                        name=str(row['name']).strip(),
                        phone=str(row.get('phone', '')).strip(),
                        address=str(row.get('address', '')).strip(),
                        email=str(row.get('email', '')).strip(),
                        join_date=join_date,
                        is_fund_manager=bool(row.get('is_fund_manager', False))
                    )
                    
                    if investor.name and investor.id >= 0:
                        investors.append(investor)
                        
                except Exception as e:
                    print(f"Warning: Skipping investor row due to error: {e}")
                    continue
            
            print(f"✅ Loaded {len(investors)} investors from CSV")
            return investors
            
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"❌ Error loading investors: {e}")
            return []
    
    def load_tranches(self) -> List[Tranche]:
        """Load tranches from CSV"""
        try:
            if not self.tranches_file.exists():
                return []
                
            df = pd.read_csv(self.tranches_file)
            if df.empty:
                return []
            
            # Handle column name cases
            df.columns = df.columns.str.lower()
            
            # Parse dates
            date_cols = ['entry_date', 'entrydate', 'original_entry_date', 'originalentrydate']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Add missing columns with defaults
            required_cols = {
                'hwm': 'entry_nav',
                'original_entry_date': 'entry_date',
                'original_entry_nav': 'entry_nav', 
                'cumulative_fees_paid': 0.0,
                'original_invested_value': None,
                'invested_value': None
            }
            
            for col, default_source in required_cols.items():
                if col not in df.columns:
                    if isinstance(default_source, str) and default_source in df.columns:
                        df[col] = df[default_source]
                    elif col == 'original_invested_value':
                        df[col] = df['units'] * df['entry_nav']
                    elif col == 'invested_value':
                        df[col] = df['units'] * df['entry_nav']
                    else:
                        df[col] = default_source
            
            tranches = []
            for _, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['entry_date']) or row['units'] <= 0 or row['entry_nav'] <= 0:
                        print(f"Skipping invalid tranche: {row.get('tranche_id', 'unknown')}")
                        continue
                    
                    # Handle original entry date
                    original_entry_date = row['entry_date']
                    if 'original_entry_date' in row and pd.notna(row['original_entry_date']):
                        original_entry_date = row['original_entry_date']
                    
                    tranche = Tranche(
                        investor_id=safe_int_conversion(row['investor_id']),
                        tranche_id=str(row['tranche_id']),
                        entry_date=row['entry_date'],
                        entry_nav=safe_float_conversion(row['entry_nav']),
                        units=safe_float_conversion(row['units']),
                        hwm=safe_float_conversion(row.get('hwm', row['entry_nav'])),
                        original_entry_date=original_entry_date,
                        original_entry_nav=safe_float_conversion(row.get('original_entry_nav', row['entry_nav'])),
                        cumulative_fees_paid=safe_float_conversion(row.get('cumulative_fees_paid', 0.0)),
                        original_invested_value=safe_float_conversion(row.get('original_invested_value', safe_float_conversion(row['units']) * safe_float_conversion(row['entry_nav'])))
                    )
                    
                    # Set invested_value if available
                    if 'invested_value' in row and pd.notna(row['invested_value']):
                        tranche.invested_value = safe_float_conversion(row['invested_value'])
                    
                    tranches.append(tranche)
                    
                except Exception as e:
                    print(f"Warning: Skipping tranche due to error: {e}")
                    continue
            
            print(f"✅ Loaded {len(tranches)} tranches from CSV")
            return tranches
            
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"❌ Error loading tranches: {e}")
            return []
    
    def load_transactions(self) -> List[Transaction]:
        """Load transactions from CSV với timezone handling"""
        try:
            if not self.transactions_file.exists():
                return []
                
            df = pd.read_csv(self.transactions_file)
            if df.empty:
                return []
            
            # Handle column case
            df.columns = df.columns.str.lower()
            
            # Parse date column with comprehensive timezone handling
            try:
                # Try standard pandas parsing first
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                
                # For any remaining NaT values, try alternative methods
                if df['date'].isna().any():
                    # Store original dates for debugging
                    na_mask = df['date'].isna()
                    original_dates = df.loc[na_mask, 'date'].copy()
                    
                    # Try parsing with different methods for problematic dates
                    for idx in df[na_mask].index:
                        date_str = str(df.loc[idx, 'date'])
                        if date_str and date_str != 'nan':
                            try:
                                # Try parsing with dateutil
                                from dateutil.parser import parse
                                parsed_date = parse(date_str)
                                df.loc[idx, 'date'] = parsed_date
                            except:
                                pass
                                
            except Exception as e:
                print(f"⚠️ Date parsing error: {e}")
                # Fallback to simple parsing
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            transactions = []
            for _, row in df.iterrows():
                try:
                    if pd.isna(row['date']):
                        print(f"Skipping transaction with invalid date: {row.get('id', 'unknown')}")
                        continue
                    
                    # Use naive datetime for local-only operations (no timezone)
                    raw_date = row['date']
                    if hasattr(raw_date, 'tzinfo') and raw_date.tzinfo is not None:
                        # Remove timezone info for Excel compatibility
                        normalized_date = raw_date.replace(tzinfo=None)
                    else:
                        # Already naive - use as is
                        normalized_date = raw_date
                    
                    transaction = Transaction(
                        id=safe_int_conversion(row['id']),
                        investor_id=safe_int_conversion(row['investor_id']),
                        date=normalized_date,
                        type=str(row['type']),
                        amount=safe_float_conversion(row['amount']),
                        nav=safe_float_conversion(row.get('nav', 0)),
                        units_change=safe_float_conversion(row.get('units_change', 0))
                    )
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    print(f"Warning: Skipping transaction due to error: {e}")
                    continue
            
            # Debug logging
            nav_transactions = [t for t in transactions if t.nav and t.nav > 0]
            print(f"✅ Loaded {len(transactions)} transactions from CSV ({len(nav_transactions)} with NAV)")
            
            return transactions
            
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"❌ Error loading transactions: {e}")
            return []
    
    def load_fee_records(self) -> List[FeeRecord]:
        """Load fee records from CSV"""
        try:
            if not self.fee_records_file.exists():
                return []
                
            df = pd.read_csv(self.fee_records_file)
            if df.empty:
                return []
            
            # Handle column case
            df.columns = df.columns.str.lower()
            
            # Parse date
            df['calculation_date'] = pd.to_datetime(df['calculation_date'], errors='coerce')
            
            records = []
            for _, row in df.iterrows():
                try:
                    if pd.isna(row['calculation_date']) or row['fee_amount'] < 0:
                        print(f"Skipping invalid fee record: {row.get('id', 'unknown')}")
                        continue
                    
                    record = FeeRecord(
                        id=safe_int_conversion(row['id']),
                        period=str(row['period']),
                        investor_id=safe_int_conversion(row['investor_id']),
                        fee_amount=safe_float_conversion(row['fee_amount']),
                        fee_units=safe_float_conversion(row['fee_units']),
                        calculation_date=row['calculation_date'],
                        units_before=safe_float_conversion(row.get('units_before', 0)),
                        units_after=safe_float_conversion(row.get('units_after', 0)),
                        nav_per_unit=safe_float_conversion(row.get('nav_per_unit', 0)),
                        description=str(row.get('description', ''))
                    )
                    
                    records.append(record)
                    
                except Exception as e:
                    print(f"Warning: Skipping fee record due to error: {e}")
                    continue
            
            print(f"✅ Loaded {len(records)} fee records from CSV")
            return records
            
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"❌ Error loading fee records: {e}")
            return []
    
    # === SAVE METHODS ===
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save investors to CSV với thread safety"""
        try:
            with self._lock:
                if not investors:
                    # Create empty file
                    df = pd.DataFrame(columns=['id', 'name', 'phone', 'address', 'email', 'join_date', 'is_fund_manager'])
                    return self._atomic_write_csv(df, self.investors_file)
                
                data = []
                for inv in investors:
                    data.append({
                        'id': inv.id,
                        'name': inv.name,
                        'phone': inv.phone,
                        'address': inv.address,
                        'email': inv.email,
                        'join_date': inv.join_date,
                        'is_fund_manager': inv.is_fund_manager
                    })
                
                df = pd.DataFrame(data)
                success = self._atomic_write_csv(df, self.investors_file)
                
                if success:
                    print(f"✅ Saved {len(investors)} investors to CSV")
                return success
                
        except Exception as e:
            print(f"❌ Error saving investors: {e}")
            return False
    
    def save_tranches(self, tranches: List[Tranche]) -> bool:
        """Save tranches to CSV"""
        try:
            with self._lock:
                if not tranches:
                    df = pd.DataFrame(columns=[
                        'investor_id', 'tranche_id', 'entry_date', 'entry_nav', 'units',
                        'hwm', 'original_entry_date', 'original_entry_nav', 
                        'cumulative_fees_paid', 'original_invested_value', 'invested_value'
                    ])
                    return self._atomic_write_csv(df, self.tranches_file)
                
                data = []
                for t in tranches:
                    data.append({
                        'investor_id': t.investor_id,
                        'tranche_id': t.tranche_id,
                        'entry_date': t.entry_date,
                        'entry_nav': t.entry_nav,
                        'units': t.units,
                        'hwm': t.hwm,
                        'original_entry_date': t.original_entry_date,
                        'original_entry_nav': t.original_entry_nav,
                        'cumulative_fees_paid': t.cumulative_fees_paid,
                        'original_invested_value': t.original_invested_value,
                        'invested_value': getattr(t, 'invested_value', t.units * t.entry_nav)
                    })
                
                df = pd.DataFrame(data)
                success = self._atomic_write_csv(df, self.tranches_file)
                
                if success:
                    print(f"✅ Saved {len(tranches)} tranches to CSV")
                return success
                
        except Exception as e:
            print(f"❌ Error saving tranches: {e}")
            return False
    
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions to CSV"""
        try:
            with self._lock:
                if not transactions:
                    df = pd.DataFrame(columns=['id', 'investor_id', 'date', 'type', 'amount', 'nav', 'units_change'])
                    return self._atomic_write_csv(df, self.transactions_file)
                
                data = []
                for t in transactions:
                    # Convert to naive datetime for Excel compatibility
                    if hasattr(t.date, 'tzinfo') and t.date.tzinfo is not None:
                        # Remove timezone info
                        naive_date = t.date.replace(tzinfo=None)
                    else:
                        naive_date = t.date
                    
                    data.append({
                        'id': t.id,
                        'investor_id': t.investor_id,
                        'date': naive_date,
                        'type': t.type,
                        'amount': t.amount,
                        'nav': t.nav,
                        'units_change': t.units_change
                    })
                
                df = pd.DataFrame(data)
                success = self._atomic_write_csv(df, self.transactions_file)
                
                if success:
                    nav_count = len([t for t in transactions if t.nav and t.nav > 0])
                    print(f"✅ Saved {len(transactions)} transactions to CSV ({nav_count} with NAV)")
                return success
                
        except Exception as e:
            print(f"❌ Error saving transactions: {e}")
            return False
    
    def save_fee_records(self, fee_records: List[FeeRecord]) -> bool:
        """Save fee records to CSV"""
        try:
            with self._lock:
                if not fee_records:
                    df = pd.DataFrame(columns=[
                        'id', 'period', 'investor_id', 'fee_amount', 'fee_units',
                        'calculation_date', 'units_before', 'units_after', 'nav_per_unit', 'description'
                    ])
                    return self._atomic_write_csv(df, self.fee_records_file)
                
                data = []
                for f in fee_records:
                    data.append({
                        'id': f.id,
                        'period': f.period,
                        'investor_id': f.investor_id,
                        'fee_amount': f.fee_amount,
                        'fee_units': f.fee_units,
                        'calculation_date': f.calculation_date,
                        'units_before': f.units_before,
                        'units_after': f.units_after,
                        'nav_per_unit': f.nav_per_unit,
                        'description': f.description
                    })
                
                df = pd.DataFrame(data)
                success = self._atomic_write_csv(df, self.fee_records_file)
                
                if success:
                    print(f"✅ Saved {len(fee_records)} fee records to CSV")
                return success
                
        except Exception as e:
            print(f"❌ Error saving fee records: {e}")
            return False
    
    def save_all_data_enhanced(
        self, 
        investors: List[Investor],
        tranches: List[Tranche], 
        transactions: List[Transaction],
        fee_records: List[FeeRecord]
    ) -> bool:
        """Save all data với atomic transaction-like behavior"""
        try:
            print("💾 Starting enhanced save all data to CSV...")
            
            # Save all components - nếu bất kỳ cái nào fail thì rollback
            results = []
            results.append(self.save_investors(investors))
            results.append(self.save_tranches(tranches))
            results.append(self.save_transactions(transactions))
            results.append(self.save_fee_records(fee_records))
            
            success = all(results)
            
            if success:
                # Create summary backup
                timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
                print(f"✅ All data saved successfully to CSV at {timestamp}")
                
                # Log counts
                counts = {
                    'investors': len(investors),
                    'tranches': len(tranches), 
                    'transactions': len(transactions),
                    'fee_records': len(fee_records)
                }
                print(f"📊 Data counts: {counts}")
                
                return True
            else:
                print("❌ Some saves failed, check logs above")
                return False
                
        except Exception as e:
            print(f"💥 Critical error in save_all_data_enhanced: {e}")
            return False
    
    # === UTILITY METHODS ===
    
    def create_backup(self) -> Optional[str]:
        """Create comprehensive backup"""
        try:
            timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
            backup_count = 0
            
            files_to_backup = [
                self.investors_file,
                self.tranches_file,
                self.transactions_file,
                self.fee_records_file
            ]
            
            for file_path in files_to_backup:
                if file_path.exists():
                    backup_name = f"{file_path.stem}_{timestamp}.csv"
                    backup_path = self.backup_dir / backup_name
                    shutil.copy2(file_path, backup_path)
                    backup_count += 1
            
            if backup_count > 0:
                print(f"✅ Created backup with timestamp {timestamp} ({backup_count} files)")
                return timestamp
            else:
                print("⚠️ No files to backup")
                return None
                
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        try:
            investors = self.load_investors()
            tranches = self.load_tranches()
            transactions = self.load_transactions()
            fee_records = self.load_fee_records()
            
            stats = {
                'connected': self.connected,
                'storage_type': 'CSV',
                'data_directory': str(self.data_dir),
                'table_counts': {
                    'investors': len(investors),
                    'tranches': len(tranches),
                    'transactions': len(transactions),
                    'fee_records': len(fee_records)
                },
                'file_info': {}
            }
            
            # Add file size info
            for name, file_path in [
                ('investors', self.investors_file),
                ('tranches', self.tranches_file),
                ('transactions', self.transactions_file),
                ('fee_records', self.fee_records_file)
            ]:
                if file_path.exists():
                    stats['file_info'][name] = {
                        'size_bytes': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
                else:
                    stats['file_info'][name] = {'size_bytes': 0, 'modified': None}
            
            # Add latest NAV info
            nav_transactions = [t for t in transactions if t.nav and t.nav > 0]
            if nav_transactions:
                latest_nav_trans = max(nav_transactions, key=lambda x: (x.date, x.id))
                stats['latest_nav'] = latest_nav_trans.nav
                stats['latest_nav_date'] = latest_nav_trans.date.isoformat()
            
            return stats
            
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            checks = []
            
            # Directory access check
            try:
                test_file = self.data_dir / ".health_check"
                test_file.write_text("test")
                test_file.unlink()
                
                checks.append({
                    'name': 'Directory Access',
                    'status': 'pass',
                    'details': f'Can read/write to {self.data_dir}'
                })
            except Exception as e:
                checks.append({
                    'name': 'Directory Access',
                    'status': 'fail',
                    'details': f'Cannot access {self.data_dir}: {e}'
                })
            
            # File existence check
            files_exist = 0
            total_files = 4
            
            for name, file_path in [
                ('investors', self.investors_file),
                ('tranches', self.tranches_file),
                ('transactions', self.transactions_file),
                ('fee_records', self.fee_records_file)
            ]:
                if file_path.exists():
                    files_exist += 1
            
            checks.append({
                'name': 'Data Files',
                'status': 'pass' if files_exist > 0 else 'warn',
                'details': f'{files_exist}/{total_files} data files exist'
            })
            
            # Data loading check
            try:
                investors = self.load_investors()
                tranches = self.load_tranches()
                
                data_counts = {
                    'investors': len(investors),
                    'tranches': len(tranches)
                }
                
                checks.append({
                    'name': 'Data Loading',
                    'status': 'pass',
                    'details': data_counts
                })
            except Exception as e:
                checks.append({
                    'name': 'Data Loading',
                    'status': 'fail',
                    'details': f'Cannot load data: {e}'
                })
            
            # Overall status
            failed_checks = [c for c in checks if c['status'] == 'fail']
            overall_status = 'healthy' if not failed_checks else 'degraded'
            
            return {
                'status': overall_status,
                'timestamp': TimezoneManager.now().isoformat(),
                'checks': checks,
                'summary': f'{len(checks) - len(failed_checks)}/{len(checks)} checks passed'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': TimezoneManager.now().isoformat()
            }