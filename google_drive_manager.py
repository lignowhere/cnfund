#!/usr/bin/env python3
"""
Google Drive Manager for Auto Export to Excel
Automatically exports fund data to Excel and uploads to Google Drive
"""

import os
import io
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import streamlit as st

# Google Drive API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    st.warning("⚠️ Google API libraries not installed. Run: pip install google-api-python-client google-auth")

from utils import format_currency, format_percentage

class GoogleDriveManager:
    """Manager for Google Drive operations and Excel exports"""
    
    def __init__(self, fund_manager):
        self.fund_manager = fund_manager
        self.service = None
        self.folder_id = None
        self.connected = False
        
        if GOOGLE_API_AVAILABLE:
            self._initialize_drive_service()
    
    def _initialize_drive_service(self):
        """Initialize Google Drive service using service account"""
        try:
            # Try multiple methods to get credentials
            creds = self._get_credentials()
            
            if creds:
                self.service = build('drive', 'v3', credentials=creds)
                self.folder_id = self._get_or_create_folder()
                self.connected = True
                st.sidebar.success("✅ Google Drive connected")
            else:
                st.sidebar.warning("⚠️ Google Drive not configured")
                
        except Exception as e:
            st.sidebar.error(f"❌ Google Drive error: {str(e)}")
            self.connected = False
    
    def _get_credentials(self):
        """Get Google credentials from various sources"""
        # Method 1: From Streamlit secrets
        try:
            if 'google_service_account' in st.secrets:
                creds = service_account.Credentials.from_service_account_info(
                    st.secrets['google_service_account'],
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                return creds
        except:
            pass
        
        # Method 2: From environment variable (JSON string)
        try:
            import json
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                service_account_info = json.loads(service_account_json)
                creds = service_account.Credentials.from_service_account_info(
                    service_account_info,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                return creds
        except:
            pass
        
        # Method 3: From local file
        try:
            service_account_file = 'service_account.json'
            if os.path.exists(service_account_file):
                creds = service_account.Credentials.from_service_account_file(
                    service_account_file,
                    scopes=['https://www.googleapis.com/auth/drive.file']
                )
                return creds
        except:
            pass
        
        return None
    
    def _get_or_create_folder(self, folder_name: str = "Fund_Management_Exports") -> Optional[str]:
        """Get or create a folder in Google Drive"""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # Create new folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')
            
        except Exception as e:
            st.error(f"Error creating folder: {str(e)}")
            return None
    
    def export_to_excel_buffer(self) -> io.BytesIO:
        """Export all data to Excel in memory"""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 1. Summary Sheet
            self._create_summary_sheet(writer)
            
            # 2. Investors Sheet
            self._create_investors_sheet(writer)
            
            # 3. Tranches Sheet
            self._create_tranches_sheet(writer)
            
            # 4. Transactions Sheet
            self._create_transactions_sheet(writer)
            
            # 5. Fee Records Sheet
            self._create_fee_records_sheet(writer)
            
            # 6. Performance Sheet
            self._create_performance_sheet(writer)
            
            # 7. Fund Manager Sheet
            self._create_fund_manager_sheet(writer)
        
        buffer.seek(0)
        return buffer
    
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
            
            media = MediaIoBaseUpload(
                file_buffer,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            # Get shareable link
            file_id = file.get('id')
            if file_id:
                # Make file publicly viewable (optional)
                self.service.permissions().create(
                    fileId=file_id,
                    body={'type': 'anyone', 'role': 'reader'}
                ).execute()
                
                web_link = file.get('webViewLink')
                st.success(f"✅ Uploaded to Google Drive: [{filename}]({web_link})")
                return True
            
            return False
            
        except Exception as e:
            st.error(f"❌ Upload error: {str(e)}")
            return False
    
    def auto_export_and_upload(self, trigger: str = "manual") -> bool:
        """Auto export to Excel and upload to Google Drive"""
        try:
            # Generate filename with timestamp
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
            
            st.info(f"💾 Local backup saved: {local_file}")
            
            # Upload to Google Drive if connected
            if self.connected:
                buffer.seek(0)  # Reset buffer position
                success = self.upload_to_drive(buffer, filename)
                if success:
                    self._cleanup_old_files()
                return success
            else:
                st.warning("⚠️ Google Drive not connected. Only local backup saved.")
                return True
                
        except Exception as e:
            st.error(f"❌ Export error: {str(e)}")
            return False
    
    def _cleanup_old_files(self, keep_days: int = 30):
        """Clean up old files from Google Drive"""
        if not self.connected:
            return
        
        try:
            # Calculate cutoff date
            cutoff_date = datetime.now() - pd.Timedelta(days=keep_days)
            cutoff_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Query old files
            query = f"'{self.folder_id}' in parents and createdTime < '{cutoff_str}' and trashed=false"
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            
            # Delete old files
            for file in files:
                self.service.files().delete(fileId=file['id']).execute()
                st.info(f"🗑️ Deleted old file: {file['name']}")
                
        except Exception as e:
            st.warning(f"⚠️ Cleanup error: {str(e)}")
    
    def schedule_monthly_export(self):
        """Schedule monthly export (to be called from main app)"""
        # Check if it's time for monthly export
        now = datetime.now()
        
        # Export on 1st day of month at 00:00
        if now.day == 1 and now.hour == 0 and now.minute < 5:
            self.auto_export_and_upload(trigger="monthly")
        
        # Also export on last day of month
        import calendar
        last_day = calendar.monthrange(now.year, now.month)[1]
        if now.day == last_day and now.hour == 23 and now.minute > 55:
            self.auto_export_and_upload(trigger="month_end")


class ExportManager:
    """Simplified export manager for quick access"""
    
    @staticmethod
    def render_export_button(fund_manager):
        """Render export button in sidebar"""
        with st.sidebar.expander("📤 Export & Backup"):
            col1, col2 = st.sidebar.columns(2)
            
            if col1.button("📊 Export Excel", use_container_width=True):
                gdrive = GoogleDriveManager(fund_manager)
                success = gdrive.auto_export_and_upload(trigger="manual")
                if success:
                    st.balloons()
            
            if col2.button("☁️ Test Drive", use_container_width=True):
                gdrive = GoogleDriveManager(fund_manager)
                if gdrive.connected:
                    st.success("✅ Google Drive connected successfully!")
                else:
                    st.error("❌ Google Drive connection failed")
            
            # Auto-export on data change
            if st.session_state.get('data_changed', False):
                with st.spinner("Auto-saving to Google Drive..."):
                    gdrive = GoogleDriveManager(fund_manager)
                    gdrive.auto_export_and_upload(trigger="auto_save")
                st.session_state.data_changed = False