#!/usr/bin/env python3
"""
Updated Backup Management Dashboard Page
Support for both Drive-backed and CSV storage systems
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.auth_helper import is_admin_authenticated, show_admin_status

# Import new backup system
try:
    from integrations.auto_backup_personal import get_auto_backup_manager, manual_backup
    AUTO_BACKUP_AVAILABLE = True
except ImportError:
    AUTO_BACKUP_AVAILABLE = False

def show_backup_status_cards():
    """Display backup status cards using PersonalAutoBackupManager"""
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Auto backup system not available")
        return
    
    # Get fund manager from session state
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund manager not initialized")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    status = backup_manager.get_backup_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🏠 Service Status",
            value="Running" if status['service_running'] else "Stopped",
            delta="Active" if status['service_running'] else "Inactive"
        )
    
    with col2:
        st.metric(
            label="💾 Local Backups",
            value=status['local_backups']['count'],
            delta=f"{status['local_backups']['total_size_mb']:.1f} MB"
        )
    
    with col3:
        cloud_count = status['cloud_backup'].get('files', 0) if status['cloud_backup']['connected'] else 0
        st.metric(
            label="☁️ Cloud Backups", 
            value=cloud_count,
            delta="Connected" if status['cloud_backup']['connected'] else "Not connected"
        )
    
    with col4:
        st.metric(
            label="📊 Today's Backups",
            value=f"{status['backups_today']}/5",
            delta="Daily limit"
        )

def handle_restore_from_backup(backup_file_path, filename):
    """Handle restore operation from backup Excel file"""
    try:
        if 'fund_manager' not in st.session_state:
            st.error("❌ Fund manager not initialized")
            return
        
        # Confirmation dialog with backup info
        st.warning(f"⚠️ Bạn có chắc chắn muốn restore từ backup: **{filename}**?")
        st.warning("🔴 **CHÚ Ý**: Thao tác này sẽ ghi đè toàn bộ dữ liệu hiện tại!")
        
        # Show preview of backup content
        try:
            import pandas as pd
            excel_data = pd.read_excel(backup_file_path, sheet_name=None)
            
            st.info("📋 **Nội dung backup sẽ được restore:**")
            backup_info = []
            for sheet_name, sheet_data in excel_data.items():
                if sheet_name in ['Investors', 'Tranches', 'Transactions', 'Fee_Records']:
                    backup_info.append(f"- **{sheet_name}**: {len(sheet_data)} records")
            
            if backup_info:
                for info in backup_info:
                    st.markdown(info)
        except Exception as e:
            st.warning(f"⚠️ Không thể preview backup: {str(e)}")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Xác nhận Restore", key="confirm_restore", type="primary"):
                with st.spinner(f"🔄 Đang restore từ {filename}..."):
                    # Create safety backup first
                    try:
                        safety_backup_success = False
                        if AUTO_BACKUP_AVAILABLE:
                            from integrations.auto_backup_personal import manual_backup
                            safety_backup_success = manual_backup(st.session_state.fund_manager, "pre_restore_safety")
                            if safety_backup_success:
                                st.info("✅ Đã tạo safety backup trước khi restore")
                    except:
                        pass  # Continue even if safety backup fails
                    # Read Excel backup file
                    import pandas as pd
                    
                    # Read all sheets from backup
                    excel_data = pd.read_excel(backup_file_path, sheet_name=None)
                    
                    success_count = 0
                    errors = []
                    
                    # Restore investors
                    if 'Investors' in excel_data:
                        try:
                            investors_df = excel_data['Investors']
                            # Convert back to CSV format and save
                            investors_df.to_csv('data/investors.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Investors: {str(e)}")
                    
                    # Restore tranches  
                    if 'Tranches' in excel_data:
                        try:
                            tranches_df = excel_data['Tranches']
                            tranches_df.to_csv('data/tranches.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Tranches: {str(e)}")
                    
                    # Restore transactions
                    if 'Transactions' in excel_data:
                        try:
                            transactions_df = excel_data['Transactions']
                            transactions_df.to_csv('data/transactions.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Transactions: {str(e)}")
                    
                    # Restore fee records
                    if 'Fee_Records' in excel_data:
                        try:
                            fees_df = excel_data['Fee_Records']
                            fees_df.to_csv('data/fee_records.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Fee Records: {str(e)}")
                    
                    # Reload fund manager data
                    st.session_state.fund_manager.load_data()
                    
                    # Show results
                    if success_count > 0:
                        st.success(f"✅ Restore thành công {success_count} bảng dữ liệu!")
                        st.balloons()
                        if errors:
                            st.warning(f"⚠️ Có {len(errors)} lỗi:")
                            for error in errors:
                                st.error(f"  - {error}")
                        
                        # Auto-refresh after 2 seconds
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Không thể restore dữ liệu")
                        for error in errors:
                            st.error(f"  - {error}")
        
        with col2:
            if st.button("❌ Hủy bỏ", key="cancel_restore"):
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Lỗi restore: {str(e)}")

def show_backup_history():
    """Show backup history from local exports folder with restore functionality"""
    st.subheader("📊 Backup History")
    
    # Warning about restore
    with st.expander("⚠️ Hướng dẫn Restore"):
        st.warning("🔴 **CHÚ Ý quan trọng về Restore:**")
        st.markdown("""
        - **Restore sẽ ghi đè toàn bộ dữ liệu hiện tại**
        - Nên tạo backup hiện tại trước khi restore
        - Restore chỉ áp dụng cho file Excel backup
        - Sau restore, hệ thống sẽ tự động reload data
        """)
    
    export_dir = Path("exports")
    if not export_dir.exists():
        st.info("📁 No backup directory found")
        return
    
    # Get all backup files
    backup_files = list(export_dir.glob("Fund_Export_*.xlsx"))
    
    if not backup_files:
        st.info("📁 No backup files found")
        return
    
    # Create backup history data
    backup_data = []
    for file_path in backup_files:
        try:
            stats = file_path.stat()
            backup_data.append({
                'Filename': file_path.name,
                'Date': datetime.fromtimestamp(stats.st_mtime),
                'Size (KB)': round(stats.st_size / 1024, 1),
                'Type': 'Auto' if 'auto_' in file_path.name else 'Manual',
                'Path': str(file_path)
            })
        except Exception as e:
            st.warning(f"⚠️ Could not read {file_path.name}: {e}")
    
    if not backup_data:
        st.info("📁 No readable backup files found")
        return
    
    # Sort by date (newest first)
    backup_data.sort(key=lambda x: x['Date'], reverse=True)
    
    # Show as dataframe
    df = pd.DataFrame(backup_data)
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Display table with restore buttons
    display_df = df.drop('Path', axis=1).copy()
    
    # Add restore column with better formatting
    st.markdown("**Danh sách Backup Files (nhấn 🔄 để restore):**")
    
    for i, row in enumerate(backup_data):
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                # Format the display with better styling
                file_date = row['Date'].strftime('%Y-%m-%d %H:%M')
                file_size_mb = row['Size (KB)'] / 1024
                type_emoji = "🤖" if row['Type'] == 'Auto' else "👤"
                
                st.markdown(f"""
                **{row['Filename']}**  
                📅 {file_date} | 📦 {file_size_mb:.1f} MB | {type_emoji} {row['Type']}
                """)
            with col2:
                if st.button(f"🔄", key=f"restore_{i}", help=f"Restore từ backup: {row['Filename']}", type="secondary"):
                    handle_restore_from_backup(row['Path'], row['Filename'])
            
            st.divider()
    
    # Show total stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Files", len(backup_data))
    with col2:
        total_size = sum(item['Size (KB)'] for item in backup_data)
        st.metric("Total Size", f"{total_size/1024:.1f} MB")
    with col3:
        if backup_data:
            # Use original datetime objects from backup_data, not the string-converted ones
            latest = max(backup_data, key=lambda x: x['Date'])
            st.metric("Latest Backup", latest['Date'].strftime('%Y-%m-%d'))

def show_cloud_backup_status():
    """Show cloud backup status and details"""
    st.subheader("☁️ Cloud Backup Status")
    
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Auto backup system not available")
        return
    
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund manager not initialized")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    status = backup_manager.get_backup_status()
    
    cloud_info = status['cloud_backup']
    
    if cloud_info['connected']:
        st.success("✅ Cloud backup connected")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"👤 Account: {cloud_info.get('account', 'Unknown')}")
            st.info(f"🔐 Method: {cloud_info.get('method', 'Unknown')}")
        
        with col2:
            st.info(f"📄 Files in Drive: {cloud_info.get('files', 0)}")
            st.info("📁 Storage: 15GB free (personal account)")
        
        # Test connection button
        if st.button("🧪 Test Connection", help="Test Google Drive connection"):
            try:
                drive_manager = backup_manager.drive_manager
                if drive_manager:
                    test_result = drive_manager.test_connection()
                    if test_result.get('connected'):
                        st.success(f"✅ Connection successful! Files: {test_result.get('files_count', 0)}")
                    else:
                        st.error("❌ Connection test failed")
                        for error in test_result.get('errors', []):
                            st.error(f"   - {error}")
                else:
                    st.warning("⚠️ Drive manager not available")
            except Exception as e:
                st.error(f"❌ Test failed: {e}")
    else:
        st.warning("⚠️ Cloud backup not connected")
        if 'error' in cloud_info:
            st.error(f"Error: {cloud_info['error']}")
        
        st.info("💡 To enable cloud backup:")
        st.markdown("""
        1. Follow setup in `SETUP_OAUTH_PERSONAL.md`
        2. Create OAuth credentials
        3. Restart the app
        """)

def show_backup_controls():
    """Show backup control buttons and settings"""
    st.subheader("🎮 Backup Controls")
    
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Auto backup system not available")
        return
    
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund manager not initialized")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Create Backup Now", type="primary", help="Create manual backup"):
            with st.spinner("Creating backup..."):
                success = manual_backup(fund_manager, "dashboard_manual")
            
            if success:
                st.success("✅ Backup created successfully!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Backup creation failed")
    
    with col2:
        if st.button("🔄 Refresh Status", help="Refresh backup status"):
            st.rerun()
    
    with col3:
        if st.button("🧹 Clean Old Backups", help="Remove old local backups (keep 10 newest)"):
            try:
                export_dir = Path("exports")
                if export_dir.exists():
                    backup_files = list(export_dir.glob("Fund_Export_*.xlsx"))
                    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    if len(backup_files) > 10:
                        files_to_delete = backup_files[10:]
                        deleted_count = 0
                        
                        for file_path in files_to_delete:
                            try:
                                file_path.unlink()
                                deleted_count += 1
                            except Exception as e:
                                st.warning(f"Could not delete {file_path.name}: {e}")
                        
                        st.success(f"🧹 Cleaned up {deleted_count} old backup files")
                        st.rerun()
                    else:
                        st.info("✅ No cleanup needed (≤10 files)")
                else:
                    st.warning("📁 No backup directory found")
                    
            except Exception as e:
                st.error(f"❌ Cleanup failed: {e}")

def show_backup_settings():
    """Show backup system settings"""
    st.subheader("⚙️ Backup Settings")
    
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Auto backup system not available")
        return
    
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund manager not initialized")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    
    # Show current configuration
    st.json({
        "Local Backup": "Always enabled",
        "Cloud Backup": "OAuth-based (personal account)",
        "Daily Schedule": "23:00 (11 PM)",
        "Max Daily Backups": "5 backups",
        "Backup Interval": "6 hours minimum",
        "Local Retention": "20 newest files",
        "Storage Cost": "$0/month (personal Google Drive)"
    })
    
    # Show backup statistics
    status = backup_manager.get_backup_status()
    
    st.subheader("📊 Statistics")
    stats_data = {
        "Total Backups Created": status['stats']['total_backups'],
        "Successful Local": status['stats']['successful_local'],
        "Successful Cloud": status['stats']['successful_cloud'],
        "Failed Backups": status['stats']['failed_backups'],
        "Service Uptime": "Running" if status['service_running'] else "Stopped"
    }
    
    if status['stats']['last_error']:
        stats_data["Last Error"] = status['stats']['last_error']

    st.json(stats_data)

def show_drive_backup_controls():
    """Show manual backup controls for Drive-backed storage"""
    st.subheader("☁️ Google Drive Backup Controls")

    # Check if using Drive handler
    if 'fund_manager' not in st.session_state:
        st.info("ℹ️ Fund manager chưa được khởi tạo")
        return

    fund_manager = st.session_state.fund_manager
    data_handler = fund_manager.data_handler

    # Check if it's Drive handler
    is_drive_handler = type(data_handler).__name__ == 'DriveBackedDataManager'

    if not is_drive_handler:
        st.info("ℹ️ Đang sử dụng CSV local storage - không cần Drive backup")
        return

    # Show Drive connection status
    col1, col2, col3 = st.columns(3)

    with col1:
        if data_handler.connected:
            st.success("✅ Google Drive đã kết nối")
        else:
            st.error("❌ Google Drive chưa kết nối")

    with col2:
        if f'{data_handler.session_key_prefix}last_backup' in st.session_state:
            last_backup = st.session_state[f'{data_handler.session_key_prefix}last_backup']
            time_ago = datetime.now() - last_backup
            minutes_ago = int(time_ago.total_seconds() / 60)
            st.metric("Backup cuối", f"{minutes_ago} phút trước")
        else:
            st.metric("Backup cuối", "Chưa có")

    with col3:
        if f'{data_handler.session_key_prefix}last_load' in st.session_state:
            last_load = st.session_state[f'{data_handler.session_key_prefix}last_load']
            time_ago = datetime.now() - last_load
            minutes_ago = int(time_ago.total_seconds() / 60)
            st.metric("Load cuối", f"{minutes_ago} phút trước")
        else:
            st.metric("Load cuối", "Chưa có")

    st.divider()

    # Manual backup button
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Backup Ngay", type="primary", key="manual_drive_backup", use_container_width=True):
            if data_handler.connected:
                success = data_handler.backup_to_drive()
                if success:
                    st.success("✅ Backup thành công!")
                    st.balloons()
                else:
                    st.error("❌ Backup thất bại")
            else:
                st.error("❌ Google Drive chưa kết nối")

    with col2:
        if st.button("🔄 Reload từ Drive", key="reload_from_drive", use_container_width=True):
            if data_handler.connected:
                with st.spinner("📥 Đang tải dữ liệu từ Drive..."):
                    success = data_handler.load_from_drive()
                    if success:
                        # Reload fund manager
                        fund_manager.load_data()
                        st.success("✅ Đã reload dữ liệu!")
                        st.rerun()
                    else:
                        st.error("❌ Reload thất bại")
            else:
                st.error("❌ Google Drive chưa kết nối")

def main():
    """Main backup dashboard function"""
    st.set_page_config(
        page_title="Backup Management",
        page_icon="💾",
        layout="wide"
    )
    
    st.title("💾 Backup Management Dashboard")

    # Check authentication (but don't require it since auth is disabled)
    if is_admin_authenticated():
        show_admin_status()
    else:
        st.success("🏠 Local System - Full Access Enabled")

    # Drive backup controls (for cloud deployment)
    show_drive_backup_controls()

    st.divider()

    # Main backup dashboard
    if AUTO_BACKUP_AVAILABLE:
        # Status cards
        show_backup_status_cards()

        st.divider()

        # Controls
        show_backup_controls()
        
        st.divider()
        
        # Two column layout for details
        col1, col2 = st.columns(2)
        
        with col1:
            show_backup_history()
        
        with col2:
            show_cloud_backup_status()
        
        st.divider()
        
        # Settings
        show_backup_settings()
        
    else:
        st.error("🚫 Auto backup system not available")
        st.info("💡 Make sure auto_backup_personal.py is properly installed")
        
        # Show debug info
        with st.expander("🔍 Debug Information"):
            if 'fund_manager' in st.session_state:
                fm = st.session_state.fund_manager
                st.json({
                    "Fund Manager Type": type(fm).__name__,
                    "Has backup_manager": hasattr(fm, 'backup_manager'),
                    "backup_manager value": str(getattr(fm, 'backup_manager', None)) if hasattr(fm, 'backup_manager') else "N/A",
                    "Data Handler Type": type(fm.data_handler).__name__,
                    "Auto Backup Available": AUTO_BACKUP_AVAILABLE,
                    "Backup System": "PersonalAutoBackupManager (integrated via app.py)"
                })
            else:
                st.warning("Fund manager not in session state")

if __name__ == "__main__":
    main()