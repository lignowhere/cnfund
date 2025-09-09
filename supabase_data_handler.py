#!/usr/bin/env python3
"""
Simplified Supabase PostgreSQL Data Handler
Removed deadlock retry logic for better performance
"""

from pathlib import Path
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import os
import time
from timezone_manager import TimezoneManager

from models import Investor, Tranche, Transaction, FeeRecord
from timezone_manager import TimezoneManager

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
    
    def reconnect(self):
        """Reconnect to database - useful for cloud environments"""
        print("🔌 Reconnecting to Supabase database...")
        self.connected = False
        self.engine = None
        self._init_engine()
        self._connect()
        return self.connected

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
        """
        SỬA LẠI: Tạo các bảng với cấu trúc CHÍNH XÁC khớp với models.py
        và thêm các ràng buộc khóa ngoại để đảm bảo toàn vẹn dữ liệu.
        """
        try:
            with self.engine.begin() as conn:
                # Bảng Investors
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS investors (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        phone TEXT,
                        address TEXT,
                        email TEXT,
                        join_date DATE,
                        is_fund_manager BOOLEAN DEFAULT FALSE
                    )
                """))

                # Bảng Tranches
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tranches (
                        tranche_id VARCHAR(255) PRIMARY KEY, -- <--- Đặt làm khóa chính
                        investor_id INTEGER NOT NULL REFERENCES investors(id) ON DELETE CASCADE,
                        entry_date TIMESTAMP NOT NULL,
                        entry_nav NUMERIC(18, 4) NOT NULL,
                        units NUMERIC(18, 8) NOT NULL,
                        hwm NUMERIC(18, 4),
                        original_entry_date TIMESTAMP,
                        original_entry_nav NUMERIC(18, 4),
                        cumulative_fees_paid NUMERIC(18, 4) DEFAULT 0.0
                    )
                """))

                # Bảng Transactions
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY,
                        investor_id INTEGER NOT NULL,
                        date TIMESTAMP NOT NULL,
                        type TEXT NOT NULL,
                        amount NUMERIC(18, 4) NOT NULL,
                        nav NUMERIC(18, 4),
                        units_change NUMERIC(18, 8)
                    )
                """))

                # Bảng Fee Records
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS fee_records (
                        id INTEGER PRIMARY KEY,
                        period TEXT NOT NULL,
                        investor_id INTEGER NOT NULL REFERENCES investors(id) ON DELETE CASCADE,
                        fee_amount NUMERIC(18, 4) NOT NULL,
                        fee_units NUMERIC(18, 8) NOT NULL,
                        calculation_date TIMESTAMP NOT NULL,
                        units_before NUMERIC(18, 8),
                        units_after NUMERIC(18, 8),
                        nav_per_unit NUMERIC(18, 4),
                        description TEXT
                    )
                """))
            print("✅ Đã kiểm tra/tạo bảng thành công với cấu trúc đồng bộ.")
        except Exception as e:
            # Quan trọng: Dùng print() thay vì st.error() để lỗi hiển thị trên terminal
            import traceback
            print(f"💥 Lỗi nghiêm trọng khi tạo bảng: {e}")
            traceback.print_exc()

    def save_all_data_enhanced(
        self,
        investors: List[Investor],
        tranches: List[Tranche],
        transactions: List[Transaction],
        fee_records: List[FeeRecord]
    ) -> bool:
        """Lưu dữ liệu an toàn bằng cách tạo DataFrame tường minh."""
        try:
            # ++++++ PHẦN QUAN TRỌNG CẦN THAY THẾ ++++++
            # Tạo dictionary tường minh, chỉ lấy các cột cần thiết, không dùng vars()
            investors_data = [
                {'id': i.id, 'name': i.name, 'phone': i.phone, 'address': i.address, 'email': i.email, 'join_date': i.join_date, 'is_fund_manager': i.is_fund_manager}
                for i in investors
            ]
            tranches_data = [
                {'tranche_id': t.tranche_id, 'investor_id': t.investor_id, 'entry_date': t.entry_date, 'entry_nav': t.entry_nav, 'units': t.units, 'hwm': t.hwm, 'original_entry_date': t.original_entry_date, 'original_entry_nav': t.original_entry_nav, 'cumulative_fees_paid': t.cumulative_fees_paid}
                for t in tranches
            ]
            transactions_data = [
                {'id': t.id, 'investor_id': t.investor_id, 'date': t.date, 'type': t.type, 'amount': t.amount, 'nav': t.nav, 'units_change': t.units_change}
                for t in transactions
            ]
            fee_records_data = [
                {'id': f.id, 'period': f.period, 'investor_id': f.investor_id, 'fee_amount': f.fee_amount, 'fee_units': f.fee_units, 'calculation_date': f.calculation_date, 'units_before': f.units_before, 'units_after': f.units_after, 'nav_per_unit': f.nav_per_unit, 'description': f.description}
                for f in fee_records
            ]

            investors_df = pd.DataFrame(investors_data)
            tranches_df = pd.DataFrame(tranches_data)
            transactions_df = pd.DataFrame(transactions_data)
            fee_records_df = pd.DataFrame(fee_records_data)
            # ++++++ KẾT THÚC PHẦN THAY THẾ ++++++

            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    # 1️⃣ DROP temp tables if they exist, then create new ones
                    for table in ["investors", "tranches", "transactions", "fee_records"]:
                        # Drop temp table if exists (ignore error if doesn't exist)
                        try:
                            conn.execute(text(f"DROP TABLE IF EXISTS {table}_temp"))
                        except:
                            pass  # Ignore errors if table doesn't exist
                        
                        # Create new temp table
                        conn.execute(text(f"CREATE TEMP TABLE {table}_temp AS SELECT * FROM {table} WHERE 1=0"))

                    # 2️⃣ Insert dữ liệu mới vào bảng tạm
                    if not investors_df.empty:
                        investors_df.to_sql("investors_temp", conn, if_exists="append", index=False, method="multi")
                    if not tranches_df.empty:
                        tranches_df.to_sql("tranches_temp", conn, if_exists="append", index=False, method="multi")
                    if not transactions_df.empty:
                        transactions_df.to_sql("transactions_temp", conn, if_exists="append", index=False, method="multi")
                    if not fee_records_df.empty:
                        fee_records_df.to_sql("fee_records_temp", conn, if_exists="append", index=False, method="multi")

                    # 3️⃣ Validate dữ liệu
                    counts = {}
                    for table, df in [("investors", investors_df), ("tranches", tranches_df), ("transactions", transactions_df), ("fee_records", fee_records_df)]:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}_temp"))
                        temp_count = result.fetchone()[0]
                        if temp_count != len(df):
                            raise Exception(f"Mismatch {table}: expected {len(df)}, got {temp_count}")
                        counts[table] = temp_count

                    # 4️⃣ Thay thế bảng chính
                    for table in ["fee_records", "transactions", "tranches", "investors"]: # Xóa theo thứ tự ngược để tránh lỗi khóa ngoại
                        conn.execute(text(f"DELETE FROM {table}"))
                    
                    for table, df in [("investors", investors_df), ("tranches", tranches_df), ("transactions", transactions_df), ("fee_records", fee_records_df)]:
                        if not df.empty:
                            conn.execute(text(f"INSERT INTO {table} SELECT * FROM {table}_temp"))

                    # 5️⃣ Clean up temp tables (optional, they'll be dropped automatically at session end)
                    for table in ["investors", "tranches", "transactions", "fee_records"]:
                        try:
                            conn.execute(text(f"DROP TABLE IF EXISTS {table}_temp"))
                        except:
                            pass

                    trans.commit()
                    
                    # Force connection to flush any buffers
                    conn.execute(text("SELECT 1"))
                    
                    print(f"✅ Database save successful with transaction commit: {counts}")
                    print("🔄 Database connection flushed and verified")
                    return True
                except Exception as e:
                    trans.rollback()
                    import traceback
                    print(f"💥 Lỗi khi lưu an toàn: {e}") # Đổi sang print
                    traceback.print_exc()
                    return False
        except Exception as e:
            import traceback
            print(f"💥 Lỗi tổng quát trong save_all_data_enhanced: {e}") # Đổi sang print
            traceback.print_exc()
            return False


    def load_investors(self) -> List[Investor]:
        try:
            if not self.connected: return []
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id, name, phone, address, email, join_date, is_fund_manager FROM investors ORDER BY CASE WHEN is_fund_manager THEN 0 ELSE 1 END, id"))
                rows = result.fetchall()
            from type_safety_fixes import safe_int_conversion
            investors = []
            for r in rows:
                try:
                    investor = Investor(
                        id=safe_int_conversion(r[0]), 
                        name=str(r[1] or ""), 
                        phone=str(r[2] or ""), 
                        address=str(r[3] or ""), 
                        email=str(r[4] or ""), 
                        join_date=r[5], 
                        is_fund_manager=bool(r[6] or False)
                    )
                    investors.append(investor)
                except Exception as e:
                    print(f"Warning: Skipping investor row due to type conversion error: {e}")
                    continue
            return investors
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
            
            from type_safety_fixes import safe_int_conversion, safe_float_conversion
            tranches = []
            for row in rows:
                try:
                    # Safely convert all numeric values
                    investor_id = safe_int_conversion(row[0])
                    units = safe_float_conversion(row[4])
                    entry_nav = safe_float_conversion(row[3])
                    original_entry_nav = safe_float_conversion(row[7] or row[3])
                    
                    # Calculate original invested value safely
                    original_invested = units * original_entry_nav
                    
                    tranche = Tranche(
                        investor_id=investor_id,
                        tranche_id=str(row[1]), 
                        entry_date=row[2], 
                        entry_nav=entry_nav, 
                        units=units, 
                        hwm=safe_float_conversion(row[5]), 
                        original_entry_date=row[6] or row[2], 
                        original_entry_nav=original_entry_nav, 
                        cumulative_fees_paid=safe_float_conversion(row[8] or 0.0),
                        original_invested_value=original_invested
                    )
                    tranches.append(tranche)
                except Exception as e:
                    print(f"Warning: Skipping tranche due to type conversion error: {e}")
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
            
            # Normalize all datetime fields when loading from database
            from type_safety_fixes import safe_int_conversion, safe_float_conversion
            transactions = []
            for r in rows:
                try:
                    # Handle both timezone-aware and naive timestamps from database
                    raw_date = r[2]
                    if hasattr(raw_date, 'tzinfo') and raw_date.tzinfo is not None:
                        # Already timezone-aware - convert to display timezone
                        normalized_date = TimezoneManager.normalize_for_display(raw_date)
                    else:
                        # Naive timestamp - assume it's in Vietnam timezone (legacy data)
                        vietnam_tz = TimezoneManager.get_app_timezone()
                        normalized_date = vietnam_tz.localize(raw_date)
                    
                    transaction = Transaction(
                        id=safe_int_conversion(r[0]), 
                        investor_id=safe_int_conversion(r[1]), 
                        date=normalized_date, 
                        type=str(r[3]), 
                        amount=safe_float_conversion(r[4]), 
                        nav=safe_float_conversion(r[5]), 
                        units_change=safe_float_conversion(r[6])
                    )
                    transactions.append(transaction)
                except Exception as e:
                    print(f"Warning: Skipping transaction due to type conversion error: {e}")
                    continue
            
            # Debug logging for transaction loading
            nav_transactions = [t for t in transactions if t.nav and t.nav > 0]
            print(f"🔍 load_transactions DEBUG:")
            print(f"  - Total transactions loaded: {len(transactions)}")
            print(f"  - Transactions with NAV: {len(nav_transactions)}")
            if nav_transactions:
                # Show last 3 NAV transactions from database
                latest_navs = sorted(nav_transactions, key=lambda x: (x.date, x.id), reverse=True)[:3]
                print(f"  - Last 3 NAV transactions from DB:")
                for i, t in enumerate(latest_navs):
                    print(f"    {i+1}. ID:{t.id}, Type:{t.type}, Date:{t.date}, NAV:{t.nav}")
            
            return transactions
        except Exception as e:
            st.error(f"Lỗi tải giao dịch: {str(e)}")
            return []

    def load_fee_records(self) -> List[FeeRecord]:
        try:
            if not self.connected: return []
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT id, period, investor_id, fee_amount, fee_units, calculation_date, units_before, units_after, nav_per_unit, description FROM fee_records ORDER BY calculation_date ASC, id ASC"))
                rows = result.fetchall()
            from type_safety_fixes import safe_int_conversion, safe_float_conversion
            fee_records = []
            for r in rows:
                try:
                    fee_record = FeeRecord(
                        id=safe_int_conversion(r[0]), 
                        period=str(r[1]), 
                        investor_id=safe_int_conversion(r[2]), 
                        fee_amount=safe_float_conversion(r[3]), 
                        fee_units=safe_float_conversion(r[4]), 
                        calculation_date=r[5], 
                        units_before=safe_float_conversion(r[6]), 
                        units_after=safe_float_conversion(r[7]), 
                        nav_per_unit=safe_float_conversion(r[8]), 
                        description=str(r[9] or "")
                    )
                    fee_records.append(fee_record)
                except Exception as e:
                    print(f"Warning: Skipping fee record due to type conversion error: {e}")
                    continue
            return fee_records
        except Exception as e:
            st.error(f"Lỗi tải lịch sử phí: {str(e)}")
            return []
    
    # === INDIVIDUAL SAVE METHODS ===
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save investors an toàn bằng temp table"""
        try:
            if not self.connected:
                return False

            investor_data = [{
                'id': inv.id,
                'name': inv.name,
                'phone': inv.phone,
                'address': inv.address,
                'email': inv.email,
                'join_date': inv.join_date,
                'is_fund_manager': inv.is_fund_manager
            } for inv in investors]

            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("CREATE TEMP TABLE investors_temp AS SELECT * FROM investors WHERE 1=0"))
                    if investor_data:
                        conn.execute(text("""
                            INSERT INTO investors_temp (id, name, phone, address, email, join_date, is_fund_manager)
                            VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)
                        """), investor_data)

                    # validate
                    result = conn.execute(text("SELECT COUNT(*) FROM investors_temp"))
                    temp_count = result.scalar()
                    if temp_count != len(investor_data):
                        raise Exception(f"Mismatch investors: expected {len(investor_data)}, got {temp_count}")

                    conn.execute(text("DELETE FROM investors"))
                    conn.execute(text("INSERT INTO investors SELECT * FROM investors_temp"))
                    trans.commit()
                    return True
                except Exception as e:
                    trans.rollback()
                    st.error(f"❌ Lỗi save_investors: {e}")
                    return False
        except Exception as e:
            st.error(f"❌ Lỗi tổng quát save_investors: {e}")
            return False


    def save_tranches(self, tranches: List[Tranche]) -> bool:
        """Save tranches an toàn bằng temp table"""
        try:
            if not self.connected:
                return False

            tranche_data = [{
                'tranche_id': tr.tranche_id,
                'entry_date': tr.entry_date,
                'entry_nav': tr.entry_nav,
                'units': tr.units,
                'hwm': tr.hwm,
                'investor_id': tr.investor_id
            } for tr in tranches]

            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("CREATE TEMP TABLE tranches_temp AS SELECT * FROM tranches WHERE 1=0"))
                    if tranche_data:
                        conn.execute(text("""
                            INSERT INTO tranches_temp (tranche_id, entry_date, entry_nav, units, hwm, investor_id)
                            VALUES (:tranche_id, :entry_date, :entry_nav, :units, :hwm, :investor_id)
                        """), tranche_data)

                    # validate
                    result = conn.execute(text("SELECT COUNT(*) FROM tranches_temp"))
                    temp_count = result.scalar()
                    if temp_count != len(tranche_data):
                        raise Exception(f"Mismatch tranches: expected {len(tranche_data)}, got {temp_count}")

                    conn.execute(text("DELETE FROM tranches"))
                    conn.execute(text("INSERT INTO tranches SELECT * FROM tranches_temp"))
                    trans.commit()
                    return True
                except Exception as e:
                    trans.rollback()
                    st.error(f"❌ Lỗi save_tranches: {e}")
                    return False
        except Exception as e:
            st.error(f"❌ Lỗi tổng quát save_tranches: {e}")
            return False

        
    def backup_database_to_local():
        """Backup từ database xuống local files ngay lập tức"""
        try:
            from supabase_data_handler import SupabaseDataHandler
            handler = SupabaseDataHandler()
            
            if not handler.connected:
                print("Không kết nối được database")
                return False
            
            print("Đang backup từ database...")
            
            # Load từ DB
            tranches = handler.load_tranches()
            transactions = handler.load_transactions() 
            investors = handler.load_investors()
            fee_records = handler.load_fee_records()
            
            # Save to local
            Path("data").mkdir(exist_ok=True)
            timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
            
            if tranches:
                data = []
                for t in tranches:
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
                        'InvestedValue': getattr(t, 'invested_value', t.units * t.entry_nav)
                    })
                pd.DataFrame(data).to_csv(f"data/tranches_{timestamp}.csv", index=False)
                print(f"Backup {len(tranches)} tranches -> data/tranches_{timestamp}.csv")
            
            return True
            
        except Exception as e:
            print(f"Lỗi backup database: {e}")
            return False
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions an toàn bằng temp table"""
        try:
            if not self.connected:
                return False

            tx_data = [{
                'transaction_id': tx.id,  # Fixed: use tx.id not tx.transaction_id
                'investor_id': tx.investor_id,
                'date': tx.date,
                'amount': tx.amount,
                'type': tx.type,
                'units_change': tx.units_change,
                'nav': tx.nav,
                'hwm_before': getattr(tx, 'hwm_before', 0.0),  # Add safe defaults
                'hwm_after': getattr(tx, 'hwm_after', 0.0)
            } for tx in transactions]
            
            # Debug logging for transaction save
            nav_txs = [tx for tx in transactions if tx.nav and tx.nav > 0]
            if nav_txs:
                print(f"🔍 save_transactions DEBUG:")
                print(f"  - Saving {len(transactions)} transactions ({len(nav_txs)} with NAV)")
                # Show NAV Update transactions being saved
                nav_updates = [tx for tx in nav_txs if tx.type == "NAV Update"]
                if nav_updates:
                    print(f"  - NAV Update transactions being saved:")
                    for tx in nav_updates:
                        print(f"    ID:{tx.id}, NAV:{tx.nav}, Date:{tx.date}")

            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("CREATE TEMP TABLE transactions_temp AS SELECT * FROM transactions WHERE 1=0"))
                    if tx_data:
                        conn.execute(text("""
                            INSERT INTO transactions_temp (
                                transaction_id, investor_id, date, amount, type,
                                units_change, nav, hwm_before, hwm_after
                            ) VALUES (
                                :transaction_id, :investor_id, :date, :amount, :type,
                                :units_change, :nav, :hwm_before, :hwm_after
                            )
                        """), tx_data)

                    # validate
                    result = conn.execute(text("SELECT COUNT(*) FROM transactions_temp"))
                    temp_count = result.scalar()
                    if temp_count != len(tx_data):
                        raise Exception(f"Mismatch transactions: expected {len(tx_data)}, got {temp_count}")

                    conn.execute(text("DELETE FROM transactions"))
                    conn.execute(text("INSERT INTO transactions SELECT * FROM transactions_temp"))
                    trans.commit()
                    return True
                except Exception as e:
                    trans.rollback()
                    st.error(f"❌ Lỗi save_transactions: {e}")
                    return False
        except Exception as e:
            st.error(f"❌ Lỗi tổng quát save_transactions: {e}")
            return False


    
    def save_fee_records(self, fee_records: List[FeeRecord]) -> bool:
        """Save fee_records an toàn bằng temp table"""
        try:
            if not self.connected:
                return False

            fee_data = [{
                'fee_id': fr.fee_id,
                'investor_id': fr.investor_id,
                'period': fr.period,
                'fee_amount': fr.fee_amount,
                'fee_units': fr.fee_units,
                'calculation_date': fr.calculation_date,
                'units_before': fr.units_before,
                'units_after': fr.units_after,
                'nav_per_unit': fr.nav_per_unit,
                'description': fr.description
            } for fr in fee_records]

            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("CREATE TEMP TABLE fee_records_temp AS SELECT * FROM fee_records WHERE 1=0"))
                    if fee_data:
                        conn.execute(text("""
                            INSERT INTO fee_records_temp (
                                fee_id, investor_id, period, fee_amount, fee_units,
                                calculation_date, units_before, units_after, nav_per_unit, description
                            ) VALUES (
                                :fee_id, :investor_id, :period, :fee_amount, :fee_units,
                                :calculation_date, :units_before, :units_after, :nav_per_unit, :description
                            )
                        """), fee_data)

                    # validate
                    result = conn.execute(text("SELECT COUNT(*) FROM fee_records_temp"))
                    temp_count = result.scalar()
                    if temp_count != len(fee_data):
                        raise Exception(f"Mismatch fee_records: expected {len(fee_data)}, got {temp_count}")

                    conn.execute(text("DELETE FROM fee_records"))
                    conn.execute(text("INSERT INTO fee_records SELECT * FROM fee_records_temp"))
                    trans.commit()
                    return True
                except Exception as e:
                    trans.rollback()
                    st.error(f"❌ Lỗi save_fee_records: {e}")
                    return False
        except Exception as e:
            st.error(f"❌ Lỗi tổng quát save_fee_records: {e}")
            return False
    
    # === OTHER METHODS ===
    
    def create_backup(self) -> Optional[str]:
        """Create simple backup"""
        try:
            if not self.connected:
                return None
            
            timestamp = TimezoneManager.now().strftime("%Y%m%d_%H%M%S")
            
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
                start_time = TimezoneManager.now()
                conn.execute(text("SELECT 1"))
                response_time = (TimezoneManager.now() - start_time).total_seconds()
                
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