#!/usr/bin/env python3
"""
Debug Fee Calculation để tìm hiểu tại sao phí = 0
"""

import sys
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.append(str(Path(__file__).parent))

from services_enhanced import EnhancedFundManager
from utils import format_currency, format_percentage

def debug_fee_calculation():
    """Debug fee calculation step by step"""
    print("🔍 DEBUGGING FEE CALCULATION")
    print("=" * 50)
    
    fm = EnhancedFundManager()
    
    # Get data from current system
    regular_investors = fm.get_regular_investors()
    latest_nav = fm.get_latest_total_nav()
    
    print(f"📊 Latest NAV: {format_currency(latest_nav)}")
    print(f"👥 Regular Investors: {len(regular_investors)}")
    
    # Debug each investor
    for investor in regular_investors:
        print(f"\n🔍 DEBUGGING {investor.display_name}")
        print("-" * 40)
        
        tranches = fm.get_investor_tranches(investor.id)
        print(f"📊 Tranches: {len(tranches)}")
        
        for i, tranche in enumerate(tranches):
            print(f"\n  Tranche {i+1}:")
            print(f"    Entry Date: {tranche.entry_date}")
            print(f"    Entry NAV: {format_currency(tranche.entry_nav)}")
            print(f"    Units: {tranche.units:.6f}")
            print(f"    HWM: {format_currency(tranche.hwm)}")
            print(f"    Original Entry NAV: {format_currency(tranche.original_entry_nav)}")
            
            # Calculate time holding
            ending_date = datetime(2024, 12, 31)  # Year 1 end
            time_delta_days = (ending_date - tranche.entry_date).days
            time_delta_years = time_delta_days / 365.25
            
            print(f"    Time holding: {time_delta_days} days ({time_delta_years:.2f} years)")
            
            # Calculate hurdle
            hurdle_multiplier = (1 + 0.06) ** time_delta_years  # 6% hurdle
            hurdle_price = tranche.entry_nav * hurdle_multiplier
            
            print(f"    Hurdle multiplier: {hurdle_multiplier:.4f}")
            print(f"    Hurdle price: {format_currency(hurdle_price)}")
            
            # Current price
            if latest_nav:
                current_price = fm.calculate_price_per_unit(latest_nav)
                print(f"    Current price: {format_currency(current_price)}")
                
                # Threshold = MAX(hurdle, HWM)
                threshold_price = max(hurdle_price, tranche.hwm)
                print(f"    Threshold (max of hurdle/HWM): {format_currency(threshold_price)}")
                
                # Profit per unit
                profit_per_unit = max(0, current_price - threshold_price)
                print(f"    Profit per unit: {format_currency(profit_per_unit)}")
                
                # Fee calculation
                tranche_excess = profit_per_unit * tranche.units
                tranche_fee = 0.20 * tranche_excess  # 20% fee
                
                print(f"    Excess profit: {format_currency(tranche_excess)}")
                print(f"    Fee (20%): {format_currency(tranche_fee)}")
        
        # Test full fee calculation
        print(f"\n📊 FULL FEE CALCULATION for {investor.display_name}:")
        fee_details = fm.calculate_investor_fee(investor.id, datetime(2024, 12, 31), latest_nav)
        
        for key, value in fee_details.items():
            if key in ['total_fee', 'hurdle_value', 'hwm_value', 'excess_profit', 'invested_value', 'balance', 'profit']:
                print(f"    {key}: {format_currency(value)}")
            else:
                print(f"    {key}: {value}")

def debug_hwm_issue():
    """Debug potential HWM issue"""
    print("\n🔍 DEBUGGING HWM ISSUE")
    print("=" * 50)
    
    fm = EnhancedFundManager()
    
    # Check if HWM is being updated incorrectly
    for investor in fm.get_regular_investors():
        tranches = fm.get_investor_tranches(investor.id)
        
        print(f"\n{investor.display_name} HWM Analysis:")
        for tranche in tranches:
            print(f"  Entry NAV: {format_currency(tranche.entry_nav)}")
            print(f"  HWM: {format_currency(tranche.hwm)}")
            print(f"  Original Entry NAV: {format_currency(tranche.original_entry_nav)}")
            
            if tranche.hwm > tranche.entry_nav * 1.1:  # HWM significantly higher
                print("  ⚠️  HWM significantly higher than entry - may block fees")

def test_manual_fee_calculation():
    """Test manual fee calculation với fixed data"""
    print("\n🔍 MANUAL FEE CALCULATION TEST")
    print("=" * 50)
    
    # Test case: 
    # - Entry: 1000đ, 100k units = 100M invested
    # - Current: 1892đ (from output)
    # - Time: ~1 year
    # - Hurdle: 6% = 1060đ
    # - Expected fee: (1892 - 1060) * 100k * 20% = 16.64M
    
    entry_price = 1000
    current_price = 1892
    units = 100000
    time_years = 1.0
    
    hurdle_price = entry_price * (1.06 ** time_years)
    print(f"Entry price: {format_currency(entry_price)}")
    print(f"Current price: {format_currency(current_price)}")
    print(f"Hurdle price: {format_currency(hurdle_price)}")
    print(f"Units: {units:,.0f}")
    
    # Assume HWM = entry price (no previous fees)
    hwm = entry_price
    threshold = max(hurdle_price, hwm)
    
    print(f"HWM: {format_currency(hwm)}")
    print(f"Threshold: {format_currency(threshold)}")
    
    profit_per_unit = max(0, current_price - threshold)
    excess_profit = profit_per_unit * units
    fee = excess_profit * 0.20
    
    print(f"Profit per unit: {format_currency(profit_per_unit)}")
    print(f"Total excess profit: {format_currency(excess_profit)}")
    print(f"Expected fee (20%): {format_currency(fee)}")
    
    if fee > 0:
        print("✅ Should have significant fees!")
    else:
        print("❌ No fees - something is wrong")

if __name__ == "__main__":
    debug_fee_calculation()
    debug_hwm_issue()
    test_manual_fee_calculation()