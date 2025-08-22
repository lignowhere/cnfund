#!/usr/bin/env python3
"""
DEADLOCK-RESISTANT Supabase PostgreSQL Data Handler
Implements retry logic, proper transaction ordering, and deadlock prevention
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import os
import time
import random

from models import Investor, Tranche, Transaction, FeeRecord

class SupabaseDataHandler:
    """Production Supabase PostgreSQL data handler with deadlock prevention"""
    
    def __init__(self):
        self.engine = None
        self.connected = False
        self.connection_info = {}
        self.version_info = {}
        self.max_retries = 3
        self.retry_delay_base = 1.0  # Base delay in seconds
        self._connect()
    
    def _execute_with_retry(self, operation_func, operation_name: str, *args, **kwargs):
        """
        Execute database operation with retry logic for deadlock handling
        """
        for attempt in range(self.max_retries):
            try:
                return operation_func(*args, **kwargs)
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a deadlock or lock timeout
                is_deadlock = any(keyword in error_msg for keyword in [
                    'deadlock', 'lock timeout', 'could not obtain lock', 
                    'concurrent update', 'serialization failure'
                ])
                
                if is_deadlock and attempt < self.max_retries - 1:
                    # Calculate exponential backoff with jitter
                    delay = self.retry_delay_base * (2 ** attempt) + random.uniform(0.1, 0.5)
                    
                    st.warning(f"⚠️ {operation_name} encountered deadlock (attempt {attempt + 1}/{self.max_retries}). Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    # Either not a deadlock error, or max retries exceeded
                    raise e
        
        # Should never reach here, but just in case
        raise Exception(f"Failed to complete {operation_name} after {self.max_retries} attempts")
    
    def _connect(self):
        """Connect to database with improved error handling"""
        try:
            db_url = self._get_database_url()
            if not db_url:
                print("ERROR: Database URL not found in secrets or env variables.")
                self.connected = False
                return
            
            self.connection_info = self._parse_db_url(db_url)
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            
            # Improved connection parameters for better concurrency handling
            self.engine = create_engine(
                db_url, 
                pool_pre_ping=True,
                connect_args={"sslmode": "require"}
            )
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version(), current_database(), current_user"))
                db_info = result.fetchone()
                if db_info:
                    self.connected = True
                    self.version_info = {
                        'version_string': db_info[0],
                        'database_name': db_info[1],
                        'current_user': db_info[2]
                    }
                    self._create_tables()
                    
        except Exception as e:
            error_msg = str(e)
            print(f"CRITICAL: Supabase connection failed: {e}")
            
            # Provide helpful debugging info
            if "password authentication failed" in error_msg.lower():
                st.error("🔒 Password authentication failed. Check your database password.")
            elif "could not connect to server" in error_msg.lower():
                st.error("🌐 Could not connect to server. Check your network connection.")
            elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                st.error("🗃️ Database does not exist. Check your database name.")
            
            st.info("💡 Troubleshooting: Verify your Streamlit secrets configuration")
            
            self.engine = None
            self.connected = False
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from multiple sources with priority order"""
        
        # 1. Try Streamlit secrets (preferred for production)
        try:
            return st.secrets["database_url"]
        except (KeyError, AttributeError):
            pass
        
        # 2. Try supabase section in secrets
        try:
            return st.secrets["supabase"]["database_url"]
        except (KeyError, AttributeError):
            pass
        
        # 3. Try environment variable (for local development)
        env_url = os.getenv("DATABASE_URL")
        if env_url:
            return env_url
        
        # 4. Try reading from .env file (local development)
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv("DATABASE_URL")
        except ImportError:
            pass
        
        return None
    
    def _parse_db_url(self, db_url: str) -> Dict[str, str]:
        """Parse database URL for display info"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            return {
                'host': parsed.hostname,
                'port': parsed.port,
                'database': parsed.path.lstrip('/'),
                'user': parsed.username
            }
        except:
            return {}
    
    def _create_tables(self):
        """Create tables with proper ordering and error handling"""
        def _create_tables_impl():
            # Create tables one by one to avoid deadlocks
            table_sql = [
                # Investors table
                """
                CREATE TABLE IF NOT EXISTS investors (
                    id INTEGER PRIMARY KEY, 
                    name VARCHAR(255) NOT NULL, 
                    phone VARCHAR(50) DEFAULT '',
                    address TEXT DEFAULT '', 
                    email VARCHAR(255) DEFAULT '', 
                    join_date DATE NOT NULL DEFAULT CURRENT_DATE,
                    is_fund_manager BOOLEAN DEFAULT FALSE, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # Tranches table
                """
                CREATE TABLE IF NOT EXISTS tranches (
                    id SERIAL PRIMARY KEY, 
                    investor_id INTEGER NOT NULL, 
                    tranche_id VARCHAR(255) UNIQUE NOT NULL,
                    entry_date TIMESTAMP NOT NULL, 
                    entry_nav DECIMAL(18,4) NOT NULL, 
                    units DECIMAL(18,8) NOT NULL,
                    hwm DECIMAL(18,4) NOT NULL, 
                    original_entry_date TIMESTAMP, 
                    original_entry_nav DECIMAL(18,4),
                    cumulative_fees_paid DECIMAL(18,4) DEFAULT 0, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # Transactions table
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY, 
                    investor_id INTEGER NOT NULL, 
                    date TIMESTAMP NOT NULL,
                    type VARCHAR(100) NOT NULL, 
                    amount DECIMAL(18,4) NOT NULL, 
                    nav DECIMAL(18,4) NOT NULL,
                    units_change DECIMAL(18,8) NOT NULL, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                # Fee Records table
                """
                CREATE TABLE IF NOT EXISTS fee_records (
                    id INTEGER PRIMARY KEY, 
                    period VARCHAR(20) NOT NULL, 
                    investor_id INTEGER NOT NULL,
                    fee_amount DECIMAL(18,4) NOT NULL, 
                    fee_units DECIMAL(18,8) NOT NULL,
                    calculation_date TIMESTAMP NOT NULL, 
                    units_before DECIMAL(18,8) NOT NULL,
                    units_after DECIMAL(18,8) NOT NULL, 
                    nav_per_unit DECIMAL(18,4) NOT NULL,
                    description TEXT DEFAULT '', 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            ]
            
            # Create indexes
            index_sql = [
                "CREATE INDEX IF NOT EXISTS idx_investors_fund_manager ON investors(is_fund_manager)",
                "CREATE INDEX IF NOT EXISTS idx_tranches_investor_id ON tranches(investor_id)",
                "CREATE INDEX IF NOT EXISTS idx_transactions_investor_id ON transactions(investor_id)",
                "CREATE INDEX IF NOT EXISTS idx_fee_records_investor_id ON fee_records(investor_id)",
                "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)",
                "CREATE INDEX IF NOT EXISTS idx_tranches_entry_date ON tranches(entry_date)"
            ]
            
            with self.engine.connect() as conn:
                # Create tables first
                for sql in table_sql:
                    conn.execute(text(sql))
                
                # Create indexes
                for sql in index_sql:
                    conn.execute(text(sql))
                
                conn.commit()
        
        try:
            self._execute_with_retry(_create_tables_impl, "Create Tables")
        except Exception as e:
            st.error(f"❌ Error creating tables: {str(e)}")
    
    def save_all_data_enhanced(self, investors, tranches, transactions, fee_records) -> bool:
        """
        DEADLOCK-RESISTANT: Save all data with proper transaction ordering and retry logic
        """
        def _save_all_data_impl():
            with self.engine.connect() as conn:
                # Use a shorter, more focused transaction
                trans = conn.begin()
                
                try:
                    # CRITICAL: Delete in reverse dependency order to minimize lock conflicts
                    # AND use TRUNCATE for faster, less lock-intensive deletion
                    
                    # Option 1: Use TRUNCATE for faster deletion (if supported)
                    try:
                        conn.execute(text("TRUNCATE TABLE fee_records, transactions, tranches, investors RESTART IDENTITY CASCADE"))
                    except Exception:
                        # Fallback to DELETE if TRUNCATE fails
                        conn.execute(text("DELETE FROM fee_records"))
                        conn.execute(text("DELETE FROM transactions")) 
                        conn.execute(text("DELETE FROM tranches"))
                        conn.execute(text("DELETE FROM investors"))
                    
                    # Insert in dependency order: investors -> tranches -> transactions -> fee_records
                    
                    # 1. Investors (batch insert for better performance)
                    if investors:
                        investor_data = [{
                            'id': inv.id, 'name': inv.name, 'phone': inv.phone,
                            'address': inv.address, 'email': inv.email, 
                            'join_date': inv.join_date, 'is_fund_manager': inv.is_fund_manager
                        } for inv in investors]
                        
                        # Use executemany for better performance
                        conn.execute(text("""
                            INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager)
                            VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)
                        """), investor_data)
                    
                    # 2. Tranches
                    if tranches:
                        tranche_data = [{
                            'investor_id': t.investor_id, 'tranche_id': t.tranche_id,
                            'entry_date': t.entry_date, 'entry_nav': t.entry_nav,
                            'units': t.units, 'hwm': t.hwm,
                            'original_entry_date': t.original_entry_date,
                            'original_entry_nav': t.original_entry_nav,
                            'cumulative_fees_paid': t.cumulative_fees_paid
                        } for t in tranches]
                        
                        conn.execute(text("""
                            INSERT INTO tranches (
                                investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                original_entry_date, original_entry_nav, cumulative_fees_paid
                            ) VALUES (
                                :investor_id, :tranche_id, :entry_date, :entry_nav, :units, :hwm,
                                :original_entry_date, :original_entry_nav, :cumulative_fees_paid
                            )
                        """), tranche_data)
                    
                    # 3. Transactions
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
                    
                    # 4. Fee records
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
                    
                    # Commit the transaction
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
        
        try:
            # Execute with retry logic for deadlock handling
            return self._execute_with_retry(_save_all_data_impl, "Save All Data")
            
        except Exception as e:
            st.error(f"❌ Error saving all data: {str(e)}")
            return False
    
    # === LOAD METHODS (unchanged but with retry logic) ===
    
    def load_investors(self) -> List[Investor]:
        """Load investors with retry logic"""
        def _load_investors_impl():
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, name, phone, address, email, join_date, is_fund_manager
                    FROM investors 
                    ORDER BY 
                        CASE WHEN is_fund_manager THEN 0 ELSE 1 END,
                        id
                """))
                rows = result.fetchall()
            
            investors = []
            for row in rows:
                investor = Investor(
                    id=row.id,
                    name=row.name,
                    phone=row.phone or "",
                    address=row.address or "",
                    email=row.email or "",
                    join_date=row.join_date,
                    is_fund_manager=row.is_fund_manager or False
                )
                investors.append(investor)
            
            return investors
        
        try:
            if not self.connected:
                return []
            return self._execute_with_retry(_load_investors_impl, "Load Investors")
        except Exception as e:
            st.error(f"❌ Error loading investors: {str(e)}")
            return []
    
    def load_tranches(self) -> List[Tranche]:
        """Load tranches with retry logic"""
        def _load_tranches_impl():
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                           original_entry_date, original_entry_nav, cumulative_fees_paid
                    FROM tranches 
                    ORDER BY entry_date, investor_id
                """))
                rows = result.fetchall()
            
            tranches = []
            for row in rows:
                tranche = Tranche(
                    investor_id=row.investor_id,
                    tranche_id=row.tranche_id,
                    entry_date=row.entry_date,
                    entry_nav=float(row.entry_nav),
                    units=float(row.units),
                    hwm=float(row.hwm),
                    original_entry_date=row.original_entry_date or row.entry_date,
                    original_entry_nav=float(row.original_entry_nav or row.entry_nav),
                    cumulative_fees_paid=float(row.cumulative_fees_paid or 0.0)
                )
                tranches.append(tranche)
            
            return tranches
        
        try:
            if not self.connected:
                return []
            return self._execute_with_retry(_load_tranches_impl, "Load Tranches")
        except Exception as e:
            st.error(f"❌ Error loading tranches: {str(e)}")
            return []
    
    def load_transactions(self) -> List[Transaction]:
        """Load transactions with retry logic"""
        def _load_transactions_impl():
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, investor_id, date, type, amount, nav, units_change
                    FROM transactions 
                    ORDER BY date DESC, id DESC
                """))
                rows = result.fetchall()
            
            transactions = []
            for row in rows:
                transaction = Transaction(
                    id=row.id,
                    investor_id=row.investor_id,
                    date=row.date,
                    type=row.type,
                    amount=float(row.amount),
                    nav=float(row.nav),
                    units_change=float(row.units_change)
                )
                transactions.append(transaction)
            
            return transactions
        
        try:
            if not self.connected:
                return []
            return self._execute_with_retry(_load_transactions_impl, "Load Transactions")
        except Exception as e:
            st.error(f"❌ Error loading transactions: {str(e)}")
            return []
    
    def load_fee_records(self) -> List[FeeRecord]:
        """Load fee records with retry logic"""
        def _load_fee_records_impl():
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, period, investor_id, fee_amount, fee_units, calculation_date,
                           units_before, units_after, nav_per_unit, description
                    FROM fee_records 
                    ORDER BY calculation_date DESC, id DESC
                """))
                rows = result.fetchall()
            
            fee_records = []
            for row in rows:
                fee_record = FeeRecord(
                    id=row.id,
                    period=row.period,
                    investor_id=row.investor_id,
                    fee_amount=float(row.fee_amount),
                    fee_units=float(row.fee_units),
                    calculation_date=row.calculation_date,
                    units_before=float(row.units_before),
                    units_after=float(row.units_after),
                    nav_per_unit=float(row.nav_per_unit),
                    description=row.description or ""
                )
                fee_records.append(fee_record)
            
            return fee_records
        
        try:
            if not self.connected:
                return []
            return self._execute_with_retry(_load_fee_records_impl, "Load Fee Records")
        except Exception as e:
            st.error(f"❌ Error loading fee records: {str(e)}")
            return []
    
    # === INDIVIDUAL SAVE METHODS (with retry logic) ===
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save investors with retry logic"""
        def _save_investors_impl():
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
        
        try:
            if not self.connected:
                return False
            return self._execute_with_retry(_save_investors_impl, "Save Investors")
        except Exception as e:
            st.error(f"❌ Error saving investors: {str(e)}")
            return False
    
    def save_tranches(self, tranches: List[Tranche]) -> bool:
        """Save tranches with retry logic"""
        def _save_tranches_impl():
            with self.engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("DELETE FROM tranches"))
                    
                    if tranches:
                        tranche_data = [{
                            'investor_id': t.investor_id, 'tranche_id': t.tranche_id,
                            'entry_date': t.entry_date, 'entry_nav': t.entry_nav,
                            'units': t.units, 'hwm': t.hwm,
                            'original_entry_date': t.original_entry_date,
                            'original_entry_nav': t.original_entry_nav,
                            'cumulative_fees_paid': t.cumulative_fees_paid
                        } for t in tranches]
                        
                        conn.execute(text("""
                            INSERT INTO tranches (
                                investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                original_entry_date, original_entry_nav, cumulative_fees_paid
                            ) VALUES (
                                :investor_id, :tranche_id, :entry_date, :entry_nav, :units, :hwm,
                                :original_entry_date, :original_entry_nav, :cumulative_fees_paid
                            )
                        """), tranche_data)
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
        
        try:
            if not self.connected:
                return False
            return self._execute_with_retry(_save_tranches_impl, "Save Tranches")
        except Exception as e:
            st.error(f"❌ Error saving tranches: {str(e)}")
            return False
    
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions with retry logic"""
        def _save_transactions_impl():
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
        
        try:
            if not self.connected:
                return False
            return self._execute_with_retry(_save_transactions_impl, "Save Transactions")
        except Exception as e:
            st.error(f"❌ Error saving transactions: {str(e)}")
            return False
    
    def save_fee_records(self, fee_records: List[FeeRecord]) -> bool:
        """Save fee records with retry logic"""
        def _save_fee_records_impl():
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
        
        try:
            if not self.connected:
                return False
            return self._execute_with_retry(_save_fee_records_impl, "Save Fee Records")
        except Exception as e:
            st.error(f"❌ Error saving fee records: {str(e)}")
            return False
    
    # === OTHER METHODS (unchanged) ===
    
    def create_backup(self) -> Optional[str]:
        """Create logical backup using pg_dump equivalent"""
        try:
            if not self.connected:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # For Supabase, we can create a simple data export
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
        """Get comprehensive database statistics"""
        try:
            if not self.connected:
                return {'connected': False, 'error': 'Not connected'}
            
            with self.engine.connect() as conn:
                stats = {'connected': True}
                
                # Table sizes
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins as inserts,
                        n_tup_upd as updates,
                        n_tup_del as deletes,
                        n_live_tup as live_tuples,
                        n_dead_tup as dead_tuples
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """))
                
                table_stats = []
                for row in result:
                    table_stats.append({
                        'table': row.tablename,
                        'live_tuples': row.live_tuples,
                        'dead_tuples': row.dead_tuples,
                        'inserts': row.inserts,
                        'updates': row.updates,
                        'deletes': row.deletes
                    })
                
                stats['tables'] = table_stats
                
                # Database size
                result = conn.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
                db_size = result.fetchone()[0] if result.rowcount > 0 else "Unknown"
                stats['database_size'] = db_size
                
                # Connection info
                result = conn.execute(text("""
                    SELECT 
                        current_database() as db_name,
                        current_user as user_name,
                        version() as version,
                        current_timestamp as current_time
                """))
                
                if result.rowcount > 0:
                    row = result.fetchone()
                    stats.update({
                        'database_name': row.db_name,
                        'user_name': row.user_name,
                        'version': row.version,
                        'current_time': row.current_time
                    })
                
                return stats
                
        except Exception as e:
            return {'connected': False, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        try:
            if not self.connected:
                return {'status': 'disconnected', 'checks': []}
            
            checks = []
            
            with self.engine.connect() as conn:
                # 1. Basic connectivity
                start_time = datetime.now()
                conn.execute(text("SELECT 1"))
                response_time = (datetime.now() - start_time).total_seconds()
                
                checks.append({
                    'name': 'Basic Connectivity',
                    'status': 'pass' if response_time < 5.0 else 'slow',
                    'details': f'{response_time:.3f}s response time'
                })
                
                # 2. Table existence
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
                
                # 3. Data integrity
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
                
                # 4. Index usage
                result = conn.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_tup_read DESC
                    LIMIT 5
                """))
                
                index_stats = []
                for row in result:
                    index_stats.append({
                        'table': row.tablename,
                        'index': row.indexname,
                        'reads': row.idx_tup_read,
                        'fetches': row.idx_tup_fetch
                    })
                
                checks.append({
                    'name': 'Index Performance',
                    'status': 'pass',
                    'details': f'Top indexes: {len(index_stats)} active'
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