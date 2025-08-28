#!/usr/bin/env python3
"""
Auto-migrate script for CNFund Supabase PostgreSQL schema
Adds missing columns, fixes datatype mismatch, adds indexes and FK constraints safely.
"""

from supabase_data_handler import SupabaseDataHandler
from sqlalchemy import text

def auto_migrate(handler: SupabaseDataHandler):
    if not handler.connected:
        print("Database not connected. Aborting migration.")
        return False

    with handler.engine.connect() as conn:
        print("Starting auto-migration...")

        # --------------------------
        # INVESTORS table
        # --------------------------
        required_cols_investors = {
            'id': 'SERIAL PRIMARY KEY',
            'name': 'VARCHAR(255) NOT NULL',
            'phone': 'VARCHAR(50) DEFAULT \'\'',
            'address': 'TEXT DEFAULT \'\'',
            'email': 'VARCHAR(255) DEFAULT \'\'',
            'join_date': 'DATE DEFAULT CURRENT_DATE',
            'is_fund_manager': 'BOOLEAN DEFAULT FALSE'
        }

        for col, col_type in required_cols_investors.items():
            conn.execute(text(f"""
                ALTER TABLE investors
                ADD COLUMN IF NOT EXISTS {col} {col_type}
            """))
        print("✅ Investors table checked/updated.")

        # --------------------------
        # TRANCHES table
        # --------------------------
        required_cols_tranches = {
            'id': 'SERIAL PRIMARY KEY',
            'investor_id': 'INTEGER NOT NULL',
            'tranche_id': 'VARCHAR(255) UNIQUE NOT NULL',
            'entry_date': 'TIMESTAMP NOT NULL',
            'entry_nav': 'NUMERIC NOT NULL',
            'units': 'NUMERIC NOT NULL',
            'hwm': 'NUMERIC NOT NULL',
            'original_entry_date': 'TIMESTAMP',
            'original_entry_nav': 'NUMERIC',
            'cumulative_fees_paid': 'NUMERIC DEFAULT 0'
        }

        for col, col_type in required_cols_tranches.items():
            conn.execute(text(f"""
                ALTER TABLE tranches
                ADD COLUMN IF NOT EXISTS {col} {col_type}
            """))
        print("✅ Tranches table checked/updated.")

        # --------------------------
        # TRANSACTIONS table
        # --------------------------
        # Fix FK: tranche_id VARCHAR matches tranches.tranche_id
        required_cols_transactions = {
            'id': 'SERIAL PRIMARY KEY',
            'investor_id': 'INTEGER NOT NULL',
            'date': 'TIMESTAMP NOT NULL',
            'type': 'VARCHAR(100) NOT NULL',
            'amount': 'NUMERIC NOT NULL',
            'nav': 'NUMERIC',
            'units_change': 'NUMERIC',
            'hwm_before': 'NUMERIC',
            'hwm_after': 'NUMERIC',
            'notes': 'TEXT',
            'tranche_id': 'VARCHAR REFERENCES tranches(tranche_id)'
        }

        for col, col_type in required_cols_transactions.items():
            conn.execute(text(f"""
                ALTER TABLE transactions
                ADD COLUMN IF NOT EXISTS {col} {col_type}
            """))
        print("✅ Transactions table checked/updated.")

        # Tạo index trên transactions.tranche_id nếu chưa có
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename='transactions' AND indexname='idx_transactions_tranche_id'
                ) THEN
                    CREATE INDEX idx_transactions_tranche_id ON transactions(tranche_id);
                END IF;
            END
            $$;
        """))
        print("✅ Index on transactions.tranche_id checked/created.")

        # --------------------------
        # FEE_RECORDS table
        # --------------------------
        required_cols_fee_records = {
            'id': 'SERIAL PRIMARY KEY',
            'period': 'VARCHAR(20) NOT NULL',
            'investor_id': 'INTEGER NOT NULL',
            'fee_amount': 'NUMERIC NOT NULL',
            'fee_units': 'NUMERIC NOT NULL',
            'calculation_date': 'TIMESTAMP NOT NULL',
            'units_before': 'NUMERIC NOT NULL',
            'units_after': 'NUMERIC NOT NULL',
            'nav_per_unit': 'NUMERIC NOT NULL',
            'description': 'TEXT DEFAULT \'\''
        }

        for col, col_type in required_cols_fee_records.items():
            conn.execute(text(f"""
                ALTER TABLE fee_records
                ADD COLUMN IF NOT EXISTS {col} {col_type}
            """))
        print("✅ Fee_records table checked/updated.")

    print("🎉 Auto-migration completed successfully.")
    return True


if __name__ == "__main__":
    handler = SupabaseDataHandler()
    auto_migrate(handler)
