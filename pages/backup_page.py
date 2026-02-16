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
        st.error("🚫 Hệ thống sao lưu tự động không khả dụng")
        return
    
    # Get fund manager from session state
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund Manager chưa được khởi tạo")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    status = backup_manager.get_backup_status()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🏠 Trạng thái dịch vụ",
            value="Đang chạy" if status['service_running'] else "Đã dừng",
            delta="Hoạt động" if status['service_running'] else "Không hoạt động"
        )
    
    with col2:
        st.metric(
            label="💾 Sao lưu cục bộ",
            value=status['local_backups']['count'],
            delta=f"{status['local_backups']['total_size_mb']:.1f} MB"
        )
    
    with col3:
        cloud_count = status['cloud_backup'].get('files', 0) if status['cloud_backup']['connected'] else 0
        st.metric(
            label="☁️ Sao lưu đám mây", 
            value=cloud_count,
            delta="Đã kết nối" if status['cloud_backup']['connected'] else "Chưa kết nối"
        )
    
    with col4:
        st.metric(
            label="📊 Sao lưu hôm nay",
            value=f"{status['backups_today']}/5",
            delta="Giới hạn ngày"
        )

def handle_restore_from_backup(backup_file_path, filename):
    """Handle restore operation from backup Excel file"""
    try:
        if 'fund_manager' not in st.session_state:
            st.error("❌ Fund Manager chưa được khởi tạo")
            return
        
        # Confirmation dialog with backup info
        st.warning(f"⚠️ Bạn có chắc chắn muốn khôi phục từ bản sao lưu: **{filename}**?")
        st.warning("🔴 **CHÚ Ý**: Thao tác này sẽ ghi đè toàn bộ dữ liệu hiện tại!")
        
        # Show preview of backup content
        try:
            import pandas as pd
            excel_data = pd.read_excel(backup_file_path, sheet_name=None)
            
            st.info("📋 **Nội dung sao lưu sẽ được khôi phục:**")
            backup_info = []
            for sheet_name, sheet_data in excel_data.items():
                if sheet_name in ['Investors', 'Tranches', 'Transactions', 'Fee_Records']:
                    backup_info.append(f"- **{sheet_name}**: {len(sheet_data)} bản ghi")
            
            if backup_info:
                for info in backup_info:
                    st.markdown(info)
        except Exception as e:
            st.warning(f"⚠️ Không thể xem trước bản sao lưu: {str(e)}")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Xác nhận khôi phục", key="confirm_restore", type="primary"):
                with st.spinner(f"🔄 Đang khôi phục từ {filename}..."):
                    # Create safety backup first
                    try:
                        safety_backup_success = False
                        if AUTO_BACKUP_AVAILABLE:
                            from integrations.auto_backup_personal import manual_backup
                            safety_backup_success = manual_backup(st.session_state.fund_manager, "pre_restore_safety")
                            if safety_backup_success:
                                st.info("✅ Đã tạo bản sao lưu an toàn trước khi khôi phục")
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
                            errors.append(f"Nhà đầu tư: {str(e)}")
                    
                    # Restore tranches  
                    if 'Tranches' in excel_data:
                        try:
                            tranches_df = excel_data['Tranches']
                            tranches_df.to_csv('data/tranches.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Đợt vốn: {str(e)}")
                    
                    # Restore transactions
                    if 'Transactions' in excel_data:
                        try:
                            transactions_df = excel_data['Transactions']
                            transactions_df.to_csv('data/transactions.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Giao dịch: {str(e)}")
                    
                    # Restore fee records
                    if 'Fee_Records' in excel_data:
                        try:
                            fees_df = excel_data['Fee_Records']
                            fees_df.to_csv('data/fee_records.csv', index=False)
                            success_count += 1
                        except Exception as e:
                            errors.append(f"Bản ghi phí: {str(e)}")
                    
                    # Reload fund manager data
                    st.session_state.fund_manager.load_data()
                    
                    # Show results
                    if success_count > 0:
                        st.success(f"✅ Khôi phục thành công {success_count} bảng dữ liệu!")
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
                        st.error("❌ Không thể khôi phục dữ liệu")
                        for error in errors:
                            st.error(f"  - {error}")
        
        with col2:
            if st.button("❌ Hủy bỏ", key="cancel_restore"):
                st.rerun()
                
    except Exception as e:
        st.error(f"❌ Lỗi khôi phục: {str(e)}")

def show_backup_history():
    """Show backup history from local exports folder with restore functionality"""
    st.subheader("📊 Lịch Sử Sao Lưu")
    
    # Warning about restore
    with st.expander("⚠️ Hướng dẫn khôi phục"):
        st.warning("🔴 **CHÚ Ý quan trọng về khôi phục:**")
        st.markdown("""
        - **Khôi phục sẽ ghi đè toàn bộ dữ liệu hiện tại**
        - Nên tạo bản sao lưu hiện tại trước khi khôi phục
        - Khôi phục chỉ áp dụng cho file Excel sao lưu
        - Sau khi khôi phục, hệ thống sẽ tự động tải lại dữ liệu
        """)
    
    export_dir = Path("exports")
    if not export_dir.exists():
        st.info("📁 Không tìm thấy thư mục sao lưu")
        return
    
    # Get all backup files
    backup_files = list(export_dir.glob("Fund_Export_*.xlsx"))
    
    if not backup_files:
        st.info("📁 Không tìm thấy file sao lưu")
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
                'Type': 'Tự động' if 'auto_' in file_path.name else 'Thủ công',
                'Path': str(file_path)
            })
        except Exception as e:
            st.warning(f"⚠️ Không thể đọc {file_path.name}: {e}")
    
    if not backup_data:
        st.info("📁 Không có file sao lưu nào đọc được")
        return
    
    # Sort by date (newest first)
    backup_data.sort(key=lambda x: x['Date'], reverse=True)
    
    # Show as dataframe
    df = pd.DataFrame(backup_data)
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Display table with restore buttons
    display_df = df.drop('Path', axis=1).copy()
    
    # Add restore column with better formatting
    st.markdown("**Danh sách file sao lưu (nhấn 🔄 để khôi phục):**")
    
    for i, row in enumerate(backup_data):
        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
                # Format the display with better styling
                file_date = row['Date'].strftime('%Y-%m-%d %H:%M')
                file_size_mb = row['Size (KB)'] / 1024
                type_emoji = "🤖" if row['Type'] == 'Tự động' else "👤"
                
                st.markdown(f"""
                **{row['Filename']}**  
                📅 {file_date} | 📦 {file_size_mb:.1f} MB | {type_emoji} {row['Type']}
                """)
            with col2:
                if st.button(f"🔄", key=f"restore_{i}", help=f"Khôi phục từ sao lưu: {row['Filename']}", type="secondary"):
                    handle_restore_from_backup(row['Path'], row['Filename'])
            
            st.divider()
    
    # Show total stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng số file", len(backup_data))
    with col2:
        total_size = sum(item['Size (KB)'] for item in backup_data)
        st.metric("Tổng dung lượng", f"{total_size/1024:.1f} MB")
    with col3:
        if backup_data:
            # Use original datetime objects from backup_data, not the string-converted ones
            latest = max(backup_data, key=lambda x: x['Date'])
            st.metric("Bản sao lưu mới nhất", latest['Date'].strftime('%Y-%m-%d'))

def show_cloud_backup_status():
    """Show cloud backup status and details"""
    st.subheader("☁️ Trạng Thái Sao Lưu Đám Mây")
    
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Hệ thống sao lưu tự động không khả dụng")
        return
    
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund Manager chưa được khởi tạo")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    status = backup_manager.get_backup_status()
    
    cloud_info = status['cloud_backup']
    
    if cloud_info['connected']:
        st.success("✅ Sao lưu đám mây đã kết nối")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"👤 Tài khoản: {cloud_info.get('account', 'Không xác định')}")
            st.info(f"🔐 Phương thức: {cloud_info.get('method', 'Không xác định')}")
        
        with col2:
            st.info(f"📄 Số tệp trên Drive: {cloud_info.get('files', 0)}")
            st.info("📁 Dung lượng: 15GB miễn phí (tài khoản cá nhân)")
        
        # Test connection button
        if st.button("🧪 Kiểm Tra Kết Nối", help="Kiểm tra kết nối Google Drive"):
            try:
                drive_manager = backup_manager.drive_manager
                if drive_manager:
                    test_result = drive_manager.test_connection()
                    if test_result.get('connected'):
                        st.success(f"✅ Kết nối thành công! Số file: {test_result.get('files_count', 0)}")
                    else:
                        st.error("❌ Kiểm tra kết nối thất bại")
                        for error in test_result.get('errors', []):
                            st.error(f"   - {error}")
                else:
                    st.warning("⚠️ Trình quản lý Drive không khả dụng")
            except Exception as e:
                st.error(f"❌ Kiểm tra thất bại: {e}")
    else:
        st.warning("⚠️ Sao lưu đám mây chưa kết nối")
        if 'error' in cloud_info:
            st.error(f"Lỗi: {cloud_info['error']}")
        
        st.info("💡 Để bật sao lưu đám mây:")
        st.markdown("""
        1. Làm theo hướng dẫn trong `SETUP_OAUTH_PERSONAL.md`
        2. Tạo thông tin xác thực OAuth
        3. Khởi động lại ứng dụng
        """)

