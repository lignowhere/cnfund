#!/usr/bin/env python3
"""
Enhanced test script để kiểm tra chức năng Export với debugging chi tiết
Chạy: python enhanced_test_export.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import os
import json
from datetime import datetime
import pandas as pd
from services_enhanced import EnhancedFundManager
import streamlit as st

# Set environment to avoid Streamlit warnings
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'

# Import after setting env
from google_drive_manager import GoogleDriveManager

def test_credentials():
    """Test all credential methods"""
    print("\n🔐 Testing credential sources...")
    
    methods = []
    
    # Method 1: Streamlit secrets (simulate)
    try:
        secrets_file = Path('.streamlit/secrets.toml')
        if secrets_file.exists():
            print("✅ Found .streamlit/secrets.toml")
            methods.append("Streamlit Secrets")
        else:
            print("❌ .streamlit/secrets.toml not found")
    except Exception as e:
        print(f"❌ Streamlit secrets error: {e}")
    
    # Method 2: Environment variable
    try:
        env_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if env_json:
            json.loads(env_json)  # Validate JSON
            print("✅ Found GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
            methods.append("Environment Variable")
        else:
            print("❌ GOOGLE_SERVICE_ACCOUNT_JSON not set")
    except json.JSONDecodeError:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON")
    except Exception as e:
        print(f"❌ Environment variable error: {e}")
    
    # Method 3: Local file
    try:
        service_file = Path('service_account.json')
        if service_file.exists():
            with open(service_file) as f:
                json.load(f)  # Validate JSON
            print("✅ Found service_account.json")
            methods.append("Local File")
        else:
            print("❌ service_account.json not found")
    except json.JSONDecodeError:
        print("❌ service_account.json is not valid JSON")
    except Exception as e:
        print(f"❌ Local file error: {e}")
    
    print(f"📋 Available credential methods: {', '.join(methods) if methods else 'None'}")
    return len(methods) > 0

def test_data_validation():
    """Test data validation before export"""
    print("\n🧪 Testing data validation...")
    
    fund_manager = EnhancedFundManager()
    
    # Check data availability
    checks = {
        "Investors": len(fund_manager.investors),
        "Tranches": len(fund_manager.tranches),
        "Transactions": len(fund_manager.transactions),
        "Fee Records": len(fund_manager.fee_records)
    }
    
    print("📊 Data summary:")
    total_records = 0
    for name, count in checks.items():
        status = "✅" if count > 0 else "⚠️"
        print(f"  {status} {name}: {count} records")
        total_records += count
    
    # Check NAV
    latest_nav = fund_manager.get_latest_total_nav()
    if latest_nav:
        print(f"  ✅ Latest NAV: {latest_nav:,.0f}đ")
        print(f"  ✅ Price per unit: {fund_manager.calculate_price_per_unit(latest_nav):,.0f}đ")
    else:
        print("  ⚠️ No NAV data available")
    
    # Check Fund Manager
    fm = fund_manager.get_fund_manager()
    if fm:
        print(f"  ✅ Fund Manager: {fm.name}")
        fm_tranches = fund_manager.get_investor_tranches(fm.id)
        print(f"  ✅ Fund Manager tranches: {len(fm_tranches)}")
    else:
        print("  ⚠️ Fund Manager not found")
    
    print(f"📈 Total data records: {total_records}")
    return total_records > 0

def test_local_export():
    """Test export to local Excel file with detailed validation"""
    print("\n🧪 Testing local Excel export...")
    
    try:
        # Initialize fund manager
        fund_manager = EnhancedFundManager()
        
        # Create exporter
        gdrive = GoogleDriveManager(fund_manager)
        
        # Export to buffer
        print("📊 Creating Excel buffer...")
        buffer = gdrive.export_to_excel_buffer()
        
        buffer_size = len(buffer.getvalue())
        print(f"✅ Buffer created - Size: {buffer_size:,} bytes")
        
        if buffer_size == 0:
            print("❌ Buffer is empty!")
            return False
        
        # Save locally
        filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        print(f"💾 Saving to: {filename}")
        
        with open(filename, 'wb') as f:
            f.write(buffer.getvalue())
        
        file_size = os.path.getsize(filename)
        print(f"✅ Excel exported - File size: {file_size:,} bytes")
        
        # Read and verify
        print("🔍 Validating Excel content...")
        sheets = pd.read_excel(filename, sheet_name=None)
        print(f"📊 Sheets in Excel: {list(sheets.keys())}")
        
        total_rows = 0
        for sheet_name, df in sheets.items():
            rows, cols = df.shape
            total_rows += rows
            print(f"  - {sheet_name}: {rows} rows, {cols} columns")
            
            # Check for empty sheets
            if rows == 0:
                print(f"    ⚠️ Sheet '{sheet_name}' is empty")
            else:
                # Show first few column names
                col_names = list(df.columns)[:5]
                print(f"    📋 Columns: {', '.join(col_names)}...")
        
        print(f"📈 Total rows across all sheets: {total_rows}")
        
        return True
        
    except Exception as e:
        print(f"❌ Local export failed: {str(e)}")
        import traceback
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

def test_google_drive_connection():
    """Test Google Drive connection with detailed diagnostics"""
    print("\n🧪 Testing Google Drive connection...")
    
    try:
        fund_manager = EnhancedFundManager()
        gdrive = GoogleDriveManager(fund_manager)
        
        if gdrive.connected:
            print("✅ Google Drive connected successfully!")
            print(f"📁 Folder ID: {gdrive.folder_id}")
            
            # Test API calls
            try:
                print("🔍 Testing API access...")
                
                # Get user info
                about = gdrive.service.about().get(fields="user,storageQuota").execute()
                user_info = about.get('user', {})
                storage = about.get('storageQuota', {})
                
                print(f"👤 Connected as: {user_info.get('displayName', 'Unknown')}")
                print(f"📧 Email: {user_info.get('emailAddress', 'Unknown')}")
                
                # Storage info (if available)
                if storage:
                    used = int(storage.get('usage', 0))
                    limit = int(storage.get('limit', 0))
                    if limit > 0:
                        usage_percent = (used / limit) * 100
                        print(f"💾 Storage: {used:,} / {limit:,} bytes ({usage_percent:.1f}%)")
                
                # Test folder access
                print(f"🔍 Testing folder access: {gdrive.folder_id}")
                results = gdrive.service.files().list(
                    q=f"'{gdrive.folder_id}' in parents",
                    fields="files(id, name, createdTime, size)",
                    pageSize=10
                ).execute()
                files = results.get('files', [])
                
                print(f"📂 Files in export folder: {len(files)}")
                for i, file in enumerate(files[:5]):  # Show first 5 files
                    name = file.get('name', 'Unknown')
                    created = file.get('createdTime', 'Unknown')
                    size = file.get('size', 'Unknown')
                    print(f"  {i+1}. {name} ({size} bytes, {created})")
                
                # Test permissions
                try:
                    print("🔍 Testing permissions...")
                    folder_info = gdrive.service.files().get(
                        fileId=gdrive.folder_id,
                        fields="permissions"
                    ).execute()
                    permissions = folder_info.get('permissions', [])
                    print(f"🔐 Folder permissions: {len(permissions)} entries")
                except Exception as perm_error:
                    print(f"⚠️ Could not check permissions: {perm_error}")
                
                return True
                
            except Exception as api_error:
                print(f"❌ API test failed: {str(api_error)}")
                return False
                
        else:
            print("❌ Google Drive connection failed")
            
            # Show error details
            error_log = gdrive.get_error_log()
            if error_log:
                print("🔍 Connection errors:")
                for error in error_log:
                    print(f"  - {error}")
            
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        import traceback
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

def test_full_export_and_upload():
    """Test full export and upload to Google Drive with step-by-step debugging"""
    print("\n🧪 Testing full export and upload...")
    
    try:
        fund_manager = EnhancedFundManager()
        gdrive = GoogleDriveManager(fund_manager)
        
        if not gdrive.connected:
            print("⚠️ Skipping upload test - Google Drive not connected")
            return False
        
        print("🚀 Starting full export process...")
        
        # Step 1: Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Test_Export_{timestamp}.xlsx"
        print(f"📄 Generated filename: {filename}")
        
        # Step 2: Create Excel buffer
        print("📊 Creating Excel buffer...")
        buffer = gdrive.export_to_excel_buffer()
        buffer_size = len(buffer.getvalue())
        print(f"✅ Buffer created: {buffer_size:,} bytes")
        
        if buffer_size == 0:
            print("❌ Buffer is empty!")
            return False
        
        # Step 3: Save local backup
        local_backup_dir = Path("exports")
        local_backup_dir.mkdir(exist_ok=True)
        local_file = local_backup_dir / filename
        
        print(f"💾 Saving local backup: {local_file}")
        with open(local_file, 'wb') as f:
            f.write(buffer.getvalue())
        
        local_size = os.path.getsize(local_file)
        print(f"✅ Local backup saved: {local_size:,} bytes")
        
        # Step 4: Upload to Google Drive
        print("☁️ Uploading to Google Drive...")
        buffer.seek(0)  # Reset buffer position
        
        upload_success = gdrive.upload_to_drive(buffer, filename)
        
        if upload_success:
            print("✅ Upload successful!")
            
            # Verify upload by listing recent files
            print("🔍 Verifying upload...")
            results = gdrive.service.files().list(
                q=f"'{gdrive.folder_id}' in parents and name='{filename}'",
                fields="files(id, name, createdTime, size)"
            ).execute()
            uploaded_files = results.get('files', [])
            
            if uploaded_files:
                uploaded_file = uploaded_files[0]
                print(f"✅ File verified on Google Drive:")
                print(f"  - ID: {uploaded_file.get('id')}")
                print(f"  - Name: {uploaded_file.get('name')}")
                print(f"  - Size: {uploaded_file.get('size', 'Unknown')} bytes")
                print(f"  - Created: {uploaded_file.get('createdTime')}")
            else:
                print("⚠️ Could not verify uploaded file")
            
            return True
        else:
            print("❌ Upload failed")
            
            # Show error details
            error_log = gdrive.get_error_log()
            if error_log:
                print("🔍 Upload errors:")
                for error in error_log[-3:]:  # Show last 3 errors
                    print(f"  - {error}")
            
            return False
            
    except Exception as e:
        print(f"❌ Full export test failed: {str(e)}")
        import traceback
        print(f"📋 Traceback:\n{traceback.format_exc()}")
        return False

def test_export_cleanup():
    """Test export folder cleanup"""
    print("\n🧪 Testing export cleanup...")
    
    exports_dir = Path("exports")
    if not exports_dir.exists():
        print("📁 No exports directory found")
        return True
    
    excel_files = list(exports_dir.glob("*.xlsx"))
    print(f"📊 Found {len(excel_files)} Excel files in exports directory")
    
    if excel_files:
        # Show file details
        for file_path in excel_files[-5:]:  # Show last 5 files
            stat = file_path.stat()
            size = stat.st_size
            modified = datetime.fromtimestamp(stat.st_mtime)
            print(f"  - {file_path.name}: {size:,} bytes, {modified.strftime('%Y-%m-%d %H:%M')}")
        
        # Clean up old test files (keep last 3)
        if len(excel_files) > 3:
            old_files = sorted(excel_files, key=lambda x: x.stat().st_mtime)[:-3]
            print(f"🧹 Cleaning up {len(old_files)} old test files...")
            for old_file in old_files:
                try:
                    old_file.unlink()
                    print(f"  🗑️ Deleted: {old_file.name}")
                except Exception as e:
                    print(f"  ⚠️ Could not delete {old_file.name}: {e}")
    
    return True

def main():
    """Run all tests with enhanced debugging"""
    print("=" * 60)
    print("🚀 Enhanced Fund Management Export Test Suite")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Load secrets from .streamlit/secrets.toml
    try:
        import toml
        secrets = toml.load('.streamlit/secrets.toml')
        if 'default' in secrets and 'drive_folder_id' in secrets['default']:
            os.environ['GOOGLE_DRIVE_FOLDER_ID'] = secrets['default']['drive_folder_id']
            print(f"Set folder ID from secrets: {os.environ['GOOGLE_DRIVE_FOLDER_ID']}")
    except Exception as e:
        print(f"Could not load secrets: {e}")

    tests = [
        ("Credential Sources", test_credentials),
        ("Data Validation", test_data_validation),
        ("Local Export", test_local_export),
        ("Google Drive Connection", test_google_drive_connection),
        ("Full Export & Upload", test_full_export_and_upload),
        ("Export Cleanup", test_export_cleanup)
    ]
    
    results = []
    start_time = datetime.now()
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        test_start = datetime.now()
        
        try:
            success = test_func()
            test_duration = datetime.now() - test_start
            results.append((test_name, success, test_duration.total_seconds()))
            
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"⏱️ {test_name}: {status} ({test_duration.total_seconds():.1f}s)")
            
        except Exception as e:
            test_duration = datetime.now() - test_start
            print(f"❌ {test_name} failed with error: {str(e)}")
            results.append((test_name, False, test_duration.total_seconds()))
            
            # Print full traceback for debugging
            import traceback
            print(f"📋 Full traceback:\n{traceback.format_exc()}")
    
    # Summary
    total_duration = datetime.now() - start_time
    print("\n" + "=" * 60)
    print("📋 Test Summary:")
    print("=" * 60)
    
    for test_name, success, duration in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:<25}: {status:<10} ({duration:.1f}s)")
    
    total_passed = sum(1 for _, success, _ in results if success)
    print(f"\n🎯 Result: {total_passed}/{len(results)} tests passed")
    print(f"⏱️ Total time: {total_duration.total_seconds():.1f} seconds")
    
    if total_passed == len(results):
        print("🎉 All tests passed! Export feature is ready to use.")
    else:
        print("⚠️ Some tests failed. Please check the configuration above.")
        
        # Specific troubleshooting advice
        print("\n🛠️ Troubleshooting Tips:")
        for test_name, success, _ in results:
            if not success:
                if "Credential" in test_name:
                    print("  - Set up Google Service Account credentials")
                    print("  - Check .streamlit/secrets.toml or service_account.json")
                elif "Connection" in test_name:
                    print("  - Verify Google Drive API is enabled")
                    print("  - Check service account permissions")
                elif "Upload" in test_name:
                    print("  - Check Google Drive storage quota")
                    print("  - Verify folder permissions")

if __name__ == "__main__":
    main()