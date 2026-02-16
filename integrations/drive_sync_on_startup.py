#!/usr/bin/env python3
"""
Auto-sync Google Drive on Streamlit Cloud Startup
Restores latest backup from Drive when app starts
"""

import os
import io
import streamlit as st
from pathlib import Path
from datetime import datetime
from typing import Optional

class DriveStartupSync:
    """Sync data from Google Drive on app startup"""

    def __init__(self):
        self.data_dir = Path("data")
        self.drive_manager = None
        self.synced = False

    def check_if_needs_sync(self) -> bool:
        """Check if we need to restore from Drive"""
        # If data folder is empty or doesn't exist → need sync
        if not self.data_dir.exists():
            return True

        # Check if essential files exist
        required_files = [
            self.data_dir / "investors.csv",
            self.data_dir / "transactions.csv"
        ]

        for file in required_files:
            if not file.exists():
                return True

        return False

    def restore_from_drive(self) -> bool:
        """Restore latest backup from Google Drive"""
        try:
            from integrations.google_drive_oauth import GoogleDriveOAuthManager

            self.drive_manager = GoogleDriveOAuthManager()

            if not self.drive_manager.connected:
                st.warning("⚠️ Google Drive chưa kết nối - khởi động với dữ liệu trống")
                return False

            # Download latest backup
            backup_file = self._find_latest_backup()

            if not backup_file:
                st.info("ℹ️ Không tìm thấy bản sao lưu trên Drive - khởi động mới")
                return False

            # Download and extract
            success = self._download_and_extract(backup_file)

            if success:
                st.success("✅ Đã khôi phục dữ liệu từ Google Drive")
                self.synced = True
                return True

            return False

        except Exception as e:
            st.error(f"❌ Khôi phục thất bại: {e}")
            return False

    def _find_latest_backup(self) -> Optional[dict]:
        """Find the most recent backup file on Drive"""
        try:
            # Search for Excel backup files
            query = f"'{self.drive_manager.folder_id}' in parents and name contains 'CNFund_Backup' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"

            results = self.drive_manager.service.files().list(
                q=query,
                orderBy='modifiedTime desc',
                pageSize=1,
                fields='files(id, name, modifiedTime, webViewLink)'
            ).execute()

            files = results.get('files', [])

            if files:
                return files[0]

            return None

        except Exception as e:
            print(f"⚠️ Could not find backup: {e}")
            return None

    def _download_and_extract(self, file_info: dict) -> bool:
        """Download Excel backup and extract to CSV"""
        try:
            import pandas as pd

            # Download file
            file_id = file_info['id']
            request = self.drive_manager.service.files().get_media(fileId=file_id)

            file_buffer = io.BytesIO()

            import googleapiclient.http
            downloader = googleapiclient.http.MediaIoBaseDownload(file_buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            file_buffer.seek(0)

            # Read Excel and extract sheets to CSV
            excel_data = pd.ExcelFile(file_buffer)

            self.data_dir.mkdir(exist_ok=True)

            # Map sheets to CSV files
            sheet_mapping = {
                'Nhà Đầu Tư': 'investors.csv',
                'Đợt Gọi Vốn': 'tranches.csv',
                'Giao Dịch': 'transactions.csv',
                'Phí Quản Lý': 'fee_records.csv'
            }

            for sheet_name, csv_file in sheet_mapping.items():
                if sheet_name in excel_data.sheet_names:
                    df = pd.read_excel(file_buffer, sheet_name=sheet_name)
                    csv_path = self.data_dir / csv_file
                    df.to_csv(csv_path, index=False)
                    print(f"✅ Restored {csv_file}")

            return True

        except Exception as e:
            print(f"❌ Extract failed: {e}")
            return False


def sync_drive_on_startup():
    """Main function to call on app startup"""
    sync = DriveStartupSync()

    # Check if sync needed
    if not sync.check_if_needs_sync():
        print("✅ Local data exists - no sync needed")
        return True

    # Restore from Drive
    print("🔄 Restoring data from Google Drive...")
    success = sync.restore_from_drive()

    return success
