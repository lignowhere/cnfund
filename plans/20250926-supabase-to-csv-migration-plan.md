# Fund Management System: Supabase to CSV Migration Plan

## Overview

This document outlines the comprehensive plan to migrate the Fund Management System from Supabase (PostgreSQL) database to a local CSV-based storage solution. The goal is to eliminate dependency on third-party cloud services while maintaining data integrity, performance, and all existing functionality.

## Current System Analysis

### Database Structure (Supabase/PostgreSQL)

The system currently uses 4 main tables:

1. **investors** - Stores investor information
   - id (INTEGER PRIMARY KEY)
   - name (TEXT NOT NULL)
   - phone (TEXT)
   - address (TEXT)
   - email (TEXT)
   - join_date (DATE)
   - is_fund_manager (BOOLEAN DEFAULT FALSE)

2. **tranches** - Tracks investment tranches
   - tranche_id (VARCHAR(255) PRIMARY KEY)
   - investor_id (INTEGER REFERENCES investors)
   - entry_date (TIMESTAMP)
   - entry_nav (NUMERIC)
   - units (NUMERIC)
   - hwm (NUMERIC)
   - original_entry_date (TIMESTAMP)
   - original_entry_nav (NUMERIC)
   - cumulative_fees_paid (NUMERIC)

3. **transactions** - Records all financial transactions
   - id (INTEGER PRIMARY KEY)
   - investor_id (INTEGER)
   - date (TIMESTAMP)
   - type (TEXT)
   - amount (NUMERIC)
   - nav (NUMERIC)
   - units_change (NUMERIC)

4. **fee_records** - Tracks fee calculations
   - id (INTEGER PRIMARY KEY)
   - period (TEXT)
   - investor_id (INTEGER REFERENCES investors)
   - fee_amount (NUMERIC)
   - fee_units (NUMERIC)
   - calculation_date (TIMESTAMP)
   - units_before (NUMERIC)
   - units_after (NUMERIC)
   - nav_per_unit (NUMERIC)
   - description (TEXT)

### Current Data Flow

1. **SupabaseDataHandler** connects to PostgreSQL via SQLAlchemy
2. Data is loaded into model objects (Investor, Tranche, Transaction, FeeRecord)
3. EnhancedFundManager manages business logic
4. Data is saved back to database using transactions for atomicity

### Existing CSV Support

The system already has partial CSV support through **EnhancedDataHandler** in `data_handler.py`:
- Can read/write investors.csv, tranches.csv, transactions.csv, fee_records.csv
- Located in `data/` directory
- Has backup functionality to `data/backups/`
- Includes validation and type safety

## Migration Architecture

### Phase 1: CSV Data Structure Design

#### File Organization
```
data/
├── investors.csv          # Investor records
├── tranches.csv          # Investment tranches
├── transactions.csv      # Transaction history
├── fee_records.csv       # Fee calculations
├── nav_history.csv       # NAV snapshots (new)
├── metadata.json         # Database metadata and versioning
└── backups/
    ├── daily/           # Daily automatic backups
    ├── manual/          # Manual backups
    └── migration/       # Pre-migration backups
```

#### CSV Schema Definitions

**investors.csv**
```csv
ID,Name,Phone,Address,Email,JoinDate,IsFundManager
0,Fund Manager,,,,2024-01-01,true
1,John Doe,0987654321,123 Main St,john@email.com,2024-01-15,false
```

**tranches.csv**
```csv
InvestorID,TrancheID,EntryDate,EntryNAV,Units,HWM,OriginalEntryDate,OriginalEntryNAV,CumulativeFeesPaid,OriginalInvestedValue,InvestedValue
1,TRN_1_1704067200,2024-01-15 10:00:00,10000.0,1000.0,10500.0,2024-01-15 10:00:00,10000.0,500.0,10000000.0,10000000.0
```

**transactions.csv**
```csv
ID,InvestorID,Date,Type,Amount,NAV,UnitsChange
1,1,2024-01-15 10:00:00,Nạp,10000000.0,10000.0,1000.0
2,0,2024-02-01 10:00:00,NAV Update,0,10500.0,0
```

**fee_records.csv**
```csv
ID,Period,InvestorID,FeeAmount,FeeUnits,CalculationDate,UnitsBefore,UnitsAfter,NAVPerUnit,Description
1,Q1-2024,1,500000.0,47.62,2024-03-31 23:59:59,1000.0,952.38,10500.0,Performance fee Q1-2024
```

### Phase 2: Enhanced CSV Data Handler Implementation

#### Core Components

1. **CSVDataHandler** class
   - Thread-safe file operations
   - Transaction-like behavior using temporary files
   - Data validation and integrity checks
   - Automatic backups before writes
   - File locking mechanism

2. **Data Integrity Features**
   - Atomic writes using temp files and rename
   - Referential integrity validation
   - Type validation and conversion
   - Data consistency checks
   - Rollback capability

3. **Performance Optimizations**
   - In-memory caching with TTL
   - Batch operations
   - Lazy loading
   - Index files for quick lookups

### Phase 3: Migration Process

#### Pre-Migration Steps

1. **Full System Backup**
   - Database dump from Supabase
   - Export all tables to CSV
   - Create migration timestamp
   - Document current state

2. **Data Validation**
   - Check for orphaned records
   - Validate foreign key relationships
   - Ensure data type compatibility
   - Verify calculation accuracy

#### Migration Execution

1. **Export from Supabase**
```python
def export_supabase_to_csv():
    supabase = SupabaseDataHandler()
    
    # Load all data
    investors = supabase.load_investors()
    tranches = supabase.load_tranches()
    transactions = supabase.load_transactions()
    fee_records = supabase.load_fee_records()
    
    # Save to CSV files
    csv_handler = CSVDataHandler()
    csv_handler.save_all_data(investors, tranches, transactions, fee_records)
```

