# database_save_optimization.py - Database-level save optimization

import streamlit as st
import time
from typing import List, Dict, Any
from sqlalchemy import text
import pandas as pd

class DatabaseSaveOptimizer:
    """Database-level save optimization"""
    
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.engine = data_handler.engine
    
    def ultra_fast_save(self, investors, tranches, transactions, fee_records) -> tuple[bool, str, Dict[str, float]]:
        """Ultra-fast save with minimal database round trips"""
        timing_info = {}
        start_time = time.time()
        
        try:
            # Step 1: Convert to DataFrames (faster bulk operations)
            prep_start = time.time()
            df_investors = self._prepare_investors_df(investors)
            df_tranches = self._prepare_tranches_df(tranches)
            df_transactions = self._prepare_transactions_df(transactions)
            df_fee_records = self._prepare_fee_records_df(fee_records)
            timing_info['preparation'] = time.time() - prep_start
            
            # Step 2: Single transaction with bulk operations
            save_start = time.time()
            success = self._bulk_save_all_tables(df_investors, df_tranches, df_transactions, df_fee_records)
            timing_info['save_execution'] = time.time() - save_start
            
            total_time = time.time() - start_time
            timing_info['total'] = total_time
            
            if success:
                return True, f"Ultra-fast save: {total_time:.1f}s", timing_info
            else:
                return False, f"Ultra-fast save failed after {total_time:.1f}s", timing_info
                
        except Exception as e:
            total_time = time.time() - start_time
            timing_info['total'] = total_time
            return False, f"Ultra-fast save error: {str(e)}", timing_info
    
    def _prepare_investors_df(self, investors) -> pd.DataFrame:
        """Convert investors to optimized DataFrame"""
        if not investors:
            return pd.DataFrame()
        
        data = []
        for inv in investors:
            data.append({
                'id': inv.id,
                'name': inv.name,
                'phone': inv.phone or '',
                'address': inv.address or '',
                'email': inv.email or '',
                'join_date': inv.join_date,
                'is_fund_manager': inv.is_fund_manager
            })
        
        return pd.DataFrame(data)
    
    def _prepare_tranches_df(self, tranches) -> pd.DataFrame:
        """Convert tranches to optimized DataFrame"""
        if not tranches:
            return pd.DataFrame()
        
        data = []
        for t in tranches:
            data.append({
                'investor_id': t.investor_id,
                'tranche_id': t.tranche_id,
                'entry_date': t.entry_date,
                'entry_nav': float(t.entry_nav),
                'units': float(t.units),
                'hwm': float(t.hwm),
                'original_entry_date': t.original_entry_date,
                'original_entry_nav': float(t.original_entry_nav),
                'cumulative_fees_paid': float(t.cumulative_fees_paid)
            })
        
        return pd.DataFrame(data)
    
    def _prepare_transactions_df(self, transactions) -> pd.DataFrame:
        """Convert transactions to optimized DataFrame"""
        if not transactions:
            return pd.DataFrame()
        
        data = []
        for t in transactions:
            data.append({
                'id': t.id,
                'investor_id': t.investor_id,
                'date': t.date,
                'type': t.type,
                'amount': float(t.amount),
                'nav': float(t.nav),
                'units_change': float(t.units_change)
            })
        
        return pd.DataFrame(data)
    
    def _prepare_fee_records_df(self, fee_records) -> pd.DataFrame:
        """Convert fee records to optimized DataFrame"""
        if not fee_records:
            return pd.DataFrame()
        
        data = []
        for f in fee_records:
            data.append({
                'id': f.id,
                'period': f.period,
                'investor_id': f.investor_id,
                'fee_amount': float(f.fee_amount),
                'fee_units': float(f.fee_units),
                'calculation_date': f.calculation_date,
                'units_before': float(f.units_before),
                'units_after': float(f.units_after),
                'nav_per_unit': float(f.nav_per_unit),
                'description': f.description or ''
            })
        
        return pd.DataFrame(data)
    
    def _bulk_save_all_tables(self, df_investors, df_tranches, df_transactions, df_fee_records) -> bool:
        """Bulk save all tables in single transaction"""
        try:
            with self.engine.begin() as conn:
                # Delete all data first (in correct order)
                conn.execute(text("DELETE FROM fee_records"))
                conn.execute(text("DELETE FROM transactions"))
                conn.execute(text("DELETE FROM tranches"))
                conn.execute(text("DELETE FROM investors"))
                
                # Bulk insert using pandas to_sql (much faster)
                if not df_investors.empty:
                    df_investors.to_sql('investors', conn, if_exists='append', index=False, method='multi')
                
                if not df_tranches.empty:
                    df_tranches.to_sql('tranches', conn, if_exists='append', index=False, method='multi')
                
                if not df_transactions.empty:
                    df_transactions.to_sql('transactions', conn, if_exists='append', index=False, method='multi')
                
                if not df_fee_records.empty:
                    df_fee_records.to_sql('fee_records', conn, if_exists='append', index=False, method='multi')
            
            return True
            
        except Exception as e:
            st.error(f"Bulk save failed: {str(e)}")
            return False

