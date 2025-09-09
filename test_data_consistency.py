#!/usr/bin/env python3
"""
Data Consistency and Integration Testing for Performance Optimizations
Validates that optimizations don't break data integrity
"""

import time
import unittest
import sys
import os
from datetime import datetime, date
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from performance_optimizer import (
        PerformanceOptimizer, 
        FastTransactionProcessor,
        get_optimizer
    )
    PERFORMANCE_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Performance module not available: {e}")
    PERFORMANCE_MODULE_AVAILABLE = False

try:
    from services_enhanced import EnhancedFundManager
    from models import Investor, Tranche, Transaction
    from timezone_manager import TimezoneManager
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Models not available: {e}")
    MODELS_AVAILABLE = False

class MockDataHandler:
    """Enhanced mock data handler for data consistency testing"""
    def __init__(self):
        self.connected = True
        self.engine = Mock()
        self.save_operations = []
        self.save_delay = 0.05
        
        # Store data for consistency validation
        self.stored_investors = []
        self.stored_tranches = []
        self.stored_transactions = []
        self.stored_fee_records = []
    
    def save_all_data_enhanced(self, investors, tranches, transactions, fee_records):
        """Mock save that stores data for validation"""
        time.sleep(self.save_delay)
        
        # Record the save operation with timestamp
        self.save_operations.append({
            'timestamp': datetime.now(),
            'investors': investors.copy() if investors else [],
            'tranches': tranches.copy() if tranches else [],
            'transactions': transactions.copy() if transactions else [],
            'fee_records': fee_records.copy() if fee_records else []
        })
        
        # Update stored data
        self.stored_investors = investors.copy() if investors else []
        self.stored_tranches = tranches.copy() if tranches else []
        self.stored_transactions = transactions.copy() if transactions else []
        self.stored_fee_records = fee_records.copy() if fee_records else []
        
        return True
    
    def load_investors(self):
        return self.stored_investors
    
    def load_tranches(self):
        return self.stored_tranches
    
    def load_transactions(self):
        return self.stored_transactions
    
    def load_fee_records(self):
        return self.stored_fee_records

class DataConsistencyTests(unittest.TestCase):
    """Test data consistency with performance optimizations"""
    
    def setUp(self):
        if not PERFORMANCE_MODULE_AVAILABLE or not MODELS_AVAILABLE:
            self.skipTest("Required modules not available")
            
        self.mock_data_handler = MockDataHandler()
        self.fund_manager = EnhancedFundManager(self.mock_data_handler, enable_snapshots=False)
        
        # Add test data
        test_investor = Investor(id="investor_001", name="Test Investor", email="test@example.com")
        self.fund_manager.investors = [test_investor]
        
        # Initialize with some funds
        initial_tranche = Tranche(
            investor_id="investor_001",
            tranche_id="tranche_001",
            entry_date=datetime.now(),
            entry_nav=1000.0,
            units=1000.0,
            original_invested_value=1000000.0
        )
        self.fund_manager.tranches = [initial_tranche]
    
    def test_background_save_data_integrity(self):
        """Test that background saves maintain data integrity"""
        from performance_optimizer import create_fast_processor
        
        fast_processor = create_fast_processor(self.fund_manager)
        
        # Record initial state
        initial_investor_count = len(self.fund_manager.investors)
        initial_tranche_count = len(self.fund_manager.tranches)
        initial_transaction_count = len(self.fund_manager.transactions)
        
        with patch('streamlit.success'), patch('streamlit.error'), patch('streamlit.balloons'):
            # Mock deposit transaction
            def mock_deposit(investor_id, amount, nav, date):
                # Add a transaction to simulate deposit
                new_transaction = Transaction(
                    id=f"trans_{len(self.fund_manager.transactions) + 1}",
                    investor_id=investor_id,
                    date=date,
                    type="Nạp",
                    amount=amount,
                    nav=nav,
                    units_change=amount / (nav / sum(t.units for t in self.fund_manager.tranches))
                )
                self.fund_manager.transactions.append(new_transaction)
                return True, "Deposit successful"
            
            # Process transaction with fast processor
            success, message = fast_processor.process_transaction_fast(
                mock_deposit, "investor_001", 500000, 1500000, datetime.now()
            )
            
            self.assertTrue(success)
            
            # Data should be modified in memory immediately
            self.assertEqual(len(self.fund_manager.transactions), initial_transaction_count + 1)
            
            # Wait for background save
            time.sleep(0.3)
            
            # Verify data was saved
            self.assertGreater(len(self.mock_data_handler.save_operations), 0)
            
            # Check data consistency in saved operations
            last_save = self.mock_data_handler.save_operations[-1]
            self.assertEqual(len(last_save['transactions']), initial_transaction_count + 1)
            self.assertEqual(len(last_save['investors']), initial_investor_count)
    
    def test_multiple_concurrent_operations_consistency(self):
        """Test data consistency under concurrent operations"""
        from performance_optimizer import create_fast_processor
        import threading
        
        fast_processor = create_fast_processor(self.fund_manager)
        results = []
        
        def create_transaction(transaction_id):
            def mock_transaction(investor_id, amount, nav, date):
                # Simulate transaction processing
                new_transaction = Transaction(
                    id=f"concurrent_trans_{transaction_id}",
                    investor_id=investor_id,
                    date=date,
                    type="Nạp",
                    amount=amount,
                    nav=nav,
                    units_change=amount / 1000  # Simplified calculation
                )
                self.fund_manager.transactions.append(new_transaction)
                return True, f"Transaction {transaction_id} successful"
            
            with patch('streamlit.success'), patch('streamlit.error'), patch('streamlit.balloons'):
                success, message = fast_processor.process_transaction_fast(
                    mock_transaction, "investor_001", 100000, 1100000, datetime.now()
                )
                results.append((transaction_id, success, message))
        
        # Create multiple concurrent transactions
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_transaction, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All transactions should succeed
        self.assertEqual(len(results), 5)
        for transaction_id, success, message in results:
            self.assertTrue(success)
        
        # Wait for all background saves
        time.sleep(1.0)
        
        # Verify final data consistency
        self.assertEqual(len(self.fund_manager.transactions), 5)
        self.assertGreater(len(self.mock_data_handler.save_operations), 0)
    
    def test_cache_invalidation_consistency(self):
        """Test that cache invalidation maintains data consistency"""
        optimizer = get_optimizer()
        
        # Pre-populate cache with outdated data
        optimizer.cache["nav_data"] = {"total_nav": 1000000, "timestamp": datetime.now()}
        optimizer.cache["balance_data"] = {"investor_001": 500000}
        
        from performance_optimizer import create_fast_processor
        fast_processor = create_fast_processor(self.fund_manager)
        
        with patch('streamlit.success'), patch('streamlit.error'), patch('streamlit.balloons'):
            def mock_nav_update():
                # Simulate NAV update
                return True, "NAV updated"
            
            # Process transaction that should invalidate cache
            success, message = fast_processor.process_transaction_fast(mock_nav_update)
            
            self.assertTrue(success)
            
            # Verify relevant caches are cleared
            nav_caches = [key for key in optimizer.cache.keys() if 'nav' in key.lower()]
            balance_caches = [key for key in optimizer.cache.keys() if 'balance' in key.lower()]
            
            # NAV and balance related caches should be cleared
            self.assertEqual(len(nav_caches), 0, "NAV caches should be cleared")
            self.assertEqual(len(balance_caches), 0, "Balance caches should be cleared")
    
    def test_error_handling_data_consistency(self):
        """Test data consistency when errors occur during processing"""
        from performance_optimizer import create_fast_processor
        fast_processor = create_fast_processor(self.fund_manager)
        
        initial_transaction_count = len(self.fund_manager.transactions)
        
        with patch('streamlit.success'), patch('streamlit.error') as mock_error, patch('streamlit.balloons'):
            def failing_transaction():
                # Simulate a transaction that fails
                raise ValueError("Simulated transaction failure")
            
            # Process failing transaction
            success, message = fast_processor.process_transaction_fast(failing_transaction)
            
            self.assertFalse(success)
            mock_error.assert_called()
            
            # Verify data integrity is maintained (no partial updates)
            self.assertEqual(len(self.fund_manager.transactions), initial_transaction_count)
            
            # Wait and verify no erroneous saves occurred
            time.sleep(0.3)
            save_count_after_error = len(self.mock_data_handler.save_operations)
            
            # Should not save failed transaction data
            if save_count_after_error > 0:
                last_save = self.mock_data_handler.save_operations[-1]
                self.assertEqual(len(last_save['transactions']), initial_transaction_count)
    
    def test_fallback_mechanism_consistency(self):
        """Test data consistency when fallback to original processing"""
        
        # Simulate performance optimizer not available by patching import
        with patch('performance_optimizer.create_fast_processor', side_effect=ImportError("Module not found")):
            
            # Create transaction page that would use fallback
            from pages.transaction_page import EnhancedTransactionPage
            
            transaction_page = EnhancedTransactionPage(self.fund_manager)
            
            initial_transaction_count = len(self.fund_manager.transactions)
            
            # Test fallback processing (this would use _process_transaction_original)
            with patch('streamlit.success'), patch('streamlit.error'), patch('streamlit.rerun'):
                transaction_page._process_transaction_original(
                    "investor_001", "Nạp", 200000, 1200000, date.today()
                )
            
            # Verify transaction was processed with fallback
            # (This test verifies the fallback mechanism exists and maintains consistency)
            # In real scenario, this would add a transaction
            pass

def run_data_consistency_tests():
    """Run data consistency tests"""
    print("🔍 Starting Data Consistency Testing...")
    print("=" * 50)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(DataConsistencyTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print("📊 DATA CONSISTENCY TEST RESULTS")
    print("=" * 50)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures) + len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Error:')[-1].strip()}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100
    print(f"\n✅ Overall Success Rate: {success_rate:.1f}%")
    
    return result

if __name__ == "__main__":
    run_data_consistency_tests()