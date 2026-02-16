# Fix: Data Model Field Mapping Issues

**Date**: 2025-09-30
**Issue**: Save/Load data failed due to mismatched field names between models and DataFrames

## 🐛 Problem Description

### Symptoms
- ❌ "Lưu dữ liệu thất bại!" error when adding transactions
- AttributeError when trying to access fields like `transaction_type`, `tranche_id`, etc.
- Data not persisting to Google Drive

### Root Cause

**Model definitions** (`core/models.py`) have different field names than what the **data handler** (`core/drive_data_handler.py`) was expecting:

#### Transaction Model Mismatch

**Model Definition**:
```python
@dataclass
class Transaction:
    id: int
    investor_id: int
    date: datetime          # ← Not 'transaction_date'
    type: str               # ← Not 'transaction_type'
    amount: float
    nav: float
    units_change: float     # ← Not 'units'
```

**Handler Expected** (WRONG):
```python
txn.transaction_date  # ❌ Should be: txn.date
txn.transaction_type  # ❌ Should be: txn.type
txn.units            # ❌ Should be: txn.units_change
txn.tranche_id       # ❌ Doesn't exist in model
txn.fee_amount       # ❌ Doesn't exist in model
txn.net_amount       # ❌ Doesn't exist in model
txn.notes            # ❌ Doesn't exist in model
```

#### FeeRecord Model Mismatch

**Model Definition**:
```python
@dataclass
class FeeRecord:
    id: int
    period: str              # ← Not 'fee_type'
    investor_id: int
    fee_amount: float
    fee_units: float
    calculation_date: datetime  # ← Not 'fee_date'
    units_before: float
    units_after: float
    nav_per_unit: float      # ← Not 'nav_at_fee'
    description: str
```

**Handler Expected** (WRONG):
```python
fee.fee_type      # ❌ Should be: fee.period
fee.fee_date      # ❌ Should be: fee.calculation_date
fee.nav_at_fee    # ❌ Should be: fee.nav_per_unit
fee.tranche_id    # ❌ Doesn't exist in model
# Missing: fee_units, units_before, units_after
```

## ✅ Solution

### Fixed Field Mappings

#### 1. Transaction Save (`_transactions_to_df`)

```python
def _transactions_to_df(self, transactions: List[Transaction]) -> pd.DataFrame:
    data = []
    for txn in transactions:
        data.append({
            'id': txn.id,
            'transaction_type': txn.type,           # ✅ Map from 'type'
            'investor_id': txn.investor_id,
            'tranche_id': getattr(txn, 'tranche_id', ''),  # ✅ Optional
            'transaction_date': txn.date,           # ✅ Map from 'date'
            'units': txn.units_change,              # ✅ Map from 'units_change'
            'nav': txn.nav,
            'amount': txn.amount,
            'fee_amount': getattr(txn, 'fee_amount', 0.0),    # ✅ Optional
            'net_amount': getattr(txn, 'net_amount', 0.0),    # ✅ Optional
            'notes': getattr(txn, 'notes', '')                # ✅ Optional
        })
    return pd.DataFrame(data)
```

#### 2. Transaction Load (`load_transactions`)

```python
def load_transactions(self) -> List[Transaction]:
    for _, row in df.iterrows():
        transaction = Transaction(
            id=safe_int_conversion(row['id']),
            investor_id=safe_int_conversion(row['investor_id']),
            date=pd.to_datetime(row['transaction_date']),    # ✅ Map to 'date'
            type=str(row['transaction_type']),               # ✅ Map to 'type'
            amount=safe_float_conversion(row['amount']),
            nav=safe_float_conversion(row['nav']),
            units_change=safe_float_conversion(row['units']) # ✅ Map to 'units_change'
        )
```

#### 3. FeeRecord Save (`_fee_records_to_df`)

```python
def _fee_records_to_df(self, fee_records: List[FeeRecord]) -> pd.DataFrame:
    data = []
    for fee in fee_records:
        data.append({
            'id': fee.id,
            'investor_id': fee.investor_id,
            'tranche_id': getattr(fee, 'tranche_id', ''),    # ✅ Optional
            'fee_date': fee.calculation_date,                # ✅ Map from 'calculation_date'
            'fee_type': fee.period,                          # ✅ Map from 'period'
            'fee_amount': fee.fee_amount,
            'nav_at_fee': fee.nav_per_unit,                  # ✅ Map from 'nav_per_unit'
            'description': fee.description,
            # ✅ Additional fields from model
            'fee_units': fee.fee_units,
            'units_before': fee.units_before,
            'units_after': fee.units_after
        })
    return pd.DataFrame(data)
```

#### 4. FeeRecord Load (`load_fee_records`)

