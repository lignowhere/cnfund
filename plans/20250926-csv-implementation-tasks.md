# CSV Migration - Detailed Implementation Tasks

## TODO List for CSV Migration

### Phase 1: CSV Data Handler Implementation

#### Task 1.1: Create CSVDataHandler class
- [ ] Create new file `csv_data_handler.py`
- [ ] Implement class structure matching SupabaseDataHandler interface
- [ ] Add file locking mechanism for Windows/Unix
- [ ] Implement atomic write operations
- [ ] Add data validation methods
- [ ] Create backup before write functionality
- [ ] Add rollback capability

**Code Structure:**
```python
# csv_data_handler.py
import pandas as pd
import os
import shutil
import fcntl  # Unix
import msvcrt  # Windows
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

class CSVDataHandler:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # File paths
        self.investors_file = self.data_dir / "investors.csv"
        self.tranches_file = self.data_dir / "tranches.csv"
        self.transactions_file = self.data_dir / "transactions.csv"
        self.fee_records_file = self.data_dir / "fee_records.csv"
        self.metadata_file = self.data_dir / "metadata.json"
        
        # Cache
        self._cache = {}
        self._cache_ttl = {}
        
        # Initialize files if not exist
        self._initialize_files()
        
    def _initialize_files(self):
        """Create CSV files with headers if they don't exist"""
        pass
        
    def _atomic_write(self, file_path: Path, df: pd.DataFrame) -> bool:
        """Perform atomic write with rollback capability"""
        pass
        
    def _acquire_lock(self, file_path: Path, exclusive: bool = True):
        """Acquire file lock for concurrent access safety"""
        pass
        
    def load_investors(self) -> List[Investor]:
        """Load investors from CSV"""
        pass
        
    def save_investors(self, investors: List[Investor]) -> bool:
        """Save investors to CSV with transaction safety"""
        pass
        
    # Similar methods for tranches, transactions, fee_records
```

#### Task 1.2: Implement file locking
- [ ] Create cross-platform file locking utility
- [ ] Add read locks for concurrent reads
- [ ] Add write locks for exclusive writes
- [ ] Implement lock timeout and retry logic
- [ ] Add deadlock detection

**Code Example:**
```python
import platform
import time

class FileLock:
    def __init__(self, file_path, timeout=10):
        self.file_path = file_path
        self.timeout = timeout
        self.lock_file = None
        self.is_windows = platform.system() == 'Windows'
        
    def acquire_read_lock(self):
        """Acquire shared read lock"""
        pass
        
    def acquire_write_lock(self):
        """Acquire exclusive write lock"""
        pass
        
    def release(self):
        """Release the lock"""
        pass
```

### Phase 2: Data Migration Utility

#### Task 2.1: Create migration script
- [ ] Create `migrate_supabase_to_csv.py`
- [ ] Add command-line interface
- [ ] Implement progress tracking
- [ ] Add validation checks
- [ ] Create rollback mechanism

**Script Structure:**
```python
# migrate_supabase_to_csv.py
import argparse
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def migrate_data():
    """Main migration function"""
    print("Starting Supabase to CSV migration...")
    
    # Step 1: Backup existing data
    backup_existing_data()
    
    # Step 2: Connect to Supabase
    supabase = connect_supabase()
    
    # Step 3: Export data
    export_data(supabase)
    
    # Step 4: Validate migration
    validate_migration()
    
    # Step 5: Update configuration
    update_config()
    
def backup_existing_data():
    """Create backup of existing CSV files"""
    pass
    
def connect_supabase():
    """Connect to Supabase database"""
    pass
    
def export_data(supabase):
    """Export all tables from Supabase to CSV"""
    pass
    
def validate_migration():
    """Validate migrated data integrity"""
    pass
    
def update_config():
    """Update application configuration"""
    pass

if __name__ == "__main__":
    migrate_data()
```

#### Task 2.2: Data validation utilities
- [ ] Create validation functions for each entity
- [ ] Add referential integrity checks
- [ ] Implement data type validation
- [ ] Add business rule validation
- [ ] Create validation report

### Phase 3: Application Integration

#### Task 3.1: Update app.py
- [ ] Replace SupabaseDataHandler import
- [ ] Update data handler initialization
- [ ] Add CSV handler fallback logic
- [ ] Update error handling
- [ ] Add migration detection

**Changes in app.py:**
```python
# app.py modifications
@st.cache_resource  
def load_data_handler():
    """Load appropriate data handler"""
    try:
        # Check if migration completed
        if is_migrated_to_csv():
            from csv_data_handler import CSVDataHandler
            data_handler = CSVDataHandler()
            if data_handler.validate_files():
                st.sidebar.success("📁 Using local CSV storage")
                return data_handler
        
        # Fallback to Supabase (during transition)
        from supabase_data_handler import SupabaseDataHandler
        data_handler = SupabaseDataHandler()
        if data_handler.connected:
            st.sidebar.info("🌐 Using Supabase database")
            return data_handler
            
    except Exception as e:
        st.error(f"Error loading data handler: {e}")
        return None
        
def is_migrated_to_csv():
    """Check if system has been migrated to CSV"""
    metadata_file = Path("data/metadata.json")
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f)
            return metadata.get("storage_type") == "csv"
    return False
```

