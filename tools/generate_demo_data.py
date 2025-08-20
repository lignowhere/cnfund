#!/usr/bin/env python3
"""
Demo Data Generator cho Enhanced Fund Management System
Tạo dữ liệu demo để test các tính năng enhanced
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date, timedelta
import random

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from services_enhanced import EnhancedFundManager
    from models import Investor, Tranche, Transaction, FeeRecord
    from utils import format_currency, format_percentage
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class DemoDataGenerator:
    """Generator cho demo data"""
    
    def __init__(self):
        self.fund_manager = EnhancedFundManager()
    
    def clear_existing_data(self):
        """Clear existing data (except fund manager)"""
        print("🧹 Clearing existing data...")
        
        # Keep fund manager, clear others
        fund_manager = self.fund_manager.get_fund_manager()
        if fund_manager:
            self.fund_manager.investors = [fund_manager]
        else:
            self.fund_manager.investors = []
        
        self.fund_manager.tranches = []
        self.fund_manager.transactions = []
        self.fund_manager.fee_records = []
        
        print("✅ Data cleared")
    
    def create_demo_investors(self):
        """Tạo demo investors"""
        print("👥 Creating demo investors...")
        
        demo_investors = [
            {"name": "Nguyễn Văn A", "phone": "0123456789", "email": "nva@email.com"},
            {"name": "Trần Thị B", "phone": "0987654321", "email": "ttb@email.com"},
            {"name": "Lê Văn C", "phone": "0111222333", "email": "lvc@email.com"},
            {"name": "Phạm Thị D", "phone": "0444555666", "email": "ptd@email.com"},
        ]
        
        for investor_data in demo_investors:
            success, message = self.fund_manager.add_investor(
                investor_data["name"],
                investor_data["phone"],
                email=investor_data["email"]
            )
            if success:
                print(f"  ✅ {message}")
            else:
                print(f"  ❌ {message}")
    
    def create_demo_transactions_year1(self):
        """Tạo demo transactions cho năm đầu (2024) với performance cao hơn"""
        print("💸 Creating Year 1 (2024) transactions...")
        
        regular_investors = self.fund_manager.get_regular_investors()
        if not regular_investors:
            print("❌ No investors found")
            return
        
        # Scenario Year 1: Investors join gradually, fund grows 35% (higher than 6% hurdle)
        base_date = datetime(2024, 1, 1)
        
        # Investor 1: Joins early, invests 100M
        investor1 = regular_investors[0]
        success, msg = self.fund_manager.process_deposit(
            investor1.id, 100000000, 100000000, base_date + timedelta(days=15)
        )
        print(f"  ✅ {investor1.name}: {msg}" if success else f"  ❌ {msg}")
        
        # NAV updates throughout the year - HIGHER PERFORMANCE
        nav_updates = [
            (base_date + timedelta(days=90), 110000000),   # +10% after 3 months
            (base_date + timedelta(days=180), 125000000),  # +25% after 6 months
            (base_date + timedelta(days=270), 130000000),  # +30% after 9 months
        ]
        
        for update_date, nav_value in nav_updates:
            success, msg = self.fund_manager.process_nav_update(nav_value, update_date)
            print(f"  📈 NAV update: {format_currency(nav_value)}")
        
        # Investor 2: Joins mid-year, invests 50M
        investor2 = regular_investors[1]
        success, msg = self.fund_manager.process_deposit(
            investor2.id, 50000000, 175000000, base_date + timedelta(days=180)
        )
        print(f"  ✅ {investor2.name}: {msg}" if success else f"  ❌ {msg}")
        
        # Investor 3: Joins later, invests 75M
        if len(regular_investors) > 2:
            investor3 = regular_investors[2]
            success, msg = self.fund_manager.process_deposit(
                investor3.id, 75000000, 250000000, base_date + timedelta(days=240)
            )
            print(f"  ✅ {investor3.name}: {msg}" if success else f"  ❌ {msg}")
        
        # End of year: Fund grows to 300M (total ~35% growth - well above 6% hurdle)
        year_end = datetime(2024, 12, 31, 15, 0, 0)
        success, msg = self.fund_manager.process_nav_update(300000000, year_end)
        print(f"  📊 Year-end NAV: {format_currency(300000000)}")
    
    def apply_year1_fees(self):
        """Áp dụng phí cuối năm 2024"""
        print("🧮 Applying Year 1 (2024) fees...")
        
        success, message = self.fund_manager.apply_year_end_fees_enhanced(
            2024, date(2024, 12, 31), 300000000  # Updated NAV
        )
        
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
    
    def create_demo_transactions_year2(self):
        """Tạo demo transactions cho năm thứ 2 (2025) với performance tốt"""
        print("💸 Creating Year 2 (2025) transactions...")
        
        regular_investors = self.fund_manager.get_regular_investors()
        
        # Year 2: Continue strong performance
        base_date = datetime(2025, 1, 1)
        
        # Start year 2 with 300M
        success, msg = self.fund_manager.process_nav_update(300000000, base_date + timedelta(days=5))
        
        # Investor 4 joins if available
        if len(regular_investors) > 3:
            investor4 = regular_investors[3]
            # Calculate current price for investor 4
            current_price = self.fund_manager.calculate_price_per_unit(300000000)
            success, msg = self.fund_manager.process_deposit(
                investor4.id, 30000000, 330000000, base_date + timedelta(days=30)
            )
            print(f"  ✅ {investor4.name}: {msg}" if success else f"  ❌ {msg}")
        
        # Mid-year: Continue strong performance
        nav_updates_y2 = [
            (base_date + timedelta(days=90), 340000000),   # +3% 
            (base_date + timedelta(days=120), 355000000),  # +7.5%
            (base_date + timedelta(days=180), 370000000),  # +12%
            (base_date + timedelta(days=240), 385000000),  # +16.5%
        ]
        
        for update_date, nav_value in nav_updates_y2:
            success, msg = self.fund_manager.process_nav_update(nav_value, update_date)
            print(f"  📈 NAV update: {format_currency(nav_value)}")
        
        # One investor makes partial withdrawal
        if len(regular_investors) > 1:
            investor2 = regular_investors[1]
            success, msg = self.fund_manager.process_withdrawal(
                investor2.id, 15000000, 370000000, base_date + timedelta(days=200)
            )
            print(f"  💸 {investor2.name} withdrawal: {msg}" if success else f"  ❌ {msg}")
        
        # Year 2 end: 400M (another strong year - 33% growth)
        year_end_2025 = datetime(2025, 12, 31, 15, 0, 0)
        success, msg = self.fund_manager.process_nav_update(400000000, year_end_2025)
        print(f"  📊 Year 2 end NAV: {format_currency(400000000)}")
    
    def apply_year2_fees(self):
        """Áp dụng phí cuối năm 2025"""
        print("🧮 Applying Year 2 (2025) fees...")
        
        success, message = self.fund_manager.apply_year_end_fees_enhanced(
            2025, date(2025, 12, 31), 400000000  # Updated NAV
        )
        
        if success:
            print(f"  ✅ {message}")
            
            # Show fund manager status after fees
            fund_manager = self.fund_manager.get_fund_manager()
            if fund_manager:
                fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
                if fm_tranches:
                    fm_units = sum(t.units for t in fm_tranches)
                    fm_value = fm_units * self.fund_manager.calculate_price_per_unit(400000000)
                    print(f"  🏛️ Fund Manager: {fm_units:.3f} units = {format_currency(fm_value)}")
        else:
            print(f"  ❌ {message}")
    
    def create_current_period_transactions(self):
        """Tạo transactions cho period hiện tại (2026)"""
        print("💸 Creating current period transactions...")
        
        # Current period: Continuing growth
        current_date = datetime.now()
        
        # Update to current with some growth
        success, msg = self.fund_manager.process_nav_update(420000000, current_date)
        print(f"  📊 Current NAV: {format_currency(420000000)}")
    
    def show_demo_summary(self):
        """Hiển thị tổng kết demo data"""
        print("\n" + "=" * 60)
        print("📊 DEMO DATA SUMMARY")
        print("=" * 60)
        
        # System overview
        regular_investors = self.fund_manager.get_regular_investors()
        fund_manager = self.fund_manager.get_fund_manager()
        
        print(f"👥 Regular Investors: {len(regular_investors)}")
        print(f"🏛️ Fund Manager: {'✅' if fund_manager else '❌'}")
        print(f"📊 Total Tranches: {len(self.fund_manager.tranches)}")
        print(f"📋 Total Transactions: {len(self.fund_manager.transactions)}")
        print(f"💰 Fee Records: {len(self.fund_manager.fee_records)}")
        
        latest_nav = self.fund_manager.get_latest_total_nav()
        if latest_nav:
            print(f"📈 Latest NAV: {format_currency(latest_nav)}")
            current_price = self.fund_manager.calculate_price_per_unit(latest_nav)
            print(f"💎 Price per Unit: {format_currency(current_price)}")
        
        # Investor summary
        print(f"\n👥 INVESTOR SUMMARY:")
        for investor in regular_investors:
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            if tranches and latest_nav:
                balance, profit, profit_perc = self.fund_manager.get_investor_balance(investor.id, latest_nav)
                lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, latest_nav)
                
                print(f"  {investor.display_name}:")
                print(f"    💰 Current Balance: {format_currency(balance)}")
                print(f"    📈 Gross Return: {format_percentage(lifetime_perf['gross_return'])}")
                print(f"    📊 Net Return: {format_percentage(lifetime_perf['net_return'])}")
                print(f"    💸 Total Fees Paid: {format_currency(lifetime_perf['total_fees_paid'])}")
        
        # Fund Manager summary
        if fund_manager and latest_nav:
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            if fm_tranches:
                fm_units = sum(t.units for t in fm_tranches)
                fm_value = fm_units * current_price
                print(f"\n🏛️ FUND MANAGER:")
                print(f"    📊 Total Units: {fm_units:.6f}")
                print(f"    💰 Total Value: {format_currency(fm_value)}")
                
                # Fee income breakdown
                fee_transactions = [t for t in self.fund_manager.transactions 
                                  if t.investor_id == fund_manager.id and t.type == 'Phí Nhận']
                total_fee_income = sum(t.amount for t in fee_transactions)
                print(f"    💸 Total Fee Income: {format_currency(total_fee_income)}")
        
        print(f"\n✅ Demo data generation completed successfully!")
    
    def generate_full_demo(self):
        """Tạo complete demo data"""
        print("🚀 Generating Complete Demo Data for Enhanced Fund Management System")
        print("=" * 80)
        
        steps = [
            ("Clear existing data", self.clear_existing_data),
            ("Create demo investors", self.create_demo_investors),
            ("Create Year 1 transactions", self.create_demo_transactions_year1),
            ("Apply Year 1 fees", self.apply_year1_fees),
            ("Create Year 2 transactions", self.create_demo_transactions_year2),
            ("Apply Year 2 fees", self.apply_year2_fees),
            ("Create current period", self.create_current_period_transactions),
            ("Save all data", lambda: self.fund_manager.save_data()),
            ("Show summary", self.show_demo_summary)
        ]
        
        for i, (step_name, step_func) in enumerate(steps, 1):
            print(f"\n📋 Step {i}: {step_name}")
            try:
                result = step_func()
                if step_name == "Save all data":
                    if result:
                        print("  ✅ Data saved successfully")
                    else:
                        print("  ❌ Error saving data")
            except Exception as e:
                print(f"  ❌ Error in {step_name}: {str(e)}")
                return False
        
        return True

def main():
    """Main demo generation function"""
    
    print("🎯 Enhanced Fund Management System - Demo Data Generator")
    print("This will create realistic demo data to test enhanced features")
    
    response = input("\n⚠️  This will REPLACE existing data. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Demo generation cancelled")
        return 1
    
    generator = DemoDataGenerator()
    success = generator.generate_full_demo()
    
    if success:
        print("\n🎉 Demo data generation completed successfully!")
        print("\nYou can now:")
        print("1. 🚀 Run the app: streamlit run app.py")
        print("2. 🧪 Run validation: python test_enhanced_system.py")
        print("3. 📊 Explore lifetime performance features")
        print("4. 💰 Test enhanced fee calculations")
        print("5. 🏛️ View fund manager dashboard")
        return 0
    else:
        print("\n❌ Demo data generation failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)