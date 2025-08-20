#!/usr/bin/env python3
"""
Manual test để tính phí thủ công và áp dụng enhanced fees
"""

import sys
from pathlib import Path
from datetime import datetime, date

sys.path.append(str(Path(__file__).parent))

from services_enhanced import EnhancedFundManager
from utils import format_currency, format_percentage

def manual_fee_application():
    """Manually apply fees với debug output"""
    print("🔧 MANUAL FEE APPLICATION WITH DEBUG")
    print("=" * 60)
    
    fm = EnhancedFundManager()
    
    # Force reset HWM để test
    print("🔧 Resetting HWM to entry NAV for testing...")
    for tranche in fm.tranches:
        if tranche.investor_id != 0:  # Not fund manager
            tranche.hwm = tranche.entry_nav
            print(f"  Reset HWM for tranche: {tranche.entry_nav}")
    
    # Test fee calculation after reset
    latest_nav = fm.get_latest_total_nav()
    ending_date = datetime(2024, 12, 31)
    
    print(f"\n📊 Testing with NAV: {format_currency(latest_nav)}")
    print(f"📅 Ending date: {ending_date}")
    
    total_fees = 0
    
    for investor in fm.get_regular_investors():
        print(f"\n🔍 Testing {investor.display_name}:")
        
        fee_details = fm.calculate_investor_fee(investor.id, ending_date, latest_nav)
        
        print(f"  Invested: {format_currency(fee_details['invested_value'])}")
        print(f"  Balance: {format_currency(fee_details['balance'])}")
        print(f"  Profit: {format_currency(fee_details['profit'])}")
        print(f"  Hurdle value: {format_currency(fee_details['hurdle_value'])}")
        print(f"  HWM value: {format_currency(fee_details['hwm_value'])}")
        print(f"  Excess profit: {format_currency(fee_details['excess_profit'])}")
        print(f"  💰 FEE: {format_currency(fee_details['total_fee'])}")
        
        total_fees += fee_details['total_fee']
    
    print(f"\n💰 TOTAL EXPECTED FEES: {format_currency(total_fees)}")
    
    if total_fees > 0:
        print("✅ Fees should be calculated! Applying enhanced fees...")
        
        # Apply enhanced fees
        success, message = fm.apply_year_end_fees_enhanced(2024, date(2024, 12, 31), latest_nav)
        
        if success:
            print(f"✅ {message}")
            
            # Check fund manager
            fund_manager = fm.get_fund_manager()
            if fund_manager:
                fm_tranches = fm.get_investor_tranches(fund_manager.id)
                if fm_tranches:
                    fm_units = sum(t.units for t in fm_tranches)
                    current_price = fm.calculate_price_per_unit(latest_nav)
                    fm_value = fm_units * current_price
                    print(f"🏛️ Fund Manager received: {fm_units:.6f} units = {format_currency(fm_value)}")
        else:
            print(f"❌ {message}")
        
        # Save results
        fm.save_data()
        print("💾 Data saved")
    
    else:
        print("❌ No fees calculated - there's still an issue with fee logic")

def create_simple_test_scenario():
    """Tạo scenario đơn giản để test fees"""
    print("\n🎯 CREATING SIMPLE TEST SCENARIO")
    print("=" * 60)
    
    fm = EnhancedFundManager()
    
    # Clear and create simple scenario
    fund_manager = fm.get_fund_manager()
    fm.investors = [fund_manager] if fund_manager else []
    fm.tranches = []
    fm.transactions = []
    fm.fee_records = []
    
    # Add 1 investor
    success, msg = fm.add_investor("Test Investor", "0123456789")
    print(f"✅ {msg}")
    
    # Simple investment: 100M at 1000đ
    regular_investors = fm.get_regular_investors()
    test_investor = regular_investors[0]
    
    entry_date = datetime(2024, 1, 1)
    success, msg = fm.process_deposit(test_investor.id, 100000000, 100000000, entry_date)
    print(f"✅ {msg}")
    
    # Big growth: NAV to 200M (100% growth in 1 year)
    year_end = datetime(2024, 12, 31)
    success, msg = fm.process_nav_update(200000000, year_end)
    print(f"✅ NAV updated to 200M")
    
    # Calculate expected fee manually
    # Entry: 1000đ, Current: 2000đ, Hurdle: 1060đ
    # Excess: (2000-1060) * 100k units = 94M
    # Fee: 94M * 20% = 18.8M
    
    print(f"\n📊 Expected fee calculation:")
    print(f"  Entry price: 1,000đ")
    print(f"  Current price: 2,000đ") 
    print(f"  Hurdle (6%): 1,060đ")
    print(f"  Excess per unit: 940đ")
    print(f"  Total excess: 94,000,000đ")
    print(f"  Expected fee (20%): 18,800,000đ")
    
    # Test fee calculation
    fee_details = fm.calculate_investor_fee(test_investor.id, year_end, 200000000)
    print(f"\n💰 Actual calculated fee: {format_currency(fee_details['total_fee'])}")
    
    if fee_details['total_fee'] > 0:
        print("✅ Fee calculation working!")
        
        # Apply fees
        success, message = fm.apply_year_end_fees_enhanced(2024, date(2024, 12, 31), 200000000)
        print(f"✅ Applied fees: {message}")
        
        fm.save_data()
        print("💾 Simple test scenario saved")
    else:
        print("❌ Fee calculation still not working")
        
        # Debug the specific issue
        tranches = fm.get_investor_tranches(test_investor.id)
        for tranche in tranches:
            print(f"\nDebug tranche:")
            print(f"  Entry NAV: {tranche.entry_nav}")
            print(f"  HWM: {tranche.hwm}")
            print(f"  Units: {tranche.units}")
            print(f"  Entry date: {tranche.entry_date}")

if __name__ == "__main__":
    manual_fee_application()
    
    print("\n" + "="*60)
    input("Press Enter to test simple scenario...")
    
    create_simple_test_scenario()