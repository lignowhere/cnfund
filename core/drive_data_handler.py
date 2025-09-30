#!/usr/bin/env python3
"""
Drive-Backed Data Handler for Streamlit Cloud
Uses Google Drive as primary storage with session state caching
Perfect for ephemeral file systems like Streamlit Cloud
"""

import io
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from .models import Investor, Tranche, Transaction, FeeRecord
from utils.timezone_manager import TimezoneManager
from utils.type_safety_fixes import safe_int_conversion, safe_float_conversion


class DriveBackedDataManager:
    """
    Data manager with Google Drive as persistent storage
    Session state used as temporary RAM cache
    """

    def __init__(self):
        self.connected = False
        self.drive_manager = None
        self.session_key_prefix = 'cnfund_data_'

        # For compatibility with existing code
        self.engine = None

        # Initialize Drive connection
        self._init_drive_manager()

        if self.connected:
            print("✅ DriveBackedDataManager initialized successfully")
        else:
            print("⚠️ DriveBackedDataManager initialized but Drive not connected")

    def _init_drive_manager(self):
        """Initialize Google Drive OAuth manager"""
        try:
            from integrations.google_drive_oauth import GoogleDriveOAuthManager

            self.drive_manager = GoogleDriveOAuthManager()

            if self.drive_manager and self.drive_manager.connected:
                self.connected = True
                print("✅ Google Drive connected via OAuth")
            else:
                print("⚠️ Google Drive not connected - OAuth setup required")
                self.connected = False

        except Exception as e:
            print(f"❌ Drive manager initialization failed: {e}")
            self.connected = False

    def reconnect(self):
        """Reconnect to Google Drive"""
        self._init_drive_manager()
        return self.connected

    # ========================================
    # Session State Management
    # ========================================

    def _is_data_loaded(self) -> bool:
        """Check if data is already loaded in session state"""
        return f'{self.session_key_prefix}loaded' in st.session_state

    def _get_session_data(self, table_name: str) -> pd.DataFrame:
        """Get DataFrame from session state"""
        key = f'{self.session_key_prefix}{table_name}'
        if key in st.session_state:
            return st.session_state[key].copy()
        return pd.DataFrame()

    def _set_session_data(self, table_name: str, df: pd.DataFrame):
        """Set DataFrame in session state"""
        key = f'{self.session_key_prefix}{table_name}'
        st.session_state[key] = df.copy()

    def _mark_as_loaded(self):
        """Mark data as loaded"""
        st.session_state[f'{self.session_key_prefix}loaded'] = True
        st.session_state[f'{self.session_key_prefix}last_load'] = datetime.now()

    # ========================================
    # Drive Sync Operations
    # ========================================

    def load_from_drive(self) -> bool:
        """Load data from Google Drive into session state"""
        if not self.connected:
            print("⚠️ Cannot load from Drive - not connected")
            return False

        try:
            with st.spinner("📥 Đang tải dữ liệu từ Google Drive..."):
                # Find latest backup
                latest_backup = self._find_latest_backup()

                if latest_backup:
                    # Download Excel file
                    excel_bytes = self._download_file(latest_backup['id'])

                    if excel_bytes:
                        # Parse Excel into session state
                        self._parse_excel_to_session(excel_bytes)
                        self._mark_as_loaded()

                        st.success(f"✅ Đã tải dữ liệu từ Drive (File: {latest_backup['name']})")
                        return True
                else:
                    # No backup found - initialize empty
                    print("ℹ️ No backup found - initializing empty data")
                    self._init_empty_data()
                    self._mark_as_loaded()
                    st.info("ℹ️ Không tìm thấy backup - khởi tạo dữ liệu mới")
                    return True

        except Exception as e:
            st.error(f"❌ Lỗi tải dữ liệu từ Drive: {e}")
            print(f"❌ Load from Drive error: {e}")
            # Initialize empty on error
            self._init_empty_data()
            self._mark_as_loaded()
            return False

    def _find_latest_backup(self) -> Optional[Dict[str, Any]]:
        """Find the most recent backup file on Drive"""
        try:
            if not self.drive_manager or not self.drive_manager.service:
                return None

            folder_id = self.drive_manager.folder_id

            # Search for Excel backup files
            query = f"'{folder_id}' in parents and name contains 'CNFund_Backup' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"

            print(f"🔍 Querying Drive for backup files...")
            print(f"   Folder ID: {folder_id}")
            print(f"   Query: {query}")

            # Get ALL matching files first (up to 100)
            # NOTE: Drive API may cache results - this can cause stale data
            results = self.drive_manager.service.files().list(
                q=query,
                orderBy='modifiedTime desc',
                pageSize=100,
                fields='files(id, name, modifiedTime, createdTime, webViewLink)',
                # Spaces parameter helps with cache busting
                spaces='drive'
            ).execute()

            print(f"✅ Query returned {len(results.get('files', []))} files")

            files = results.get('files', [])

            if not files:
                return None

            # Sort by filename timestamp (most reliable)
            # Format: CNFund_Backup_YYYYMMDD_HHMMSS.xlsx
            def extract_timestamp(filename: str) -> str:
                """Extract timestamp from filename for sorting"""
                try:
                    # CNFund_Backup_20250930_143020.xlsx -> 20250930_143020
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        # Get last two parts before .xlsx
                        timestamp = '_'.join(parts[-2:]).replace('.xlsx', '')
                        return timestamp
                    return '0'
                except:
                    return '0'

            # Sort files by extracted timestamp (descending)
            sorted_files = sorted(files, key=lambda f: extract_timestamp(f['name']), reverse=True)

            # DEBUG: Show ALL files with timestamps for troubleshooting
            print(f"\n{'='*80}")
            print(f"📂 BACKUP FILE SELECTION DEBUG")
            print(f"{'='*80}")
            print(f"Total files found: {len(files)}")
            print(f"\n📋 All backup files (sorted by filename timestamp):")
            for i, f in enumerate(sorted_files[:10], 1):  # Show top 10
                ts = extract_timestamp(f['name'])
                print(f"   {i}. {f['name']}")
                print(f"      Timestamp: {ts}")
                print(f"      Modified:  {f.get('modifiedTime', 'N/A')}")
                print(f"      Created:   {f.get('createdTime', 'N/A')}")
                print(f"      File ID:   {f.get('id', 'N/A')}")
                print()

            latest = sorted_files[0]

            print(f"✅ SELECTED FILE: {latest['name']}")
            print(f"   File ID: {latest.get('id', 'N/A')}")
            print(f"{'='*80}\n")

            return latest

        except Exception as e:
            print(f"⚠️ Could not find backup: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _download_file(self, file_id: str) -> Optional[io.BytesIO]:
        """Download file from Drive"""
        try:
            import googleapiclient.http

            request = self.drive_manager.service.files().get_media(fileId=file_id)

            file_buffer = io.BytesIO()
            downloader = googleapiclient.http.MediaIoBaseDownload(file_buffer, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()

            file_buffer.seek(0)
            return file_buffer

        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None

    def _parse_excel_to_session(self, excel_bytes: io.BytesIO):
        """Parse Excel file and load into session state"""
        try:
            # Read Excel sheets
            excel_data = pd.ExcelFile(excel_bytes)

            # Map sheet names to session keys
            sheet_mapping = {
                'Nhà Đầu Tư': 'investors',
                'Đợt Gọi Vốn': 'tranches',
                'Giao Dịch': 'transactions',
                'Phí Quản Lý': 'fee_records'
            }

            for sheet_name, table_name in sheet_mapping.items():
                if sheet_name in excel_data.sheet_names:
                    df = pd.read_excel(excel_bytes, sheet_name=sheet_name)
                    self._set_session_data(table_name, df)
                    print(f"✅ Loaded {len(df)} rows from {sheet_name}")
                else:
                    # Sheet doesn't exist - create empty
                    self._set_session_data(table_name, self._get_empty_df(table_name))

        except Exception as e:
            print(f"❌ Parse Excel error: {e}")
            raise

    def _init_empty_data(self):
        """Initialize empty DataFrames in session state"""
        tables = ['investors', 'tranches', 'transactions', 'fee_records']

        for table_name in tables:
            empty_df = self._get_empty_df(table_name)
            self._set_session_data(table_name, empty_df)

        print("✅ Initialized empty data structures")

    def _get_empty_df(self, table_name: str) -> pd.DataFrame:
        """Get empty DataFrame with correct columns"""
        schemas = {
            'investors': ['id', 'name', 'phone', 'address', 'email', 'join_date', 'is_fund_manager'],
            'tranches': ['investor_id', 'tranche_id', 'entry_date', 'entry_nav', 'units',
                        'original_invested_value', 'hwm', 'original_entry_date',
                        'original_entry_nav', 'cumulative_fees_paid'],
            'transactions': ['id', 'transaction_type', 'investor_id', 'tranche_id',
                            'transaction_date', 'units', 'nav', 'amount', 'fee_amount',
                            'net_amount', 'notes'],
            'fee_records': ['id', 'investor_id', 'tranche_id', 'fee_date', 'fee_type',
                           'fee_amount', 'nav_at_fee', 'description']
        }

        return pd.DataFrame(columns=schemas.get(table_name, []))

    def backup_to_drive(self, auto_cleanup: bool = True, keep_recent: int = 10) -> bool:
        """
        Backup all session data to Google Drive

        Args:
            auto_cleanup: Automatically delete old backups (default: True)
            keep_recent: Number of recent backups to keep (default: 10)
        """
        if not self.connected:
            st.warning("⚠️ Không thể backup - Drive chưa kết nối")
            return False

        try:
            with st.spinner("💾 Đang sao lưu lên Google Drive..."):
                # Create Excel from session state
                excel_buffer = self._create_excel_from_session()

                if not excel_buffer:
                    return False

                # Upload to Drive
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"CNFund_Backup_{timestamp}.xlsx"

                print(f"📤 Uploading: {filename}")
                success = self.drive_manager.upload_to_drive(excel_buffer, filename)

                if success:
                    print(f"✅ Upload successful: {filename}")

                    # IMPORTANT: Wait for Drive API to index the file
                    # Drive API has eventual consistency - file may not appear immediately in search
                    import time
                    print("⏳ Waiting 2 seconds for Drive API indexing...")
                    time.sleep(2)

                    # Verify file appears in search results
                    print("🔍 Verifying file appears in Drive search...")
                    verification_attempt = self._find_latest_backup()
                    if verification_attempt and verification_attempt['name'] == filename:
                        print(f"✅ Verification passed: File {filename} found in Drive")
                    else:
                        found_name = verification_attempt['name'] if verification_attempt else 'None'
                        print(f"⚠️ Verification issue: Expected {filename}, found {found_name}")
                        print(f"   This might be a Drive API indexing delay")

                    st.session_state[f'{self.session_key_prefix}last_backup'] = datetime.now()
                    st.session_state[f'{self.session_key_prefix}last_backup_filename'] = filename

                    # Auto cleanup old backups
                    if auto_cleanup:
                        self._cleanup_old_backups(keep_recent)

                    return True
                else:
                    print(f"❌ Upload failed: {filename}")

                return False

        except Exception as e:
            st.error(f"❌ Lỗi backup: {e}")
            print(f"❌ Backup error: {e}")
            return False

    def _cleanup_old_backups(self, keep_recent: int = 10):
        """
        Delete old backup files, keeping only the most recent ones

        Args:
            keep_recent: Number of recent backups to keep (default: 10)
        """
        try:
            if not self.drive_manager or not self.drive_manager.service:
                return

            folder_id = self.drive_manager.folder_id

            # Get ALL backup files
            query = f"'{folder_id}' in parents and name contains 'CNFund_Backup' and mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and trashed=false"

            results = self.drive_manager.service.files().list(
                q=query,
                orderBy='modifiedTime desc',
                pageSize=100,
                fields='files(id, name, modifiedTime)'
            ).execute()

            files = results.get('files', [])

            if len(files) <= keep_recent:
                print(f"✅ Cleanup: {len(files)} backups (within limit of {keep_recent})")
                return

            # Sort by filename timestamp
            def extract_timestamp(filename: str) -> str:
                try:
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        timestamp = '_'.join(parts[-2:]).replace('.xlsx', '')
                        return timestamp
                    return '0'
                except:
                    return '0'

            sorted_files = sorted(files, key=lambda f: extract_timestamp(f['name']), reverse=True)

            # Keep recent, delete old
            files_to_keep = sorted_files[:keep_recent]
            files_to_delete = sorted_files[keep_recent:]

            print(f"🧹 Cleanup: Keeping {len(files_to_keep)} backups, deleting {len(files_to_delete)} old files")

            # Delete old files
            deleted_count = 0
            for file in files_to_delete:
                try:
                    self.drive_manager.service.files().delete(fileId=file['id']).execute()
                    deleted_count += 1
                    print(f"   🗑️ Deleted: {file['name']}")
                except Exception as e:
                    print(f"   ⚠️ Could not delete {file['name']}: {e}")

            print(f"✅ Cleanup completed: Deleted {deleted_count} old backups")

        except Exception as e:
            print(f"⚠️ Cleanup error (non-critical): {e}")

    def _create_excel_from_session(self) -> Optional[io.BytesIO]:
        """Create Excel file from session state data"""
        try:
            excel_buffer = io.BytesIO()

            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                # Write each table
                tables = {
                    'Nhà Đầu Tư': 'investors',
                    'Đợt Gọi Vốn': 'tranches',
                    'Giao Dịch': 'transactions',
                    'Phí Quản Lý': 'fee_records'
                }

                for sheet_name, table_name in tables.items():
                    df = self._get_session_data(table_name)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

            excel_buffer.seek(0)
            return excel_buffer

        except Exception as e:
            print(f"❌ Create Excel error: {e}")
            return None

    # ========================================
    # Data Access Methods (compatible with CSVDataHandler)
    # ========================================

    def ensure_data_loaded(self, force_reload: bool = False, max_age_seconds: int = 300):
        """
        Ensure data is loaded - load from Drive if needed

        Args:
            force_reload: Force reload from Drive even if already loaded
            max_age_seconds: Maximum age of cached data in seconds (default: 5 minutes)
        """
        should_reload = force_reload or not self._is_data_loaded()

        # Check data freshness - reload if too old
        if not should_reload and self._is_data_loaded():
            last_load_key = f'{self.session_key_prefix}last_load'
            if last_load_key in st.session_state:
                last_load_time = st.session_state[last_load_key]
                age_seconds = (datetime.now() - last_load_time).total_seconds()

                if age_seconds > max_age_seconds:
                    print(f"🔄 Data cached for {age_seconds:.0f}s (max: {max_age_seconds}s) - reloading from Drive")
                    should_reload = True

        if should_reload:
            self.load_from_drive()

    def load_investors(self) -> List[Investor]:
        """Load investors from session state"""
        self.ensure_data_loaded()

        try:
            df = self._get_session_data('investors')

            if df.empty:
                return []

            # Parse DataFrame to Investor objects
            investors = []
            for _, row in df.iterrows():
                try:
                    # Parse join_date
                    join_date = date.today()
                    if 'join_date' in row and pd.notna(row['join_date']):
                        if hasattr(row['join_date'], 'date'):
                            join_date = row['join_date'].date()
                        else:
                            join_date = pd.to_datetime(row['join_date']).date()

                    investor = Investor(
                        id=safe_int_conversion(row.get('id', 0)),
                        name=str(row.get('name', '')).strip(),
                        phone=str(row.get('phone', '')).strip(),
                        address=str(row.get('address', '')).strip(),
                        email=str(row.get('email', '')).strip(),
                        join_date=join_date,
                        is_fund_manager=bool(row.get('is_fund_manager', False))
                    )

                    if investor.name and investor.id >= 0:
                        investors.append(investor)

                except Exception as e:
                    print(f"Warning: Skipping investor row: {e}")
                    continue

            return investors

        except Exception as e:
            print(f"❌ Error loading investors: {e}")
            return []

    def load_tranches(self) -> List[Tranche]:
        """Load tranches from session state"""
        self.ensure_data_loaded()

        try:
            df = self._get_session_data('tranches')

            if df.empty:
                return []

            tranches = []
            for _, row in df.iterrows():
                try:
                    # Parse dates
                    entry_date = pd.to_datetime(row['entry_date'])
                    original_entry_date = pd.to_datetime(row.get('original_entry_date', row['entry_date']))

                    tranche = Tranche(
                        investor_id=safe_int_conversion(row['investor_id']),
                        tranche_id=str(row['tranche_id']),
                        entry_date=entry_date,
                        entry_nav=safe_float_conversion(row['entry_nav']),
                        units=safe_float_conversion(row['units']),
                        original_invested_value=safe_float_conversion(row['original_invested_value']),
                        hwm=safe_float_conversion(row.get('hwm', row['entry_nav'])),
                        original_entry_date=original_entry_date,
                        original_entry_nav=safe_float_conversion(row.get('original_entry_nav', row['entry_nav'])),
                        cumulative_fees_paid=safe_float_conversion(row.get('cumulative_fees_paid', 0.0))
                    )

                    tranches.append(tranche)

                except Exception as e:
                    print(f"Warning: Skipping tranche row: {e}")
                    continue

            return tranches

        except Exception as e:
            print(f"❌ Error loading tranches: {e}")
            return []

    def load_transactions(self) -> List[Transaction]:
        """Load transactions from session state"""
        self.ensure_data_loaded()

        try:
            df = self._get_session_data('transactions')

            if df.empty:
                return []

            transactions = []
            for _, row in df.iterrows():
                try:
                    # Transaction model fields: id, investor_id, date, type, amount, nav, units_change
                    transaction = Transaction(
                        id=safe_int_conversion(row['id']),
                        investor_id=safe_int_conversion(row['investor_id']),
                        date=pd.to_datetime(row['transaction_date']),  # Map to 'date'
                        type=str(row['transaction_type']),  # Map to 'type'
                        amount=safe_float_conversion(row.get('amount', 0.0)),
                        nav=safe_float_conversion(row.get('nav', 0.0)),
                        units_change=safe_float_conversion(row.get('units', 0.0))  # Map to 'units_change'
                    )

                    transactions.append(transaction)

                except Exception as e:
                    print(f"Warning: Skipping transaction row: {e}")
                    continue

            return transactions

        except Exception as e:
            print(f"❌ Error loading transactions: {e}")
            return []

    def load_fee_records(self) -> List[FeeRecord]:
        """Load fee records from session state"""
        self.ensure_data_loaded()

        try:
            df = self._get_session_data('fee_records')

            if df.empty:
                return []

            fee_records = []
            for _, row in df.iterrows():
                try:
                    # FeeRecord model fields: id, period, investor_id, fee_amount, fee_units,
                    # calculation_date, units_before, units_after, nav_per_unit, description
                    fee_record = FeeRecord(
                        id=safe_int_conversion(row['id']),
                        investor_id=safe_int_conversion(row['investor_id']),
                        period=str(row['fee_type']),  # Map 'fee_type' to 'period'
                        fee_amount=safe_float_conversion(row['fee_amount']),
                        fee_units=safe_float_conversion(row.get('fee_units', 0.0)),
                        calculation_date=pd.to_datetime(row['fee_date']),  # Map to 'calculation_date'
                        units_before=safe_float_conversion(row.get('units_before', 0.0)),
                        units_after=safe_float_conversion(row.get('units_after', 0.0)),
                        nav_per_unit=safe_float_conversion(row.get('nav_at_fee', 0.0)),  # Map to 'nav_per_unit'
                        description=str(row.get('description', ''))
                    )

                    fee_records.append(fee_record)

                except Exception as e:
                    print(f"Warning: Skipping fee record row: {e}")
                    continue

            return fee_records

        except Exception as e:
            print(f"❌ Error loading fee records: {e}")
            return []

    # ========================================
    # Save Methods
    # ========================================

    def save_all_data_enhanced(
        self,
        investors: List[Investor],
        tranches: List[Tranche],
        transactions: List[Transaction],
        fee_records: List[FeeRecord]
    ) -> bool:
        """Save all data to session state and backup to Drive"""
        try:
            print(f"💾 Starting save: {len(investors)} investors, {len(tranches)} tranches, {len(transactions)} transactions, {len(fee_records)} fee records")

            # Convert to DataFrames
            print("📊 Converting to DataFrames...")
            investors_df = self._investors_to_df(investors)
            tranches_df = self._tranches_to_df(tranches)
            transactions_df = self._transactions_to_df(transactions)
            fee_records_df = self._fee_records_to_df(fee_records)

            print(f"✅ DataFrames created: {len(investors_df)} investors, {len(tranches_df)} tranches, {len(transactions_df)} transactions, {len(fee_records_df)} fees")

            # Save to session state
            print("💾 Saving to session state...")
            self._set_session_data('investors', investors_df)
            self._set_session_data('tranches', tranches_df)
            self._set_session_data('transactions', transactions_df)
            self._set_session_data('fee_records', fee_records_df)

            # IMPORTANT: Mark data as stale to force reload on next access
            # This ensures changes are picked up by other sessions/users
            # We set last_load to a very old time to trigger immediate reload
            st.session_state[f'{self.session_key_prefix}last_load'] = datetime.now() - timedelta(hours=24)

            print("✅ Session state updated (marked as stale for next reload)")

            # Backup to Drive
            print("☁️ Backing up to Drive...")
            success = self.backup_to_drive()

            if success:
                print("✅ Save completed successfully")
            else:
                print("⚠️ Drive backup failed (session state saved)")

            return success

        except Exception as e:
            print(f"❌ Error saving data: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _investors_to_df(self, investors: List[Investor]) -> pd.DataFrame:
        """Convert investors to DataFrame"""
        data = []
        for inv in investors:
            data.append({
                'id': inv.id,
                'name': inv.name,
                'phone': inv.phone,
                'address': inv.address,
                'email': inv.email,
                'join_date': inv.join_date,
                'is_fund_manager': inv.is_fund_manager
            })
        return pd.DataFrame(data)

    def _tranches_to_df(self, tranches: List[Tranche]) -> pd.DataFrame:
        """Convert tranches to DataFrame"""
        data = []
        for tranche in tranches:
            data.append({
                'investor_id': tranche.investor_id,
                'tranche_id': tranche.tranche_id,
                'entry_date': tranche.entry_date,
                'entry_nav': tranche.entry_nav,
                'units': tranche.units,
                'original_invested_value': tranche.original_invested_value,
                'hwm': tranche.hwm,
                'original_entry_date': tranche.original_entry_date,
                'original_entry_nav': tranche.original_entry_nav,
                'cumulative_fees_paid': tranche.cumulative_fees_paid
            })
        return pd.DataFrame(data)

    def _transactions_to_df(self, transactions: List[Transaction]) -> pd.DataFrame:
        """Convert transactions to DataFrame"""
        data = []
        for txn in transactions:
            data.append({
                'id': txn.id,
                'transaction_type': txn.type,  # Model uses 'type', not 'transaction_type'
                'investor_id': txn.investor_id,
                'tranche_id': getattr(txn, 'tranche_id', ''),  # Optional field
                'transaction_date': txn.date,  # Model uses 'date', not 'transaction_date'
                'units': txn.units_change,  # Model uses 'units_change', not 'units'
                'nav': txn.nav,
                'amount': txn.amount,
                'fee_amount': getattr(txn, 'fee_amount', 0.0),  # Optional field
                'net_amount': getattr(txn, 'net_amount', 0.0),  # Optional field
                'notes': getattr(txn, 'notes', '')  # Optional field
            })
        return pd.DataFrame(data)

    def _fee_records_to_df(self, fee_records: List[FeeRecord]) -> pd.DataFrame:
        """Convert fee records to DataFrame"""
        data = []
        for fee in fee_records:
            data.append({
                'id': fee.id,
                'investor_id': fee.investor_id,
                'tranche_id': getattr(fee, 'tranche_id', ''),  # Optional field
                'fee_date': fee.calculation_date,  # Model uses 'calculation_date'
                'fee_type': fee.period,  # Model uses 'period' for fee type/period
                'fee_amount': fee.fee_amount,
                'nav_at_fee': fee.nav_per_unit,  # Model uses 'nav_per_unit'
                'description': fee.description,
                # Additional fields from model
                'fee_units': fee.fee_units,
                'units_before': fee.units_before,
                'units_after': fee.units_after
            })
        return pd.DataFrame(data)