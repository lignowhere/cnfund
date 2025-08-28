#!/usr/bin/env python3
"""
CORRECT RECOVERY SCRIPT
Tái tạo tranches với Entry NAV = price per unit (đúng), không phải total NAV
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import uuid

def correct_recovery():
    print("CORRECT TRANCHES RECOVERY")
    print("=" * 50)
    
    data_dir = Path("data")
    
    # Load data
    trans_df = pd.read_csv(data_dir / "transactions.csv")
    trans_df['Date'] = pd.to_datetime(trans_df['Date'])
    trans_df = trans_df.sort_values(['Date', 'ID'])
    
    inv_df = pd.read_csv(data_dir / "investors.csv")
    
    print(f"Loaded {len(trans_df)} transactions, {len(inv_df)} investors")
    
    # State tracking
    fund_state = {
        'tranches': {},  # tranche_id -> tranche_data
        'total_units': 0.0,
        'latest_total_nav': None
    }
    
    final_tranches = []
    tranche_counter = 1
    
    print("\nProcessing transactions chronologically...")
    
    for _, trans in trans_df.iterrows():
        trans_id = trans['ID']
        investor_id = int(trans['InvestorID'])
        trans_type = trans['Type']
        amount = float(trans['Amount'])
        total_nav = float(trans['NAV'])
        date = trans['Date']
        units_change = float(trans.get('UnitsChange', 0))
        
        print(f"\n{date.date()} - ID:{trans_id} - Investor {investor_id} - {trans_type}")
        print(f"  Amount: {amount:,.0f}, Total NAV: {total_nav:,.0f}")
        
        if trans_type == 'Nạp':
            # FIXED: Calculate price per unit correctly
            if fund_state['total_units'] > 0 and fund_state['latest_total_nav']:
                price_per_unit = fund_state['latest_total_nav'] / fund_state['total_units']
            else:
                price_per_unit = 10000.0  # Default first price
            
            units = amount / price_per_unit
            
            tranche_id = f"CORRECT_{tranche_counter:04d}"
            tranche_counter += 1
            
            tranche = {
                'InvestorID': investor_id,
                'TrancheID': tranche_id,
                'EntryDate': date,
                'EntryNAV': price_per_unit,  # CORRECT: Price per unit, not total NAV
                'Units': units,
                'HWM': price_per_unit,
                'OriginalEntryDate': date,
                'OriginalEntryNAV': price_per_unit,
                'CumulativeFeesPaid': 0.0,
                'OriginalInvestedValue': amount,
                'InvestedValue': amount  # Initial invested value
            }
            
            fund_state['tranches'][tranche_id] = tranche
            fund_state['total_units'] += units
            
            print(f"  -> Created tranche: {units:.6f} units @ {price_per_unit:,.0f} VND/unit")
            print(f"  -> Total fund units: {fund_state['total_units']:.6f}")
        
        # Update latest NAV for price calculations
        fund_state['latest_total_nav'] = total_nav

        if trans_type == 'Rút':
            # Withdraw: reduce units proportionally
            withdrawal_amount = abs(amount)
            
            if fund_state['latest_total_nav']:
                current_price = fund_state['latest_total_nav'] / fund_state['total_units'] if fund_state['total_units'] > 0 else 10000
            else:
                current_price = total_nav / fund_state['total_units'] if fund_state['total_units'] > 0 else 10000
            
            units_to_remove = withdrawal_amount / current_price
            
            # Apply proportional reduction
            investor_tranches = [(tid, t) for tid, t in fund_state['tranches'].items() if t['InvestorID'] == investor_id]
            investor_units = sum(t['Units'] for _, t in investor_tranches)
            
            if investor_units > 0:
                for tranche_id, tranche in investor_tranches:
                    proportion = tranche['Units'] / investor_units
                    reduction = units_to_remove * proportion
                    
                    tranche['Units'] = max(0, tranche['Units'] - reduction)
                    tranche['InvestedValue'] = tranche['Units'] * tranche['EntryNAV']
                
                fund_state['total_units'] = max(0, fund_state['total_units'] - units_to_remove)
                print(f"  -> Reduced {units_to_remove:.6f} units from investor {investor_id}")
        
        elif trans_type == 'Phí':
            # Fee: similar to withdrawal
            fee_amount = abs(amount)
            
            if fund_state['latest_total_nav']:
                current_price = fund_state['latest_total_nav'] / fund_state['total_units'] if fund_state['total_units'] > 0 else 10000
            else:
                current_price = total_nav / fund_state['total_units'] if fund_state['total_units'] > 0 else 10000
            
            fee_units = fee_amount / current_price
            
            investor_tranches = [(tid, t) for tid, t in fund_state['tranches'].items() if t['InvestorID'] == investor_id]
            investor_units = sum(t['Units'] for _, t in investor_tranches)
            
            if investor_units > 0:
                for tranche_id, tranche in investor_tranches:
                    proportion = tranche['Units'] / investor_units
                    reduction = fee_units * proportion
                    
                    tranche['Units'] = max(0, tranche['Units'] - reduction)
                    tranche['CumulativeFeesPaid'] += (reduction * current_price)
                    tranche['InvestedValue'] = tranche['Units'] * tranche['EntryNAV']
                
                fund_state['total_units'] = max(0, fund_state['total_units'] - fee_units)
                print(f"  -> Applied fee: {fee_units:.6f} units from investor {investor_id}")
        
        elif trans_type == 'NAV Update':
            # Update total NAV and HWM
            fund_state['latest_total_nav'] = total_nav
            
            if fund_state['total_units'] > 0:
                new_price = total_nav / fund_state['total_units']
                
                # Update HWM for all tranches if new price is higher
                for tranche_id, tranche in fund_state['tranches'].items():
                    if new_price > tranche['HWM']:
                        old_hwm = tranche['HWM']
                        tranche['HWM'] = new_price
                        print(f"    Updated HWM for {tranche_id}: {old_hwm:,.0f} -> {new_price:,.0f}")
                
                print(f"  -> Updated NAV: {total_nav:,.0f} -> Price: {new_price:,.2f} VND/unit")
            else:
                print(f"  -> Updated NAV: {total_nav:,.0f} (no units to price)")
    
    # Collect final tranches (only those with units > 0)
    for tranche_id, tranche in fund_state['tranches'].items():
        if tranche['Units'] > 0.000001:
            final_tranches.append(tranche)
    
    print(f"\nFINAL RESULTS:")
    print(f"Total tranches: {len(final_tranches)}")
    print(f"Total units: {fund_state['total_units']:.6f}")
    
    if fund_state['latest_total_nav']:
        final_price = fund_state['latest_total_nav'] / fund_state['total_units'] if fund_state['total_units'] > 0 else 0
        print(f"Final NAV: {fund_state['latest_total_nav']:,.0f}")
        print(f"Final price per unit: {final_price:,.2f}")
    
    # Show per-investor summary
    print(f"\nPER-INVESTOR BREAKDOWN:")
    for investor_id in inv_df['ID']:
        if investor_id == 0:  # Skip fund manager
            continue
            
        investor_name = inv_df[inv_df['ID'] == investor_id]['Name'].iloc[0]
        investor_tranches = [t for t in final_tranches if t['InvestorID'] == investor_id]
        
        if investor_tranches:
            total_units = sum(t['Units'] for t in investor_tranches)
            total_invested = sum(t['InvestedValue'] for t in investor_tranches)
            total_original = sum(t['OriginalInvestedValue'] for t in investor_tranches)
            
            if fund_state['latest_total_nav'] and fund_state['total_units'] > 0:
                current_price = fund_state['latest_total_nav'] / fund_state['total_units']
                current_balance = total_units * current_price
                profit = current_balance - total_invested
            else:
                current_balance = profit = 0
            
            print(f"\n  {investor_name} (ID: {investor_id}):")
            print(f"    Tranches: {len(investor_tranches)}")
            print(f"    Units: {total_units:.6f}")
            print(f"    Original Investment: {total_original:,.0f}")
            print(f"    Current Invested Value: {total_invested:,.0f}")
            print(f"    Current Balance: {current_balance:,.0f}")
            print(f"    Profit: {profit:,.0f}")
            
            # Show tranche details
            for t in investor_tranches:
                print(f"      {t['TrancheID']}: {t['Units']:.6f} units @ {t['EntryNAV']:,.2f}/unit (HWM: {t['HWM']:,.2f})")
    
    # Save corrected tranches
    if final_tranches:
        df = pd.DataFrame(final_tranches)
        
        # Backup existing file first
        existing_file = data_dir / "tranches.csv"
        if existing_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = data_dir / f"tranches_broken_{timestamp}.csv"
            existing_file.rename(backup_path)
            print(f"\nBacked up broken tranches to: {backup_path.name}")
        
        # Save corrected data
        df.to_csv(existing_file, index=False)
        print(f"\nSAVED CORRECTED TRANCHES: {len(final_tranches)} records")
        
        # Quick validation
        print(f"\nQUICK VALIDATION:")
        print(f"  Entry NAV range: {df['EntryNAV'].min():,.2f} - {df['EntryNAV'].max():,.2f}")
        print(f"  HWM range: {df['HWM'].min():,.2f} - {df['HWM'].max():,.2f}")
        print(f"  Units range: {df['Units'].min():.6f} - {df['Units'].max():.6f}")
        
        # Check if values look reasonable now
        if df['EntryNAV'].max() < 1_000_000:  # Less than 1M per unit
            print("  ✅ Entry NAV values look reasonable now")
        else:
            print("  ⚠️  Entry NAV values still too high")
        
        return True
    else:
        print("\nERROR: No tranches to save")
        return False

if __name__ == "__main__":
    if not Path("data").exists():
        print("ERROR: data/ directory not found")
        exit(1)
    
    success = correct_recovery()
    
    if success:
        print("\n" + "="*50)
        print("RECOVERY COMPLETED!")
        print("NEXT STEPS:")
        print("1. Restart Streamlit app: streamlit run app.py")
        print("2. Check Reports page to verify correct balances")
        print("3. Test fee calculation - should now show proper fees")
        print("="*50)
    else:
        print("\nRECOVERY FAILED!")
    
    exit(0 if success else 1)