```python
def load_fee_records(self) -> List[FeeRecord]:
    for _, row in df.iterrows():
        fee_record = FeeRecord(
            id=safe_int_conversion(row['id']),
            investor_id=safe_int_conversion(row['investor_id']),
            period=str(row['fee_type']),                            # ✅ Map to 'period'
            fee_amount=safe_float_conversion(row['fee_amount']),
            fee_units=safe_float_conversion(row.get('fee_units', 0.0)),
            calculation_date=pd.to_datetime(row['fee_date']),       # ✅ Map to 'calculation_date'
            units_before=safe_float_conversion(row.get('units_before', 0.0)),
            units_after=safe_float_conversion(row.get('units_after', 0.0)),
            nav_per_unit=safe_float_conversion(row.get('nav_at_fee', 0.0)),  # ✅ Map to 'nav_per_unit'
            description=str(row.get('description', ''))
        )
```

### Added Debug Logging

Enhanced `save_all_data_enhanced` with detailed logging:

```python
def save_all_data_enhanced(...) -> bool:
    try:
        print(f"💾 Starting save: {len(investors)} investors, {len(tranches)} tranches...")

        print("📊 Converting to DataFrames...")
        # ... conversion ...

        print(f"✅ DataFrames created: {len(investors_df)} investors...")

        print("💾 Saving to session state...")
        # ... save ...

        print("✅ Session state updated")

        print("☁️ Backing up to Drive...")
        success = self.backup_to_drive()

        if success:
            print("✅ Save completed successfully")
        else:
            print("⚠️ Drive backup failed (session state saved)")
```

## 📊 Field Mapping Reference

### Transaction Fields

| DataFrame Column    | Model Field   | Notes                  |
|---------------------|---------------|------------------------|
| `id`                | `id`          | ✅ Direct mapping      |
| `investor_id`       | `investor_id` | ✅ Direct mapping      |
| `transaction_date`  | `date`        | 🔄 Renamed             |
| `transaction_type`  | `type`        | 🔄 Renamed             |
| `units`             | `units_change`| 🔄 Renamed             |
| `amount`            | `amount`      | ✅ Direct mapping      |
| `nav`               | `nav`         | ✅ Direct mapping      |
| `tranche_id`        | N/A           | ⚠️ Optional (not in model) |
| `fee_amount`        | N/A           | ⚠️ Optional (not in model) |
| `net_amount`        | N/A           | ⚠️ Optional (not in model) |
| `notes`             | N/A           | ⚠️ Optional (not in model) |

### FeeRecord Fields

| DataFrame Column | Model Field        | Notes                  |
|------------------|--------------------|------------------------|
| `id`             | `id`               | ✅ Direct mapping      |
| `investor_id`    | `investor_id`      | ✅ Direct mapping      |
| `fee_date`       | `calculation_date` | 🔄 Renamed             |
| `fee_type`       | `period`           | 🔄 Renamed             |
| `nav_at_fee`     | `nav_per_unit`     | 🔄 Renamed             |
| `fee_amount`     | `fee_amount`       | ✅ Direct mapping      |
| `description`    | `description`      | ✅ Direct mapping      |
| `fee_units`      | `fee_units`        | ✅ Added to DataFrame  |
| `units_before`   | `units_before`     | ✅ Added to DataFrame  |
| `units_after`    | `units_after`      | ✅ Added to DataFrame  |
| `tranche_id`     | N/A                | ⚠️ Optional (not in model) |

## 🎯 Testing

### Verify Fix

1. **Add Transaction**:
   ```
   ✅ Transaction should save successfully
   ✅ Check logs for "✅ Save completed successfully"
   ```

2. **Reload App**:
   ```
   ✅ Transaction should appear in list
   ✅ Data persisted to Google Drive
   ```

3. **Check Logs**:
   ```
   💾 Starting save: X investors, Y tranches, Z transactions...
   📊 Converting to DataFrames...
   ✅ DataFrames created: ...
   💾 Saving to session state...
   ✅ Session state updated
   ☁️ Backing up to Drive...
   ✅ Save completed successfully
   ```

## 🐛 Troubleshooting

### Still Getting Save Errors?

**Check logs for**:
1. Which step failed (converting, session save, or Drive backup)?
2. Specific error message from traceback

**Common issues**:
- **Converting fails**: Check model field names match mappings
- **Session save fails**: Check Streamlit session state
- **Drive backup fails**: Check OAuth connection and folder permissions

### Data Not Loading?

**Check**:
1. Excel file structure matches expected columns
2. Field mappings in `load_*` methods are correct
3. DataFrame column names haven't changed

## 📚 Related Files

- `core/models.py` - Model definitions (source of truth)
- `core/drive_data_handler.py` - Save/Load implementation
- `core/services_enhanced.py` - Business logic using models

## 🎉 Result

✅ **Save/Load now works correctly**
✅ **Field names properly mapped**
✅ **Optional fields handled gracefully**
✅ **Debug logging for troubleshooting**
✅ **Data persists to Google Drive**

---

**Key Lesson**: Always check model definitions when working with data persistence! Field name mismatches cause silent failures.