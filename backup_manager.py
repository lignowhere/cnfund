#!/usr/bin/env python3
"""
Comprehensive Backup Manager cho Fund Management System
Provides auto daily backups, persistent storage, và recovery capabilities
"""

import os
import pickle
import json
import shutil
import gzip
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
import copy
from timezone_manager import TimezoneManager
import threading
import schedule
import time
from pathlib import Path
import logging

class BackupManager:
    """
    Enhanced backup system với:
    - Auto daily backups
    - Persistent storage
    - File management
    - Recovery capabilities
    - Compression support
    """
    
    def __init__(self, backup_dir: str = "backups", 
                 auto_backup: bool = True,
                 max_daily_backups: int = 30,
                 max_operation_snapshots: int = 50,
                 compress_backups: bool = True):
        
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        self.daily_backup_dir = self.backup_dir / "daily"
        self.daily_backup_dir.mkdir(exist_ok=True)
        
        self.operation_backup_dir = self.backup_dir / "operations"
        self.operation_backup_dir.mkdir(exist_ok=True)
        
        self.max_daily_backups = max_daily_backups
        self.max_operation_snapshots = max_operation_snapshots
        self.compress_backups = compress_backups
        
        # In-memory snapshots (cho operations)
        self.operation_snapshots: Dict[str, Dict[str, Any]] = {}
        self.snapshot_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Backup history
        self.backup_history: List[Dict[str, Any]] = []
        self._load_backup_history()
        
        # Auto backup settings
        self.auto_backup_enabled = auto_backup
        self.last_daily_backup = None
        self._load_last_backup_info()
        
        # Setup logging
        self._setup_logging()
        
        # Start auto backup scheduler if enabled
        if self.auto_backup_enabled:
            self._setup_auto_backup_scheduler()
    
    def _setup_logging(self):
        """Setup logging for backup operations"""
        log_file = self.backup_dir / "backup.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('BackupManager')
    
    def create_operation_snapshot(self, fund_manager, operation_type: str, description: str = "") -> str:
        """
        Tạo snapshot cho operations (in-memory, quick access)
        """
        snapshot_id = f"{operation_type}_{TimezoneManager.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Deep copy data
            snapshot_data = {
                'investors': [asdict(inv) for inv in fund_manager.investors],
                'tranches': [asdict(tr) for tr in fund_manager.tranches],
                'transactions': [asdict(txn) for txn in fund_manager.transactions],
                'fee_records': [asdict(fr) for fr in fund_manager.fee_records],
                'timestamp': TimezoneManager.now().isoformat(),
                'operation_type': operation_type,
                'description': description
            }
            
            # Store in memory
            self.operation_snapshots[snapshot_id] = copy.deepcopy(snapshot_data)
            
            # Store metadata
            self.snapshot_metadata[snapshot_id] = {
                'timestamp': TimezoneManager.now().isoformat(),
                'operation_type': operation_type,
                'description': description,
                'investors_count': len(fund_manager.investors),
                'tranches_count': len(fund_manager.tranches),
                'transactions_count': len(fund_manager.transactions),
                'fee_records_count': len(fund_manager.fee_records),
                'size_mb': len(str(snapshot_data)) / (1024 * 1024)
            }
            
            # Cleanup old operation snapshots
            self._cleanup_operation_snapshots()
            
            self.logger.info(f"Created operation snapshot: {snapshot_id}")
            return snapshot_id
            
        except Exception as e:
            self.logger.error(f"Error creating operation snapshot: {e}")
            return None
    
    def restore_operation_snapshot(self, fund_manager, snapshot_id: str) -> bool:
        """
        Restore từ operation snapshot
        """
        if snapshot_id not in self.operation_snapshots:
            self.logger.error(f"Operation snapshot {snapshot_id} not found!")
            return False
        
        try:
            from models import Investor, Tranche, Transaction, FeeRecord
            snapshot_data = self.operation_snapshots[snapshot_id]
            
            # Clear current data
            fund_manager.investors.clear()
            fund_manager.tranches.clear()
            fund_manager.transactions.clear()
            fund_manager.fee_records.clear()
            
            # Restore investors
            for inv_data in snapshot_data['investors']:
                if isinstance(inv_data.get('join_date'), str):
                    inv_data['join_date'] = datetime.fromisoformat(inv_data['join_date']).date()
                fund_manager.investors.append(Investor(**inv_data))
            
            # Restore tranches
            for tr_data in snapshot_data['tranches']:
                if isinstance(tr_data.get('entry_date'), str):
                    tr_data['entry_date'] = datetime.fromisoformat(tr_data['entry_date'])
                if isinstance(tr_data.get('original_entry_date'), str):
                    tr_data['original_entry_date'] = datetime.fromisoformat(tr_data['original_entry_date'])
                
                tranche = Tranche(**tr_data)
                fund_manager.tranches.append(tranche)
            
            # Restore transactions
            for txn_data in snapshot_data['transactions']:
                if isinstance(txn_data.get('date'), str):
                    txn_data['date'] = datetime.fromisoformat(txn_data['date'])
                fund_manager.transactions.append(Transaction(**txn_data))
            
            # Restore fee records
            for fr_data in snapshot_data['fee_records']:
                if isinstance(fr_data.get('calculation_date'), str):
                    fr_data['calculation_date'] = datetime.fromisoformat(fr_data['calculation_date'])
                fund_manager.fee_records.append(FeeRecord(**fr_data))
            
            self.logger.info(f"Restored operation snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring operation snapshot: {e}")
            return False
    
    def create_daily_backup(self, fund_manager, backup_type: str = "DAILY_AUTO") -> str:
        """
        Tạo daily backup với persistent storage
        """
        timestamp = TimezoneManager.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"{backup_type}_{timestamp}"
        
        try:
            # Create backup data
            backup_data = {
                'backup_id': backup_id,
                'backup_type': backup_type,
                'timestamp': TimezoneManager.now().isoformat(),
                'date': date.today().isoformat(),
                'data': {
                    'investors': [asdict(inv) for inv in fund_manager.investors],
                    'tranches': [asdict(tr) for tr in fund_manager.tranches],
                    'transactions': [asdict(txn) for txn in fund_manager.transactions],
                    'fee_records': [asdict(fr) for fr in fund_manager.fee_records]
                },
                'metadata': {
                    'investors_count': len(fund_manager.investors),
                    'tranches_count': len(fund_manager.tranches),
                    'transactions_count': len(fund_manager.transactions),
                    'fee_records_count': len(fund_manager.fee_records),
                    'total_units': sum(t.units for t in fund_manager.tranches),
                    'total_investors': len([inv for inv in fund_manager.investors if not inv.is_fund_manager])
                }
            }
            
            # Save to file
            backup_file = self.daily_backup_dir / f"{backup_id}.pkl"
            if self.compress_backups:
                backup_file = backup_file.with_suffix('.pkl.gz')
                with gzip.open(backup_file, 'wb') as f:
                    pickle.dump(backup_data, f)
            else:
                with open(backup_file, 'wb') as f:
                    pickle.dump(backup_data, f)
            
            # Update backup history
            backup_info = {
                'backup_id': backup_id,
                'backup_type': backup_type,
                'timestamp': TimezoneManager.now().isoformat(),
                'date': date.today().isoformat(),
                'file_path': str(backup_file),
                'file_size_mb': backup_file.stat().st_size / (1024 * 1024),
                'compressed': self.compress_backups,
                **backup_data['metadata']
            }
            
            self.backup_history.append(backup_info)
            self._save_backup_history()
            
            # Update last backup info
            self.last_daily_backup = date.today()
            self._save_last_backup_info()
            
            # Cleanup old backups
            self._cleanup_daily_backups()
            
            self.logger.info(f"Created daily backup: {backup_id} ({backup_info['file_size_mb']:.2f} MB)")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Error creating daily backup: {e}")
            return None
    
    def restore_daily_backup(self, fund_manager, backup_id: str = None, backup_date: str = None) -> bool:
        """
        Restore từ daily backup
        """
        backup_info = None
        
        # Find backup
        if backup_id:
            backup_info = next((b for b in self.backup_history if b['backup_id'] == backup_id), None)
        elif backup_date:
            # Find latest backup for date
            date_backups = [b for b in self.backup_history if b['date'] == backup_date]
            if date_backups:
                backup_info = max(date_backups, key=lambda x: x['timestamp'])
        else:
            # Get latest backup
            if self.backup_history:
                backup_info = max(self.backup_history, key=lambda x: x['timestamp'])
        
        if not backup_info:
            self.logger.error("No backup found to restore")
            return False
        
        backup_file = Path(backup_info['file_path'])
        if not backup_file.exists():
            self.logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            # Load backup data
            if backup_info.get('compressed', False):
                with gzip.open(backup_file, 'rb') as f:
                    backup_data = pickle.load(f)
            else:
                with open(backup_file, 'rb') as f:
                    backup_data = pickle.load(f)
            
            from models import Investor, Tranche, Transaction, FeeRecord
            data = backup_data['data']
            
            # Clear current data
            fund_manager.investors.clear()
            fund_manager.tranches.clear()
            fund_manager.transactions.clear()
            fund_manager.fee_records.clear()
            
            # Restore data (same logic as operation snapshot)
            for inv_data in data['investors']:
                if isinstance(inv_data.get('join_date'), str):
                    inv_data['join_date'] = datetime.fromisoformat(inv_data['join_date']).date()
                fund_manager.investors.append(Investor(**inv_data))
            
            for tr_data in data['tranches']:
                if isinstance(tr_data.get('entry_date'), str):
                    tr_data['entry_date'] = datetime.fromisoformat(tr_data['entry_date'])
                if isinstance(tr_data.get('original_entry_date'), str):
                    tr_data['original_entry_date'] = datetime.fromisoformat(tr_data['original_entry_date'])
                fund_manager.tranches.append(Tranche(**tr_data))
            
            for txn_data in data['transactions']:
                if isinstance(txn_data.get('date'), str):
                    txn_data['date'] = datetime.fromisoformat(txn_data['date'])
                fund_manager.transactions.append(Transaction(**txn_data))
            
            for fr_data in data['fee_records']:
                if isinstance(fr_data.get('calculation_date'), str):
                    fr_data['calculation_date'] = datetime.fromisoformat(fr_data['calculation_date'])
                fund_manager.fee_records.append(FeeRecord(**fr_data))
            
            self.logger.info(f"Restored daily backup: {backup_info['backup_id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring daily backup: {e}")
            return False
    
    def list_daily_backups(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        List daily backups từ N days gần đây
        """
        cutoff_date = date.today() - timedelta(days=days)
        recent_backups = [
            b for b in self.backup_history 
            if TimezoneManager.normalize_for_display(
                datetime.fromisoformat(b['date'])).date() >= cutoff_date
        ]
        
        return sorted(recent_backups, key=lambda x: x['timestamp'], reverse=True)
    
    def list_operation_snapshots(self) -> List[Dict[str, Any]]:
        """
        List operation snapshots
        """
        snapshots_list = []
        for snapshot_id, metadata in self.snapshot_metadata.items():
            snapshots_list.append({
                'id': snapshot_id,
                **metadata
            })
        
        return sorted(snapshots_list, key=lambda x: x['timestamp'], reverse=True)
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Get backup system statistics
        """
        # Use timezone-aware datetime to avoid comparison issues
        now = TimezoneManager.now()
        today = date.today()
        
        # Daily backup stats
        daily_backups = len(self.backup_history)
        recent_daily_backups = len([b for b in self.backup_history 
                                   if (now - TimezoneManager.normalize_for_display(
                                       datetime.fromisoformat(b['timestamp']))).days <= 7])
        
        total_backup_size = sum(b.get('file_size_mb', 0) for b in self.backup_history)
        
        # Operation snapshot stats
        operation_snapshots = len(self.operation_snapshots)
        
        # Last backup info
        last_backup = None
        if self.backup_history:
            last_backup = max(self.backup_history, key=lambda x: x['timestamp'])
        
        return {
            'daily_backups': {
                'total': daily_backups,
                'recent_7_days': recent_daily_backups,
                'total_size_mb': round(total_backup_size, 2),
                'last_backup': last_backup,
                'last_backup_date': self.last_daily_backup.isoformat() if self.last_daily_backup else None
            },
            'operation_snapshots': {
                'current_count': operation_snapshots,
                'max_count': self.max_operation_snapshots
            },
            'auto_backup': {
                'enabled': self.auto_backup_enabled,
                'next_backup': "Daily at 23:00" if self.auto_backup_enabled else "Disabled"
            },
            'storage': {
                'backup_dir': str(self.backup_dir),
                'compression_enabled': self.compress_backups
            }
        }
    
    def _setup_auto_backup_scheduler(self):
        """
        Setup auto backup scheduler
        """
        schedule.every().day.at("23:00").do(self._scheduled_backup)
        schedule.every().day.at("12:00").do(self._scheduled_backup)  # Lunch backup
        
        # Start scheduler in background thread
        def run_scheduler():
            while self.auto_backup_enabled:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        self.logger.info("Auto backup scheduler started (12:00 và 23:00 daily)")
    
    def _scheduled_backup(self):
        """
        Scheduled backup job (cần fund_manager instance)
        """
        self.logger.info("Auto backup triggered, but requires fund_manager instance")
        # This will be called from main application
    
    def trigger_auto_backup(self, fund_manager):
        """
        Trigger auto backup (called from main app)
        """
        if not self.auto_backup_enabled:
            return False
        
        # Check if backup needed today
        if self.last_daily_backup == date.today():
            self.logger.info("Daily backup already completed today")
            return True
        
        backup_id = self.create_daily_backup(fund_manager, "DAILY_AUTO")
        if backup_id:
            self.logger.info(f"Auto backup completed: {backup_id}")
            return True
        else:
            self.logger.error("Auto backup failed")
            return False
    
    def _cleanup_operation_snapshots(self):
        """
        Cleanup old operation snapshots
        """
        if len(self.operation_snapshots) <= self.max_operation_snapshots:
            return
        
        # Sort by timestamp and remove oldest
        sorted_snapshots = sorted(
            self.snapshot_metadata.items(),
            key=lambda x: x[1]['timestamp']
        )
        
        snapshots_to_remove = len(self.operation_snapshots) - self.max_operation_snapshots
        for i in range(snapshots_to_remove):
            snapshot_id = sorted_snapshots[i][0]
            if snapshot_id in self.operation_snapshots:
                del self.operation_snapshots[snapshot_id]
            if snapshot_id in self.snapshot_metadata:
                del self.snapshot_metadata[snapshot_id]
        
        self.logger.info(f"Cleaned up {snapshots_to_remove} old operation snapshots")
    
    def _cleanup_daily_backups(self):
        """
        Cleanup old daily backups
        """
        if len(self.backup_history) <= self.max_daily_backups:
            return
        
        # Sort by timestamp and remove oldest files
        sorted_backups = sorted(self.backup_history, key=lambda x: x['timestamp'])
        backups_to_remove = len(self.backup_history) - self.max_daily_backups
        
        removed_count = 0
        for backup in sorted_backups[:backups_to_remove]:
            backup_file = Path(backup['file_path'])
            if backup_file.exists():
                backup_file.unlink()
                removed_count += 1
            
            # Remove from history
            self.backup_history.remove(backup)
        
        if removed_count > 0:
            self._save_backup_history()
            self.logger.info(f"Cleaned up {removed_count} old daily backup files")
    
    def _load_backup_history(self):
        """
        Load backup history from file
        """
        history_file = self.backup_dir / "backup_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    self.backup_history = json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading backup history: {e}")
                self.backup_history = []
    
    def _save_backup_history(self):
        """
        Save backup history to file
        """
        history_file = self.backup_dir / "backup_history.json"
        try:
            with open(history_file, 'w') as f:
                json.dump(self.backup_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving backup history: {e}")
    
    def _load_last_backup_info(self):
        """
        Load last backup info
        """
        info_file = self.backup_dir / "last_backup_info.json"
        if info_file.exists():
            try:
                with open(info_file, 'r') as f:
                    info = json.load(f)
                    if info.get('last_daily_backup'):
                        self.last_daily_backup = datetime.fromisoformat(info['last_daily_backup']).date()
            except Exception as e:
                self.logger.error(f"Error loading last backup info: {e}")
    
    def _save_last_backup_info(self):
        """
        Save last backup info
        """
        info_file = self.backup_dir / "last_backup_info.json"
        try:
            info = {
                'last_daily_backup': self.last_daily_backup.isoformat() if self.last_daily_backup else None,
                'updated_at': TimezoneManager.now().isoformat()
            }
            with open(info_file, 'w') as f:
                json.dump(info, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving last backup info: {e}")

# Utility functions
def create_emergency_backup(fund_manager, backup_dir: str = "emergency_backups") -> str:
    """
    Create emergency backup (standalone function)
    """
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = TimezoneManager.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f"EMERGENCY_{timestamp}.pkl.gz")
    
    backup_data = {
        'backup_type': 'EMERGENCY',
        'timestamp': TimezoneManager.now().isoformat(),
        'data': {
            'investors': [asdict(inv) for inv in fund_manager.investors],
            'tranches': [asdict(tr) for tr in fund_manager.tranches],
            'transactions': [asdict(txn) for txn in fund_manager.transactions],
            'fee_records': [asdict(fr) for fr in fund_manager.fee_records]
        }
    }
    
    with gzip.open(backup_file, 'wb') as f:
        pickle.dump(backup_data, f)
    
    print(f"🚨 Emergency backup created: {backup_file}")
    return backup_file