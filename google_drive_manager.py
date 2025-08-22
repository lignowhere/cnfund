#!/usr/bin/env python3
"""
Fixed Google Drive Manager - Works with Streamlit UI
"""

import os
import io
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import streamlit as st
import traceback
import json

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
    """Fixed Manager for Google Drive operations and Excel exports"""

    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.service = None
        self.folder_id = None
        self.connected = False
        self.error_log: List[str] = []

        if GOOGLE_API_AVAILABLE:
            self._initialize_drive_service()

    def _log_error(self, message: str, error: Exception = None):
        """Log error with details"""
        error_msg = f"{datetime.now().strftime('%H:%M:%S')}: {message}"
        if error:
            error_msg += f" - {str(error)}"
        self.error_log.append(error_msg)
        print(f"ERROR: {error_msg}")

    def _initialize_drive_service(self):
        """Initialize with better Streamlit compatibility"""
        try:
            creds = self._get_credentials_streamlit()
            
            if creds:
                self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)
                
                # Get folder ID from secrets or use default
                self.folder_id = self._get_folder_id()
                
                # Test connection
                try:
                    about = self.service.about().get(fields="user").execute()
                    user = about.get('user', {})
                    print(f"✅ Connected as: {user.get('displayName', 'Unknown')}")
                    self.connected = True
                    
                    # Don't show success in sidebar during initialization
                    # It will be shown by ExportManager
                    
                except Exception as test_error:
                    self._log_error("Connection test failed", test_error)
                    self.connected = False
            else:
                self._log_error("No valid credentials found")
                self.connected = False
                
        except Exception as e:
            self._log_error("Initialization failed", e)
            self.connected = False

    def _get_credentials_streamlit(self):
        """Get credentials optimized for Streamlit"""
        try:
            # Priority 1: Check Streamlit secrets first (most reliable in Streamlit)
            if hasattr(st, 'secrets'):
                # Try different secret structures
                service_account_info = None
                
                # Structure 1: Direct google_service_account
                if 'google_service_account' in st.secrets:
                    service_account_info = dict(st.secrets['google_service_account'])
                    print("📋 Using st.secrets['google_service_account']")
                
                # Structure 2: Under default section
                elif 'default' in st.secrets and 'google_service_account' in st.secrets['default']:
                    service_account_info = dict(st.secrets['default']['google_service_account'])
                    print("📋 Using st.secrets['default']['google_service_account']")
                
                # Structure 3: Individual fields in secrets
                elif 'type' in st.secrets and st.secrets['type'] == 'service_account':
                    service_account_info = {
                        'type': st.secrets['type'],
                        'project_id': st.secrets.get('project_id'),
                        'private_key_id': st.secrets.get('private_key_id'),
                        'private_key': st.secrets.get('private_key'),
                        'client_email': st.secrets.get('client_email'),
                        'client_id': st.secrets.get('client_id'),
                        'auth_uri': st.secrets.get('auth_uri'),
                        'token_uri': st.secrets.get('token_uri'),
                        'auth_provider_x509_cert_url': st.secrets.get('auth_provider_x509_cert_url'),
                        'client_x509_cert_url': st.secrets.get('client_x509_cert_url')
                    }
                    print("📋 Using individual st.secrets fields")
                
                if service_account_info:
                    # Clean up the private key (handle newline issues)
                    if 'private_key' in service_account_info:
                        private_key = service_account_info['private_key']
                        if isinstance(private_key, str):
                            # Fix newline characters
                            private_key = private_key.replace('\\n', '\n')
                            service_account_info['private_key'] = private_key
                    
                    creds = service_account.Credentials.from_service_account_info(
                        service_account_info,
                        scopes=['https://www.googleapis.com/auth/drive.file']
                    )
                    print("✅ Credentials loaded from Streamlit secrets")
                    return creds
                    
        except Exception as e:
            self._log_error(f"Streamlit secrets failed", e)

        # Priority 2: Environment variable
        try:
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                service_account_info = json.loads(service_account_json)
                creds = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                print("✅ Credentials loaded from environment variable")
                return creds
        except Exception as e:
            self._log_error(f"Environment variable failed", e)

        # Priority 3: Local file
        try:
            service_account_file = 'service_account.json'
            if os.path.exists(service_account_file):
                creds = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                print("✅ Credentials loaded from local file")
                return creds
        except Exception as e:
            self._log_error(f"Local file failed", e)

        return None

    def _get_folder_id(self) -> str:
        """Get folder ID from various sources"""
        folder_id = None
        
        # Try to get from Streamlit secrets
        if hasattr(st, 'secrets'):
            if 'drive_folder_id' in st.secrets:
                folder_id = st.secrets['drive_folder_id']
            elif 'default' in st.secrets and 'drive_folder_id' in st.secrets['default']:
                folder_id = st.secrets['default']['drive_folder_id']
        
        # Try environment variable
        if not folder_id:
            folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        
        # Use your specific folder ID as fallback
        if not folder_id:
            folder_id = '1BGrypQLMNmEDcmKntPMiPAgCB6GZsHno'
        
        print(f"📂 Using folder ID: {folder_id}")
        return folder_id

    def test_connection(self) -> Dict[str, Any]:
        """Test connection and return detailed info"""
        result = {
            'connected': False,
            'user': None,
            'folder_access': False,
            'files_count': 0,
            'errors': []
        }
        
        if not self.connected or not self.service:
            result['errors'].append("Not connected to Google Drive")
            return result
        
        try:
            # Get user info
            about = self.service.about().get(fields="user").execute()
            user_info = about.get('user', {})
            result['user'] = {
                'name': user_info.get('displayName', 'Unknown'),
                'email': user_info.get('emailAddress', 'Unknown')
            }
            result['connected'] = True
            
            # Test folder access
            try:
                results = self.service.files().list(
                    q=f"'{self.folder_id}' in parents and trashed=false",
                    fields="files(id, name)",
                    pageSize=10,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()
                files = results.get('files', [])
                result['folder_access'] = True
                result['files_count'] = len(files)
            except Exception as folder_error:
                result['errors'].append(f"Folder access error: {str(folder_error)}")
                
        except Exception as e:
            result['errors'].append(f"Connection test error: {str(e)}")
            
        return result

    def export_to_excel_buffer(self) -> io.BytesIO:
        """Export all data to Excel in memory"""
        buffer = io.BytesIO()

        try:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                self._create_summary_sheet(writer)
                self._create_investors_sheet(writer)
                self._create_tranches_sheet(writer)
                self._create_transactions_sheet(writer)
                self._create_fee_records_sheet(writer)
                self._create_performance_sheet(writer)
                self._create_fund_manager_sheet(writer)

            buffer.seek(0)
            return buffer

        except Exception as e:
            self._log_error("Excel export failed", e)
            raise

    # [Copy all the _create_*_sheet methods from the original file - they remain the same]
    # I'm omitting them here for brevity, but they should be included

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
        """Upload file to Google Drive"""
        if not self.connected or not self.service:
            st.error("❌ Google Drive not connected")
            return False

        try:
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }

            file_buffer.seek(0)

            media = MediaIoBaseUpload(
                file_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink',
                supportsAllDrives=True
            ).execute()

            file_id = file.get('id')
            if file_id:
                # Try to set permissions (optional)
                try:
                    self.service.permissions().create(
                        fileId=file_id,
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                except:
                    pass  # Ignore permission errors

                web_link = file.get('webViewLink', '')
                if web_link:
                    st.success(f"✅ Uploaded: [{filename}]({web_link})")
                else:
                    st.success(f"✅ Uploaded: {filename}")
                return True

            return False

        except Exception as e:
            self._log_error(f"Upload failed", e)
            st.error(f"❌ Upload error: {str(e)}")
            return False

    def auto_export_and_upload(self, trigger: str = "manual") -> bool:
        """Auto export to Excel and upload to Google Drive"""
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Fund_Export_{timestamp}_{trigger}.xlsx"

            # Export to buffer
            buffer = self.export_to_excel_buffer()

            # Save local backup
            local_backup_dir = Path("exports")
            local_backup_dir.mkdir(exist_ok=True)
            local_file = local_backup_dir / filename

            with open(local_file, 'wb') as f:
                f.write(buffer.getvalue())

            st.info(f"💾 Local backup: {local_file}")

            # Upload to Google Drive if connected
            if self.connected:
                buffer.seek(0)
                return self.upload_to_drive(buffer, filename)
            else:
                st.warning("⚠️ Google Drive not connected. Only local backup saved.")
                return True

        except Exception as e:
            self._log_error(f"Export failed", e)
            st.error(f"❌ Export error: {str(e)}")
            return False

    def schedule_monthly_export(self):
        """Schedule monthly export"""
        pass  # Simplified for now


class ExportManager:
    """Simplified export manager"""

    @staticmethod
    def render_export_button(fund_manager):
        """Render export button in sidebar"""
        with st.sidebar.expander("📤 Export & Backup"):
            col1, col2 = st.sidebar.columns(2)

            if col1.button("📊 Export", use_container_width=True, key="export_btn"):
                try:
                    gdrive = GoogleDriveManager(fund_manager)
                    with st.spinner("Exporting..."):
                        success = gdrive.auto_export_and_upload(trigger="manual")
                    if success:
                        st.balloons()
                except Exception as e:
                    st.error(f"Export failed: {str(e)}")

            if col2.button("☁️ Test", use_container_width=True, key="test_btn"):
                try:
                    gdrive = GoogleDriveManager(fund_manager)
                    test_result = gdrive.test_connection()
                    
                    if test_result['connected']:
                        st.success("✅ Connected!")
                        if test_result['user']:
                            st.info(f"User: {test_result['user']['name']}")
                            st.info(f"Files: {test_result['files_count']}")
                    else:
                        st.error("❌ Not connected")
                        for error in test_result['errors']:
                            st.error(error)
                except Exception as e:
                    st.error(f"Test failed: {str(e)}")