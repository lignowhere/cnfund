#!/usr/bin/env python3
"""
Migration Script cho Enhanced Fund Management System
Nâng cấp dữ liệu từ version cũ sang version mới với fund manager tracking
"""

import pandas as pd
from pathlib import Path
from datetime import date, datetime
import shutil
import sys

def create_migration_backup():
    """Tạo backup trước khi migration"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("data/migration_backup_" + timestamp)
        backup_dir.mkdir(exist_ok=True)
        
        data_dir = Path("data")
        csv_files = ["investors.csv", "tranches.csv", "transactions.csv"]
        
        for file_name in csv_files:
            file_path = data_dir / file_name
            if file_path.exists():
                shutil.copy2(file_path, backup_dir / file_name)
                print(f"✅ Backed up {file_name}")
            else:
                print(f"⚠️  {file_name} not found")
        
        print(f"🗂️  Backup created at: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return None

def migrate_investors():
    """Migrate investors.csv để thêm IsFundManager column"""
    try:
        investors_file = Path("data/investors.csv")
        
        if not investors_file.exists():
            print("⚠️  investors.csv not found, creating new file")
            # Tạo file mới với fund manager
            df_new = pd.DataFrame({
                'ID': [0],
                'Name': ['Fund Manager'],
                'Phone': [''],
                'Address': [''],
                'Email': [''],
                'JoinDate': [date.today()],
                'IsFundManager': [True]
            })
            df_new.to_csv(investors_file, index=False)
            print("✅ Created new investors.csv with Fund Manager")
            return True
        
        # Load existing data
        df = pd.read_csv(investors_file, dtype={'Phone': 'str'})
        
        # Check if IsFundManager column exists
        if 'IsFundManager' not in df.columns:
            df['IsFundManager'] = False
            print("✅ Added IsFundManager column")
        
        # Check if Fund Manager exists (ID = 0)
        if not (df['ID'] == 0).any():
            # Add Fund Manager at the beginning
            fund_manager = pd.DataFrame({
                'ID': [0],
                'Name': ['Fund Manager'],
                'Phone': [''],
                'Address': [''],
                'Email': [''],
                'JoinDate': [date.today()],
                'IsFundManager': [True]
            })
            
            # Shift existing IDs up by 1 if needed to avoid conflicts
            if (df['ID'] == 0).any():
                df['ID'] = df['ID'] + 1
                print("⚠️  Shifted existing investor IDs to avoid conflict with Fund Manager")
            
            df = pd.concat([fund_manager, df], ignore_index=True)
            print("✅ Added Fund Manager (ID=0)")
        else:
            # Update existing ID=0 to be fund manager
            df.loc[df['ID'] == 0, 'IsFundManager'] = True
            print("✅ Updated existing ID=0 as Fund Manager")
        
        # Save updated file
        df.to_csv(investors_file, index=False)
        print(f"💾 Updated investors.csv with {len(df)} records")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating investors: {str(e)}")
        return False

def migrate_tranches():
    """Migrate tranches.csv để thêm new fields"""
    try:
        tranches_file = Path("data/tranches.csv")
        
        if not tranches_file.exists():
            print("⚠️  tranches.csv not found, creating empty file")
            df_new = pd.DataFrame(columns=[
                'InvestorID', 'TrancheID', 'EntryDate', 'EntryNAV', 'Units', 'HWM',
                'OriginalEntryDate', 'OriginalEntryNAV', 'CumulativeFeesPaid'
            ])
            df_new.to_csv(tranches_file, index=False)
            print("✅ Created new tranches.csv")
            return True
        
        # Load existing data
        df = pd.read_csv(tranches_file)
        
        if df.empty:
            print("📝 tranches.csv is empty, adding new columns")
            df = pd.DataFrame(columns=[
                'InvestorID', 'TrancheID', 'EntryDate', 'EntryNAV', 'Units', 'HWM',
                'OriginalEntryDate', 'OriginalEntryNAV', 'CumulativeFeesPaid'
            ])
        else:
            # Add missing columns
            if 'HWM' not in df.columns:
                df['HWM'] = df['EntryNAV']
                print("✅ Added HWM column")
            
            if 'OriginalEntryDate' not in df.columns:
                df['OriginalEntryDate'] = df['EntryDate']
                print("✅ Added OriginalEntryDate column")
            
            if 'OriginalEntryNAV' not in df.columns:
                df['OriginalEntryNAV'] = df['EntryNAV']
                print("✅ Added OriginalEntryNAV column")
            
            if 'CumulativeFeesPaid' not in df.columns:
                df['CumulativeFeesPaid'] = 0.0
                print("✅ Added CumulativeFeesPaid column")
        
        # Save updated file
        df.to_csv(tranches_file, index=False)
        print(f"💾 Updated tranches.csv with {len(df)} records")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating tranches: {str(e)}")
        return False

def create_fee_records_file():
    """Tạo fee_records.csv file"""
    try:
        fee_records_file = Path("data/fee_records.csv")
        
        if fee_records_file.exists():
            print("ℹ️  fee_records.csv already exists")
            return True
        
        # Create empty fee records file
        df_new = pd.DataFrame(columns=[
            'ID', 'Period', 'InvestorID', 'FeeAmount', 'FeeUnits',
            'CalculationDate', 'UnitsBefore', 'UnitsAfter', 'NAVPerUnit', 'Description'
        ])
        df_new.to_csv(fee_records_file, index=False)
        print("✅ Created fee_records.csv")
        return True
        
    except Exception as e:
        print(f"❌ Error creating fee_records.csv: {str(e)}")
        return False

def verify_migration():
    """Verify migration was successful"""
    try:
        print("\n🔍 Verifying migration...")
        
        # Check investors.csv
        investors_file = Path("data/investors.csv")
        if investors_file.exists():
            df_inv = pd.read_csv(investors_file)
            fund_manager_exists = (df_inv['ID'] == 0).any()
            has_fund_manager_column = 'IsFundManager' in df_inv.columns
            
            print(f"👥 Investors: {len(df_inv)} records")
            print(f"🏛️  Fund Manager exists: {'✅' if fund_manager_exists else '❌'}")
            print(f"🏛️  IsFundManager column: {'✅' if has_fund_manager_column else '❌'}")
        else:
            print("❌ investors.csv not found")
            return False
        
        # Check tranches.csv
        tranches_file = Path("data/tranches.csv")
        if tranches_file.exists():
            df_tranches = pd.read_csv(tranches_file)
            required_columns = ['OriginalEntryDate', 'OriginalEntryNAV', 'CumulativeFeesPaid']
            missing_columns = [col for col in required_columns if col not in df_tranches.columns]
            
            print(f"📊 Tranches: {len(df_tranches)} records")
            print(f"📊 New columns: {'✅' if not missing_columns else '❌ Missing: ' + str(missing_columns)}")
        else:
            print("✅ tranches.csv created (empty)")
        
        # Check fee_records.csv
        fee_records_file = Path("data/fee_records.csv")
        if fee_records_file.exists():
            df_fee = pd.read_csv(fee_records_file)
            print(f"💰 Fee records: {len(df_fee)} records")
            print("✅ fee_records.csv exists")
        else:
            print("❌ fee_records.csv not found")
            return False
        
        print("\n🎉 Migration verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying migration: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting Enhanced Fund Management System Migration")
    print("=" * 60)
    
    # Step 1: Create backup
    print("\n📦 Step 1: Creating backup...")
    backup_dir = create_migration_backup()
    if not backup_dir:
        print("❌ Backup failed, aborting migration")
        return False
    
    # Step 2: Migrate investors
    print("\n👥 Step 2: Migrating investors...")
    if not migrate_investors():
        print("❌ Investor migration failed")
        return False
    
    # Step 3: Migrate tranches
    print("\n📊 Step 3: Migrating tranches...")
    if not migrate_tranches():
        print("❌ Tranche migration failed")
        return False
    
    # Step 4: Create fee records file
    print("\n💰 Step 4: Creating fee records file...")
    if not create_fee_records_file():
        print("❌ Fee records file creation failed")
        return False
    
    # Step 5: Verify migration
    print("\n🔍 Step 5: Verifying migration...")
    if not verify_migration():
        print("❌ Migration verification failed")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print(f"📁 Backup available at: {backup_dir}")
    print("\n📋 Next steps:")
    print("1. Update your app.py to use EnhancedFundManager")
    print("2. Test the enhanced features")
    print("3. Verify all data is correct before proceeding")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)