def show_backup_controls():
    """Show backup control buttons and settings"""
    st.subheader("🎮 Điều Khiển Sao Lưu")
    
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Hệ thống sao lưu tự động không khả dụng")
        return
    
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund Manager chưa được khởi tạo")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Tạo Sao Lưu Ngay", type="primary", help="Tạo bản sao lưu thủ công"):
            with st.spinner("Đang tạo bản sao lưu..."):
                success = manual_backup(fund_manager, "dashboard_manual")
            
            if success:
                st.success("✅ Tạo bản sao lưu thành công!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Tạo bản sao lưu thất bại")
    
    with col2:
        if st.button("🔄 Làm Mới Trạng Thái", help="Làm mới trạng thái sao lưu"):
            st.rerun()
    
    with col3:
        if st.button("🧹 Dọn Dẹp Sao Lưu Cũ", help="Xóa bản sao lưu cục bộ cũ (giữ 10 bản mới nhất)"):
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
                                st.warning(f"Không thể xóa {file_path.name}: {e}")
                        
                        st.success(f"🧹 Đã dọn dẹp {deleted_count} file sao lưu cũ")
                        st.rerun()
                    else:
                        st.info("✅ Không cần dọn dẹp (≤10 file)")
                else:
                    st.warning("📁 Không tìm thấy thư mục sao lưu")
                    
            except Exception as e:
                st.error(f"❌ Dọn dẹp thất bại: {e}")

def show_backup_settings():
    """Show backup system settings"""
    st.subheader("⚙️ Cài Đặt Sao Lưu")
    
    if not AUTO_BACKUP_AVAILABLE:
        st.error("🚫 Hệ thống sao lưu tự động không khả dụng")
        return
    
    if 'fund_manager' not in st.session_state:
        st.error("❌ Fund Manager chưa được khởi tạo")
        return
    
    fund_manager = st.session_state.fund_manager
    backup_manager = get_auto_backup_manager(fund_manager)
    
    # Show current configuration
    st.json({
        "Sao lưu cục bộ": "Luôn bật",
        "Sao lưu đám mây": "Dựa trên OAuth (tài khoản cá nhân)",
        "Daily Schedule": "23:00 (11 PM)",
        "Số sao lưu tối đa mỗi ngày": "5 bản",
        "Khoảng cách sao lưu": "Tối thiểu 6 giờ",
        "Lưu giữ cục bộ": "20 file mới nhất",
        "Chi phí lưu trữ": "$0/tháng (Google Drive cá nhân)"
    })
    
    # Show backup statistics
    status = backup_manager.get_backup_status()
    
    st.subheader("📊 Thống Kê")
    stats_data = {
        "Tổng số bản sao lưu đã tạo": status['stats']['total_backups'],
        "Sao lưu cục bộ thành công": status['stats']['successful_local'],
        "Sao lưu đám mây thành công": status['stats']['successful_cloud'],
        "Sao lưu thất bại": status['stats']['failed_backups'],
        "Thời gian hoạt động dịch vụ": "Đang chạy" if status['service_running'] else "Đã dừng"
    }
    
    if status['stats']['last_error']:
        stats_data["Lỗi gần nhất"] = status['stats']['last_error']

    st.json(stats_data)

