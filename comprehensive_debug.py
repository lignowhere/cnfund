#!/usr/bin/env python3
"""
COMPREHENSIVE DEBUG & FIX SCRIPT
Phát hiện và khắc phục tất cả vấn đề trong hệ thống quản lý quỹ
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from pathlib import Path
import json

class ComprehensiveDebugger:
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.engine = None
        self.setup_database()
    
    def setup_database(self):
        """Setup database connection"""
        try:
            db_url = os.getenv("DATABASE_URL")
            if not db_url:
                print("Enter your DATABASE_URL:")
                db_url = input().strip()
            
            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            
            self.engine = create_engine(db_url, pool_pre_ping=True)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            self.engine = None
    
    def debug_data_integrity(self):
        """Kiểm tra tính toàn vẹn dữ liệu"""
        print("\n=== DEBUGGING DATA INTEGRITY ===")
        
        if not self.engine:
            self.issues.append("No database connection")
            return
        
        try:
            with self.engine.connect() as conn:
                # Check table counts
                tables = ['investors', 'tranches', 'transactions', 'fee_records']
                counts = {}
                
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    counts[table] = result.fetchone()[0]
                    print(f"  {table}: {counts[table]} records")
                
                # Check missing investors for tranches
                result = conn.execute(text("""
                    SELECT t.investor_id, COUNT(*) as tranche_count
                    FROM tranches t
                    LEFT JOIN investors i ON t.investor_id = i.id
                    WHERE i.id IS NULL
                    GROUP BY t.investor_id
                """))
                
                orphan_tranches = result.fetchall()
                if orphan_tranches:
                    for investor_id, count in orphan_tranches:
                        issue = f"Orphan tranches: {count} tranches for non-existent investor {investor_id}"
                        self.issues.append(issue)
                        print(f"  ❌ {issue}")
                
                # Check investors with deposits but no tranches
                result = conn.execute(text("""
                    WITH deposit_investors AS (
                        SELECT DISTINCT investor_id FROM transactions WHERE type = 'Nạp'
                    ),
                    tranche_investors AS (
                        SELECT DISTINCT investor_id FROM tranches
                    )
                    SELECT d.investor_id
                    FROM deposit_investors d
                    LEFT JOIN tranche_investors t ON d.investor_id = t.investor_id
                    WHERE t.investor_id IS NULL
                """))
                
                missing_tranches = [row[0] for row in result.fetchall()]
                if missing_tranches:
                    issue = f"Missing tranches for investors: {missing_tranches}"
                    self.issues.append(issue)
                    print(f"  ❌ {issue}")
                
                # Check HWM vs Entry NAV consistency
                result = conn.execute(text("""
                    SELECT tranche_id, entry_nav, hwm
                    FROM tranches 
                    WHERE hwm < entry_nav
                """))
                
                invalid_hwm = result.fetchall()
                if invalid_hwm:
                    for tranche_id, entry_nav, hwm in invalid_hwm:
                        issue = f"Invalid HWM: {tranche_id} has HWM {hwm} < Entry NAV {entry_nav}"
                        self.issues.append(issue)
                        print(f"  ❌ {issue}")
                
                # Check extreme Entry NAV values (likely errors)
                result = conn.execute(text("""
                    SELECT tranche_id, entry_nav, units
                    FROM tranches 
                    WHERE entry_nav > 100000 OR entry_nav < 1000
                """))
                
                extreme_nav = result.fetchall()
                if extreme_nav:
                    for tranche_id, entry_nav, units in extreme_nav:
                        issue = f"Extreme Entry NAV: {tranche_id} has Entry NAV {entry_nav}"
                        self.issues.append(issue)
                        print(f"  ⚠️ {issue}")
                
                print(f"✅ Data integrity check complete. Found {len(self.issues)} issues.")
                
        except Exception as e:
            issue = f"Data integrity check failed: {e}"
            self.issues.append(issue)
            print(f"  ❌ {issue}")
    
    def debug_fee_calculation(self):
        """Debug tính phí performance"""
        print("\n=== DEBUGGING FEE CALCULATION ===")
        
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                # Get latest NAV
                result = conn.execute(text("""
                    SELECT nav FROM transactions 
                    WHERE nav > 0 
                    ORDER BY date DESC, id DESC 
                    LIMIT 1
                """))
                
                latest_nav_row = result.fetchone()
                if not latest_nav_row:
                    self.issues.append("No NAV data found")
                    return
                
                latest_nav = float(latest_nav_row[0])
                print(f"  Latest NAV: {latest_nav:,.0f}")
                
                # Calculate current price per unit
                result = conn.execute(text("SELECT SUM(units) FROM tranches"))
                total_units = float(result.fetchone()[0] or 0)
                
                if total_units <= 0:
                    self.issues.append("No units found in tranches")
                    return
                
                current_price = latest_nav / total_units
                print(f"  Current price per unit: {current_price:,.2f}")
                
                # Analyze fee calculation for each investor
                result = conn.execute(text("""
                    SELECT DISTINCT investor_id FROM tranches 
                    WHERE investor_id != 0
                    ORDER BY investor_id
                """))
                
                investor_ids = [row[0] for row in result.fetchall()]
                
                for investor_id in investor_ids:
                    print(f"\n  Analyzing Investor {investor_id}:")
                    
                    # Get investor tranches
                    result = conn.execute(text("""
                        SELECT tranche_id, entry_date, entry_nav, units, hwm
                        FROM tranches 
                        WHERE investor_id = :investor_id
                    """), {'investor_id': investor_id})
                    
                    tranches = result.fetchall()
                    
                    total_units_inv = sum(float(t[3]) for t in tranches)
                    current_balance = total_units_inv * current_price
                    total_invested = sum(float(t[3]) * float(t[2]) for t in tranches)
                    
                    print(f"    Balance: {current_balance:,.0f}")
                    print(f"    Invested: {total_invested:,.0f}")
                    print(f"    Profit: {current_balance - total_invested:,.0f}")
                    
                    total_fee = 0
                    total_hwm_value = 0
                    total_hurdle_value = 0
                    total_excess_profit = 0
                    
                    for tranche_id, entry_date, entry_nav, units, hwm in tranches:
                        entry_date = pd.to_datetime(entry_date)
                        days_held = (datetime.now() - entry_date).days
                        years_held = days_held / 365.25
                        
                        hurdle_price = float(entry_nav) * ((1 + 0.06) ** years_held)
                        threshold_price = max(hurdle_price, float(hwm))
                        
                        profit_per_unit = max(0, current_price - threshold_price)
                        excess_profit = profit_per_unit * float(units)
                        fee = excess_profit * 0.20
                        
                        total_fee += fee
                        total_hwm_value += float(hwm) * float(units)
                        total_hurdle_value += hurdle_price * float(units)
                        total_excess_profit += excess_profit
                        
                        print(f"    Tranche {tranche_id}:")
                        print(f"      Days held: {days_held}")
                        print(f"      Entry NAV: {float(entry_nav):,.0f}")
                        print(f"      HWM: {float(hwm):,.0f}")
                        print(f"      Hurdle: {hurdle_price:,.0f}")
                        print(f"      Threshold: {threshold_price:,.0f}")
                        print(f"      Current: {current_price:,.0f}")
                        print(f"      Excess profit: {excess_profit:,.0f}")
                        print(f"      Fee: {fee:,.0f}")
                    
                    print(f"    TOTAL:")
                    print(f"      HWM Value: {total_hwm_value:,.0f}")
                    print(f"      Hurdle Value: {total_hurdle_value:,.0f}")
                    print(f"      Excess Profit: {total_excess_profit:,.0f}")
                    print(f"      Performance Fee: {total_fee:,.0f}")
                    
                    # Check for issues
                    if total_excess_profit == 0 and current_balance > total_invested:
                        threshold_value = max(total_hwm_value, total_hurdle_value)
                        if threshold_value >= current_balance:
                            issue = f"Investor {investor_id}: Threshold ({threshold_value:,.0f}) >= Balance ({current_balance:,.0f})"
                            self.issues.append(issue)
                            print(f"      ❌ {issue}")
                            
                            # Diagnose the cause
                            if total_hwm_value >= current_balance:
                                cause = f"HWM Value too high: {total_hwm_value:,.0f}"
                                self.issues.append(f"Investor {investor_id}: {cause}")
                                print(f"        Root cause: {cause}")
                
        except Exception as e:
            issue = f"Fee calculation debug failed: {e}"
            self.issues.append(issue)
            print(f"  ❌ {issue}")
    
    def debug_recovery_completeness(self):
        """Check if recovery was complete"""
        print("\n=== DEBUGGING RECOVERY COMPLETENESS ===")
        
        if not self.engine:
            return
        
        try:
            with self.engine.connect() as conn:
                # Count transaction types vs expected tranches
                result = conn.execute(text("""
                    SELECT type, COUNT(*) as count
                    FROM transactions
                    GROUP BY type
                    ORDER BY type
                """))
                
                transaction_counts = dict(result.fetchall())
                print("  Transaction counts:")
                for t_type, count in transaction_counts.items():
                    print(f"    {t_type}: {count}")
                
                # Check for missing Fund Manager tranches from "Phí Nhận"
                phi_nhan_count = transaction_counts.get('Phí Nhận', 0)
                
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM tranches WHERE investor_id = 0
                """))
                fm_tranche_count = result.fetchone()[0]
                
                print(f"  Fund Manager analysis:")
                print(f"    'Phí Nhận' transactions: {phi_nhan_count}")
                print(f"    Fund Manager tranches: {fm_tranche_count}")
                
                if phi_nhan_count > 0 and fm_tranche_count == 0:
                    issue = f"Missing Fund Manager tranches: {phi_nhan_count} 'Phí Nhận' but 0 FM tranches"
                    self.issues.append(issue)
                    print(f"    ❌ {issue}")
                elif phi_nhan_count > fm_tranche_count:
                    issue = f"Incomplete Fund Manager tranches: {phi_nhan_count} 'Phí Nhận' vs {fm_tranche_count} FM tranches"
                    self.issues.append(issue)
                    print(f"    ⚠️ {issue}")
                
                # Check for investors with deposits but no tranches
                result = conn.execute(text("""
                    SELECT t.investor_id, COUNT(*) as deposit_count
                    FROM transactions t
                    LEFT JOIN tranches tr ON t.investor_id = tr.investor_id
                    WHERE t.type = 'Nạp' AND tr.investor_id IS NULL
                    GROUP BY t.investor_id
                """))
                
                missing_investor_tranches = result.fetchall()
                for investor_id, deposit_count in missing_investor_tranches:
                    issue = f"Investor {investor_id}: {deposit_count} deposits but no tranches"
                    self.issues.append(issue)
                    print(f"    ❌ {issue}")
                
        except Exception as e:
            issue = f"Recovery completeness check failed: {e}"
            self.issues.append(issue)
            print(f"  ❌ {issue}")
    
    def fix_all_issues(self):
        """Attempt to fix identified issues"""
        print("\n=== APPLYING FIXES ===")
        
        if not self.engine:
            print("❌ No database connection - cannot apply fixes")
            return
        
        try:
            with self.engine.begin() as trans:
                fixes_applied = 0
                
                # Fix 1: Complete missing Fund Manager tranches from "Phí Nhận"
                print("  Fix 1: Adding missing Fund Manager tranches...")
                result = trans.execute(text("""
                    SELECT id, date, amount, nav, units_change
                    FROM transactions
                    WHERE type = 'Phí Nhận' AND investor_id = 0
                    ORDER BY date, id
                """))
                
                phi_nhan_transactions = result.fetchall()
                
                for trans_id, date, amount, nav, units_change in phi_nhan_transactions:
                    # Check if FM tranche already exists for this transaction
                    check_result = trans.execute(text("""
                        SELECT COUNT(*) FROM tranches
                        WHERE investor_id = 0 
                        AND ABS(EXTRACT(EPOCH FROM (entry_date - :date))) < 3600
                        AND ABS(units - :units) < 0.000001
                    """), {'date': date, 'units': float(units_change)})
                    
                    if check_result.fetchone()[0] == 0:
                        # Create missing FM tranche
                        current_price = float(nav) / self.get_total_units_at_date(trans, date) if nav > 0 else 10000
                        
                        tranche_id = f"FEE_RECOVERED_{trans_id}_{int(datetime.now().timestamp())}"
                        
                        trans.execute(text("""
                            INSERT INTO tranches (
                                investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                original_entry_date, original_entry_nav, cumulative_fees_paid
                            ) VALUES (
                                0, :tranche_id, :date, :price, :units, :price,
                                :date, :price, 0
                            )
                        """), {
                            'tranche_id': tranche_id,
                            'date': date,
                            'price': current_price,
                            'units': float(units_change)
                        })
                        
                        fixes_applied += 1
                        print(f"    Created FM tranche for transaction {trans_id}")
                
                # Fix 2: Correct extreme Entry NAV values
                print("  Fix 2: Correcting extreme Entry NAV values...")
                result = trans.execute(text("""
                    SELECT tranche_id, entry_date, entry_nav, units
                    FROM tranches
                    WHERE entry_nav > 100000 OR entry_nav < 1000
                """))
                
                extreme_tranches = result.fetchall()
                
                for tranche_id, entry_date, entry_nav, units in extreme_tranches:
                    # Calculate reasonable Entry NAV based on date
                    reasonable_nav = self.estimate_reasonable_nav(trans, entry_date)
                    
                    if reasonable_nav and abs(reasonable_nav - float(entry_nav)) > 1000:
                        trans.execute(text("""
                            UPDATE tranches 
                            SET entry_nav = :reasonable_nav,
                                original_entry_nav = :reasonable_nav
                            WHERE tranche_id = :tranche_id
                        """), {
                            'reasonable_nav': reasonable_nav,
                            'tranche_id': tranche_id
                        })
                        
                        fixes_applied += 1
                        print(f"    Fixed Entry NAV for {tranche_id}: {entry_nav} -> {reasonable_nav}")
                
                # Fix 3: Correct HWM values that are unreasonably high
                print("  Fix 3: Correcting inflated HWM values...")
                
                # Get reasonable current price
                latest_nav = self.get_latest_nav(trans)
                total_units = self.get_total_units_at_date(trans, datetime.now())
                current_price = latest_nav / total_units if total_units > 0 else 10000
                
                result = trans.execute(text("""
                    SELECT tranche_id, entry_date, entry_nav, hwm, units
                    FROM tranches
                    WHERE hwm > entry_nav * 3  -- HWM more than 3x entry (suspicious)
                """))
                
                inflated_hwm = result.fetchall()
                
                for tranche_id, entry_date, entry_nav, hwm, units in inflated_hwm:
                    # Calculate reasonable HWM based on historical performance
                    reasonable_hwm = self.calculate_reasonable_hwm(trans, entry_date, float(entry_nav))
                    
                    if reasonable_hwm < float(hwm):
                        trans.execute(text("""
                            UPDATE tranches 
                            SET hwm = :reasonable_hwm
                            WHERE tranche_id = :tranche_id
                        """), {
                            'reasonable_hwm': reasonable_hwm,
                            'tranche_id': tranche_id
                        })
                        
                        fixes_applied += 1
                        print(f"    Fixed HWM for {tranche_id}: {hwm} -> {reasonable_hwm}")
                
                print(f"  ✅ Applied {fixes_applied} fixes successfully")
                self.fixes_applied.extend([f"Fix_{i+1}" for i in range(fixes_applied)])
                
        except Exception as e:
            print(f"  ❌ Error applying fixes: {e}")
    
    def get_total_units_at_date(self, conn, target_date):
        """Calculate total units at a specific date"""
        try:
            result = conn.execute(text("""
                SELECT COALESCE(SUM(units), 0) FROM tranches
                WHERE entry_date <= :date
            """), {'date': target_date})
            return float(result.fetchone()[0])
        except:
            return 0
    
    def get_latest_nav(self, conn):
        """Get latest NAV value"""
        try:
            result = conn.execute(text("""
                SELECT nav FROM transactions 
                WHERE nav > 0 
                ORDER BY date DESC, id DESC 
                LIMIT 1
            """))
            row = result.fetchone()
            return float(row[0]) if row else 100000000
        except:
            return 100000000
    
    def estimate_reasonable_nav(self, conn, entry_date):
        """Estimate reasonable NAV for a given date"""
        try:
            # Find NAV updates around the entry date
            result = conn.execute(text("""
                SELECT nav, date FROM transactions
                WHERE type = 'NAV Update' AND nav > 0
                AND ABS(EXTRACT(EPOCH FROM (date - :entry_date))) < 86400 * 30
                ORDER BY ABS(EXTRACT(EPOCH FROM (date - :entry_date)))
                LIMIT 1
            """), {'entry_date': entry_date})
            
            row = result.fetchone()
            if row:
                nav, date = row
                total_units = self.get_total_units_at_date(conn, date)
                return float(nav) / total_units if total_units > 0 else 10000
            
            return 10000  # Default reasonable price
            
        except:
            return 10000
    
    def calculate_reasonable_hwm(self, conn, entry_date, entry_nav):
        """Calculate reasonable HWM based on historical NAV performance"""
        try:
            # Find highest price achieved since entry date
            result = conn.execute(text("""
                SELECT MAX(nav) FROM transactions
                WHERE type = 'NAV Update' AND nav > 0 AND date >= :entry_date
            """), {'entry_date': entry_date})
            
            max_nav_row = result.fetchone()
            if max_nav_row and max_nav_row[0]:
                max_nav = float(max_nav_row[0])
                
                # Get average total units during this period
                result = conn.execute(text("""
                    SELECT AVG(total_units) FROM (
                        SELECT SUM(units) as total_units
                        FROM tranches t
                        JOIN transactions tr ON tr.date >= :entry_date AND tr.type = 'NAV Update'
                        WHERE t.entry_date <= tr.date
                        GROUP BY tr.date
                        LIMIT 10
                    ) avg_units
                """), {'entry_date': entry_date})
                
                avg_units_row = result.fetchone()
                if avg_units_row and avg_units_row[0]:
                    avg_units = float(avg_units_row[0])
                    max_price = max_nav / avg_units
                    return max(entry_nav, max_price)
            
            # Fallback: reasonable growth from entry NAV
            return entry_nav * 2  # Assume at most 100% growth
            
        except:
            return entry_nav * 1.5  # Conservative growth
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*60)
        print("COMPREHENSIVE DEBUG REPORT")
        print("="*60)
        
        print(f"\n📊 ISSUES IDENTIFIED: {len(self.issues)}")
        if self.issues:
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("  ✅ No issues found")
        
        print(f"\n🔧 FIXES APPLIED: {len(self.fixes_applied)}")
        if self.fixes_applied:
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"  {i}. {fix}")
        else:
            print("  No fixes applied")
        
        print(f"\n📋 RECOMMENDATIONS:")
        if self.issues:
            print("  1. Restart your Streamlit application")
            print("  2. Test fee calculations on a few investors")
            print("  3. Verify all investors show proper performance data")
            print("  4. Run this debug script periodically to catch issues early")
        else:
            print("  System appears to be functioning correctly")
        
        print("\n" + "="*60)
    
    def run_complete_debug(self):
        """Run all debug checks and fixes"""
        print("🔍 STARTING COMPREHENSIVE SYSTEM DEBUG")
        print("This will identify and fix all known issues...")
        
        # Run all debug checks
        self.debug_data_integrity()
        self.debug_fee_calculation()
        self.debug_recovery_completeness()
        
        # Apply fixes if issues found
        if self.issues:
            print(f"\n⚠️ Found {len(self.issues)} issues. Attempting fixes...")
            self.fix_all_issues()
        
        # Generate final report
        self.generate_report()
        
        return len(self.issues) == 0  # Return True if no issues found

def main():
    debugger = ComprehensiveDebugger()
    
    try:
        success = debugger.run_complete_debug()
        return success
    except KeyboardInterrupt:
        print("\n⏹️ Debug interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)