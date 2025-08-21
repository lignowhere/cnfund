#!/usr/bin/env python3
"""
PRODUCTION MIGRATION SCRIPT: CSV → Supabase PostgreSQL
Ready to run with your actual database
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import psycopg2
from sqlalchemy import create_engine, text

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Your actual Supabase database URL
DATABASE_URL = "postgresql://postgres.qnnwnqsitsyegqeceypk:5uGkDiIthYfb3kx1@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"

class ProductionSupabaseHandler:
    """Production Supabase handler for migration"""
    
    def __init__(self):
        self.engine = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Connect to your Supabase PostgreSQL"""
        try:
            print(f"🔗 Connecting to Supabase...")
            
            # Ensure correct psycopg2 format
            db_url = DATABASE_URL
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            
            # Create engine with optimized settings for Supabase
            self.engine = create_engine(
                db_url,
                pool_size=3,
                max_overflow=5,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"sslmode": "require"}
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()
                if version:
                    self.connected = True
                    print("✅ Supabase PostgreSQL connected successfully")
                    print(f"📊 Database version: {version[0][:50]}...")
                    self._create_tables()
                    
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            self.connected = False
    
    def _create_tables(self):
        """Create all tables for Enhanced Fund Management"""
        try:
            print("🏗️ Creating/verifying database tables...")
            
            with self.engine.connect() as conn:
                # Investors table with is_fund_manager support
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS investors (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        phone VARCHAR(50),
                        address TEXT,
                        email VARCHAR(255),
                        join_date DATE NOT NULL,
                        is_fund_manager BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Enhanced tranches table with new fields
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS tranches (
                        id SERIAL PRIMARY KEY,
                        investor_id INTEGER NOT NULL,
                        tranche_id VARCHAR(255) UNIQUE NOT NULL,
                        entry_date TIMESTAMP NOT NULL,
                        entry_nav DECIMAL(15,2) NOT NULL,
                        units DECIMAL(15,6) NOT NULL,
                        hwm DECIMAL(15,2) NOT NULL,
                        original_entry_date TIMESTAMP,
                        original_entry_nav DECIMAL(15,2),
                        cumulative_fees_paid DECIMAL(15,2) DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Transactions table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY,
                        investor_id INTEGER NOT NULL,
                        date TIMESTAMP NOT NULL,
                        type VARCHAR(100) NOT NULL,
                        amount DECIMAL(15,2) NOT NULL,
                        nav DECIMAL(15,2) NOT NULL,
                        units_change DECIMAL(15,6) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Fee records table for enhanced tracking
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS fee_records (
                        id INTEGER PRIMARY KEY,
                        period VARCHAR(10) NOT NULL,
                        investor_id INTEGER NOT NULL,
                        fee_amount DECIMAL(15,2) NOT NULL,
                        fee_units DECIMAL(15,6) NOT NULL,
                        calculation_date TIMESTAMP NOT NULL,
                        units_before DECIMAL(15,6) NOT NULL,
                        units_after DECIMAL(15,6) NOT NULL,
                        nav_per_unit DECIMAL(15,2) NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # Create indexes for performance
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_tranches_investor ON tranches(investor_id)",
                    "CREATE INDEX IF NOT EXISTS idx_tranches_date ON tranches(entry_date)",
                    "CREATE INDEX IF NOT EXISTS idx_transactions_investor ON transactions(investor_id)",
                    "CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)",
                    "CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)",
                    "CREATE INDEX IF NOT EXISTS idx_fee_records_investor ON fee_records(investor_id)",
                    "CREATE INDEX IF NOT EXISTS idx_fee_records_period ON fee_records(period)"
                ]
                
                for index_sql in indexes:
                    conn.execute(text(index_sql))
                
                conn.commit()
                print("✅ Database tables and indexes created/verified")
                
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")
    
    def migrate_data(self, investors_data, tranches_data, transactions_data, fee_records_data):
        """Migrate all data to Supabase with enhanced error handling"""
        try:
            if not self.connected:
                print("❌ Not connected to database")
                return False
            
            print("🚀 Starting data migration...")
            
            with self.engine.connect() as conn:
                # Begin transaction
                trans = conn.begin()
                
                try:
                    # Clear existing data (be careful in production!)
                    print("🧹 Clearing existing data...")
                    conn.execute(text("TRUNCATE TABLE fee_records, transactions, tranches, investors RESTART IDENTITY CASCADE"))
                    
                    # Migrate investors
                    print(f"👥 Migrating {len(investors_data)} investors...")
                    for inv in investors_data:
                        conn.execute(text("""
                            INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager)
                            VALUES (:id, :name, :phone, :address, :email, :join_date, :is_fund_manager)
                        """), {
                            'id': inv.id,
                            'name': inv.name,
                            'phone': inv.phone,
                            'address': inv.address,
                            'email': inv.email,
                            'join_date': inv.join_date,
                            'is_fund_manager': inv.is_fund_manager
                        })
                    
                    # Migrate tranches
                    print(f"📊 Migrating {len(tranches_data)} tranches...")
                    for tranche in tranches_data:
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
                    
                    # Migrate transactions
                    print(f"📋 Migrating {len(transactions_data)} transactions...")
                    for trans_item in transactions_data:
                        conn.execute(text("""
                            INSERT INTO transactions (id, investor_id, date, type, amount, nav, units_change)
                            VALUES (:id, :investor_id, :date, :type, :amount, :nav, :units_change)
                        """), {
                            'id': trans_item.id,
                            'investor_id': trans_item.investor_id,
                            'date': trans_item.date,
                            'type': trans_item.type,
                            'amount': trans_item.amount,
                            'nav': trans_item.nav,
                            'units_change': trans_item.units_change
                        })
                    
                    # Migrate fee records
                    print(f"💰 Migrating {len(fee_records_data)} fee records...")
                    for fee in fee_records_data:
                        conn.execute(text("""
                            INSERT INTO fee_records (
                                id, period, investor_id, fee_amount, fee_units, calculation_date,
                                units_before, units_after, nav_per_unit, description
                            ) VALUES (
                                :id, :period, :investor_id, :fee_amount, :fee_units, :calculation_date,
                                :units_before, :units_after, :nav_per_unit, :description
                            )
                        """), {
                            'id': fee.id,
                            'period': fee.period,
                            'investor_id': fee.investor_id,
                            'fee_amount': fee.fee_amount,
                            'fee_units': fee.fee_units,
                            'calculation_date': fee.calculation_date,
                            'units_before': fee.units_before,
                            'units_after': fee.units_after,
                            'nav_per_unit': fee.nav_per_unit,
                            'description': fee.description
                        })
                    
                    # Commit transaction
                    trans.commit()
                    print("✅ All data migrated successfully!")
                    
                    # Verify migration
                    self._verify_migration(conn)
                    
                    return True
                    
                except Exception as e:
                    trans.rollback()
                    print(f"❌ Migration failed, rolled back: {str(e)}")
                    return False
                
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")
            return False
    
    def _verify_migration(self, conn):
        """Verify that migration was successful"""
        try:
            print("\n🔍 Verifying migration...")
            
            tables = ['investors', 'tranches', 'transactions', 'fee_records']
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                print(f"   📊 {table}: {count} records")
            
            # Check for Fund Manager
            result = conn.execute(text("SELECT name FROM investors WHERE is_fund_manager = true"))
            fm = result.fetchone()
            if fm:
                print(f"   🛡️ Fund Manager: {fm[0]}")
            
        except Exception as e:
            print(f"   ⚠️ Verification error: {str(e)}")

def load_csv_data():
    """Load data from CSV files"""
    print("📁 Loading data from CSV files...")
    
    try:
        import pandas as pd
        from models import Investor, Tranche, Transaction, FeeRecord
        
        # Load investors
        investors = []
        try:
            df = pd.read_csv("data/investors.csv", dtype={'Phone': 'str'})
            df['JoinDate'] = pd.to_datetime(df['JoinDate'], errors='coerce')
            df['Phone'] = df['Phone'].fillna('').astype(str).replace('nan', '')
            
            # Add is_fund_manager column if not exists
            if 'IsFundManager' not in df.columns:
                df['IsFundManager'] = False
            
            for _, row in df.iterrows():
                investor = Investor(
                    id=int(row['ID']),
                    name=str(row['Name']),
                    phone=str(row.get('Phone', '')),
                    address=str(row.get('Address', '')),
                    email=str(row.get('Email', '')),
                    join_date=row['JoinDate'].date() if pd.notna(row['JoinDate']) else pd.Timestamp.now().date(),
                    is_fund_manager=bool(row.get('IsFundManager', False))
                )
                investors.append(investor)
                
            print(f"   ✅ Loaded {len(investors)} investors")
        except FileNotFoundError:
            print("   ⚠️ investors.csv not found")
        
        # Load tranches
        tranches = []
        try:
            df = pd.read_csv("data/tranches.csv")
            df['EntryDate'] = pd.to_datetime(df['EntryDate'], errors='coerce')
            
            # Add missing enhanced columns with backward compatibility
            if 'HWM' not in df.columns:
                df['HWM'] = df['EntryNAV']
            if 'OriginalEntryDate' not in df.columns:
                df['OriginalEntryDate'] = df['EntryDate']
            if 'OriginalEntryNAV' not in df.columns:
                df['OriginalEntryNAV'] = df['EntryNAV']
            if 'CumulativeFeesPaid' not in df.columns:
                df['CumulativeFeesPaid'] = 0.0
            
            df['OriginalEntryDate'] = pd.to_datetime(df['OriginalEntryDate'], errors='coerce')
            df['OriginalEntryDate'] = df['OriginalEntryDate'].fillna(df['EntryDate'])
            
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
                
            print(f"   ✅ Loaded {len(tranches)} tranches")
        except FileNotFoundError:
            print("   ⚠️ tranches.csv not found")
        
        # Load transactions
        transactions = []
        try:
            df = pd.read_csv("data/transactions.csv")
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            
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
                
            print(f"   ✅ Loaded {len(transactions)} transactions")
        except FileNotFoundError:
            print("   ⚠️ transactions.csv not found")
        
        # Load fee records
        fee_records = []
        try:
            df = pd.read_csv("data/fee_records.csv")
            df['CalculationDate'] = pd.to_datetime(df['CalculationDate'], errors='coerce')
            
            for _, row in df.iterrows():
                fee_record = FeeRecord(
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
                fee_records.append(fee_record)
                
            print(f"   ✅ Loaded {len(fee_records)} fee records")
        except FileNotFoundError:
            print("   ⚠️ fee_records.csv not found")
        
        return investors, tranches, transactions, fee_records
        
    except Exception as e:
        print(f"❌ Error loading CSV data: {str(e)}")
        return [], [], [], []

def main():
    """Main migration function"""
    print("🗃️ Enhanced Fund Management System - Production Migration")
    print("=" * 70)
    print(f"🎯 Target: Supabase PostgreSQL")
    print(f"🔗 Host: db.qnnwnqsitsyegqeceypk.supabase.co")
    print("=" * 70)
    
    # Step 1: Connect to Supabase
    print("\n🔗 Step 1: Connecting to Supabase...")
    handler = ProductionSupabaseHandler()
    
    if not handler.connected:
        print("❌ Failed to connect to Supabase. Check your database URL and network.")
        return False
    
    # Step 2: Load CSV data
    print("\n📁 Step 2: Loading CSV data...")
    investors, tranches, transactions, fee_records = load_csv_data()
    
    if not any([investors, tranches, transactions, fee_records]):
        print("❌ No data found to migrate. Please check your CSV files.")
        return False
    
    # Step 3: Migrate data
    print("\n🚀 Step 3: Migrating data to Supabase...")
    success = handler.migrate_data(investors, tranches, transactions, fee_records)
    
    if success:
        print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("📊 Migration Summary:")
        print(f"   👥 Investors: {len(investors)}")
        print(f"   📊 Tranches: {len(tranches)}")
        print(f"   📋 Transactions: {len(transactions)}")
        print(f"   💰 Fee Records: {len(fee_records)}")
        print("\n✅ Your Enhanced Fund Management System is now using Supabase!")
        print("🚀 Ready for production deployment on Streamlit Cloud!")
        print("\n🔄 Next steps:")
        print("   1. Test the application locally: streamlit run app.py")
        print("   2. Deploy to Streamlit Cloud with secrets configured")
        print("   3. Verify all features work correctly")
        
        return True
    else:
        print("❌ Migration failed! Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)