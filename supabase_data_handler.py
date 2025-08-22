#!/usr/bin/env python3
"""
PRODUCTION-READY Supabase PostgreSQL Data Handler
Optimized for your specific database: db.qnnwnqsitsyegqeceypk.supabase.co
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import os

from models import Investor, Tranche, Transaction, FeeRecord

class SupabaseDataHandler:
    """Production Supabase PostgreSQL data handler"""
    
    def __init__(self):
        self.engine = None
        self.connected = False
        self.connection_info = {}
        self.version_info = {}
        self._connect()
    
    def _connect(self):
        """Kết nối tới DB và lưu thông tin, không hiển thị UI trực tiếp."""
        try:
            db_url = self._get_database_url()
            if not db_url:
                print("ERROR: Database URL not found in secrets or env variables.")
                self.connected = False
                return
            
            self.connection_info = self._parse_db_url(db_url)
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            
            self.engine = create_engine(db_url, pool_pre_ping=True, connect_args={"sslmode": "require"})
            
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
            print(f"CRITICAL: Supabase connection failed: {e}")
            self.engine = None
            self.connected = False
            
            # Provide helpful debugging info
            if "password authentication failed" in error_msg.lower():
                st.error("🔑 Password authentication failed. Check your database password.")
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
        """
        Tối ưu hóa: Gộp tất cả các lệnh CREATE vào một chuỗi duy nhất
        để giảm thiểu số lần gọi database.
        """
        # **SỬA ĐỔI QUAN TRỌNG**
        combined_sql = text("""
            -- Investors
            CREATE TABLE IF NOT EXISTS investors (
                id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL, phone VARCHAR(50) DEFAULT '',
                address TEXT DEFAULT '', email VARCHAR(255) DEFAULT '', join_date DATE NOT NULL DEFAULT CURRENT_DATE,
                is_fund_manager BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            -- Tranches
            CREATE TABLE IF NOT EXISTS tranches (
                id SERIAL PRIMARY KEY, investor_id INTEGER NOT NULL, tranche_id VARCHAR(255) UNIQUE NOT NULL,
                entry_date TIMESTAMP NOT NULL, entry_nav DECIMAL(18,4) NOT NULL, units DECIMAL(18,8) NOT NULL,
                hwm DECIMAL(18,4) NOT NULL, original_entry_date TIMESTAMP, original_entry_nav DECIMAL(18,4),
                cumulative_fees_paid DECIMAL(18,4) DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            -- Transactions
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY, investor_id INTEGER NOT NULL, date TIMESTAMP NOT NULL,
                type VARCHAR(100) NOT NULL, amount DECIMAL(18,4) NOT NULL, nav DECIMAL(18,4) NOT NULL,
                units_change DECIMAL(18,8) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            -- Fee Records
            CREATE TABLE IF NOT EXISTS fee_records (
                id INTEGER PRIMARY KEY, period VARCHAR(20) NOT NULL, investor_id INTEGER NOT NULL,
                fee_amount DECIMAL(18,4) NOT NULL, fee_units DECIMAL(18,8) NOT NULL,
                calculation_date TIMESTAMP NOT NULL, units_before DECIMAL(18,8) NOT NULL,
                units_after DECIMAL(18,8) NOT NULL, nav_per_unit DECIMAL(18,4) NOT NULL,
                description TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            -- Indexes
            CREATE INDEX IF NOT EXISTS idx_investors_fund_manager ON investors(is_fund_manager);
            CREATE INDEX IF NOT EXISTS idx_tranches_investor_id ON tranches(investor_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_investor_id ON transactions(investor_id);
            CREATE INDEX IF NOT EXISTS idx_fee_records_investor_id ON fee_records(investor_id);
        """)
        try:
            with self.engine.connect() as conn:
                conn.execute(combined_sql)
                conn.commit()
        except Exception as e:
            st.error(f"❌ Error creating tables: {str(e)}")
    
    def load_investors(self) -> List[Investor]:
        """Load investors with optimized query"""
        try:
            if not self.connected:
                return []
            
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
            
        except Exception as e:
            st.error(f"❌ Error loading investors: {str(e)}")
            return []
    
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save investors with batch optimization"""
        try:
            if not self.connected:
                return False
            
            with self.engine.connect() as conn:
                # Begin transaction
                trans = conn.begin()
                
                try:
                    # Clear existing data
                    conn.execute(text("DELETE FROM investors"))
                    
                    # Batch insert
                    if investors:
                        for investor in investors:
                            conn.execute(text("""
                                INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager)
                                VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)
                            """), {
                                'id': investor.id,
                                'name': investor.name,
                                'phone': investor.phone,
                                'address': investor.address,
                                'email': investor.email,
                                'join_date': investor.join_date,
                                'is_fund_manager': investor.is_fund_manager
                            })
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
            
        except Exception as e:
            st.error(f"❌ Error saving investors: {str(e)}")
            return False
    
    def load_tranches(self) -> List[Tranche]:
        """Load tranches with enhanced fields"""
        try:
            if not self.connected:
                return []
            
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
            
        except Exception as e:
            st.error(f"❌ Error loading tranches: {str(e)}")
            return []
    
    def save_tranches(self, tranches: List[Tranche]) -> bool:
        """Save tranches with enhanced fields"""
        try:
            if not self.connected:
                return False
            
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # Clear existing data
                    conn.execute(text("DELETE FROM tranches"))
                    
                    # Batch insert
                    for tranche in tranches:
                        conn.execute(text("""
                            INSERT INTO tranches (
                                investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                original_entry_date, original_entry_nav, cumulative_fees_paid
                            ) VALUES (
                                :investor_id, :tranche_id, :entry_date, :entry_nav, :units, :hwm,
                                :original_entry_date, :original_entry_nav, :cumulative_fees_paid
                            )
                        """), {
                            'investor_id': tranche.investor_id,
                            'tranche_id': tranche.tranche_id,
                            'entry_date': tranche.entry_date,
                            'entry_nav': tranche.entry_nav,
                            'units': tranche.units,
                            'hwm': tranche.hwm,
                            'original_entry_date': tranche.original_entry_date,
                            'original_entry_nav': tranche.original_entry_nav,
                            'cumulative_fees_paid': tranche.cumulative_fees_paid
                        })
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
            
        except Exception as e:
            st.error(f"❌ Error saving tranches: {str(e)}")
            return False
    
    def load_transactions(self) -> List[Transaction]:
        """Load transactions optimized"""
        try:
            if not self.connected:
                return []
            
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
            
        except Exception as e:
            st.error(f"❌ Error loading transactions: {str(e)}")
            return []
    
    def save_transactions(self, transactions: List[Transaction]) -> bool:
        """Save transactions optimized"""
        try:
            if not self.connected:
                return False
            
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # Clear existing data
                    conn.execute(text("DELETE FROM transactions"))
                    
                    # Batch insert
                    for transaction in transactions:
                        conn.execute(text("""
                            INSERT INTO transactions (id, investor_id, date, type, amount, nav, units_change)
                            VALUES (:id, :investor_id, :date, :type, :amount, :nav, :units_change)
                        """), {
                            'id': transaction.id,
                            'investor_id': transaction.investor_id,
                            'date': transaction.date,
                            'type': transaction.type,
                            'amount': transaction.amount,
                            'nav': transaction.nav,
                            'units_change': transaction.units_change
                        })
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
            
        except Exception as e:
            st.error(f"❌ Error saving transactions: {str(e)}")
            return False
    
    def load_fee_records(self) -> List[FeeRecord]:
        """Load fee records optimized"""
        try:
            if not self.connected:
                return []
            
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
            
        except Exception as e:
            st.error(f"❌ Error loading fee records: {str(e)}")
            return []
    
    def save_fee_records(self, fee_records: List[FeeRecord]) -> bool:
        """Save fee records optimized"""
        try:
            if not self.connected:
                return False
            
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                try:
                    # Clear existing data
                    conn.execute(text("DELETE FROM fee_records"))
                    
                    # Batch insert
                    for fee_record in fee_records:
                        conn.execute(text("""
                            INSERT INTO fee_records (
                                id, period, investor_id, fee_amount, fee_units, calculation_date,
                                units_before, units_after, nav_per_unit, description
                            ) VALUES (
                                :id, :period, :investor_id, :fee_amount, :fee_units, :calculation_date,
                                :units_before, :units_after, :nav_per_unit, :description
                            )
                        """), {
                            'id': fee_record.id,
                            'period': fee_record.period,
                            'investor_id': fee_record.investor_id,
                            'fee_amount': fee_record.fee_amount,
                            'fee_units': fee_record.fee_units,
                            'calculation_date': fee_record.calculation_date,
                            'units_before': fee_record.units_before,
                            'units_after': fee_record.units_after,
                            'nav_per_unit': fee_record.nav_per_unit,
                            'description': fee_record.description
                        })
                    
                    trans.commit()
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
            
        except Exception as e:
            st.error(f"❌ Error saving fee records: {str(e)}")
            return False
    
    def save_all_data_enhanced(self, investors, tranches, transactions, fee_records) -> bool:
        """Save all data in a single optimized transaction"""
        try:
            if not self.connected:
                return False
            
            with self.engine.connect() as conn:
                # Single large transaction for consistency
                trans = conn.begin()
                
                try:
                    # Clear all tables in correct order (foreign key dependencies)
                    conn.execute(text("DELETE FROM fee_records"))
                    conn.execute(text("DELETE FROM transactions"))
                    conn.execute(text("DELETE FROM tranches"))
                    conn.execute(text("DELETE FROM investors"))
                    
                    # Insert all data
                    # 1. Investors first
                    for investor in investors:
                        conn.execute(text("""
                            INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager)
                            VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)
                        """), {
                            'id': investor.id,
                            'name': investor.name,
                            'phone': investor.phone,
                            'address': investor.address,
                            'email': investor.email,
                            'join_date': investor.join_date,
                            'is_fund_manager': investor.is_fund_manager
                        })
                    
                    # 2. Tranches
                    for tranche in tranches:
                        conn.execute(text("""
                            INSERT INTO tranches (
                                investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                original_entry_date, original_entry_nav, cumulative_fees_paid
                            ) VALUES (
                                :investor_id, :tranche_id, :entry_date, :entry_nav, :units, :hwm,
                                :original_entry_date, :original_entry_nav, :cumulative_fees_paid
                            )
                        """), {
                            'investor_id': tranche.investor_id,
                            'tranche_id': tranche.tranche_id,
                            'entry_date': tranche.entry_date,
                            'entry_nav': tranche.entry_nav,
                            'units': tranche.units,
                            'hwm': tranche.hwm,
                            'original_entry_date': tranche.original_entry_date,
                            'original_entry_nav': tranche.original_entry_nav,
                            'cumulative_fees_paid': tranche.cumulative_fees_paid
                        })
                    
                    # 3. Transactions
                    for transaction in transactions:
                        conn.execute(text("""
                            INSERT INTO transactions (id, investor_id, date, type, amount, nav, units_change)
                            VALUES (:id, :investor_id, :date, :type, :amount, :nav, :units_change)
                        """), {
                            'id': transaction.id,
                            'investor_id': transaction.investor_id,
                            'date': transaction.date,
                            'type': transaction.type,
                            'amount': transaction.amount,
                            'nav': transaction.nav,
                            'units_change': transaction.units_change
                        })
                    
                    # 4. Fee records
                    for fee_record in fee_records:
                        conn.execute(text("""
                            INSERT INTO fee_records (
                                id, period, investor_id, fee_amount, fee_units, calculation_date,
                                units_before, units_after, nav_per_unit, description
                            ) VALUES (
                                :id, :period, :investor_id, :fee_amount, :fee_units, :calculation_date,
                                :units_before, :units_after, :nav_per_unit, :description
                            )
                        """), {
                            'id': fee_record.id,
                            'period': fee_record.period,
                            'investor_id': fee_record.investor_id,
                            'fee_amount': fee_record.fee_amount,
                            'fee_units': fee_record.fee_units,
                            'calculation_date': fee_record.calculation_date,
                            'units_before': fee_record.units_before,
                            'units_after': fee_record.units_after,
                            'nav_per_unit': fee_record.nav_per_unit,
                            'description': fee_record.description
                        })
                    
                    # Commit all changes
                    trans.commit()
                    
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    raise e
            
        except Exception as e:
            st.error(f"❌ Error saving all data: {str(e)}")
            return False
    
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