def show_drive_backup_controls():
    """Show manual backup controls for Drive-backed storage"""
    st.subheader("☁️ Điều Khiển Sao Lưu Google Drive")

    # Check if using Drive handler
    if 'fund_manager' not in st.session_state:
        st.info("ℹ️ Chưa khởi tạo Fund Manager")
        return

    fund_manager = st.session_state.fund_manager
    data_handler = fund_manager.data_handler

    # Check if it's Drive handler
    is_drive_handler = type(data_handler).__name__ == 'DriveBackedDataManager'

    if not is_drive_handler:
        st.warning("⚠️ Hệ thống cần Google Drive để hoạt động")
        st.info("💡 Ứng dụng hiện đang dùng Google Drive làm nơi lưu trữ chính cho cả cục bộ và đám mây")
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
            st.metric("Sao lưu cuối", f"{minutes_ago} phút trước")
        else:
            st.metric("Sao lưu cuối", "Chưa có")

    with col3:
        if f'{data_handler.session_key_prefix}last_load' in st.session_state:
            last_load = st.session_state[f'{data_handler.session_key_prefix}last_load']
            time_ago = datetime.now() - last_load
            minutes_ago = int(time_ago.total_seconds() / 60)
            st.metric("Tải cuối", f"{minutes_ago} phút trước")
        else:
            st.metric("Tải cuối", "Chưa có")

    st.divider()

    # Manual backup button
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("💾 Sao Lưu Ngay", type="primary", key="manual_drive_backup", use_container_width=True):
            if data_handler.connected:
                success = data_handler.backup_to_drive()
                if success:
                    st.success("✅ Sao lưu thành công!")
                    st.balloons()
                else:
                    st.error("❌ Sao lưu thất bại")
            else:
                st.error("❌ Google Drive chưa kết nối")

    with col2:
        if st.button("🔄 Tải Lại Từ Drive", key="reload_from_drive", use_container_width=True):
            if data_handler.connected:
                with st.spinner("📥 Đang tải dữ liệu từ Drive..."):
                    success = data_handler.load_from_drive()
                    if success:
                        # Reload fund manager
                        fund_manager.load_data()
                        st.success("✅ Đã tải lại dữ liệu!")
                        st.rerun()
                    else:
                        st.error("❌ Tải lại thất bại")
            else:
                st.error("❌ Google Drive chưa kết nối")

def main():
    """Main backup dashboard function"""
    st.set_page_config(
        page_title="Quản lý sao lưu",
        page_icon="💾",
        layout="wide"
    )
    
    st.title("💾 Bảng Điều Khiển Quản Lý Sao Lưu")

    # Check authentication (but don't require it since auth is disabled)
    if is_admin_authenticated():
        show_admin_status()
    else:
        st.success("🏠 Hệ thống cục bộ - Đã bật toàn quyền truy cập")

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
        st.error("🚫 Hệ thống sao lưu tự động không khả dụng")
        st.info("💡 Hãy đảm bảo auto_backup_personal.py đã được cài đặt đúng")
        
        # Show debug info
        with st.expander("🔍 Thông Tin Gỡ Lỗi"):
            if 'fund_manager' in st.session_state:
                fm = st.session_state.fund_manager
                st.json({
                    "Loại Fund Manager": type(fm).__name__,
                    "Có backup_manager": hasattr(fm, 'backup_manager'),
                    "Giá trị backup_manager": str(getattr(fm, 'backup_manager', None)) if hasattr(fm, 'backup_manager') else "Không có",
                    "Loại Data Handler": type(fm.data_handler).__name__,
                    "Sao lưu tự động khả dụng": AUTO_BACKUP_AVAILABLE,
                    "Hệ thống sao lưu": "PersonalAutoBackupManager (tích hợp qua app.py)"
                })
            else:
                st.warning("Không tìm thấy Fund Manager trong trạng thái phiên")

if __name__ == "__main__":
    main()
