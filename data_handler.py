import pandas as pd
import shutil
from typing import List, Optional
from datetime import datetime
import streamlit as st

from config import *
from models import Investor, Tranche, Transaction

class DataHandler:
    """Xử lý tất cả operations với CSV"""
    
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
        """Load investors"""
        try:
            df = pd.read_csv(INVESTORS_FILE, dtype={'Phone': 'str'})
            if df.empty:
                return []
            
            df['JoinDate'] = pd.to_datetime(df['JoinDate'], errors='coerce')
            df['Phone'] = df['Phone'].fillna('').astype(str).replace('nan', '')
            
            investors = []
            for _, row in df.iterrows():
                investor = Investor(
                    id=int(row['ID']),
                    name=str(row['Name']),
                    phone=str(row.get('Phone', '')),
                    address=str(row.get('Address', '')),
                    email=str(row.get('Email', '')),
                    join_date=row['JoinDate'].date() if pd.notna(row['JoinDate']) else date.today()
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
        """Save investors"""
        try:
            data = [{
                'ID': inv.id, 'Name': inv.name, 'Phone': inv.phone,
                'Address': inv.address, 'Email': inv.email, 'JoinDate': inv.join_date
            } for inv in investors]
            
            pd.DataFrame(data).to_csv(INVESTORS_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Lỗi save investors: {str(e)}")
            return False
    
    @staticmethod
    def load_tranches() -> List[Tranche]:
        """Load tranches"""
        try:
            df = pd.read_csv(TRANCHES_FILE)
            if df.empty:
                return []
            
            df['EntryDate'] = pd.to_datetime(df['EntryDate'], errors='coerce')
            if 'HWM' not in df.columns:
                df['HWM'] = df['EntryNAV']
            
            tranches = []
            for _, row in df.iterrows():
                tranche = Tranche(
                    investor_id=int(row['InvestorID']),
                    tranche_id=str(row['TrancheID']),
                    entry_date=row['EntryDate'],
                    entry_nav=float(row['EntryNAV']),
                    units=float(row['Units']),
                    hwm=float(row.get('HWM', row['EntryNAV']))
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
        """Save tranches"""
        try:
            data = [{
                'InvestorID': t.investor_id, 'TrancheID': t.tranche_id,
                'EntryDate': t.entry_date, 'EntryNAV': t.entry_nav,
                'Units': t.units, 'HWM': t.hwm
            } for t in tranches]
            
            pd.DataFrame(data).to_csv(TRANCHES_FILE, index=False)
            return True
        except Exception as e:
            st.error(f"Lỗi save tranches: {str(e)}")
            return False
    
    @staticmethod
    def load_transactions() -> List[Transaction]:
        """Load transactions"""
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
        """Save transactions"""
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
    def save_all_data(investors, tranches, transactions) -> bool:
        """Save all data với backup"""
        try:
            DataHandler.create_backup()
            return (DataHandler.save_investors(investors) and 
                   DataHandler.save_tranches(tranches) and 
                   DataHandler.save_transactions(transactions))
        except Exception as e:
            st.error(f"Lỗi save data: {str(e)}")
            return False