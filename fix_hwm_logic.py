#!/usr/bin/env python3
"""
Fix HWM Logic - HWM chỉ nên update sau khi đã thu phí
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from services_enhanced import EnhancedFundManager
from utils import format_currency

def fix_hwm_logic():
    """Fix HWM logic trong services_enhanced.py"""
    
    print("🔧 FIXING HWM LOGIC")
    print("=" * 50)
    
    fm = EnhancedFundManager()
    
    print("📊 Current HWM values:")
    for investor in fm.get_regular_investors():
        tranches = fm.get_investor_tranches(investor.id)
        for i, tranche in enumerate(tranches):
            print(f"  {investor.name} - Tranche {i+1}:")
            print(f"    Entry NAV: {format_currency(tranche.entry_nav)}")
            print(f"    Original Entry NAV: {format_currency(tranche.original_entry_nav)}")
            print(f"    HWM: {format_currency(tranche.hwm)}")
    
    print("\n🔧 Resetting HWM to original entry NAV...")
    
    # Reset HWM to original entry NAV (correct for fee calculation)
    for tranche in fm.tranches:
        if tranche.investor_id != 0:  # Not fund manager
            tranche.hwm = tranche.original_entry_nav
    
    print("✅ HWM reset completed")
    
    # Test fee calculation now
    latest_nav = fm.get_latest_total_nav()
    
    print(f"\n💰 Testing fee calculation with corrected HWM:")
    total_fees = 0
    
    for investor in fm.get_regular_investors():
        from datetime import datetime
        fee_details = fm.calculate_investor_fee(investor.id, datetime(2024, 12, 31), latest_nav)
        
        print(f"  {investor.name}: {format_currency(fee_details['total_fee'])}")
        total_fees += fee_details['total_fee']
    
    print(f"\n💰 Total expected fees: {format_currency(total_fees)}")
    
    if total_fees > 0:
        print("✅ Fee calculation now working!")
        
        # Apply fees
        from datetime import date
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
                    print(f"🏛️ Fund Manager: {fm_units:.3f} units = {format_currency(fm_value)}")
        
        # Save corrected data
        fm.save_data()
        print("💾 Corrected data saved")
        
        return True
    else:
        print("❌ Still no fees - need to check fee calculation logic")
        return False

if __name__ == "__main__":
    fix_hwm_logic()