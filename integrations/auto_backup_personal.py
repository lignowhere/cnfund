#!/usr/bin/env python3
"""
Comprehensive Auto Backup System for Personal Google Drive
Integrates local backup + personal Google Drive with multiple triggers
"""

import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
import streamlit as st

class PersonalAutoBackupManager:
    """
    Complete auto backup solution for personal Google Drive
    Features:
    - Local backup (always reliable)
    - Personal Google Drive backup (OAuth-based) 
    - Multiple triggers: manual, schedule, data changes, app events
    - Smart deduplication and cleanup
    """
    
    def __init__(self, fund_manager=None):
        self.fund_manager = fund_manager
        self.running = False
        self.backup_thread = None
        self.last_backup_time = None
        self.backup_count_today = 0
        self.backup_stats = {
            'total_backups': 0,
            'successful_local': 0,
            'successful_cloud': 0,
            'failed_backups': 0,
            'last_error': None
        }
        
        # Configuration
        self.config = {
            'local_backup': True,           # Always enabled
            'cloud_backup': True,           # Depends on OAuth setup
            'auto_schedule': True,          # Daily scheduled backups
            'backup_on_changes': True,      # Backup when data changes
            'max_daily_backups': 5,        # Limit per day
            'backup_hour': 23,              # Daily backup time (23:00)
            'backup_interval_hours': 6,     # Minimum hours between auto backups
        }
        
        # Initialize managers
        self.local_backup_dir = Path("exports")
        self.local_backup_dir.mkdir(exist_ok=True)
        
        # Get hybrid drive manager
        self.drive_manager = None
        if fund_manager:
            self._init_drive_manager()
        
        print("🚀 PersonalAutoBackupManager initialized")
    
    def _init_drive_manager(self):
        """Initialize Google Drive manager"""
        try:
            from integrations.google_drive_oauth import GoogleDriveOAuthManager
            self.drive_manager = GoogleDriveOAuthManager()

            if self.drive_manager.connected:
                print(f"📋 Drive Manager: OAuth")
                print(f"📋 Connected: {self.drive_manager.connected}")
            else:
                print("⚠️ Drive manager not connected - OAuth setup required")

        except Exception as e:
            print(f"⚠️ Drive manager init failed: {e}")
            self.drive_manager = None
    
    def start_auto_backup_service(self):
        """Start the auto backup background service"""
        if self.running:
            return
        
        self.running = True
        self.backup_thread = threading.Thread(target=self._backup_service_loop, daemon=True)
        self.backup_thread.start()
        print("✅ Auto backup service started")
    
    def stop_auto_backup_service(self):
        """Stop the auto backup service"""
        self.running = False
        if self.backup_thread:
            self.backup_thread.join(timeout=5)
        print("🛑 Auto backup service stopped")
    
    def _backup_service_loop(self):
        """Main backup service loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check daily scheduled backup
                if self._should_do_scheduled_backup(current_time):
                    self._perform_backup("scheduled")
                
                # Check for data changes (simplified)
                # In a real implementation, this would monitor file changes
                
                # Sleep for 5 minutes before next check
                time.sleep(300)  # 5 minutes
                
            except Exception as e:
                print(f"⚠️ Backup service error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _should_do_scheduled_backup(self, current_time: datetime) -> bool:
        """Check if scheduled backup should run"""
        if not self.config['auto_schedule']:
            return False
        
        # Check if it's backup time (within 5 minutes of configured hour)
        backup_time = current_time.replace(hour=self.config['backup_hour'], minute=0, second=0, microsecond=0)
        time_diff = abs((current_time - backup_time).total_seconds())
        
        if time_diff > 300:  # More than 5 minutes away
            return False
        
        # Check if backup already done today
        if self.last_backup_time:
            if self.last_backup_time.date() == current_time.date():
                return False
        
        # Check daily limit
        if self.backup_count_today >= self.config['max_daily_backups']:
            return False
        
        return True
    
    def manual_backup(self, description: str = "manual") -> bool:
        """Manually trigger a backup"""
        return self._perform_backup("manual", description)
    
    def backup_on_transaction(self, transaction_type: str = "transaction") -> bool:
        """Trigger backup after important transactions"""
        # Check if enough time has passed since last backup
        if self.last_backup_time:
            time_since_last = datetime.now() - self.last_backup_time
            if time_since_last.total_seconds() < (self.config['backup_interval_hours'] * 3600):
                print(f"⏱️ Skipping backup - too soon since last ({time_since_last})")
                return True  # Not an error
        
        return self._perform_backup(f"auto_{transaction_type}")
    
    def _perform_backup(self, trigger: str, description: str = None) -> bool:
        """Perform the actual backup operation"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"Fund_Export_{timestamp}_{trigger}"
            
            if description:
                clean_desc = "".join(c for c in description if c.isalnum() or c in "-_")[:20]
                backup_name += f"_{clean_desc}"
            
            backup_name += ".xlsx"
            
            print(f"🔄 Starting backup: {backup_name}")
            
            # Local backup (always try this first)
            local_success = self._create_local_backup(backup_name)
            
            # Cloud backup (if available)
            cloud_success = False
            if self.drive_manager and self.config['cloud_backup']:
                cloud_success = self._create_cloud_backup(backup_name)
            
            # Update stats
            self.backup_stats['total_backups'] += 1
            if local_success:
                self.backup_stats['successful_local'] += 1
            if cloud_success:
                self.backup_stats['successful_cloud'] += 1
            
            if not (local_success or cloud_success):
                self.backup_stats['failed_backups'] += 1
                return False
            
            # Update tracking
            self.last_backup_time = datetime.now()
            if self.last_backup_time.date() == datetime.now().date():
                self.backup_count_today += 1
            else:
                self.backup_count_today = 1
            
            success_msg = []
            if local_success:
                success_msg.append("Local")
            if cloud_success:
                success_msg.append("Cloud")
            
            print(f"✅ Backup successful: {' + '.join(success_msg)} - {backup_name}")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            self.backup_stats['failed_backups'] += 1
            self.backup_stats['last_error'] = str(e)
            return False
    
    def _create_local_backup(self, filename: str) -> bool:
        """Create local backup"""
        try:
            if not self.fund_manager:
                print("⚠️ No fund manager available for backup")
                return False

            # Create export buffer using Google Drive manager
            from integrations.google_drive_manager import GoogleDriveManager
            temp_manager = GoogleDriveManager(self.fund_manager)
            buffer = temp_manager.export_to_excel_buffer()

            # Save to local file
            local_file = self.local_backup_dir / filename
            with open(local_file, 'wb') as f:
                f.write(buffer.getvalue())

            file_size = local_file.stat().st_size
            print(f"💾 Local backup: {local_file} ({file_size:,} bytes)")

            # Cleanup old local backups (keep last 20)
            self._cleanup_local_backups()

            return True

        except Exception as e:
            print(f"❌ Local backup failed: {e}")
            return False
    
    def _create_cloud_backup(self, filename: str) -> bool:
        """Create cloud backup using OAuth manager"""
        try:
            if not self.drive_manager:
                return False

            if not self.drive_manager.connected:
                print("⚠️ Cloud backup skipped - not connected")
                return False

            # Create buffer using Google Drive manager
            from integrations.google_drive_manager import GoogleDriveManager
            temp_manager = GoogleDriveManager(self.fund_manager)
            buffer = temp_manager.export_to_excel_buffer()

            # Upload to cloud
            success = self.drive_manager.upload_to_drive(buffer, filename)

            if success:
                print(f"☁️ Cloud backup: {filename}")

            return success

        except Exception as e:
            print(f"❌ Cloud backup failed: {e}")
            return False
    
    def _cleanup_local_backups(self, keep_count: int = 20):
        """Clean up old local backups"""
        try:
            backup_files = list(self.local_backup_dir.glob("Fund_Export_*.xlsx"))
            if len(backup_files) <= keep_count:
                return
            
            # Sort by modification time, keep newest
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            files_to_delete = backup_files[keep_count:]
            
            for old_file in files_to_delete:
                old_file.unlink()
                print(f"🧹 Cleaned up old backup: {old_file.name}")
                
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
    
    def get_backup_status(self) -> Dict:
        """Get comprehensive backup status"""
        # Count local backups
        local_backups = list(self.local_backup_dir.glob("Fund_Export_*.xlsx"))
        local_total_size = sum(f.stat().st_size for f in local_backups)

        # Get cloud status
        cloud_info = {"connected": False, "files": 0}
        if self.drive_manager:
            try:
                cloud_info["connected"] = self.drive_manager.connected
                if self.drive_manager.connected:
                    test_result = self.drive_manager.test_connection()
                    cloud_info["files"] = test_result.get('files_count', 0)
                    cloud_info["account"] = test_result.get('user', {}).get('email', 'Unknown')
                    cloud_info["method"] = "OAuth"
            except Exception as e:
                cloud_info["error"] = str(e)

        return {
            'service_running': self.running,
            'last_backup': self.last_backup_time.isoformat() if self.last_backup_time else None,
            'backups_today': self.backup_count_today,
            'local_backups': {
                'count': len(local_backups),
                'total_size_mb': local_total_size / (1024 * 1024),
                'directory': str(self.local_backup_dir)
            },
            'cloud_backup': cloud_info,
            'stats': self.backup_stats,
            'config': self.config
        }
    
    def print_status(self):
        """Print nice status overview"""
        status = self.get_backup_status()
        
        print("\n" + "="*60)
        print("🚀 PERSONAL AUTO BACKUP SYSTEM STATUS")
        print("="*60)
        
        # Service status
        service_emoji = "✅" if status['service_running'] else "🛑"
        print(f"{service_emoji} Background Service: {'Running' if status['service_running'] else 'Stopped'}")
        
        # Last backup
        if status['last_backup']:
            last_backup = datetime.fromisoformat(status['last_backup'])
            time_ago = datetime.now() - last_backup
            print(f"⏰ Last Backup: {last_backup.strftime('%Y-%m-%d %H:%M')} ({time_ago} ago)")
        else:
            print("⏰ Last Backup: Never")
        
        print(f"📊 Backups Today: {status['backups_today']}/{self.config['max_daily_backups']}")
        
        # Local backups
        local = status['local_backups']
        print(f"\n💾 Local Backups: {local['count']} files ({local['total_size_mb']:.1f} MB)")
        print(f"   📁 Directory: {local['directory']}")
        
        # Cloud backups
        cloud = status['cloud_backup']
        if cloud['connected']:
            cloud_emoji = "☁️"
            method_info = f" ({cloud.get('method', 'unknown')})"
            print(f"{cloud_emoji} Cloud Backup: Connected{method_info}")
            print(f"   👤 Account: {cloud.get('account', 'Unknown')}")
            print(f"   📄 Files: {cloud.get('files', 0)}")
        else:
            print("☁️ Cloud Backup: Not connected")
            if 'error' in cloud:
                print(f"   ❌ Error: {cloud['error']}")
        
        # Statistics
        stats = status['stats']
        print(f"\n📈 Statistics:")
        print(f"   Total Backups: {stats['total_backups']}")
        print(f"   Successful Local: {stats['successful_local']}")
        print(f"   Successful Cloud: {stats['successful_cloud']}")
        print(f"   Failed: {stats['failed_backups']}")
        
        if stats['last_error']:
            print(f"   ⚠️ Last Error: {stats['last_error']}")
        
        print("="*60)

# Global instance for app integration
_auto_backup_manager = None

def get_auto_backup_manager(fund_manager=None):
    """Get or create global auto backup manager instance"""
    global _auto_backup_manager
    if _auto_backup_manager is None:
        _auto_backup_manager = PersonalAutoBackupManager(fund_manager)
    elif fund_manager and not _auto_backup_manager.fund_manager:
        _auto_backup_manager.fund_manager = fund_manager
        _auto_backup_manager._init_drive_manager()
    return _auto_backup_manager

def start_auto_backup_service(fund_manager):
    """Start auto backup service (called from main app)"""
    manager = get_auto_backup_manager(fund_manager)
    manager.start_auto_backup_service()
    return manager

def manual_backup(fund_manager, description="manual"):
    """Trigger manual backup (called from UI)"""
    manager = get_auto_backup_manager(fund_manager)
    return manager.manual_backup(description)

def backup_after_transaction(fund_manager, transaction_type="transaction"):
    """Backup after important data changes"""
    manager = get_auto_backup_manager(fund_manager)
    return manager.backup_on_transaction(transaction_type)

if __name__ == "__main__":
    # Demo
    manager = PersonalAutoBackupManager()
    manager.print_status()
    
    print("\nDemo completed. Use with fund_manager for full functionality.")