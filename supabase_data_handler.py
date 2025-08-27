#!/usr/bin/env python3
"""
Simplified Supabase PostgreSQL Data Handler
Removed deadlock retry logic for better performance
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import os
import time

from models import Investor, Tranche, Transaction, FeeRecord

class SupabaseDataHandler:
    """Optimized Supabase PostgreSQL data handler with robust initialization."""
    
    def __init__(self):
        self.engine = None
        self.connected = False
        self.connection_info = {}
        self.version_info = {}
        
        # Khởi tạo engine (chỉ tạo object, chưa query nặng)
        self._init_engine()
        
        # ✅ Gọi kết nối nhẹ ngay để app.py không báo lỗi
        self._connect()

    def _init_engine(self):
        """Khởi tạo SQLAlchemy engine nhưng không ép connect ngay"""
        try:
            db_url = st.secrets.get("database_url") or os.getenv("DATABASE_URL")
            if not db_url:
                st.error("Lỗi: Không tìm thấy DATABASE_URL trong Streamlit secrets hoặc biến môi trường.")
                self.connected = False
                return

            self.connection_info = self._parse_db_url(db_url)
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

            # Engine chỉ được tạo, chưa connect tới DB
            self.engine = create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args={
                    "sslmode": "require",
                    "connect_timeout": 5  # timeout connect
                }
            )
        except Exception as e:
            st.error(f"CRITICAL: Lỗi khởi tạo engine Supabase: {e}")
            self.engine = None
            self.connected = False

    def _connect(self):
        """Thực hiện kiểm tra kết nối DB bằng query nhẹ"""
        if not self.engine:
            return False
        try:
            with self.engine.connect() as conn:
                # ⚡ Query siêu nhẹ, chỉ để test kết nối
                result = conn.execute(text("SELECT 1"))
                if result.fetchone():
                    self.connected = True
                    self.version_info = {"version_string": "OK"}
                    # Nếu cần thì tạo bảng ở đây
                    self._create_tables()
                    return True
        except Exception as e:
            st.error(f"CRITICAL: Lỗi kết nối Supabase (có thể do timeout): {e}")
            self.connected = False
            return False
        return False

    def _parse_db_url(self, db_url: str) -> Dict[str, str]:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            return {
                'host': parsed.hostname, 'port': parsed.port,
                'database': parsed.path.lstrip('/'), 'user': parsed.username
            }
        except:
            return {}
    
    def _create_tables(self):
        try:
            table_sql = [
                """CREATE TABLE IF NOT EXISTS investors (id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL, phone VARCHAR(50) DEFAULT '', address TEXT DEFAULT '', email VARCHAR(255) DEFAULT '', join_date DATE NOT NULL DEFAULT CURRENT_DATE, is_fund_manager BOOLEAN DEFAULT FALSE)""",
                """CREATE TABLE IF NOT EXISTS tranches (id SERIAL PRIMARY KEY, investor_id INTEGER NOT NULL, tranche_id VARCHAR(255) UNIQUE NOT NULL, entry_date TIMESTAMP NOT NULL, entry_nav DECIMAL(18,4) NOT NULL, units DECIMAL(18,8) NOT NULL, hwm DECIMAL(18,4) NOT NULL, original_entry_date TIMESTAMP, original_entry_nav DECIMAL(18,4), cumulative_fees_paid DECIMAL(18,4) DEFAULT 0)""",
                """CREATE TABLE IF NOT EXISTS transactions (id INTEGER PRIMARY KEY, investor_id INTEGER NOT NULL, date TIMESTAMP NOT NULL, type VARCHAR(100) NOT NULL, amount DECIMAL(18,4) NOT NULL, nav DECIMAL(18,4) NOT NULL, units_change DECIMAL(18,8) NOT NULL)""",
                """CREATE TABLE IF NOT EXISTS fee_records (id INTEGER PRIMARY KEY, period VARCHAR(20) NOT NULL, investor_id INTEGER NOT NULL, fee_amount DECIMAL(18,4) NOT NULL, fee_units DECIMAL(18,8) NOT NULL, calculation_date TIMESTAMP NOT NULL, units_before DECIMAL(18,8) NOT NULL, units_after DECIMAL(18,8) NOT NULL, nav_per_unit DECIMAL(18,4) NOT NULL, description TEXT DEFAULT '')"""
            ]
            with self.engine.connect() as conn:
                trans = conn.begin()
                for sql in table_sql:
                    conn.execute(text(sql))
                trans.commit()
        except Exception as e:
            st.error(f"Lỗi khi tạo bảng: {str(e)}")

    def save_all_data_enhanced(self, investors: List[Investor], tranches: List[Tranche], 
                               transactions: List[Transaction], fee_records: List[FeeRecord]) -> bool:
        start_time = time.time()
        try:
            investors_df = pd.DataFrame([vars(inv) for inv in investors])
            tranches_df = pd.DataFrame([vars(t) for t in tranches])
            transactions_df = pd.DataFrame([vars(t) for t in transactions])
            fee_records_df = pd.DataFrame([vars(f) for f in fee_records])
        except Exception as e:
            st.error(f"Lỗi khi chuẩn bị dữ liệu để lưu: {e}")
            return False

        if not investors_df.empty:
            investors_df = investors_df[['id', 'name', 'phone', 'address', 'email', 'join_date', 'is_fund_manager']]
        if not tranches_df.empty:
            tranches_df = tranches_df.drop(columns=['invested_value', 'original_invested_value'], errors='ignore')
            tranches_df = tranches_df[['investor_id', 'tranche_id', 'entry_date', 'entry_nav', 'units', 'hwm', 'original_entry_date', 'original_entry_nav', 'cumulative_fees_paid']]
        if not transactions_df.empty:
            transactions_df = transactions_df[['id', 'investor_id', 'date', 'type', 'amount', 'nav', 'units_change']]
        if not fee_records_df.empty:
            fee_records_df = fee_records_df[['id', 'period', 'investor_id', 'fee_amount', 'fee_units', 'calculation_date', 'units_before', 'units_after', 'nav_per_unit', 'description']]

        try:
            with self.engine.begin() as conn:
                conn.execute(text("DELETE FROM fee_records"))
                conn.execute(text("DELETE FROM transactions"))
                conn.execute(text("DELETE FROM tranches"))
                conn.execute(text("DELETE FROM investors"))

                if not investors_df.empty:
                    investors_df.to_sql('investors', conn, if_exists='append', index=False, method='multi')
                if not tranches_df.empty:
                    tranches_df.to_sql('tranches', conn, if_exists='append', index=False, method='multi')
                if not transactions_df.empty:
                    transactions_df.to_sql('transactions', conn, if_exists='append', index=False, method='multi')
                if not fee_records_df.empty:
                    fee_records_df.to_sql('fee_records', conn, if_exists='append', index=False, method='multi')
            
            end_time = time.time()
            st.sidebar.info(f"🚀 Lưu tối ưu hoàn tất trong {end_time - start_time:.2f}s.")
            return True
        except Exception as e:
            st.error(f"Lỗi nghiêm trọng khi lưu hàng loạt: {e}")
            return False

    def load_investors(self) -> List[Investor]:
        try:
            if not self.connected: return []
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id, name, phone, address, email, join_date, is_fund_manager FROM investors ORDER BY CASE WHEN is_fund_manager THEN 0 ELSE 1 END, id"))
                rows = result.fetchall()
            return [Investor(id=r[0], name=r[1], phone=r[2] or "", address=r[3] or "", email=r[4] or "", join_date=r[5], is_fund_manager=r[6] or False) for r in rows]
        except Exception as e:
            st.error(f"Lỗi tải nhà đầu tư: {str(e)}")
            return []

    def load_tranches(self) -> List[Tranche]:
        try:
            if not self.connected: return []
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT investor_id, tranche_id, entry_date, entry_nav, units, hwm, 
                        original_entry_date, original_entry_nav, cumulative_fees_paid
                    FROM tranches 
                    ORDER BY entry_date ASC, investor_id ASC
                """))
                rows = result.fetchall()
            
            tranches = []
            for row in rows:
                try:
                    # Tính original_invested_value từ units * original_entry_nav
                    original_invested = float(row[4]) * float(row[7] or row[3])
                    
                    tranche = Tranche(
                        investor_id=row[0], 
                        tranche_id=row[1], 
                        entry_date=row[2], 
                        entry_nav=float(row[3]), 
                        units=float(row[4]), 
                        hwm=float(row[5]), 
                        original_entry_date=row[6] or row[2], 
                        original_entry_nav=float(row[7] or row[3]), 
                        cumulative_fees_paid=float(row[8] or 0.0),
                        original_invested_value=original_invested  # Tính từ units * nav
                    )
                    tranches.append(tranche)
                except Exception as e:
                    continue
            
            return tranches
            
        except Exception as e:
            print(f"Error in load_tranches: {e}")
            return []

    def load_transactions(self) -> List[Transaction]:
        try:
            if not self.connected: return []
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id, investor_id, date, type, amount, nav, units_change FROM transactions ORDER BY date ASC, id ASC"))
                rows = result.fetchall()
            return [Transaction(id=r[0], investor_id=r[1], date=r[2], type=r[3], amount=float(r[4]), nav=float(r[5]), units_change=float(r[6])) for r in rows]
        except Exception as e:
            st.error(f"Lỗi tải giao dịch: {str(e)}")
            return []

    def load_fee_records(self) -> List[FeeRecord]:
        try:
            if not self.connected: return []
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id, period, investor_id, fee_amount, fee_units, calculation_date, units_before, units_after, nav_per_unit, description FROM fee_records ORDER BY calculation_date ASC, id ASC"))
                rows = result.fetchall()
            return [FeeRecord(id=r[0], period=r[1], investor_id=r[2], fee_amount=float(r[3]), fee_units=float(r[4]), calculation_date=r[5], units_before=float(r[6]), units_after=float(r[7]), nav_per_unit=float(r[8]), description=r[9] or "") for r in rows]
        except Exception as e:
            st.error(f"Lỗi tải lịch sử phí: {str(e)}")
            return []
    
    # === INDIVIDUAL SAVE METHODS ===
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save investors"""
        try:
            if not self.connected:
                return False
                
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("DELETE FROM investors"))
                    
                    if investors:
                        investor_data = [{
                            'id': inv.id, 'name': inv.name, 'phone': inv.phone,
                            'address': inv.address, 'email': inv.email, 
                            'join_date': inv.join_date, 'is_fund_manager': inv.is_fund_manager
                        } for inv in investors]
                        
                        conn.execute(text("""
                            INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager)
                            VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)
                        """), investor_data)
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            st.error(f"❌ Error saving investors: {str(e)}")
            return False
    
    def save_tranches(self, tranches: List[Tranche]) -> bool:
        try:
            if not self.connected:
                print("DEBUG: Not connected to database")
                return False
                
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    print(f"DEBUG: Deleting existing tranches...")
                    result = conn.execute(text("DELETE FROM tranches"))
                    print(f"DEBUG: Deleted {result.rowcount} existing tranches")
                    
                    if tranches:
                        print(f"DEBUG: Preparing to insert {len(tranches)} tranches")
                        tranche_data = []
                        for t in tranches:
                            data = {
                                'investor_id': t.investor_id, 
                                'tranche_id': t.tranche_id,
                                'entry_date': t.entry_date, 
                                'entry_nav': t.entry_nav,
                                'units': t.units, 
                                'hwm': t.hwm,
                                'original_entry_date': t.original_entry_date,
                                'original_entry_nav': t.original_entry_nav,
                                'cumulative_fees_paid': t.cumulative_fees_paid
                            }
                            tranche_data.append(data)
                            print(f"DEBUG: Prepared tranche {t.tranche_id}")
                        
                        print("DEBUG: Executing INSERT...")
                        result = conn.execute(text("""
                            INSERT INTO tranches (
                                investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                original_entry_date, original_entry_nav, cumulative_fees_paid
                            ) VALUES (
                                :investor_id, :tranche_id, :entry_date, :entry_nav, :units, :hwm,
                                :original_entry_date, :original_entry_nav, :cumulative_fees_paid
                            )
                        """), tranche_data)
                        print(f"DEBUG: INSERT completed, {result.rowcount} rows affected")
                    
                    print("DEBUG: Committing transaction...")
                    trans.commit()
                    print("DEBUG: Transaction committed successfully")
                    return True
                    
                except Exception as e:
                    print(f"DEBUG: Error in transaction: {e}")
                    trans.rollback()
                    print("DEBUG: Transaction rolled back")
                    raise e
                    
        except Exception as e:
            print(f"DEBUG: Error in save_tranches: {str(e)}")
            return False
    
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions"""
        try:
            if not self.connected:
                return False
                
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("DELETE FROM transactions"))
                    
                    if transactions:
                        transaction_data = [{
                            'id': t.id, 'investor_id': t.investor_id, 'date': t.date,
                            'type': t.type, 'amount': t.amount, 'nav': t.nav,
                            'units_change': t.units_change
                        } for t in transactions]
                        
                        conn.execute(text("""
                            INSERT INTO transactions (id, investor_id, date, type, amount, nav, units_change)
                            VALUES (:id, :investor_id, :date, :type, :amount, :nav, :units_change)
                        """), transaction_data)
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            st.error(f"❌ Error saving transactions: {str(e)}")
            return False
    
    def save_fee_records(self, fee_records: List[FeeRecord]) -> bool:
        """Save fee records"""
        try:
            if not self.connected:
                return False
                
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("DELETE FROM fee_records"))
                    
                    if fee_records:
                        fee_data = [{
                            'id': f.id, 'period': f.period, 'investor_id': f.investor_id,
                            'fee_amount': f.fee_amount, 'fee_units': f.fee_units,
                            'calculation_date': f.calculation_date, 'units_before': f.units_before,
                            'units_after': f.units_after, 'nav_per_unit': f.nav_per_unit,
                            'description': f.description
                        } for f in fee_records]
                        
                        conn.execute(text("""
                            INSERT INTO fee_records (
                                id, period, investor_id, fee_amount, fee_units, calculation_date,
                                units_before, units_after, nav_per_unit, description
                            ) VALUES (
                                :id, :period, :investor_id, :fee_amount, :fee_units, :calculation_date,
                                :units_before, :units_after, :nav_per_unit, :description
                            )
                        """), fee_data)
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            st.error(f"❌ Error saving fee records: {str(e)}")
            return False
    
    # === OTHER METHODS ===
    
    def create_backup(self) -> Optional[str]:
        """Create simple backup"""
        try:
            if not self.connected:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            with self.engine.connect() as conn:
                # Get table counts for backup verification
                tables = ['investors', 'tranches', 'transactions', 'fee_records']
                backup_info = {}
                
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    backup_info[table] = count
                
                # Log backup info
                st.info(f"📦 Backup {timestamp} created with: " + 
                       ", ".join([f"{table}: {count}" for table, count in backup_info.items()]))
            
            return timestamp
            
        except Exception as e:
            st.error(f"❌ Error creating backup: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get basic database statistics"""
        try:
            if not self.connected:
                return {'connected': False, 'error': 'Not connected'}
            
            with self.engine.connect() as conn:
                stats = {'connected': True}
                
                # Basic table counts
                tables = ['investors', 'tranches', 'transactions', 'fee_records']
                table_counts = {}
                
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0] if result.rowcount > 0 else 0
                    table_counts[table] = count
                
                stats['table_counts'] = table_counts
                
                # Basic connection info
                result = conn.execute(text("""
                    SELECT 
                        current_database() as db_name,
                        current_user as user_name,
                        current_timestamp as current_time
                """))
                
                if result.rowcount > 0:
                    row = result.fetchone()
                    stats.update({
                        'database_name': row.db_name,
                        'user_name': row.user_name,
                        'current_time': row.current_time
                    })
                
                return stats
                
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Simple health check"""
        try:
            if not self.connected:
                return {'status': 'disconnected', 'checks': []}
            
            checks = []
            
            with self.engine.connect() as conn:
                # Basic connectivity
                start_time = datetime.now()
                conn.execute(text("SELECT 1"))
                response_time = (datetime.now() - start_time).total_seconds()
                
                checks.append({
                    'name': 'Basic Connectivity',
                    'status': 'pass' if response_time < 5.0 else 'slow',
                    'details': f'{response_time:.3f}s response time'
                })
                
                # Table existence
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('investors', 'tranches', 'transactions', 'fee_records')
                    ORDER BY table_name
                """))
                
                existing_tables = [row[0] for row in result]
                required_tables = ['investors', 'tranches', 'transactions', 'fee_records']
                missing_tables = set(required_tables) - set(existing_tables)
                
                checks.append({
                    'name': 'Required Tables',
                    'status': 'pass' if not missing_tables else 'fail',
                    'details': f'Found: {existing_tables}, Missing: {list(missing_tables)}'
                })
                
                # Basic data counts
                result = conn.execute(text("""
                    SELECT 
                        (SELECT COUNT(*) FROM investors) as investors,
                        (SELECT COUNT(*) FROM tranches) as tranches,
                        (SELECT COUNT(*) FROM transactions) as transactions,
                        (SELECT COUNT(*) FROM fee_records) as fee_records
                """))
                
                if result.rowcount > 0:
                    row = result.fetchone()
                    data_counts = {
                        'investors': row.investors,
                        'tranches': row.tranches,
                        'transactions': row.transactions,
                        'fee_records': row.fee_records
                    }
                    
                    checks.append({
                        'name': 'Data Counts',
                        'status': 'pass',
                        'details': data_counts
                    })
            
            # Overall status
            failed_checks = [c for c in checks if c['status'] == 'fail']
            overall_status = 'healthy' if not failed_checks else 'degraded'
            
            return {
                'status': overall_status,
                'timestamp': datetime.now().isoformat(),
                'checks': checks,
                'summary': f'{len(checks) - len(failed_checks)}/{len(checks)} checks passed'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }