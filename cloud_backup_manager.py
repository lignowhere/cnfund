#!/usr/bin/env python3
"""
Cloud-Compatible Backup Manager cho Supabase + Streamlit Cloud
Provides backup solutions that work in cloud environments
"""

import os
import json
import base64
import gzip
import tempfile
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
import copy
import logging
import io
import streamlit as st
from pathlib import Path
from sqlalchemy import text

class CloudBackupManager:
    """
    Cloud-compatible backup system designed for Supabase + Streamlit Cloud:
    
    - Stores backups in Supabase database (backup_snapshots table)
    - Uses Streamlit Cloud file system only for temporary operations
    - Supports both database-level và application-level backups
    - Compressed storage để save database space
    """
    
    def __init__(self, supabase_handler, 
                 max_backups: int = 50,
                 max_operation_snapshots: int = 20,
                 compress_backups: bool = True):
        
        self.supabase_handler = supabase_handler
        self.max_backups = max_backups
        self.max_operation_snapshots = max_operation_snapshots
        self.compress_backups = compress_backups
        
        # In-memory operation snapshots (temporary)
        self.operation_snapshots: Dict[str, Dict[str, Any]] = {}
        self.snapshot_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Setup logging
        self._setup_logging()
        
        # Initialize backup table in Supabase
        self._ensure_backup_table()
    
    def _setup_logging(self):
        """Setup logging for cloud environment"""
        # Use Streamlit's built-in logging in cloud
        self.logger = logging.getLogger('CloudBackupManager')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _ensure_backup_table(self):
        """
        Ensure backup_snapshots table exists in Supabase
        """
        if not self.supabase_handler or not self.supabase_handler.connected:
            self.logger.warning("Supabase not connected - backup table initialization skipped")
            return
        
        try:
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS backup_snapshots (
                id SERIAL PRIMARY KEY,
                backup_id VARCHAR(255) UNIQUE NOT NULL,
                backup_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                backup_date DATE NOT NULL,
                description TEXT,
                data_compressed BYTEA,
                metadata JSONB,
                file_size_bytes INTEGER,
                is_compressed BOOLEAN DEFAULT true,
                created_by VARCHAR(100) DEFAULT 'system'
            );
            
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_backup_snapshots_backup_id ON backup_snapshots(backup_id);
            CREATE INDEX IF NOT EXISTS idx_backup_snapshots_backup_date ON backup_snapshots(backup_date);
            CREATE INDEX IF NOT EXISTS idx_backup_snapshots_backup_type ON backup_snapshots(backup_type);
            CREATE INDEX IF NOT EXISTS idx_backup_snapshots_created_at ON backup_snapshots(created_at);
            """
            
            with self.supabase_handler.engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
            
            self.logger.info("Backup table initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize backup table: {e}")
    
    def create_operation_snapshot(self, fund_manager, operation_type: str, description: str = "") -> str:
        """
        Create lightweight operation snapshot (in-memory only)
        """
        snapshot_id = f"{operation_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        try:
            # Create minimal snapshot data
            snapshot_data = {
                'investors': [asdict(inv) for inv in fund_manager.investors],
                'tranches': [asdict(tr) for tr in fund_manager.tranches],
                'transactions': [asdict(txn) for txn in fund_manager.transactions],
                'fee_records': [asdict(fr) for fr in fund_manager.fee_records],
                'timestamp': datetime.now().isoformat(),
                'operation_type': operation_type,
                'description': description
            }
            
            # Store in memory (temporary)
            self.operation_snapshots[snapshot_id] = copy.deepcopy(snapshot_data)
            
            # Store metadata
            self.snapshot_metadata[snapshot_id] = {
                'timestamp': datetime.now().isoformat(),
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
        Restore from in-memory operation snapshot
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
            
            # Restore data (same logic as before)
            self._restore_data_from_snapshot(fund_manager, snapshot_data['investors'], 
                                           snapshot_data['tranches'], 
                                           snapshot_data['transactions'], 
                                           snapshot_data['fee_records'])
            
            self.logger.info(f"Restored operation snapshot: {snapshot_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring operation snapshot: {e}")
            return False
    
    def create_database_backup(self, fund_manager, backup_type: str = "MANUAL") -> str:
        """
        Create database backup stored in Supabase
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_id = f"{backup_type}_{timestamp}"
        
        if not self.supabase_handler or not self.supabase_handler.connected:
            self.logger.error("Supabase not connected - cannot create database backup")
            return None
        
        try:
            # Create backup data
            backup_data = {
                'backup_id': backup_id,
                'backup_type': backup_type,
                'timestamp': datetime.now().isoformat(),
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
                    'backup_size_mb': 0  # Will be calculated
                }
            }
            
            # Serialize và compress data
            data_json = json.dumps(backup_data, ensure_ascii=False, default=str)
            data_bytes = data_json.encode('utf-8')
            
            if self.compress_backups:
                data_compressed = gzip.compress(data_bytes)
            else:
                data_compressed = data_bytes
            
            # Calculate size
            backup_data['metadata']['backup_size_mb'] = len(data_compressed) / (1024 * 1024)
            
            # Store in Supabase
            insert_sql = """
            INSERT INTO backup_snapshots 
            (backup_id, backup_type, backup_date, description, data_compressed, 
             metadata, file_size_bytes, is_compressed, created_by)
            VALUES (:backup_id, :backup_type, :backup_date, :description, 
                    :data_compressed, :metadata, :file_size_bytes, :is_compressed, :created_by)
            """
            
            with self.supabase_handler.engine.connect() as conn:
                conn.execute(text(insert_sql), {
                    'backup_id': backup_id,
                    'backup_type': backup_type,
                    'backup_date': date.today(),
                    'description': backup_data.get('description', f'{backup_type} backup'),
                    'data_compressed': data_compressed,
                    'metadata': json.dumps(backup_data['metadata']),
                    'file_size_bytes': len(data_compressed),
                    'is_compressed': self.compress_backups,
                    'created_by': 'streamlit_app'
                })
                conn.commit()
            
            # Cleanup old backups
            self._cleanup_database_backups()
            
            self.logger.info(f"Created database backup: {backup_id} ({backup_data['metadata']['backup_size_mb']:.2f} MB)")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Error creating database backup: {e}")
            return None
    
    def restore_database_backup(self, fund_manager, backup_id: str = None, backup_date: str = None) -> bool:
        """
        Restore from database backup
        """
        if not self.supabase_handler or not self.supabase_handler.connected:
            self.logger.error("Supabase not connected - cannot restore backup")
            return False
        
        try:
            # Find backup
            if backup_id:
                query_sql = "SELECT * FROM backup_snapshots WHERE backup_id = :backup_id"
                params = {'backup_id': backup_id}
            elif backup_date:
                query_sql = """
                SELECT * FROM backup_snapshots 
                WHERE backup_date = :backup_date 
                ORDER BY created_at DESC LIMIT 1
                """
                params = {'backup_date': backup_date}
            else:
                query_sql = "SELECT * FROM backup_snapshots ORDER BY created_at DESC LIMIT 1"
                params = {}
            
            with self.supabase_handler.engine.connect() as conn:
                result = conn.execute(text(query_sql), params).fetchone()
            
            if not result:
                self.logger.error("No backup found to restore")
                return False
            
            # Decompress and load data
            data_compressed = result.data_compressed
            
            if result.is_compressed:
                data_bytes = gzip.decompress(data_compressed)
            else:
                data_bytes = data_compressed
            
            data_json = data_bytes.decode('utf-8')
            backup_data = json.loads(data_json)
            
            # Clear current data
            fund_manager.investors.clear()
            fund_manager.tranches.clear()
            fund_manager.transactions.clear()
            fund_manager.fee_records.clear()
            
            # Restore data
            data = backup_data['data']
            self._restore_data_from_snapshot(fund_manager, data['investors'], 
                                           data['tranches'], data['transactions'], 
                                           data['fee_records'])
            
            self.logger.info(f"Restored database backup: {result.backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring database backup: {e}")
            return False
    
    def _restore_data_from_snapshot(self, fund_manager, investors_data, tranches_data, transactions_data, fee_records_data):
        """
        Helper method to restore data from snapshot
        """
        from models import Investor, Tranche, Transaction, FeeRecord
        
        # Restore investors
        for inv_data in investors_data:
            if isinstance(inv_data.get('join_date'), str):
                inv_data['join_date'] = datetime.fromisoformat(inv_data['join_date']).date()
            fund_manager.investors.append(Investor(**inv_data))
        
        # Restore tranches
        for tr_data in tranches_data:
            if isinstance(tr_data.get('entry_date'), str):
                tr_data['entry_date'] = datetime.fromisoformat(tr_data['entry_date'])
            if isinstance(tr_data.get('original_entry_date'), str):
                tr_data['original_entry_date'] = datetime.fromisoformat(tr_data['original_entry_date'])
            fund_manager.tranches.append(Tranche(**tr_data))
        
        # Restore transactions
        for txn_data in transactions_data:
            if isinstance(txn_data.get('date'), str):
                txn_data['date'] = datetime.fromisoformat(txn_data['date'])
            fund_manager.transactions.append(Transaction(**txn_data))
        
        # Restore fee records
        for fr_data in fee_records_data:
            if isinstance(fr_data.get('calculation_date'), str):
                fr_data['calculation_date'] = datetime.fromisoformat(fr_data['calculation_date'])
            fund_manager.fee_records.append(FeeRecord(**fr_data))
    
    def list_database_backups(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        List database backups from last N days
        """
        if not self.supabase_handler or not self.supabase_handler.connected:
            return []
        
        try:
            cutoff_date = date.today() - timedelta(days=days)
            
            query_sql = """
            SELECT backup_id, backup_type, backup_date, created_at, 
                   description, metadata, file_size_bytes, is_compressed
            FROM backup_snapshots 
            WHERE backup_date >= :cutoff_date
            ORDER BY created_at DESC
            """
            
            with self.supabase_handler.engine.connect() as conn:
                results = conn.execute(text(query_sql), {'cutoff_date': cutoff_date}).fetchall()
            
            backups = []
            for row in results:
                # Handle metadata - could be string (JSON) or already a dict
                if row.metadata:
                    if isinstance(row.metadata, str):
                        metadata = json.loads(row.metadata)
                    else:
                        metadata = row.metadata  # Already a dict
                else:
                    metadata = {}
                
                backup_info = {
                    'backup_id': row.backup_id,
                    'backup_type': row.backup_type,
                    'date': row.backup_date.isoformat(),
                    'timestamp': row.created_at.isoformat(),
                    'description': row.description or '',
                    'file_size_mb': (row.file_size_bytes or 0) / (1024 * 1024),
                    'compressed': row.is_compressed,
                    'investors_count': metadata.get('investors_count', 0),
                    'tranches_count': metadata.get('tranches_count', 0),
                    'transactions_count': metadata.get('transactions_count', 0),
                    'fee_records_count': metadata.get('fee_records_count', 0)
                }
                backups.append(backup_info)
            
            return backups
            
        except Exception as e:
            self.logger.error(f"Error listing database backups: {e}")
            return []
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """
        Get backup system statistics for cloud environment
        """
        try:
            # Database backups stats
            database_backups = self.list_database_backups(30)
            
            # Handle timezone-aware vs timezone-naive datetime comparison
            now = datetime.now()
            recent_database_backups = 0
            for b in database_backups:
                try:
                    backup_time = datetime.fromisoformat(b['timestamp'])
                    # Make both datetime objects timezone-naive for comparison
                    if backup_time.tzinfo is not None:
                        backup_time = backup_time.replace(tzinfo=None)
                    if now.tzinfo is not None:
                        now = now.replace(tzinfo=None)
                    
                    if (now - backup_time).days <= 7:
                        recent_database_backups += 1
                except (ValueError, TypeError):
                    # Skip if timestamp parsing fails
                    continue
            
            total_backup_size = sum(b.get('file_size_mb', 0) for b in database_backups)
            
            # Operation snapshots stats  
            operation_snapshots = len(self.operation_snapshots)
            
            # Last backup info
            last_backup = database_backups[0] if database_backups else None
            
            return {
                'enabled': True,
                'storage_type': 'supabase_database',
                'database_backups': {
                    'total': len(database_backups),
                    'recent_7_days': recent_database_backups,
                    'total_size_mb': round(total_backup_size, 2),
                    'last_backup': last_backup,
                    'last_backup_date': last_backup['date'] if last_backup else None
                },
                'operation_snapshots': {
                    'current_count': operation_snapshots,
                    'max_count': self.max_operation_snapshots
                },
                'auto_backup': {
                    'enabled': True,  # Can be triggered manually
                    'next_backup': "On-demand via dashboard"
                },
                'storage': {
                    'storage_type': 'supabase_database',
                    'backup_location': 'Supabase Database',
                    'compression_enabled': self.compress_backups,
                    'environment': 'Streamlit Cloud'
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting backup stats: {e}")
            return {
                'enabled': False,
                'error': str(e)
            }
    
    def _cleanup_operation_snapshots(self):
        """
        Cleanup old in-memory operation snapshots
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
    
    def _cleanup_database_backups(self):
        """
        Cleanup old database backups
        """
        if not self.supabase_handler or not self.supabase_handler.connected:
            return
        
        try:
            # Keep only the most recent backups
            delete_sql = """
            DELETE FROM backup_snapshots 
            WHERE id NOT IN (
                SELECT id FROM backup_snapshots 
                ORDER BY created_at DESC 
                LIMIT :max_backups
            )
            """
            
            with self.supabase_handler.engine.connect() as conn:
                result = conn.execute(text(delete_sql), {'max_backups': self.max_backups})
                deleted_count = result.rowcount
                conn.commit()
            
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old database backups")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up database backups: {e}")
    
    def list_operation_snapshots(self) -> List[Dict[str, Any]]:
        """
        List current in-memory operation snapshots
        """
        snapshots_list = []
        for snapshot_id, metadata in self.snapshot_metadata.items():
            snapshots_list.append({
                'id': snapshot_id,
                **metadata
            })
        
        return sorted(snapshots_list, key=lambda x: x['timestamp'], reverse=True)
    
    def create_downloadable_backup(self, fund_manager) -> Tuple[str, bytes]:
        """
        Create a downloadable backup file for local storage
        """
        try:
            backup_data = {
                'backup_type': 'DOWNLOAD',
                'timestamp': datetime.now().isoformat(),
                'date': date.today().isoformat(),
                'data': {
                    'investors': [asdict(inv) for inv in fund_manager.investors],
                    'tranches': [asdict(tr) for tr in fund_manager.tranches],
                    'transactions': [asdict(txn) for txn in fund_manager.transactions],
                    'fee_records': [asdict(fr) for fr in fund_manager.fee_records]
                }
            }
            
            # Convert to JSON and compress
            data_json = json.dumps(backup_data, ensure_ascii=False, default=str, indent=2)
            data_bytes = data_json.encode('utf-8')
            
            if self.compress_backups:
                compressed_data = gzip.compress(data_bytes)
                filename = f"fund_backup_{date.today().strftime('%Y%m%d')}.json.gz"
                return filename, compressed_data
            else:
                filename = f"fund_backup_{date.today().strftime('%Y%m%d')}.json"
                return filename, data_bytes
                
        except Exception as e:
            self.logger.error(f"Error creating downloadable backup: {e}")
            return None, None