2. **Data Transformation**
   - Convert timestamps to timezone-aware format
   - Normalize numeric precision
   - Handle NULL values appropriately
   - Generate missing IDs if needed

3. **Verification**
   - Compare record counts
   - Validate calculations
   - Test critical operations
   - Verify data relationships

### Phase 4: Application Updates

#### Code Changes Required

1. **app.py modifications**
```python
# Replace Supabase import
# from supabase_data_handler import SupabaseDataHandler
from csv_data_handler import CSVDataHandler

def load_data_handler():
    """Load CSV data handler"""
    try:
        data_handler = CSVDataHandler()
        if not data_handler.validate_data_files():
            st.error("Missing or corrupted data files")
            return None
        return data_handler
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None
```

2. **Remove Supabase dependencies**
   - Remove SQLAlchemy requirements
   - Remove psycopg2 dependency
   - Update requirements.txt
   - Clean up connection strings

3. **Update backup system**
   - Simplify to file-based backups only
   - Remove cloud backup manager references
   - Update backup restoration process

### Phase 5: Data Safety and Recovery

#### Transaction Safety

1. **Write Operations**
```python
def safe_write_csv(self, file_path, data):
    """Atomic CSV write with rollback"""
    temp_file = f"{file_path}.tmp"
    backup_file = f"{file_path}.bak"
    
    try:
        # Create backup
        if os.path.exists(file_path):
            shutil.copy2(file_path, backup_file)
        
        # Write to temp file
        data.to_csv(temp_file, index=False)
        
        # Validate temp file
        test_read = pd.read_csv(temp_file)
        if len(test_read) != len(data):
            raise ValueError("Data validation failed")
        
        # Atomic rename
        os.replace(temp_file, file_path)
        
        # Clean up backup
        if os.path.exists(backup_file):
            os.remove(backup_file)
            
    except Exception as e:
        # Rollback
        if os.path.exists(backup_file):
            os.replace(backup_file, file_path)
        raise e
```

2. **Concurrent Access**
   - File locking using fcntl (Unix) or msvcrt (Windows)
   - Read-write locks for performance
   - Queue-based write operations
   - Retry mechanism for locked files

#### Backup Strategy

1. **Automatic Backups**
   - Before each write operation
   - Daily snapshots at midnight
   - Keep last 30 days of backups
   - Compress old backups

2. **Manual Backups**
   - Export function in UI
   - Timestamped archives
   - Include metadata
   - Option to backup to external drive

### Phase 6: Testing Plan

#### Unit Tests

1. **Data Handler Tests**
   - CRUD operations for each entity
   - Transaction safety
   - Concurrent access
   - Data validation
   - Error recovery

2. **Migration Tests**
   - Export accuracy
   - Import completeness
   - Data transformation
   - Relationship preservation

#### Integration Tests

1. **Business Logic**
   - NAV calculations
   - Fee calculations
   - Transaction processing
   - Report generation

2. **Performance Tests**
   - Load times
   - Save operations
   - Concurrent users
   - Large datasets

#### User Acceptance Tests

1. **Functionality**
   - All features work as before
   - No data loss
   - Performance acceptable
   - Backup/restore works

## Implementation Timeline

### Week 1: Preparation
- [ ] Create comprehensive backups
- [ ] Set up development environment
- [ ] Write CSVDataHandler class
- [ ] Implement data validation

### Week 2: Core Development
- [ ] Implement atomic file operations
- [ ] Add transaction safety
- [ ] Create migration scripts
- [ ] Write unit tests

### Week 3: Migration
- [ ] Export production data
- [ ] Run migration scripts
- [ ] Validate migrated data
- [ ] Update application code

### Week 4: Testing & Deployment
- [ ] Run comprehensive tests
- [ ] Fix identified issues
- [ ] User acceptance testing
- [ ] Deploy to production

## Risk Mitigation

### Identified Risks

1. **Data Loss**
   - Mitigation: Multiple backup strategies
   - Recovery: Rollback procedures

2. **Concurrent Access Issues**
   - Mitigation: File locking mechanism
   - Recovery: Queue-based operations

3. **Performance Degradation**
   - Mitigation: In-memory caching
   - Recovery: Database fallback option

4. **Data Corruption**
   - Mitigation: Validation at every step
   - Recovery: Automatic backup restoration

## Success Criteria

1. **Zero Data Loss** - All records migrated successfully
2. **Functionality Preserved** - All features work as before
3. **Performance Maintained** - Response times within 10% of current
4. **Data Integrity** - All validations pass
5. **User Satisfaction** - No user-facing issues

## Post-Migration Tasks

1. **Monitoring**
   - Watch for errors
   - Monitor performance
   - Track user feedback

2. **Optimization**
   - Tune cache settings
   - Optimize file I/O
   - Improve indexing

3. **Documentation**
   - Update user guides
   - Developer documentation
   - Backup procedures

## Rollback Plan

If critical issues arise:

1. **Immediate Rollback**
   - Restore Supabase connection
   - Revert code changes
   - Restore from backup

2. **Data Recovery**
   - Export CSV data
   - Import to Supabase
   - Verify data integrity

3. **Communication**
   - Notify users
   - Document issues
   - Plan remediation

## Conclusion

This migration plan provides a comprehensive approach to transitioning from Supabase to local CSV storage. The key benefits include:

- **Independence** from third-party services
- **Simplicity** of data management
- **Portability** of data files
- **Cost savings** from eliminated hosting
- **Full control** over data and backups

The plan prioritizes data safety, maintains functionality, and ensures a smooth transition for users.