class MinimalSaveOptimizer:
    """Minimal save optimization for fastest possible saves"""
    
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.engine = data_handler.engine
    
    def minimal_save(self, investors, tranches, transactions, fee_records) -> tuple[bool, str, float]:
        """Minimal save with only essential data"""
        start_time = time.time()
        
        try:
            # Only save changed data (not implemented yet - would require change tracking)
            # For now, use optimized bulk save
            
            with self.engine.begin() as conn:
                # Truncate tables (faster than DELETE)
                conn.execute(text("TRUNCATE TABLE fee_records RESTART IDENTITY CASCADE"))
                conn.execute(text("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE"))
                conn.execute(text("TRUNCATE TABLE tranches RESTART IDENTITY CASCADE"))
                conn.execute(text("TRUNCATE TABLE investors RESTART IDENTITY CASCADE"))
                
                # Bulk insert with optimized batch size
                self._fast_bulk_insert(conn, 'investors', investors)
                self._fast_bulk_insert(conn, 'tranches', tranches)
                self._fast_bulk_insert(conn, 'transactions', transactions)
                self._fast_bulk_insert(conn, 'fee_records', fee_records)
            
            save_time = time.time() - start_time
            return True, f"Minimal save completed in {save_time:.1f}s", save_time
            
        except Exception as e:
            save_time = time.time() - start_time
            return False, f"Minimal save failed: {str(e)}", save_time
    
    def _fast_bulk_insert(self, conn, table_name: str, data_objects: List):
        """Fast bulk insert with optimized SQL"""
        if not data_objects:
            return
        
        if table_name == 'investors':
            values = []
            for inv in data_objects:
                values.append(f"({inv.id}, '{inv.name}', '{inv.phone or ''}', '{inv.address or ''}', "
                            f"'{inv.email or ''}', '{inv.join_date}', {inv.is_fund_manager})")
            
            if values:
                sql = f"""
                INSERT INTO investors (id, name, phone, address, email, join_date, is_fund_manager)
                VALUES {', '.join(values)}
                """
                conn.execute(text(sql))
        
        elif table_name == 'tranches':
            values = []
            for t in data_objects:
                values.append(f"({t.investor_id}, '{t.tranche_id}', '{t.entry_date}', "
                            f"{t.entry_nav}, {t.units}, {t.hwm}, '{t.original_entry_date}', "
                            f"{t.original_entry_nav}, {t.cumulative_fees_paid})")
            
            if values:
                sql = f"""
                INSERT INTO tranches (investor_id, tranche_id, entry_date, entry_nav, units, hwm,
                                    original_entry_date, original_entry_nav, cumulative_fees_paid)
                VALUES {', '.join(values)}
                """
                conn.execute(text(sql))
        
        elif table_name == 'transactions':
            values = []
            for t in data_objects:
                values.append(f"({t.id}, {t.investor_id}, '{t.date}', '{t.type}', "
                            f"{t.amount}, {t.nav}, {t.units_change})")
            
            if values:
                sql = f"""
                INSERT INTO transactions (id, investor_id, date, type, amount, nav, units_change)
                VALUES {', '.join(values)}
                """
                conn.execute(text(sql))
        
        elif table_name == 'fee_records':
            values = []
            for f in data_objects:
                values.append(f"({f.id}, '{f.period}', {f.investor_id}, {f.fee_amount}, "
                            f"{f.fee_units}, '{f.calculation_date}', {f.units_before}, "
                            f"{f.units_after}, {f.nav_per_unit}, '{f.description or ''}')")
            
            if values:
                sql = f"""
                INSERT INTO fee_records (id, period, investor_id, fee_amount, fee_units,
                                       calculation_date, units_before, units_after, nav_per_unit, description)
                VALUES {', '.join(values)}
                """
                conn.execute(text(sql))

