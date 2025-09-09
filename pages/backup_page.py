#!/usr/bin/env python3
"""
Backup Management Dashboard Page
Provides comprehensive backup management UI
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import plotly.express as px
import plotly.graph_objects as go
from chart_utils import safe_plotly_chart
from pathlib import Path
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from auth_helper import check_admin_authentication, show_admin_status

def show_backup_status_cards(fund_manager):
    """Display backup status cards"""
    status = fund_manager.get_backup_status()
    
    if not status['enabled']:
        st.error("🚫 Backup system is DISABLED")
        return
    
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Check storage type for appropriate stats (check both locations)
    storage_type = status.get('storage_type', 'local')  # First check root level
    if storage_type == 'local' and 'storage' in status:
        storage_type = status['storage'].get('storage_type', 'local')  # Fallback to nested
    
    if storage_type == 'supabase_database':
        backup_stats = status.get('database_backups', {})
    else:
        backup_stats = status.get('daily_backups', {})
    
    with col1:
        st.metric(
            label="📅 Total Backups",
            value=backup_stats.get('total', 0),
            delta=f"{backup_stats.get('recent_7_days', 0)} last 7 days"
        )
    
    with col2:
        storage_label = "☁️ Cloud Storage" if storage_type == 'supabase_database' else "💾 Local Storage"
        
        # Get compression status
        compression_enabled = False
        if 'storage' in status:
            compression_enabled = status['storage'].get('compression_enabled', False)
        
        st.metric(
            label=storage_label,
            value=f"{backup_stats.get('total_size_mb', 0):.1f} MB",
            delta="Compressed" if compression_enabled else "Uncompressed"
        )
    
    with col3:
        ops_stats = status.get('operation_snapshots', {'current_count': 0, 'max_count': 50})
        st.metric(
            label="⚡ Op. Snapshots",
            value=f"{ops_stats['current_count']}/{ops_stats['max_count']}",
            delta="In Memory"
        )
    
    with col4:
        last_backup = backup_stats.get('last_backup_date')
        if last_backup:
            try:
                days_ago = (date.today() - date.fromisoformat(last_backup)).days
                delta_text = "Today" if days_ago == 0 else f"{days_ago} days ago"
            except:
                delta_text = "Recent"
        else:
            delta_text = "Never"
        
        st.metric(
            label="🕐 Last Backup",
            value=last_backup or "Never",
            delta=delta_text
        )

def show_backup_controls(fund_manager):
    """Display backup control buttons"""
    st.subheader("🎛️ Backup Controls")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Create Manual Backup", type="primary"):
            with st.spinner("Creating backup..."):
                backup_id = fund_manager.create_manual_backup("MANUAL_UI")
                if backup_id:
                    st.success(f"✅ Backup created: `{backup_id}`")
                    st.rerun()
                else:
                    st.error("❌ Failed to create backup")
    
    with col2:
        if st.button("🚨 Emergency Backup", type="secondary"):
            with st.spinner("Creating emergency backup..."):
                backup_id = fund_manager.create_emergency_backup()
                if backup_id:
                    st.success(f"✅ Emergency backup: `{backup_id}`")
                    st.rerun()
                else:
                    st.error("❌ Failed to create emergency backup")
    
    with col3:
        if st.button("🤖 Trigger Auto Backup"):
            with st.spinner("Triggering auto backup..."):
                success = fund_manager.trigger_auto_backup_if_needed()
                if success:
                    st.success("✅ Auto backup completed")
                    st.rerun()
                else:
                    st.info("ℹ️ Auto backup not needed (already completed today)")
    
    with col4:
        if st.button("🔍 Validate Data"):
            with st.spinner("Validating data integrity..."):
                result = fund_manager.validate_data_integrity(detailed=False)
                if result['is_valid']:
                    st.success(f"✅ Data integrity OK ({result['summary']['total_warnings']} warnings)")
                else:
                    st.error(f"❌ Data integrity issues: {result['summary']['total_errors']} errors")
                    with st.expander("Show Errors"):
                        for error in result['errors']:
                            st.error(error)
    
    # Add download backup feature for cloud environment
    if hasattr(fund_manager.backup_manager, 'create_downloadable_backup'):
        st.markdown("---")
        st.subheader("📥 Download Backup")
        
        col_download1, col_download2 = st.columns([3, 1])
        
        with col_download1:
            st.info("💡 **Download Backup**: Create a local backup file you can save to your computer")
        
        with col_download2:
            if st.button("📥 Create Download", type="secondary"):
                with st.spinner("Creating downloadable backup..."):
                    try:
                        filename, backup_bytes = fund_manager.backup_manager.create_downloadable_backup(fund_manager)
                        
                        if filename and backup_bytes:
                            st.download_button(
                                label="💾 Download Backup File",
                                data=backup_bytes,
                                file_name=filename,
                                mime="application/gzip" if filename.endswith('.gz') else "application/json",
                                type="primary"
                            )
                            st.success(f"✅ Backup ready: `{filename}` ({len(backup_bytes)/1024:.1f} KB)")
                        else:
                            st.error("❌ Failed to create downloadable backup")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

def show_backup_history(fund_manager):
    """Display backup history table"""
    st.subheader("📋 Backup History")
    
    # Filter controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        days_filter = st.selectbox(
            "Show backups from last:",
            options=[7, 14, 30, 60, 90],
            index=2,  # Default 30 days
            format_func=lambda x: f"{x} days"
        )
    
    with col2:
        backup_types = ["All", "MANUAL", "AUTO", "EMERGENCY", "PRE_RESTORE"]
        type_filter = st.selectbox("Backup Type:", backup_types)
    
    with col3:
        st.write("")  # Spacer
        refresh_button = st.button("🔄 Refresh")
    
    # Get backup data
    backups = fund_manager.list_available_backups(days_filter)
    
    # Apply type filter
    if type_filter != "All":
        backups = [b for b in backups if b['backup_type'] == type_filter]
    
    if not backups:
        st.info("No backups found for the selected criteria")
        return
    
    # Convert to DataFrame for better display
    backup_data = []
    for backup in backups:
        backup_date = backup['date']
        backup_time = datetime.fromisoformat(backup['timestamp']).strftime('%H:%M:%S')
        
        backup_data.append({
            'ID': backup['backup_id'],
            'Type': backup['backup_type'],
            'Date': backup_date,
            'Time': backup_time,
            'Size (MB)': f"{backup['file_size_mb']:.2f}",
            'Investors': backup['investors_count'],
            'Tranches': backup['tranches_count'],
            'Transactions': backup['transactions_count'],
            'Fee Records': backup['fee_records_count']
        })
    
    df = pd.DataFrame(backup_data)
    
    # Display table with selection
    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config={
            'ID': st.column_config.TextColumn('Backup ID', width="large"),
            'Type': st.column_config.SelectboxColumn('Type', width="small"),
            'Date': st.column_config.DateColumn('Date', width="medium"),
            'Time': st.column_config.TimeColumn('Time', width="small"),
            'Size (MB)': st.column_config.NumberColumn('Size (MB)', format="%.2f")
        }
    )
    
    return backups

def show_restore_controls(fund_manager, backups):
    """Display restore controls"""
    st.subheader("🔄 Restore Operations")
    
    if not backups:
        st.warning("No backups available for restore")
        return
    
    # Restore by backup selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Create options for selectbox
        backup_options = [""] + [f"{b['backup_id']} ({b['backup_type']}) - {b['date']}" for b in backups]
        selected_backup = st.selectbox(
            "Select backup to restore:",
            options=backup_options,
            help="Choose a backup from the history above"
        )
    
    with col2:
        st.write("")  # Spacer for alignment
        restore_button = st.button("🔄 Restore Selected", type="primary")
    
    # Restore by date
    st.write("**Or restore latest backup from specific date:**")
    col3, col4 = st.columns([2, 1])
    
    with col3:
        restore_date = st.date_input(
            "Select date:",
            value=date.today(),
            max_value=date.today(),
            help="Will restore the latest backup from this date"
        )
    
    with col4:
        st.write("")  # Spacer
        restore_date_button = st.button("🔄 Restore by Date")
    
    # Handle restore operations
    if restore_button and selected_backup and selected_backup != "":
        backup_id = selected_backup.split(" ")[0]  # Extract backup ID
        
        # Confirmation
        st.warning("⚠️ **WARNING**: This will OVERWRITE current data!")
        
        confirm_restore = st.checkbox("I understand this will replace all current data")
        
        if confirm_restore:
            if st.button("⚠️ CONFIRM RESTORE", type="secondary"):
                with st.spinner("Restoring backup..."):
                    success = fund_manager.restore_from_backup(backup_id=backup_id)
                    if success:
                        st.success("✅ Restore completed successfully!")
                        st.info("💡 Data has been restored. Please refresh other pages to see changes.")
                        st.balloons()
                    else:
                        st.error("❌ Restore failed. Check logs for details.")
    
    if restore_date_button:
        # Confirmation for date restore
        st.warning("⚠️ **WARNING**: This will OVERWRITE current data!")
        
        confirm_date_restore = st.checkbox("I understand this will restore latest backup from selected date")
        
        if confirm_date_restore:
            if st.button("⚠️ CONFIRM DATE RESTORE", type="secondary"):
                with st.spinner("Restoring from date..."):
                    success = fund_manager.restore_from_backup(backup_date=restore_date.isoformat())
                    if success:
                        st.success("✅ Date restore completed successfully!")
                        st.info("💡 Data has been restored. Please refresh other pages to see changes.")
                        st.balloons()
                    else:
                        st.error("❌ Date restore failed. Check logs for details.")

def show_backup_charts(fund_manager):
    """Display backup charts and analytics"""
    st.subheader("📊 Backup Analytics")
    
    backups = fund_manager.list_available_backups(30)  # Last 30 days
    
    if not backups:
        st.info("No backup data available for charts")
        return
    
    # Prepare data for charts
    df = pd.DataFrame(backups)
    df['date'] = pd.to_datetime(df['date'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Backup frequency by date
        daily_counts = df.groupby('date').size().reset_index(name='count')
        
        fig_freq = px.bar(
            daily_counts,
            x='date',
            y='count',
            title='Daily Backup Frequency',
            labels={'count': 'Number of Backups', 'date': 'Date'}
        )
        fig_freq.update_layout(height=300)
        safe_plotly_chart(fig_freq, use_container_width=True)
    
    with col2:
        # Backup size over time
        fig_size = px.line(
            df.sort_values('timestamp'),
            x='timestamp',
            y='file_size_mb',
            color='backup_type',
            title='Backup Size Trend',
            labels={'file_size_mb': 'Size (MB)', 'timestamp': 'Time'}
        )
        fig_size.update_layout(height=300)
        safe_plotly_chart(fig_size, use_container_width=True)
    
    # Backup type distribution
    type_counts = df['backup_type'].value_counts()
    
    fig_pie = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title='Backup Types Distribution'
    )
    fig_pie.update_layout(height=300)
    safe_plotly_chart(fig_pie, use_container_width=True)

def show_backup_settings(fund_manager):
    """Display backup settings panel"""
    st.subheader("⚙️ Backup Settings")
    
    status = fund_manager.get_backup_status()
    
    if not status['enabled']:
        st.error("Backup system is disabled")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Current Settings:**")
        
        # Check if cloud environment
        storage_type = status['storage'].get('storage_type', 'local')
        environment = status['storage'].get('environment', 'Local')
        
        if storage_type == 'supabase_database':
            st.write(f"☁️ Environment: **{environment}**")
            st.write(f"🗄️ Storage: **{status['storage'].get('backup_location', 'Supabase Database')}**")
            st.write(f"🗜️ Compression: {'✅ Enabled' if status['storage']['compression_enabled'] else '❌ Disabled'}")
            st.write(f"📊 Database Backups: {status.get('database_backups', {}).get('total', 0)}")
        else:
            st.write(f"📁 Backup Directory: `{status['storage'].get('backup_dir', 'N/A')}`")
            st.write(f"🗜️ Compression: {'✅ Enabled' if status['storage']['compression_enabled'] else '❌ Disabled'}")
            st.write(f"📅 Schedule: {status['auto_backup']['next_backup']}")
        
        st.write(f"🤖 Auto Backup: {'✅ Enabled' if status['auto_backup']['enabled'] else '❌ Disabled'}")
        st.write(f"⚡ Max Operation Snapshots: {status['operation_snapshots']['max_count']}")
    
    with col2:
        st.info("**Storage Info:**")
        
        # Use appropriate stats based on backup type
        if storage_type == 'supabase_database':
            db_stats = status.get('database_backups', {})
            st.write(f"💾 Total Backups: {db_stats.get('total', 0)}")
            st.write(f"📊 Total Size: {db_stats.get('total_size_mb', 0):.2f} MB")
            st.write(f"🕐 Last Backup: {db_stats.get('last_backup_date') or 'Never'}")
            st.write(f"📈 Recent (7 days): {db_stats.get('recent_7_days', 0)}")
            
            # Storage usage breakdown
            if db_stats.get('total', 0) > 0:
                avg_size = db_stats.get('total_size_mb', 0) / db_stats.get('total', 1)
                st.write(f"📏 Average Size: {avg_size:.2f} MB/backup")
        else:
            daily_stats = status.get('daily_backups', {})
            st.write(f"💾 Total Backups: {daily_stats.get('total', 0)}")
            st.write(f"📊 Total Size: {daily_stats.get('total_size_mb', 0):.2f} MB")
            st.write(f"🕐 Last Backup: {daily_stats.get('last_backup_date') or 'Never'}")
            
            # Storage usage breakdown
            if daily_stats.get('total', 0) > 0:
                avg_size = daily_stats.get('total_size_mb', 0) / daily_stats.get('total', 1)
                st.write(f"📏 Average Size: {avg_size:.2f} MB/backup")

def show_operation_snapshots(fund_manager):
    """Display operation snapshots info"""
    st.subheader("⚡ Operation Snapshots")
    
    if not fund_manager.backup_manager:
        st.error("Backup manager not available")
        return
    
    snapshots = fund_manager.backup_manager.list_operation_snapshots()
    
    if not snapshots:
        st.info("No operation snapshots available")
        return
    
    # Display snapshots
    snapshot_data = []
    for snap in snapshots[:20]:  # Show last 20
        timestamp = datetime.fromisoformat(snap['timestamp'])
        snapshot_data.append({
            'ID': snap['id'],
            'Operation': snap['operation_type'],
            'Time': timestamp.strftime('%H:%M:%S'),
            'Date': timestamp.strftime('%Y-%m-%d'),
            'Description': snap.get('description', ''),
            'Size (MB)': f"{snap.get('size_mb', 0):.2f}"
        })
    
    df = pd.DataFrame(snapshot_data)
    st.dataframe(df, width="stretch", hide_index=True)
    
    if len(snapshots) > 20:
        st.info(f"Showing latest 20 of {len(snapshots)} operation snapshots")

def main():
    """Main backup dashboard page"""
    st.title("💾 Backup Management Dashboard")
    
    # Show admin authentication status with logout option (authenticated by main app already)
    show_admin_status()
    
    st.markdown("---")
    
    # Get fund manager from session state (set by main app)
    fund_manager = st.session_state.get('fund_manager')
    
    if not fund_manager:
        st.error("🚫 Fund Manager not initialized. Please go to main page first.")
        st.info("💡 This usually happens if you accessed this page directly. Please go through the main application.")
        return
    
    if not hasattr(fund_manager, 'backup_manager') or not fund_manager.backup_manager:
        st.error("🚫 Backup system not enabled.")
        st.info("💡 Backup system may be disabled in the fund manager configuration.")
        
        # Debug information
        with st.expander("🔍 Debug Information"):
            st.write("**Fund Manager Type:**", type(fund_manager).__name__)
            st.write("**Has backup_manager attribute:**", hasattr(fund_manager, 'backup_manager'))
            if hasattr(fund_manager, 'backup_manager'):
                st.write("**backup_manager value:**", fund_manager.backup_manager)
            
            # Check data handler
            if hasattr(fund_manager, 'data_handler'):
                data_handler = fund_manager.data_handler
                st.write("**Data Handler Type:**", type(data_handler).__name__)
                st.write("**Data Handler connected:**", getattr(data_handler, 'connected', 'No connected attribute'))
                st.write("**Data Handler has engine:**", hasattr(data_handler, 'engine'))
                if hasattr(data_handler, 'engine'):
                    st.write("**Engine value:**", data_handler.engine)
        return
    
    # Auto-refresh every 30 seconds
    if st.button("🔄 Auto Refresh (30s)", help="Auto refresh the dashboard"):
        st.rerun()
    
    # Main dashboard sections
    show_backup_status_cards(fund_manager)
    
    st.markdown("---")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎛️ Controls", 
        "📋 History", 
        "🔄 Restore", 
        "📊 Analytics", 
        "⚙️ Settings"
    ])
    
    with tab1:
        show_backup_controls(fund_manager)
        st.markdown("---")
        show_operation_snapshots(fund_manager)
    
    with tab2:
        backups = show_backup_history(fund_manager)
    
    with tab3:
        backups = fund_manager.list_available_backups(30)
        show_restore_controls(fund_manager, backups)
    
    with tab4:
        show_backup_charts(fund_manager)
    
    with tab5:
        show_backup_settings(fund_manager)
    
    # Footer
    st.markdown("---")
    st.markdown("*💾 Backup Dashboard - Protecting your fund data 24/7*")

if __name__ == "__main__":
    main()