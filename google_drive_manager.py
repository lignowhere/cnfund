#!/usr/bin/env python3
"""
Enhanced Google Drive Manager with better error handling and debugging
"""

import os
import io
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import streamlit as st
import traceback

# Google Drive API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    st.warning("⚠️ Google API libraries not installed. Run: pip install google-api-python-client google-auth")

from utils import format_currency, format_percentage

class GoogleDriveManager:
    """Enhanced Manager for Google Drive operations and Excel exports"""

    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.service = None
        self.folder_id = '1BGrypQLMNmEDcmKntPMiPAgCB6GZsHno'
        self.connected = False
        self.error_log: List[str] = []

        if GOOGLE_API_AVAILABLE:
            self._initialize_drive_service()

    def _log_error(self, message: str, error: Exception = None):
        """Log error with details"""
        error_msg = f"{datetime.now()}: {message}"
        if error:
            error_msg += f" - {str(error)}"
        self.error_log.append(error_msg)
        print(f"ERROR: {error_msg}")  # For console debugging

    def _initialize_drive_service(self):
        try:
            creds = self._get_credentials()
            if creds:
                self.service = build('drive', 'v3', credentials=creds)

                # Test kết nối
                try:
                    about = self.service.about().get(fields="user").execute()
                    print(f"✅ Connected as: {about.get('user', {}).get('displayName', 'Unknown')}")
                except Exception as probe_err:
                    print(f"⚠️ Could not fetch user info: {probe_err}")

                # --- Luôn ưu tiên dùng folder_id nếu có ---
                folder_id_from_secrets = None
                if "drive_folder_id" in st.secrets:
                    folder_id_from_secrets = st.secrets["drive_folder_id"]
                elif "default" in st.secrets and "drive_folder_id" in st.secrets["default"]:
                    folder_id_from_secrets = st.secrets["default"]["drive_folder_id"]

                if folder_id_from_secrets:
                    self.folder_id = folder_id_from_secrets
                    print(f"📂 Using provided folder_id from secrets: {self.folder_id}")
                elif os.getenv("GOOGLE_DRIVE_FOLDER_ID"):
                    self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
                    print(f"📂 Using provided folder_id from env: {self.folder_id}")
                else:
                    # fallback: tìm/tạo folder mới
                    self.folder_id = self._get_or_create_folder()

                self.connected = bool(self.folder_id)
                if self.connected:
                    st.sidebar.success("✅ Google Drive connected")
                else:
                    st.sidebar.error("❌ Failed to setup Google Drive folder")
            else:
                st.sidebar.warning("⚠️ Google Drive not configured")
                self.connected = False
        except Exception as e:
            self._log_error("Google Drive initialization failed", e)
            st.sidebar.error(f"❌ Google Drive error: {str(e)}")
            self.connected = False



    def _get_credentials(self):
        """Get Google credentials from various sources"""
        print("🔐 Attempting to get Google credentials...")

        # Method 1: From Streamlit secrets
        try:
            if hasattr(st, 'secrets') and 'google_service_account' in st.secrets:
                print("📋 Using Streamlit secrets...")
                creds = service_account.Credentials.from_service_account_info(
                    st.secrets['google_service_account'],
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                print("✅ Streamlit secrets loaded successfully")
                return creds
        except Exception as e:
            print(f"❌ Streamlit secrets failed: {e}")

        # Method 2: From environment variable (JSON string)
        try:
            import json
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                print("📋 Using environment variable...")
                service_account_info = json.loads(service_account_json)
                creds = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                print("✅ Environment variable loaded successfully")
                return creds
        except Exception as e:
            print(f"❌ Environment variable failed: {e}")

        # Method 3: From local file
        try:
            service_account_file = 'service_account.json'
            if os.path.exists(service_account_file):
                print("📋 Using local service account file...")
                creds = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                print("✅ Local file loaded successfully")
                return creds
            else:
                print("❌ service_account.json not found")
        except Exception as e:
            print(f"❌ Local file failed: {e}")

        print("❌ No valid credentials found")
        return None

    def _get_or_create_folder(self, folder_name: str = "Fund_Management_Exports") -> Optional[str]:
        """Get or create a folder in Google Drive"""
        try:
            print(f"📁 Looking for folder: {folder_name}")

            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query, 
                fields="files(id, name)",
                supportsAllDrives=True, 
                includeItemsFromAllDrives=True
            ).execute()
            folders = results.get('files', [])

            if folders:
                folder_id = folders[0]['id']
                print(f"✅ Found existing folder: {folder_id}")
                return folder_id

            print(f"📁 Creating new folder: {folder_name}")
            # Create new folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=file_metadata, 
                fields='id',
                supportsAllDrives=True
            ).execute()
            folder_id = folder.get('id')
            print(f"✅ Created new folder: {folder_id}")
            return folder_id

        except Exception as e:
            self._log_error(f"Error creating folder: {folder_name}", e)
            return None

    def export_to_excel_buffer(self) -> io.BytesIO:
        """Export all data to Excel in memory"""
        print("📊 Starting Excel export...")
        buffer = io.BytesIO()

        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # 1. Summary Sheet
                print("  - Creating Summary sheet...")
                self._create_summary_sheet(writer)

                # 2. Investors Sheet
                print("  - Creating Investors sheet...")
                self._create_investors_sheet(writer)

                # 3. Tranches Sheet
                print("  - Creating Tranches sheet...")
                self._create_tranches_sheet(writer)

                # 4. Transactions Sheet
                print("  - Creating Transactions sheet...")
                self._create_transactions_sheet(writer)

                # 5. Fee Records Sheet
                print("  - Creating Fee Records sheet...")
                self._create_fee_records_sheet(writer)

                # 6. Performance Sheet
                print("  - Creating Performance sheet...")
                self._create_performance_sheet(writer)

                # 7. Fund Manager Sheet
                print("  - Creating Fund Manager sheet...")
                self._create_fund_manager_sheet(writer)

            buffer.seek(0)
            print(f"✅ Excel export completed - Size: {len(buffer.getvalue())} bytes")
            return buffer

        except Exception as e:
            self._log_error("Excel export failed", e)
            raise

    def _create_summary_sheet(self, writer):
        """Create summary sheet with key metrics"""
        latest_nav = self.fund_manager.get_latest_total_nav() or 0

        summary_data = {
            'Metric': [
                'Export Date',
                'Total NAV',
                'Price per Unit',
                'Total Investors',
                'Regular Investors',
                'Total Tranches',
                'Total Units',
                'Total Transactions',
                'Total Fees Collected',
                'Fund Manager Units',
                'Fund Manager Value'
            ],
            'Value': []
        }

        # Calculate metrics
        current_price = self.fund_manager.calculate_price_per_unit(latest_nav) if latest_nav > 0 else 0
        total_units = sum(t.units for t in self.fund_manager.tranches)
        regular_investors = self.fund_manager.get_regular_investors()

        # Fund Manager metrics
        fund_manager = self.fund_manager.get_fund_manager()
        fm_units = 0
        fm_value = 0
        if fund_manager:
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            fm_units = sum(t.units for t in fm_tranches)
            fm_value = fm_units * current_price if current_price > 0 else 0

        # Total fees from fee records
        total_fees = sum(record.fee_amount for record in self.fund_manager.fee_records)

        summary_data['Value'] = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            format_currency(latest_nav),
            format_currency(current_price),
            len(self.fund_manager.investors),
            len(regular_investors),
            len(self.fund_manager.tranches),
            f"{total_units:.6f}",
            len(self.fund_manager.transactions),
            format_currency(total_fees),
            f"{fm_units:.6f}",
            format_currency(fm_value)
        ]

        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)

    def _create_investors_sheet(self, writer):
        """Create investors sheet with current balances"""
        latest_nav = self.fund_manager.get_latest_total_nav() or 0

        investors_data = []
        for investor in self.fund_manager.investors:
            tranches = self.fund_manager.get_investor_tranches(investor.id)
            total_units = sum(t.units for t in tranches)

            if latest_nav > 0 and total_units > 0:
                balance, profit, profit_perc = self.fund_manager.get_investor_balance(investor.id, latest_nav)
                lifetime_perf = self.fund_manager.get_investor_lifetime_performance(investor.id, latest_nav)
            else:
                balance = profit = profit_perc = 0
                lifetime_perf = self.fund_manager._empty_performance_stats()

            investors_data.append({
                'ID': investor.id,
                'Name': investor.name,
                'Phone': investor.phone,
                'Email': investor.email,
                'Address': investor.address,
                'Join Date': investor.join_date,
                'Is Fund Manager': investor.is_fund_manager,
                'Total Units': total_units,
                'Current Balance': balance,
                'Current Profit': profit,
                'Current Profit %': profit_perc,
                'Original Invested': lifetime_perf['original_invested'],
                'Total Fees Paid': lifetime_perf['total_fees_paid'],
                'Gross Return': lifetime_perf['gross_return'],
                'Net Return': lifetime_perf['net_return']
            })

        df_investors = pd.DataFrame(investors_data)

        # Format columns
        currency_cols = ['Current Balance', 'Current Profit', 'Original Invested', 'Total Fees Paid']
        for col in currency_cols:
            if col in df_investors.columns:
                df_investors[col] = df_investors[col].apply(format_currency)

        percentage_cols = ['Current Profit %', 'Gross Return', 'Net Return']
        for col in percentage_cols:
            if col in df_investors.columns:
                df_investors[col] = df_investors[col].apply(format_percentage)

        df_investors.to_excel(writer, sheet_name='Investors', index=False)

    def _create_tranches_sheet(self, writer):
        """Create tranches sheet"""
        latest_nav = self.fund_manager.get_latest_total_nav() or 0
        current_price = self.fund_manager.calculate_price_per_unit(latest_nav) if latest_nav > 0 else 0

        tranches_data = []
        for tranche in self.fund_manager.tranches:
            investor = self.fund_manager.get_investor_by_id(tranche.investor_id)
            current_value = tranche.units * current_price if current_price > 0 else 0

            tranches_data.append({
                'Investor ID': tranche.investor_id,
                'Investor Name': investor.name if investor else 'Unknown',
                'Tranche ID': tranche.tranche_id,
                'Entry Date': tranche.entry_date,
                'Entry NAV': tranche.entry_nav,
                'Units': tranche.units,
                'HWM': tranche.hwm,
                'Original Entry Date': tranche.original_entry_date,
                'Original Entry NAV': tranche.original_entry_nav,
                'Cumulative Fees Paid': tranche.cumulative_fees_paid,
                'Invested Value': tranche.invested_value,
                'Current Value': current_value,
                'Profit/Loss': current_value - tranche.invested_value
            })

        df_tranches = pd.DataFrame(tranches_data)

        # Format columns
        currency_cols = ['Entry NAV', 'HWM', 'Original Entry NAV', 'Cumulative Fees Paid', 
                        'Invested Value', 'Current Value', 'Profit/Loss']
        for col in currency_cols:
            if col in df_tranches.columns:
                df_tranches[col] = df_tranches[col].apply(format_currency)

        df_tranches.to_excel(writer, sheet_name='Tranches', index=False)

    def _create_transactions_sheet(self, writer):
        """Create transactions sheet"""
        transactions_data = []
        for trans in self.fund_manager.transactions:
            investor = self.fund_manager.get_investor_by_id(trans.investor_id)

            transactions_data.append({
                'ID': trans.id,
                'Date': trans.date,
                'Investor ID': trans.investor_id,
                'Investor Name': investor.name if investor else 'System',
                'Type': trans.type,
                'Amount': trans.amount,
                'NAV': trans.nav,
                'Units Change': trans.units_change
            })

        df_transactions = pd.DataFrame(transactions_data)

        # Format columns
        if not df_transactions.empty:
            df_transactions['Amount'] = df_transactions['Amount'].apply(format_currency)
            df_transactions['NAV'] = df_transactions['NAV'].apply(format_currency)

        df_transactions.to_excel(writer, sheet_name='Transactions', index=False)

    def _create_fee_records_sheet(self, writer):
        """Create fee records sheet"""
        fee_data = []
        for record in self.fund_manager.fee_records:
            investor = self.fund_manager.get_investor_by_id(record.investor_id)

            fee_data.append({
                'ID': record.id,
                'Period': record.period,
                'Calculation Date': record.calculation_date,
                'Investor ID': record.investor_id,
                'Investor Name': investor.name if investor else 'Unknown',
                'Fee Amount': record.fee_amount,
                'Fee Units': record.fee_units,
                'Units Before': record.units_before,
                'Units After': record.units_after,
                'NAV per Unit': record.nav_per_unit,
                'Description': record.description
            })

        df_fees = pd.DataFrame(fee_data)

        # Format columns
        if not df_fees.empty:
            df_fees['Fee Amount'] = df_fees['Fee Amount'].apply(format_currency)
            df_fees['NAV per Unit'] = df_fees['NAV per Unit'].apply(format_currency)

        df_fees.to_excel(writer, sheet_name='Fee Records', index=False)

    def _create_performance_sheet(self, writer):
        """Create performance analysis sheet"""
        latest_nav = self.fund_manager.get_latest_total_nav() or 0

        performance_data = []
        for investor in self.fund_manager.get_regular_investors():
            if latest_nav > 0:
                perf = self.fund_manager.get_investor_lifetime_performance(investor.id, latest_nav)
                fee_details = self.fund_manager.calculate_investor_fee(
                    investor.id, 
                    datetime.now(), 
                    latest_nav
                )

                performance_data.append({
                    'Investor': investor.name,
                    'Original Invested': perf['original_invested'],
                    'Current Value': perf['current_value'],
                    'Total Fees Paid': perf['total_fees_paid'],
                    'Gross Profit': perf['gross_profit'],
                    'Net Profit': perf['net_profit'],
                    'Gross Return %': perf['gross_return'] * 100,
                    'Net Return %': perf['net_return'] * 100,
                    'Current Units': perf['current_units'],
                    'Pending Fee': fee_details['total_fee']
                })

        df_performance = pd.DataFrame(performance_data)

        # Format columns
        if not df_performance.empty:
            currency_cols = ['Original Invested', 'Current Value', 'Total Fees Paid', 
                           'Gross Profit', 'Net Profit', 'Pending Fee']
            for col in currency_cols:
                if col in df_performance.columns:
                    df_performance[col] = df_performance[col].apply(format_currency)

            df_performance['Gross Return %'] = df_performance['Gross Return %'].apply(lambda x: f"{x:.2f}%")
            df_performance['Net Return %'] = df_performance['Net Return %'].apply(lambda x: f"{x:.2f}%")

        df_performance.to_excel(writer, sheet_name='Performance', index=False)

    def _create_fund_manager_sheet(self, writer):
        """Create fund manager specific sheet"""
        fund_manager = self.fund_manager.get_fund_manager()
        if not fund_manager:
            pd.DataFrame({'Message': ['No Fund Manager found']}).to_excel(
                writer, sheet_name='Fund Manager', index=False
            )
            return

        latest_nav = self.fund_manager.get_latest_total_nav() or 0
        fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)

        # Fund Manager summary
        fm_summary = {
            'Metric': [
                'Total Units',
                'Total Value',
                'Number of Tranches',
                'Total Fee Income',
                'Average Entry Price'
            ],
            'Value': []
        }

        total_units = sum(t.units for t in fm_tranches)
        current_price = self.fund_manager.calculate_price_per_unit(latest_nav) if latest_nav > 0 else 0
        total_value = total_units * current_price

        # Calculate total fee income
        fee_transactions = [t for t in self.fund_manager.transactions 
                           if t.investor_id == fund_manager.id and t.type == 'Phí Nhận']
        total_fee_income = sum(t.amount for t in fee_transactions)

        # Average entry price
        total_invested = sum(t.invested_value for t in fm_tranches)
        avg_entry_price = total_invested / total_units if total_units > 0 else 0

        fm_summary['Value'] = [
            f"{total_units:.6f}",
            format_currency(total_value),
            len(fm_tranches),
            format_currency(total_fee_income),
            format_currency(avg_entry_price)
        ]

        df_fm_summary = pd.DataFrame(fm_summary)
        df_fm_summary.to_excel(writer, sheet_name='Fund Manager', index=False, startrow=0)

        # Tranches detail
        if fm_tranches:
            fm_tranches_data = []
            for tranche in fm_tranches:
                current_value = tranche.units * current_price if current_price > 0 else 0

                fm_tranches_data.append({
                    'Entry Date': tranche.entry_date,
                    'Entry NAV': format_currency(tranche.entry_nav),
                    'Units': f"{tranche.units:.6f}",
                    'Invested Value': format_currency(tranche.invested_value),
                    'Current Value': format_currency(current_value),
                    'Profit/Loss': format_currency(current_value - tranche.invested_value)
                })

            df_fm_tranches = pd.DataFrame(fm_tranches_data)
            df_fm_tranches.to_excel(writer, sheet_name='Fund Manager', index=False, startrow=8)

    def upload_to_drive(self, file_buffer: io.BytesIO, filename: str) -> bool:
        """Upload file to Google Drive with enhanced error handling"""
        if not self.connected or not self.service:
            self._log_error("Google Drive not connected")
            st.error("❌ Google Drive not connected")
            return False

        try:
            print(f"📤 Starting upload: {filename}")
            print(f"📊 File size: {len(file_buffer.getvalue())} bytes")
            print(f"📁 Target folder: {self.folder_id}")

            # Check if file_buffer has content
            if len(file_buffer.getvalue()) == 0:
                self._log_error("File buffer is empty")
                st.error("❌ Export produced empty buffer")
                return False

            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }

            # Reset buffer position
            file_buffer.seek(0)

            media = MediaIoBaseUpload(
                file_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )

            print("🚀 Uploading to Google Drive...")
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink',
                supportsAllDrives=True
            ).execute()

            # Get shareable link
            file_id = file.get('id')
            if file_id:
                print(f"✅ File uploaded successfully: {file_id}")

                # Make file publicly viewable (optional)
                try:
                    self.service.permissions().create(
                        fileId=file_id,
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                    print("🔓 File made publicly viewable")
                except Exception as perm_error:
                    print(f"⚠️ Could not set permissions: {perm_error}")

                web_link = file.get('webViewLink')
                if web_link:
                    print(f"🔗 File link: {web_link}")
                    st.success(f"✅ Uploaded to Google Drive: [{filename}]({web_link})")
                else:
                    st.success(f"✅ Uploaded to Google Drive: {filename}")

                return True
            else:
                self._log_error("No file ID returned from upload")
                st.error("❌ Upload failed: No file ID returned")
                return False

        except HttpError as http_error:
            error_detail = f"HTTP {http_error.resp.status}: {http_error.content.decode('utf-8') if getattr(http_error, 'content', None) else 'Unknown HTTP error'}"
            self._log_error(f"Google Drive HTTP error: {error_detail}")
            st.error(f"❌ Upload HTTP error: {http_error.resp.status}")
            return False

        except Exception as e:
            self._log_error(f"Upload error: {str(e)}")
            st.error(f"❌ Upload error: {str(e)}")
            print(f"📋 Full traceback:\n{traceback.format_exc()}")
            return False

    def auto_export_and_upload(self, trigger: str = "manual") -> bool:
        """Auto export to Excel and upload to Google Drive with enhanced error handling"""
        try:
            print(f"🎯 Starting auto export (trigger: {trigger})...")

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Fund_Export_{timestamp}_{trigger}.xlsx"
            print(f"📄 Generated filename: {filename}")

            # Export to buffer
            print("📊 Exporting to Excel buffer...")
            buffer = self.export_to_excel_buffer()

            if len(buffer.getvalue()) == 0:
                self._log_error("Excel buffer is empty")
                st.error("❌ Excel buffer is empty")
                return False

            # Save local backup
            local_backup_dir = Path("exports")
            local_backup_dir.mkdir(exist_ok=True)
            local_file = local_backup_dir / filename

            print(f"💾 Saving local backup: {local_file}")
            with open(local_file, 'wb') as f:
                f.write(buffer.getvalue())

            st.info(f"💾 Local backup saved: {local_file}")

            # Upload to Google Drive if connected
            if self.connected:
                print("☁️ Google Drive connected, starting upload...")
                buffer.seek(0)  # Reset buffer position
                success = self.upload_to_drive(buffer, filename)
                if success:
                    print("🧹 Running cleanup of old files...")
                    self._cleanup_old_files()
                return success
            else:
                print("⚠️ Google Drive not connected")
                st.warning("⚠️ Google Drive not connected. Only local backup saved.")
                return True

        except Exception as e:
            self._log_error(f"Auto export failed: {str(e)}")
            st.error(f"❌ Export error: {str(e)}")
            print(f"📋 Full traceback:\n{traceback.format_exc()}")
            return False

    def _cleanup_old_files(self, keep_days: int = 30):
        """Clean up old files from Google Drive"""
        if not self.connected:
            return

        try:
            print(f"🧹 Cleaning up files older than {keep_days} days...")

            # Calculate cutoff date
            cutoff_date = datetime.now() - pd.Timedelta(days=keep_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%S')

            # Query old files
            query = f"'{self.folder_id}' in parents and createdTime < '{cutoff_str}' and trashed=false"
            results = self.service.files().list(
                q=query, 
                fields="files(id, name, createdTime)",
                supportsAllDrives=True, 
                includeItemsFromAllDrives=True
            ).execute()
            files = results.get('files', [])

            print(f"🗑️ Found {len(files)} old files to delete")

            # Delete old files
            for file in files:
                try:
                    self.service.files().delete(fileId=file['id']).execute()
                    print(f"🗑️ Deleted: {file['name']} (Created: {file.get('createdTime', 'Unknown')})")
                    st.info(f"🗑️ Deleted old file: {file['name']}")
                except Exception as delete_error:
                    print(f"⚠️ Could not delete {file['name']}: {delete_error}")

        except Exception as e:
            self._log_error(f"Cleanup error: {str(e)}")
            print(f"⚠️ Cleanup error: {str(e)}")

    def schedule_monthly_export(self):
        """Schedule monthly export (to be called from main app)"""
        # Check if it's time for monthly export
        now = datetime.now()

        # Export on 1st day of month at 00:00
        if now.day == 1 and now.hour == 0 and now.minute < 5:
            print("📅 Running scheduled monthly export...")
            self.auto_export_and_upload(trigger="monthly")

        # Also export on last day of month
        import calendar
        last_day = calendar.monthrange(now.year, now.month)[1]
        if now.day == last_day and now.hour == 23 and now.minute > 55:
            print("📅 Running scheduled month-end export...")
            self.auto_export_and_upload(trigger="month_end")

    def get_error_log(self) -> List[str]:
        """Get error log for debugging"""
        return self.error_log

    def clear_error_log(self):
        """Clear error log"""
        self.error_log = []


class ExportManager:
    """Enhanced export manager for quick access"""

    @staticmethod
    def render_export_button(fund_manager):
        """Render enhanced export button in sidebar with debugging info"""
        with st.sidebar.expander("📤 Export & Backup"):
            col1, col2 = st.sidebar.columns(2)

            if col1.button("📊 Export Excel", use_container_width=True):
                gdrive = GoogleDriveManager(fund_manager)

                # Show connection status
                if gdrive.connected:
                    st.info(f"✅ Connected to folder: {gdrive.folder_id}")
                else:
                    st.warning("⚠️ Google Drive not connected")
                    # Show error log
                    error_log = gdrive.get_error_log()
                    if error_log:
                        st.error("Recent errors:")
                        for error in error_log[-3:]:
                            st.text(error)

                with st.spinner("🚀 Exporting..."):
                    success = gdrive.auto_export_and_upload(trigger="manual")

                if success:
                    st.balloons()
                else:
                    st.error("❌ Export failed. Check error log for details.")
                    # Show detailed error log
                    error_log = gdrive.get_error_log()
                    if error_log:
                        with st.expander("🔍 Error Details"):
                            for error in error_log[-5:]:
                                st.text(error)

            if col2.button("☁️ Test Drive", use_container_width=True):
                gdrive = GoogleDriveManager(fund_manager)

                # Detailed connection test
                st.info("🔍 Testing Google Drive connection...")

                if gdrive.connected:
                    st.success("✅ Google Drive connected successfully!")
                    st.info(f"📁 Folder ID: {gdrive.folder_id}")

                    try:
                        # Test folder access & user info
                        about = gdrive.service.about().get(fields="user,storageQuota").execute()
                        user_info = about.get('user', {})
                        st.info(f"👤 Connected as: {user_info.get('displayName', 'Unknown')}")
                        st.info(f"📧 Email: {user_info.get('emailAddress', 'Unknown')}")

                        # Test folder listing
                        results = gdrive.service.files().list(
                            q=f"'{gdrive.folder_id}' in parents and trashed=false",
                            fields="files(id, name, createdTime)",
                            pageSize=5,
                            supportsAllDrives=True,
                            includeItemsFromAllDrives=True
                        ).execute()
                        files = results.get('files', [])

                        if files:
                            st.info(f"📂 Found {len(files)} files in export folder")
                            for file in files[:3]:
                                st.text(f"  - {file.get('name', 'Unknown')}")
                        else:
                            st.info("📂 Export folder is empty")

                    except Exception as test_error:
                        st.error(f"❌ Connection test failed: {str(test_error)}")
                else:
                    st.error("❌ Google Drive connection failed")
                    # Show detailed error information
                    error_log = gdrive.get_error_log()
                    if error_log:
                        with st.expander("🔍 Connection Errors"):
                            for error in error_log:
                                st.text(error)

                    # Show troubleshooting tips
                    with st.expander("🛠️ Troubleshooting"):
                        st.markdown("""
                        **Check these items:**
                        1. **Streamlit Secrets**: `.streamlit/secrets.toml` contains `[google_service_account]`
                        2. **Environment Variable**: `GOOGLE_SERVICE_ACCOUNT_JSON` is set
                        3. **Local File**: `service_account.json` exists in project root
                        4. **Service Account Permissions**: Has access to Google Drive API
                        5. **API Enabled**: Google Drive API is enabled in Google Cloud Console
                        """)

            # Show last export info
            export_dir = Path("exports")
            if export_dir.exists():
                excel_files = list(export_dir.glob("*.xlsx"))
                if excel_files:
                    latest_file = max(excel_files, key=lambda x: x.stat().st_mtime)
                    file_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                    st.text(f"📋 Last export: {file_time.strftime('%Y-%m-%d %H:%M')}")

            # Auto-export on data change
            if st.session_state.get('data_changed', False):
                with st.spinner("Auto-saving to Google Drive..."):
                    gdrive = GoogleDriveManager(fund_manager)
                    success = gdrive.auto_export_and_upload(trigger="auto_save")
                    if not success:
                        st.warning("⚠️ Auto-save failed, but data is saved locally")
                st.session_state.data_changed = False