import pandas as pd
import shutil
from typing import List, Optional
from datetime import datetime, date, timedelta
import streamlit as st

from config import *
from models import Investor, Tranche, Transaction, FeeRecord, validate_tranche, validate_transaction, validate_fee_record

class EnhancedDataHandler:
    """
    FIXED: Enhanced data handler với proper connection attribute và error handling
    """
    
    def __init__(self):
        """Initialize with connection status"""
        self.connected = True  # FIXED: Add missing connected attribute
        self._validate_directories()
    
    def _validate_directories(self):
        """Ensure required directories exist"""
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create directories: {e}")
            self.connected = False
    
    @staticmethod
    def create_backup() -> Optional[str]:
        """Tạo backup với enhanced error handling"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_count = 0
            
            for file_path in [INVESTORS_FILE, TRANCHES_FILE, TRANSACTIONS_FILE]:
                if file_path.exists():
                    backup_name = f"{file_path.stem}_{timestamp}.csv"
                    backup_path = BACKUP_DIR / backup_name
                    
                    # Ensure backup directory exists
                    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(file_path, backup_path)
                    backup_count += 1
            
            # Also backup fee records if exists
            fee_file = DATA_DIR / "fee_records.csv"
            if fee_file.exists():
                backup_name = f"fee_records_{timestamp}.csv"
                shutil.copy2(fee_file, BACKUP_DIR / backup_name)
                backup_count += 1
            
            return timestamp if backup_count > 0 else None
            
        except Exception as e:
            print(f"Backup failed: {str(e)}")
            return None
    
    def load_investors(self) -> List[Investor]:
        """FIXED: Load investors với comprehensive validation"""
        try:
            if not INVESTORS_FILE.exists():
                return []
                
            df = pd.read_csv(INVESTORS_FILE, dtype={'Phone': 'str'})
            if df.empty:
                return []
            
            # Clean and validate data
            df['JoinDate'] = pd.to_datetime(df['JoinDate'], errors='coerce')
            df['Phone'] = df['Phone'].fillna('').astype(str).replace('nan', '')
            
            # Add is_fund_manager column if not exists (backward compatibility)
            if 'IsFundManager' not in df.columns:
                df['IsFundManager'] = False
            
            investors = []
            for _, row in df.iterrows():
                try:
                    # Handle missing or invalid join dates
                    join_date = date.today()
                    if pd.notna(row['JoinDate']):
                        join_date = row['JoinDate'].date()
                    
                    investor = Investor(
                        id=int(row['ID']),
                        name=str(row['Name']).strip(),
                        phone=str(row.get('Phone', '')).strip(),
                        address=str(row.get('Address', '')).strip(),
                        email=str(row.get('Email', '')).strip(),
                        join_date=join_date,
                        is_fund_manager=bool(row.get('IsFundManager', False))
                    )
                    
                    # Basic validation
                    if investor.name and investor.id >= 0:
                        investors.append(investor)
                    else:
                        print(f"Skipping invalid investor: {row}")
                        
                except Exception as e:
                    print(f"Error loading investor row {row['ID']}: {str(e)}")
                    continue
            
            return investors
            
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load investors: {str(e)}")
            return []
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """FIXED: Save investors với validation"""
        try:
            if not investors:
                # Create empty file if no investors
                pd.DataFrame(columns=['ID', 'Name', 'Phone', 'Address', 'Email', 'JoinDate', 'IsFundManager']).to_csv(INVESTORS_FILE, index=False)
                return True
            
            # Validate investors before saving
            valid_investors = []
            for inv in investors:
                if inv.name and inv.id >= 0:
                    valid_investors.append(inv)
                else:
                    print(f"Skipping invalid investor: {inv}")
            
            if not valid_investors:
                st.warning("Không có investor hợp lệ để lưu")
                return False
            
            data = []
            for inv in valid_investors:
                data.append({
                    'ID': inv.id, 
                    'Name': inv.name, 
                    'Phone': inv.phone,
                    'Address': inv.address, 
                    'Email': inv.email, 
                    'JoinDate': inv.join_date,
                    'IsFundManager': inv.is_fund_manager
                })
            
            # Ensure directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            pd.DataFrame(data).to_csv(INVESTORS_FILE, index=False)
            return True
            
        except Exception as e:
            st.error(f"Lỗi save investors: {str(e)}")
            return False
    
    def load_tranches(self) -> List[Tranche]:
        """Load tranches với comprehensive validation + hỗ trợ InvestedValue"""
        try:
            if not TRANCHES_FILE.exists():
                return []
                
            df = pd.read_csv(TRANCHES_FILE)
            if df.empty:
                return []
            
            # Parse dates
            df['EntryDate'] = pd.to_datetime(df['EntryDate'], errors='coerce')
            
            # Add new columns if not exists (backward compatibility)
            required_columns = {
                'HWM': 'EntryNAV',
                'OriginalEntryDate': 'EntryDate', 
                'OriginalEntryNAV': 'EntryNAV',
                'CumulativeFeesPaid': 0.0,
                'OriginalInvestedValue': None,
                'InvestedValue': None
            }
            
            for col, default_source in required_columns.items():
                if col not in df.columns:
                    if isinstance(default_source, str):
                        df[col] = df[default_source]
                    elif col == "OriginalInvestedValue":
                        df[col] = df['Units'] * df['EntryNAV']
                    elif col == "InvestedValue":
                        df[col] = df['Units'] * df['EntryNAV']
                    else:
                        df[col] = default_source
            
            # Handle original date parsing
            df['OriginalEntryDate'] = pd.to_datetime(df['OriginalEntryDate'], errors='coerce')
            df['OriginalEntryDate'] = df['OriginalEntryDate'].fillna(df['EntryDate'])
            
            tranches = []
            for _, row in df.iterrows():
                try:
                    if pd.isna(row['EntryDate']) or row['Units'] <= 0 or row['EntryNAV'] <= 0:
                        print(f"Skipping invalid tranche: {row['TrancheID']}")
                        continue
                    
                    tranche = Tranche(
                        investor_id=int(row['InvestorID']),
                        tranche_id=str(row['TrancheID']),
                        entry_date=row['EntryDate'],
                        entry_nav=float(row['EntryNAV']),
                        units=float(row['Units']),
                        original_invested_value=float(row.get('OriginalInvestedValue', row['Units'] * row['EntryNAV'])),
                        hwm=float(row.get('HWM', row['EntryNAV'])),
                        original_entry_date=row['OriginalEntryDate'],
                        original_entry_nav=float(row.get('OriginalEntryNAV', row['EntryNAV'])),
                        cumulative_fees_paid=float(row.get('CumulativeFeesPaid', 0.0))
                    )
                    
                    # Set invested_value nếu file có cột này
                    if "InvestedValue" in row and pd.notna(row["InvestedValue"]):
                        tranche.invested_value = float(row["InvestedValue"])
                    
                    is_valid, errors = validate_tranche(tranche)
                    if is_valid:
                        tranches.append(tranche)
                    else:
                        print(f"Invalid tranche {tranche.tranche_id}: {errors}")
                        
                except Exception as e:
                    print(f"Error loading tranche {row.get('TrancheID', 'unknown')}: {str(e)}")
                    continue
            
            return tranches
            
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load tranches: {str(e)}")
            return []

    
    def save_tranches(self, tranches: List[Tranche]) -> bool:
        """Save tranches với validation + lưu InvestedValue"""
        try:
            valid_tranches = []
            for t in tranches:
                is_valid, errors = validate_tranche(t)
                if is_valid:
                    valid_tranches.append(t)
                else:
                    print(f"Skipping invalid tranche {t.tranche_id}: {errors}")
            
            if not tranches:
                columns = ['InvestorID', 'TrancheID', 'EntryDate', 'EntryNAV', 'Units', 
                        'HWM', 'OriginalEntryDate', 'OriginalEntryNAV', 'CumulativeFeesPaid',
                        'OriginalInvestedValue', 'InvestedValue']
                pd.DataFrame(columns=columns).to_csv(TRANCHES_FILE, index=False)
                return True
            
            data = []
            for t in valid_tranches:
                data.append({
                    'InvestorID': t.investor_id, 
                    'TrancheID': t.tranche_id,
                    'EntryDate': t.entry_date, 
                    'EntryNAV': t.entry_nav,
                    'Units': t.units, 
                    'HWM': t.hwm,
                    'OriginalEntryDate': t.original_entry_date,
                    'OriginalEntryNAV': t.original_entry_nav,
                    'CumulativeFeesPaid': t.cumulative_fees_paid,
                    'OriginalInvestedValue': t.original_invested_value,
                    'InvestedValue': t.invested_value
                })
            
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(data).to_csv(TRANCHES_FILE, index=False)
            return True
            
        except Exception as e:
            st.error(f"Lỗi save tranches: {str(e)}")
            return False

    
    def load_transactions(self) -> List[Transaction]:
        """FIXED: Load transactions với validation"""
        try:
            if not TRANSACTIONS_FILE.exists():
                return []
                
            df = pd.read_csv(TRANSACTIONS_FILE)
            if df.empty:
                return []
            
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            transactions = []
            for _, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['Date']):
                        print(f"Skipping transaction with invalid date: {row['ID']}")
                        continue
                    
                    transaction = Transaction(
                        id=int(row['ID']),
                        investor_id=int(row['InvestorID']),
                        date=row['Date'],
                        type=str(row['Type']),
                        amount=float(row['Amount']),
                        nav=float(row['NAV']),
                        units_change=float(row['UnitsChange'])
                    )
                    
                    # Validate transaction
                    is_valid, errors = validate_transaction(transaction)
                    if is_valid:
                        transactions.append(transaction)
                    else:
                        print(f"Invalid transaction {transaction.id}: {errors}")
                        
                except Exception as e:
                    print(f"Error loading transaction {row.get('ID', 'unknown')}: {str(e)}")
                    continue
            
            return transactions
            
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load transactions: {str(e)}")
            return []
    
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """FIXED: Save transactions với validation"""
        try:
            # Validate transactions before saving
            valid_transactions = []
            for t in transactions:
                is_valid, errors = validate_transaction(t)
                if is_valid:
                    valid_transactions.append(t)
                else:
                    print(f"Skipping invalid transaction {t.id}: {errors}")
            
            if not transactions:
                # Create empty file
                columns = ['ID', 'InvestorID', 'Date', 'Type', 'Amount', 'NAV', 'UnitsChange']
                pd.DataFrame(columns=columns).to_csv(TRANSACTIONS_FILE, index=False)
                return True
            
            data = []
            for t in valid_transactions:
                data.append({
                    'ID': t.id, 
                    'InvestorID': t.investor_id, 
                    'Date': t.date,
                    'Type': t.type, 
                    'Amount': t.amount, 
                    'NAV': t.nav,
                    'UnitsChange': t.units_change
                })
            
            # Ensure directory exists  
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            pd.DataFrame(data).to_csv(TRANSACTIONS_FILE, index=False)
            return True
            
        except Exception as e:
            st.error(f"Lỗi save transactions: {str(e)}")
            return False
    
    def load_fee_records(self) -> List[FeeRecord]:
        """FIXED: Load fee records với validation"""
        try:
            fee_file = DATA_DIR / "fee_records.csv"
            if not fee_file.exists():
                return []
                
            df = pd.read_csv(fee_file)
            if df.empty:
                return []
            
            df['CalculationDate'] = pd.to_datetime(df['CalculationDate'], errors='coerce')
            
            records = []
            for _, row in df.iterrows():
                try:
                    # Validate required fields
                    if pd.isna(row['CalculationDate']) or row['FeeAmount'] < 0:
                        print(f"Skipping invalid fee record: {row['ID']}")
                        continue
                    
                    record = FeeRecord(
                        id=int(row['ID']),
                        period=str(row['Period']),
                        investor_id=int(row['InvestorID']),
                        fee_amount=float(row['FeeAmount']),
                        fee_units=float(row['FeeUnits']),
                        calculation_date=row['CalculationDate'],
                        units_before=float(row['UnitsBefore']),
                        units_after=float(row['UnitsAfter']),
                        nav_per_unit=float(row['NAVPerUnit']),
                        description=str(row.get('Description', ''))
                    )
                    
                    # Validate fee record
                    is_valid, errors = validate_fee_record(record)
                    if is_valid:
                        records.append(record)
                    else:
                        print(f"Invalid fee record {record.id}: {errors}")
                        
                except Exception as e:
                    print(f"Error loading fee record {row.get('ID', 'unknown')}: {str(e)}")
                    continue
            
            return records
            
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load fee records: {str(e)}")
            return []
    
    def save_fee_records(self, fee_records: List[FeeRecord]) -> bool:
        """FIXED: Save fee records với validation"""
        try:
            # Validate fee records before saving
            valid_records = []
            for record in fee_records:
                is_valid, errors = validate_fee_record(record)
                if is_valid:
                    valid_records.append(record)
                else:
                    print(f"Skipping invalid fee record {record.id}: {errors}")
            
            fee_file = DATA_DIR / "fee_records.csv"
            
            if not fee_records:
                # Create empty file
                columns = ['ID', 'Period', 'InvestorID', 'FeeAmount', 'FeeUnits',
                          'CalculationDate', 'UnitsBefore', 'UnitsAfter', 'NAVPerUnit', 'Description']
                pd.DataFrame(columns=columns).to_csv(fee_file, index=False)
                return True
            
            data = []
            for record in valid_records:
                data.append({
                    'ID': record.id, 
                    'Period': record.period, 
                    'InvestorID': record.investor_id,
                    'FeeAmount': record.fee_amount, 
                    'FeeUnits': record.fee_units,
                    'CalculationDate': record.calculation_date, 
                    'UnitsBefore': record.units_before,
                    'UnitsAfter': record.units_after, 
                    'NAVPerUnit': record.nav_per_unit,
                    'Description': record.description
                })
            
            # Ensure directory exists
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            pd.DataFrame(data).to_csv(fee_file, index=False)
            return True
            
        except Exception as e:
            st.error(f"Lỗi save fee records: {str(e)}")
            return False
    
    def save_all_data_enhanced(self, investors, tranches, transactions, fee_records) -> bool:
        """FIXED: Save all data với comprehensive validation và backup"""
        try:
            # Create backup before saving
            backup_timestamp = self.create_backup()
            if backup_timestamp:
                print(f"Created backup: {backup_timestamp}")
            
            # Validate all data before saving
            validation_results = self.validate_all_data(investors, tranches, transactions, fee_records)
            
            if not validation_results['valid']:
                st.error("Dữ liệu không hợp lệ, không thể lưu!")
                for error in validation_results['errors']:
                    st.error(f"• {error}")
                return False
            
            # Display warnings if any
            if validation_results['warnings']:
                st.warning("Có một số cảnh báo:")
                for warning in validation_results['warnings']:
                    st.warning(f"• {warning}")
            
            # Save all components
            success = (
                self.save_investors(investors) and 
                self.save_tranches(tranches) and 
                self.save_transactions(transactions) and
                self.save_fee_records(fee_records)
            )
            
            if success:
                print(f"Successfully saved all data at {datetime.now()}")
            else:
                st.error("Lưu dữ liệu thất bại!")
            
            return success
            
        except Exception as e:
            st.error(f"Lỗi save enhanced data: {str(e)}")
            return False
    
    def validate_all_data(self, investors, tranches, transactions, fee_records) -> dict:
        """
        FIXED: Comprehensive validation of all data
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Validate individual components
            invalid_investors = sum(1 for inv in investors if not inv.name or inv.id < 0)
            invalid_tranches = sum(1 for t in tranches if not validate_tranche(t)[0])
            invalid_transactions = sum(1 for trans in transactions if not validate_transaction(trans)[0])
            invalid_fee_records = sum(1 for f in fee_records if not validate_fee_record(f)[0])
            
            results['stats']['total_investors'] = len(investors)
            results['stats']['total_tranches'] = len(tranches) 
            results['stats']['total_transactions'] = len(transactions)
            results['stats']['total_fee_records'] = len(fee_records)
            results['stats']['invalid_investors'] = invalid_investors
            results['stats']['invalid_tranches'] = invalid_tranches
            results['stats']['invalid_transactions'] = invalid_transactions
            results['stats']['invalid_fee_records'] = invalid_fee_records
            
            # Check for critical errors
            if invalid_investors > 0:
                results['errors'].append(f"{invalid_investors} invalid investors found")
                results['valid'] = False
            
            if invalid_tranches > 0:
                results['errors'].append(f"{invalid_tranches} invalid tranches found")
                results['valid'] = False
            
            if invalid_transactions > 0:
                results['errors'].append(f"{invalid_transactions} invalid transactions found")
                results['valid'] = False
            
            if invalid_fee_records > 0:
                results['errors'].append(f"{invalid_fee_records} invalid fee records found")
                results['valid'] = False
            
            # Cross-validation checks
            investor_ids = {inv.id for inv in investors if inv.name and inv.id >= 0}
            
            # Check if all tranche investor_ids exist
            orphan_tranches = [t for t in tranches if t.investor_id not in investor_ids]
            if orphan_tranches:
                results['errors'].append(f"{len(orphan_tranches)} tranches reference non-existent investors")
                results['valid'] = False
            
            # Check if all transaction investor_ids exist (except fund manager transactions)
            orphan_transactions = [t for t in transactions if t.investor_id not in investor_ids and t.investor_id != 0]
            if orphan_transactions:
                results['errors'].append(f"{len(orphan_transactions)} transactions reference non-existent investors")
                results['valid'] = False
            
            # Check if all fee record investor_ids exist
            orphan_fee_records = [f for f in fee_records if f.investor_id not in investor_ids]
            if orphan_fee_records:
                results['errors'].append(f"{len(orphan_fee_records)} fee records reference non-existent investors")
                results['valid'] = False
            
            # Business logic warnings
            fund_managers = [inv for inv in investors if inv.is_fund_manager]
            if len(fund_managers) == 0:
                results['warnings'].append("No fund manager found")
            elif len(fund_managers) > 1:
                results['warnings'].append(f"Multiple fund managers found: {len(fund_managers)}")
            
            # Check for duplicate investor IDs
            investor_id_counts = {}
            for inv in investors:
                investor_id_counts[inv.id] = investor_id_counts.get(inv.id, 0) + 1
            
            duplicate_ids = [id for id, count in investor_id_counts.items() if count > 1]
            if duplicate_ids:
                results['errors'].append(f"Duplicate investor IDs: {duplicate_ids}")
                results['valid'] = False
            
            # Check for negative units in tranches
            negative_units_tranches = [t for t in tranches if t.units <= 0]
            if negative_units_tranches:
                results['errors'].append(f"{len(negative_units_tranches)} tranches have non-positive units")
                results['valid'] = False
            
            # Check for unreasonable NAV values
            extreme_nav_transactions = [t for t in transactions if t.nav > 0 and (t.nav < 1000 or t.nav > 10_000_000_000)]
            if extreme_nav_transactions:
                results['warnings'].append(f"{len(extreme_nav_transactions)} transactions have unusual NAV values")
            
            return results
            
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Validation error: {str(e)}")
            return results
    
    def get_data_statistics(self) -> dict:
        """
        FIXED: Get comprehensive data statistics
        """
        try:
            investors = self.load_investors()
            tranches = self.load_tranches()
            transactions = self.load_transactions()
            fee_records = self.load_fee_records()
            
            stats = {
                'investors': {
                    'total': len(investors),
                    'fund_managers': len([i for i in investors if i.is_fund_manager]),
                    'regular': len([i for i in investors if not i.is_fund_manager])
                },
                'tranches': {
                    'total': len(tranches),
                    'total_units': sum(t.units for t in tranches),
                    'total_invested_value': sum(t.invested_value for t in tranches),
                    'total_original_value': sum(t.original_invested_value for t in tranches),
                    'total_fees_paid': sum(t.cumulative_fees_paid for t in tranches)
                },
                'transactions': {
                    'total': len(transactions),
                    'deposits': len([t for t in transactions if t.type == 'Nạp']),
                    'withdrawals': len([t for t in transactions if t.type == 'Rút']),
                    'nav_updates': len([t for t in transactions if t.type == 'NAV Update']),
                    'fees': len([t for t in transactions if t.type in ['Phí', 'Phí Nhận']])
                },
                'fee_records': {
                    'total': len(fee_records),
                    'total_fee_amount': sum(f.fee_amount for f in fee_records),
                    'total_fee_units': sum(f.fee_units for f in fee_records)
                }
            }
            
            # Add latest NAV if available
            nav_transactions = [t for t in transactions if t.nav > 0]
            if nav_transactions:
                latest_nav_trans = max(nav_transactions, key=lambda x: (x.date, x.id))
                stats['latest_nav'] = latest_nav_trans.nav
                stats['latest_nav_date'] = latest_nav_trans.date
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """
        Cleanup old backup files
        Returns: number of files cleaned up
        """
        try:
            if not BACKUP_DIR.exists():
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cleanup_count = 0
            
            for backup_file in BACKUP_DIR.glob("*.csv"):
                if backup_file.stat().st_mtime < cutoff_date.timestamp():
                    backup_file.unlink()
                    cleanup_count += 1
            
            return cleanup_count
            
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")
            return 0