#### Task 3.2: Update services_enhanced.py
- [ ] Make data handler agnostic
- [ ] Update save operations
- [ ] Ensure compatibility with both handlers
- [ ] Update backup logic

### Phase 4: Testing Implementation

#### Task 4.1: Create unit tests
- [ ] Test CSV read/write operations
- [ ] Test atomic writes
- [ ] Test file locking
- [ ] Test concurrent access
- [ ] Test data validation

**Test Structure:**
```python
# test_csv_handler.py
import unittest
import tempfile
from pathlib import Path
from csv_data_handler import CSVDataHandler

class TestCSVHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.handler = CSVDataHandler(self.temp_dir)
        
    def test_atomic_write(self):
        """Test atomic write operations"""
        pass
        
    def test_concurrent_access(self):
        """Test concurrent read/write access"""
        pass
        
    def test_data_integrity(self):
        """Test data integrity after operations"""
        pass
```

#### Task 4.2: Create integration tests
- [ ] Test full transaction flow
- [ ] Test fee calculations
- [ ] Test NAV updates
- [ ] Test report generation
- [ ] Test backup/restore

### Phase 5: Performance Optimization

#### Task 5.1: Implement caching
- [ ] Add in-memory cache for frequently accessed data
- [ ] Implement cache TTL
- [ ] Add cache invalidation
- [ ] Create cache warming on startup

**Cache Implementation:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedCSVHandler(CSVDataHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_ttl = 60  # seconds
        self._cache = {}
        self._cache_timestamps = {}
        
    def _get_cached(self, key, loader_func, ttl=None):
        """Get data from cache or load if expired"""
        ttl = ttl or self.cache_ttl
        now = datetime.now()
        
        if key in self._cache:
            if now - self._cache_timestamps[key] < timedelta(seconds=ttl):
                return self._cache[key]
        
        # Load fresh data
        data = loader_func()
        self._cache[key] = data
        self._cache_timestamps[key] = now
        return data
```

#### Task 5.2: Create indexes
- [ ] Build investor ID index
- [ ] Create transaction date index
- [ ] Add tranche lookup index
- [ ] Implement binary search for large files

### Phase 6: Deployment

#### Task 6.1: Pre-deployment checklist
- [ ] Run all tests
- [ ] Backup production data
- [ ] Prepare rollback script
- [ ] Update documentation
- [ ] Notify users

#### Task 6.2: Deployment steps
- [ ] Deploy to staging environment
- [ ] Run migration script
- [ ] Validate migrated data
- [ ] Test all functionality
- [ ] Deploy to production

#### Task 6.3: Post-deployment
- [ ] Monitor for errors
- [ ] Check performance metrics
- [ ] Gather user feedback
- [ ] Document lessons learned

### Phase 7: Cleanup

#### Task 7.1: Remove Supabase dependencies
- [ ] Remove supabase_data_handler.py
- [ ] Remove SQLAlchemy from requirements.txt
- [ ] Remove psycopg2 from requirements.txt
- [ ] Clean up environment variables
- [ ] Update .gitignore

#### Task 7.2: Code cleanup
- [ ] Remove unused imports
- [ ] Delete deprecated functions
- [ ] Update comments and docstrings
- [ ] Refactor for simplicity

## Critical Implementation Notes

### Data Integrity
1. Always validate data before and after operations
2. Use checksums for critical operations
3. Implement automatic backup before writes
4. Keep audit log of all changes

### Performance Considerations
1. Use pandas for bulk operations
2. Implement lazy loading for large datasets
3. Cache frequently accessed data
4. Use chunked reads for memory efficiency

### Error Handling
1. Graceful degradation on errors
2. Automatic retry with exponential backoff
3. Comprehensive error logging
4. User-friendly error messages

### Security
1. Validate all input data
2. Sanitize file paths
3. Implement access controls
4. Encrypt sensitive data at rest

## Success Metrics

- [ ] All data migrated without loss
- [ ] Performance within 10% of database
- [ ] Zero data corruption incidents
- [ ] All tests passing
- [ ] User acceptance confirmed

## Emergency Procedures

### Rollback Procedure
1. Stop application
2. Restore Supabase configuration
3. Revert code changes
4. Restart application
5. Verify functionality

### Data Recovery
1. Identify corrupted files
2. Restore from latest backup
3. Replay transaction log if available
4. Validate recovered data
5. Resume operations

## Timeline

- **Week 1**: CSV handler implementation
- **Week 2**: Migration utility and testing
- **Week 3**: Integration and optimization
- **Week 4**: Deployment and monitoring

This detailed task list provides specific, actionable items for implementing the CSV migration. Each task includes code examples and clear acceptance criteria.