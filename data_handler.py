import pandas as pd
import shutil
from typing import List, Optional
from datetime import datetime, date
import streamlit as st

from config import *
from models import Investor, Tranche, Transaction, FeeRecord

class EnhancedDataHandler:
    """Enhanced data handler với support cho fee records và new fields"""
    
    @staticmethod
    def create_backup() -> Optional[str]:
        """Tạo backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            for file_path in [INVESTORS_FILE, TRANCHES_FILE, TRANSACTIONS_FILE]:
                if file_path.exists():
                    backup_name = f"{file_path.stem}_{timestamp}.csv"
                    shutil.copy2(file_path, BACKUP_DIR / backup_name)
            return timestamp
        except Exception:
            return None
    
    @staticmethod
    def load_investors() -> List[Investor]:
        """Load investors với support cho is_fund_manager field"""
        try:
            df = pd.read_csv(INVESTORS_FILE, dtype={'Phone': 'str'})
            if df.empty:
                return []
            
            df['JoinDate'] = pd.to_datetime(df['JoinDate'], errors='coerce')
            df['Phone'] = df['Phone'].fillna('').astype(str).replace('nan', '')
            
            # Add is_fund_manager column if not exists (backward compatibility)
            if 'IsFundManager' not in df.columns:
                df['IsFundManager'] = False
            
            investors = []
            for _, row in df.iterrows():
                investor = Investor(
                    id=int(row['ID']),
                    name=str(row['Name']),
                    phone=str(row.get('Phone', '')),
                    address=str(row.get('Address', '')),
                    email=str(row.get('Email', '')),
                    join_date=row['JoinDate'].date() if pd.notna(row['JoinDate']) else date.today(),
                    is_fund_manager=bool(row.get('IsFundManager', False))
                )
                investors.append(investor)
            return investors
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load investors: {str(e)}")
            return []
    
    @staticmethod
    def save_investors(investors: List[Investor]) -> bool:
        """Save investors với is_fund_manager field"""
        try:
            data = [{
                'ID': inv.id, 'Name': inv.name, 'Phone': inv.phone,
                'Address': inv.address, 'Email': inv.email, 'JoinDate': inv.join_date,
                'IsFundManager': inv.is_fund_manager
            } for inv in investors]
            
            pd.DataFrame(data).to_csv(INVESTORS_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Lỗi save investors: {str(e)}")
            return False
    
    @staticmethod
    def load_tranches() -> List[Tranche]:
        """Load tranches với new fields"""
        try:
            df = pd.read_csv(TRANCHES_FILE)
            if df.empty:
                return []
            
            df['EntryDate'] = pd.to_datetime(df['EntryDate'], errors='coerce')
            
            # Add new columns if not exists (backward compatibility)
            if 'HWM' not in df.columns:
                df['HWM'] = df['EntryNAV']
            if 'OriginalEntryDate' not in df.columns:
                df['OriginalEntryDate'] = df['EntryDate']
            if 'OriginalEntryNAV' not in df.columns:
                df['OriginalEntryNAV'] = df['EntryNAV']
            if 'CumulativeFeesPaid' not in df.columns:
                df['CumulativeFeesPaid'] = 0.0
            
            # Handle original date parsing
            df['OriginalEntryDate'] = pd.to_datetime(df['OriginalEntryDate'], errors='coerce')
            # Fill NaT values with EntryDate
            df['OriginalEntryDate'] = df['OriginalEntryDate'].fillna(df['EntryDate'])
            
            tranches = []
            for _, row in df.iterrows():
                tranche = Tranche(
                    investor_id=int(row['InvestorID']),
                    tranche_id=str(row['TrancheID']),
                    entry_date=row['EntryDate'],
                    entry_nav=float(row['EntryNAV']),
                    units=float(row['Units']),
                    hwm=float(row.get('HWM', row['EntryNAV'])),
                    original_entry_date=row['OriginalEntryDate'],
                    original_entry_nav=float(row.get('OriginalEntryNAV', row['EntryNAV'])),
                    cumulative_fees_paid=float(row.get('CumulativeFeesPaid', 0.0))
                )
                tranches.append(tranche)
            return tranches
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load tranches: {str(e)}")
            return []
    
    @staticmethod
    def save_tranches(tranches: List[Tranche]) -> bool:
        """Save tranches với new fields"""
        try:
            data = [{
                'InvestorID': t.investor_id, 'TrancheID': t.tranche_id,
                'EntryDate': t.entry_date, 'EntryNAV': t.entry_nav,
                'Units': t.units, 'HWM': t.hwm,
                'OriginalEntryDate': t.original_entry_date,
                'OriginalEntryNAV': t.original_entry_nav,
                'CumulativeFeesPaid': t.cumulative_fees_paid
            } for t in tranches]
            
            pd.DataFrame(data).to_csv(TRANCHES_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Lỗi save tranches: {str(e)}")
            return False
    
    @staticmethod
    def load_transactions() -> List[Transaction]:
        """Load transactions (unchanged)"""
        try:
            df = pd.read_csv(TRANSACTIONS_FILE)
            if df.empty:
                return []
            
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
            transactions = []
            for _, row in df.iterrows():
                transaction = Transaction(
                    id=int(row['ID']),
                    investor_id=int(row['InvestorID']),
                    date=row['Date'],
                    type=str(row['Type']),
                    amount=float(row['Amount']),
                    nav=float(row['NAV']),
                    units_change=float(row['UnitsChange'])
                )
                transactions.append(transaction)
            return transactions
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load transactions: {str(e)}")
            return []
    
    @staticmethod
    def save_transactions(transactions: List[Transaction]) -> bool:
        """Save transactions (unchanged)"""
        try:
            data = [{
                'ID': t.id, 'InvestorID': t.investor_id, 'Date': t.date,
                'Type': t.type, 'Amount': t.amount, 'NAV': t.nav,
                'UnitsChange': t.units_change
            } for t in transactions]
            
            pd.DataFrame(data).to_csv(TRANSACTIONS_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Lỗi save transactions: {str(e)}")
            return False
    
    @staticmethod
    def load_fee_records() -> List[FeeRecord]:
        """Load fee records"""
        try:
            fee_file = DATA_DIR / "fee_records.csv"
            df = pd.read_csv(fee_file)
            if df.empty:
                return []
            
            df['CalculationDate'] = pd.to_datetime(df['CalculationDate'], errors='coerce')
            
            records = []
            for _, row in df.iterrows():
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
                records.append(record)
            return records
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Lỗi load fee records: {str(e)}")
            return []
    
    @staticmethod
    def save_fee_records(fee_records: List[FeeRecord]) -> bool:
        """Save fee records"""
        try:
            fee_file = DATA_DIR / "fee_records.csv"
            data = [{
                'ID': record.id, 'Period': record.period, 'InvestorID': record.investor_id,
                'FeeAmount': record.fee_amount, 'FeeUnits': record.fee_units,
                'CalculationDate': record.calculation_date, 'UnitsBefore': record.units_before,
                'UnitsAfter': record.units_after, 'NAVPerUnit': record.nav_per_unit,
                'Description': record.description
            } for record in fee_records]
            
            pd.DataFrame(data).to_csv(fee_file, index=False)
            return True
        except Exception as e:
            st.error(f"Lỗi save fee records: {str(e)}")
            return False
    
    @staticmethod
    def save_all_data_enhanced(investors, tranches, transactions, fee_records) -> bool:
        """Save all data including fee records"""
        try:
            EnhancedDataHandler.create_backup()
            return (EnhancedDataHandler.save_investors(investors) and 
                   EnhancedDataHandler.save_tranches(tranches) and 
                   EnhancedDataHandler.save_transactions(transactions) and
                   EnhancedDataHandler.save_fee_records(fee_records))
        except Exception as e:
            st.error(f"Lỗi save enhanced data: {str(e)}")
            return False