class NetworkOptimizer:
    """Optimize network-related database operations"""
    
    def __init__(self, data_handler):
        self.data_handler = data_handler
        self.engine = data_handler.engine
    
    def test_connection_speed(self) -> Dict[str, float]:
        """Test various aspects of database connection speed"""
        results = {}
        
        try:
            # Test 1: Simple ping
            start_time = time.time()
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results['ping'] = time.time() - start_time
            
            # Test 2: Small query
            start_time = time.time()
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM investors"))
                result.fetchone()
            results['small_query'] = time.time() - start_time
            
            # Test 3: Transaction overhead
            start_time = time.time()
            with self.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            results['transaction_overhead'] = time.time() - start_time
            
            # Test 4: Bulk operation simulation
            start_time = time.time()
            with self.engine.connect() as conn:
                conn.execute(text("SELECT * FROM investors LIMIT 1"))
            results['bulk_simulation'] = time.time() - start_time
            
        except Exception as e:
            st.error(f"Connection speed test failed: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def optimize_connection_settings(self):
        """Suggest connection optimizations"""
        speed_test = self.test_connection_speed()
        
        suggestions = []
        
        if speed_test.get('ping', 0) > 1.0:
            suggestions.append("High network latency detected. Consider using connection pooling.")
        
        if speed_test.get('transaction_overhead', 0) > 0.5:
            suggestions.append("High transaction overhead. Batch operations recommended.")
        
        if speed_test.get('small_query', 0) > 0.3:
            suggestions.append("Query execution slow. Check database server performance.")
        
        return suggestions

# === INTEGRATION FUNCTIONS ===

def apply_database_save_optimization(fund_manager):
    """Apply database-level save optimization"""
    
    data_handler = fund_manager.data_handler
    db_optimizer = DatabaseSaveOptimizer(data_handler)
    minimal_optimizer = MinimalSaveOptimizer(data_handler)
    
    def ultra_fast_save_data():
        """Ultra-fast save method"""
        success, message, timing = db_optimizer.ultra_fast_save(
            fund_manager.investors,
            fund_manager.tranches,
            fund_manager.transactions,
            fund_manager.fee_records
        )
        
        # Show performance feedback
        if timing:
            total_time = timing.get('total', 0)
            prep_time = timing.get('preparation', 0)
            save_time = timing.get('save_execution', 0)
            
            if total_time > 8:
                st.sidebar.error(f"🔴 Ultra save: {total_time:.1f}s")
            elif total_time > 4:
                st.sidebar.warning(f"🟡 Ultra save: {total_time:.1f}s")
            else:
                st.sidebar.success(f"🟢 Ultra save: {total_time:.1f}s")
            
            # Detailed breakdown
            if total_time > 3:
                with st.sidebar.expander("⚡ Ultra Save Breakdown"):
                    st.write(f"Preparation: {prep_time:.2f}s")
                    st.write(f"Database: {save_time:.2f}s")
                    st.write(f"Network ratio: {(save_time/total_time*100):.0f}%")
        
        return success
    
    def minimal_save_data():
        """Minimal save method"""
        success, message, save_time = minimal_optimizer.minimal_save(
            fund_manager.investors,
            fund_manager.tranches,
            fund_manager.transactions,
            fund_manager.fee_records
        )
        
        if save_time > 5:
            st.sidebar.warning(f"🟡 Minimal save: {save_time:.1f}s")
        else:
            st.sidebar.success(f"🟢 Minimal save: {save_time:.1f}s")
        
        return success
    
    # Add new methods to fund manager
    fund_manager.ultra_fast_save_data = ultra_fast_save_data
    fund_manager.minimal_save_data = minimal_save_data
    
    return fund_manager

def render_database_diagnostics(data_handler):
    """Render database diagnostics UI"""
    st.subheader("🔬 Database Diagnostics")
    
    network_optimizer = NetworkOptimizer(data_handler)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏃 Test Connection Speed", width="stretch"):
            with st.spinner("Testing connection speed..."):
                speed_results = network_optimizer.test_connection_speed()
                
                if 'error' not in speed_results:
                    st.subheader("📊 Speed Test Results")
                    
                    for test_name, duration in speed_results.items():
                        if duration > 1.0:
                            st.error(f"🔴 {test_name}: {duration:.2f}s")
                        elif duration > 0.5:
                            st.warning(f"🟡 {test_name}: {duration:.2f}s")
                        else:
                            st.success(f"🟢 {test_name}: {duration:.2f}s")
                else:
                    st.error(f"Speed test failed: {speed_results['error']}")
    
    with col2:
        if st.button("💡 Get Optimization Tips", width="stretch"):
            suggestions = network_optimizer.optimize_connection_settings()
            
            if suggestions:
                st.subheader("💡 Optimization Suggestions")
                for suggestion in suggestions:
                    st.info(f"• {suggestion}")
            else:
                st.success("✅ Connection performance looks good!")

def enhanced_save_options(fund_manager):
    """Enhanced save options with database optimization"""
    
    if not st.session_state.get('data_changed', False):
        return
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Enhanced Save Options")
    
    save_method = st.sidebar.radio(
        "Save Method",
        ["🚀 Ultra Fast", "⚡ Minimal", "📊 Standard"],
        key="enhanced_save_method"
    )
    
    if save_method == "🚀 Ultra Fast":
        if st.sidebar.button("💾 Ultra Fast Save", width="stretch"):
            if hasattr(fund_manager, 'ultra_fast_save_data'):
                success = fund_manager.ultra_fast_save_data()
            else:
                success = fund_manager.save_data()
            
            if success:
                st.session_state.data_changed = False
                st.sidebar.success("✅ Ultra fast save completed")
            else:
                st.sidebar.error("❌ Ultra fast save failed")
    
    elif save_method == "⚡ Minimal":
        if st.sidebar.button("💾 Minimal Save", width="stretch"):
            if hasattr(fund_manager, 'minimal_save_data'):
                success = fund_manager.minimal_save_data()
            else:
                success = fund_manager.save_data()
            
            if success:
                st.session_state.data_changed = False
                st.sidebar.success("✅ Minimal save completed")
            else:
                st.sidebar.error("❌ Minimal save failed")
    
    elif save_method == "📊 Standard":
        if st.sidebar.button("💾 Standard Save", width="stretch"):
            start_time = time.time()
            success = fund_manager.save_data()
            save_time = time.time() - start_time
            
            if success:
                st.session_state.data_changed = False
                st.sidebar.success(f"✅ Standard save: {save_time:.1f}s")
            else:
                st.sidebar.error("❌ Standard save failed")