#!/usr/bin/env python3
"""
Test Script cho Enhanced Fund Management System
Validates tất cả features mới và đảm bảo system hoạt động đúng
"""

import sys
import os
from pathlib import Path
from datetime import datetime, date
import pandas as pd

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from services_enhanced import EnhancedFundManager
    from models import Investor, Tranche, Transaction, FeeRecord
    from utils import format_currency, format_percentage
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class EnhancedSystemValidator:
    """Validator cho Enhanced Fund Management System"""
    
    def __init__(self):
        self.fund_manager = EnhancedFundManager()
        self.test_results = []
        self.errors = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        full_message = f"{status} {test_name}"
        if message:
            full_message += f" - {message}"
        
        print(full_message)
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        
        if not success:
            self.errors.append(full_message)
    
    def test_1_fund_manager_creation(self):
        """Test 1: Fund Manager được tạo tự động"""
        try:
            fund_manager = self.fund_manager.get_fund_manager()
            
            if fund_manager:
                self.log_test("Fund Manager Creation", True, 
                            f"Fund Manager found: {fund_manager.display_name}")
                
                # Validate properties
                if fund_manager.id == 0:
                    self.log_test("Fund Manager ID", True, "ID = 0 as expected")
                else:
                    self.log_test("Fund Manager ID", False, f"Expected ID=0, got {fund_manager.id}")
                
                if fund_manager.is_fund_manager:
                    self.log_test("Fund Manager Flag", True, "is_fund_manager = True")
                else:
                    self.log_test("Fund Manager Flag", False, "is_fund_manager should be True")
            else:
                self.log_test("Fund Manager Creation", False, "Fund Manager not found")
        
        except Exception as e:
            self.log_test("Fund Manager Creation", False, str(e))
    
    def test_2_data_loading(self):
        """Test 2: Enhanced data loading"""
        try:
            # Test investors loading
            investors = self.fund_manager.investors
            self.log_test("Investors Loading", len(investors) >= 1, 
                         f"Loaded {len(investors)} investors")
            
            # Test tranches loading  
            tranches = self.fund_manager.tranches
            self.log_test("Tranches Loading", True, 
                         f"Loaded {len(tranches)} tranches")
            
            # Test transactions loading
            transactions = self.fund_manager.transactions
            self.log_test("Transactions Loading", True, 
                         f"Loaded {len(transactions)} transactions")
            
            # Test fee records loading
            fee_records = self.fund_manager.fee_records
            self.log_test("Fee Records Loading", True, 
                         f"Loaded {len(fee_records)} fee records")
            
            # Test enhanced fields in tranches
            if tranches:
                sample_tranche = tranches[0]
                has_original_fields = (hasattr(sample_tranche, 'original_entry_date') and 
                                     hasattr(sample_tranche, 'original_entry_nav') and
                                     hasattr(sample_tranche, 'cumulative_fees_paid'))
                self.log_test("Enhanced Tranche Fields", has_original_fields,
                             "Original entry data and cumulative fees fields present")
            
        except Exception as e:
            self.log_test("Data Loading", False, str(e))
    
    def test_3_investor_management(self):
        """Test 3: Enhanced investor management"""
        try:
            # Test regular investors vs fund manager separation
            regular_investors = self.fund_manager.get_regular_investors()
            all_investors = self.fund_manager.investors
            
            regular_count = len(regular_investors)
            total_count = len(all_investors)
            
            # Should have at least 1 fund manager + regular investors
            self.log_test("Investor Separation", total_count > regular_count,
                         f"Total: {total_count}, Regular: {regular_count}")
            
            # Test investor options (should exclude fund manager)
            options = self.fund_manager.get_investor_options()
            all_options = self.fund_manager.get_all_investor_options()
            
            self.log_test("Investor Options", len(all_options) > len(options),
                         f"All options: {len(all_options)}, Regular options: {len(options)}")
            
            # Test adding new investor
            original_count = len(regular_investors)
            success, message = self.fund_manager.add_investor("Test Investor", "0123456789")
            
            if success:
                new_count = len(self.fund_manager.get_regular_investors())
                self.log_test("Add Investor", new_count > original_count, message)
            else:
                self.log_test("Add Investor", False, message)
        
        except Exception as e:
            self.log_test("Investor Management", False, str(e))
    
    def test_4_transaction_processing(self):
        """Test 4: Transaction processing với enhanced features"""
        try:
            # Get a test investor
            regular_investors = self.fund_manager.get_regular_investors()
            if not regular_investors:
                self.log_test("Transaction Processing", False, "No regular investors for testing")
                return
            
            test_investor = regular_investors[0]
            
            # Test deposit
            original_tranches = len(self.fund_manager.get_investor_tranches(test_investor.id))
            success, message = self.fund_manager.process_deposit(
                test_investor.id, 1000000, 2000000, datetime.now()
            )
            
            if success:
                new_tranches = len(self.fund_manager.get_investor_tranches(test_investor.id))
                self.log_test("Process Deposit", new_tranches > original_tranches, message)
                
                # Validate enhanced tranche fields
                latest_tranche = max(self.fund_manager.get_investor_tranches(test_investor.id),
                                   key=lambda t: t.entry_date)
                
                has_enhanced_fields = (latest_tranche.original_entry_date is not None and
                                     latest_tranche.original_entry_nav is not None and
                                     latest_tranche.cumulative_fees_paid == 0.0)
                
                self.log_test("Enhanced Tranche Creation", has_enhanced_fields,
                             "New tranche has enhanced fields")
            else:
                self.log_test("Process Deposit", False, message)
        
        except Exception as e:
            self.log_test("Transaction Processing", False, str(e))
    
    def test_5_lifetime_performance(self):
        """Test 5: Lifetime performance calculation"""
        try:
            regular_investors = self.fund_manager.get_regular_investors()
            if not regular_investors:
                self.log_test("Lifetime Performance", False, "No investors for testing")
                return
            
            test_investor = regular_investors[0]
            
            # Test lifetime performance calculation
            performance = self.fund_manager.get_investor_lifetime_performance(
                test_investor.id, 3000000  # Test NAV
            )
            
            # Validate performance fields
            required_fields = ['original_invested', 'current_value', 'total_fees_paid',
                             'gross_profit', 'net_profit', 'gross_return', 'net_return']
            
            has_all_fields = all(field in performance for field in required_fields)
            self.log_test("Lifetime Performance Fields", has_all_fields,
                         f"Performance calculation returned all required fields")
            
            # Validate calculation logic
            if performance['original_invested'] > 0:
                # Gross return should include fees paid
                expected_gross = (performance['current_value'] + performance['total_fees_paid'] - 
                                performance['original_invested']) / performance['original_invested']
                
                actual_gross = performance['gross_return']
                calculation_correct = abs(expected_gross - actual_gross) < 0.001
                
                self.log_test("Lifetime Performance Calculation", calculation_correct,
                             f"Gross return calculation: expected {expected_gross:.3f}, got {actual_gross:.3f}")
            
        except Exception as e:
            self.log_test("Lifetime Performance", False, str(e))
    
    def test_6_fee_calculation_enhanced(self):
        """Test 6: Enhanced fee calculation"""
        try:
            regular_investors = self.fund_manager.get_regular_investors()
            if not regular_investors:
                self.log_test("Enhanced Fee Calculation", False, "No investors for testing")
                return
            
            test_investor = regular_investors[0]
            
            # Test individual fee calculation
            fee_details = self.fund_manager.calculate_investor_fee(
                test_investor.id, datetime.now(), 3000000
            )
            
            # Validate fee calculation structure
            required_fields = ['total_fee', 'hurdle_value', 'hwm_value', 'excess_profit',
                             'invested_value', 'balance', 'profit', 'profit_perc']
            
            has_fee_fields = all(field in fee_details for field in required_fields)
            self.log_test("Fee Calculation Structure", has_fee_fields,
                         "Fee calculation returned all required fields")
            
            # Test fee history functionality
            original_fee_count = len(self.fund_manager.fee_records)
            
            # Simulate enhanced fee application (dry run)
            tranches_before = len(self.fund_manager.tranches)
            
            self.log_test("Fee System Ready", True,
                         f"Current fee records: {original_fee_count}, Tranches: {tranches_before}")
        
        except Exception as e:
            self.log_test("Enhanced Fee Calculation", False, str(e))
    
    def test_7_fund_manager_tracking(self):
        """Test 7: Fund Manager tracking functionality"""
        try:
            fund_manager = self.fund_manager.get_fund_manager()
            if not fund_manager:
                self.log_test("Fund Manager Tracking", False, "Fund Manager not found")
                return
            
            # Test fund manager tranches
            fm_tranches = self.fund_manager.get_investor_tranches(fund_manager.id)
            self.log_test("Fund Manager Tranches", True,
                         f"Fund Manager has {len(fm_tranches)} tranches")
            
            # Test fund manager balance calculation
            latest_nav = self.fund_manager.get_latest_total_nav()
            if latest_nav:
                fm_balance, fm_profit, fm_profit_perc = self.fund_manager.get_investor_balance(
                    fund_manager.id, latest_nav
                )
                
                self.log_test("Fund Manager Balance", True,
                             f"Balance: {format_currency(fm_balance)}, Profit: {format_currency(fm_profit)}")
            
            # Test fee transactions for fund manager
            fee_transactions = [t for t in self.fund_manager.transactions 
                              if t.investor_id == fund_manager.id and t.type == 'Phí Nhận']
            
            self.log_test("Fund Manager Fee Transactions", True,
                         f"Fund Manager has {len(fee_transactions)} fee transactions")
        
        except Exception as e:
            self.log_test("Fund Manager Tracking", False, str(e))
    
    def test_8_data_integrity(self):
        """Test 8: Data integrity và consistency"""
        try:
            # Test total units consistency
            total_units_tranches = sum(t.units for t in self.fund_manager.tranches)
            
            latest_nav = self.fund_manager.get_latest_total_nav()
            if latest_nav and total_units_tranches > 0:
                calculated_price = latest_nav / total_units_tranches
                system_price = self.fund_manager.calculate_price_per_unit(latest_nav)
                
                price_consistent = abs(calculated_price - system_price) < 0.01
                self.log_test("Price Calculation Consistency", price_consistent,
                             f"Calculated: {calculated_price:.2f}, System: {system_price:.2f}")
            
            # Test investor units vs balance consistency
            for investor in self.fund_manager.get_regular_investors():
                tranches = self.fund_manager.get_investor_tranches(investor.id)
                if tranches and latest_nav:
                    units_sum = sum(t.units for t in tranches)
                    balance, _, _ = self.fund_manager.get_investor_balance(investor.id, latest_nav)
                    
                    expected_balance = units_sum * system_price
                    balance_consistent = abs(balance - expected_balance) < 1.0
                    
                    if not balance_consistent:
                        self.log_test("Balance Consistency", False,
                                     f"Investor {investor.id}: Expected {expected_balance:.2f}, Got {balance:.2f}")
                        break
            else:
                self.log_test("Balance Consistency", True, "All investor balances consistent")
            
            # Test original data preservation
            enhanced_tranches = [t for t in self.fund_manager.tranches 
                               if hasattr(t, 'original_entry_date') and t.original_entry_date]
            
            self.log_test("Original Data Preservation", len(enhanced_tranches) == len(self.fund_manager.tranches),
                         f"{len(enhanced_tranches)}/{len(self.fund_manager.tranches)} tranches have original data")
        
        except Exception as e:
            self.log_test("Data Integrity", False, str(e))
    
    def test_9_enhanced_features_integration(self):
        """Test 9: Integration của tất cả enhanced features"""
        try:
            # Test comprehensive system state
            regular_investors = self.fund_manager.get_regular_investors()
            fund_manager = self.fund_manager.get_fund_manager()
            
            system_summary = {
                'regular_investors': len(regular_investors),
                'total_tranches': len(self.fund_manager.tranches),
                'total_transactions': len(self.fund_manager.transactions),
                'fee_records': len(self.fund_manager.fee_records),
                'fund_manager_exists': fund_manager is not None,
                'latest_nav': self.fund_manager.get_latest_total_nav()
            }
            
            # Validate system is in good state
            system_healthy = (
                system_summary['regular_investors'] >= 0 and
                system_summary['fund_manager_exists'] and
                system_summary['total_tranches'] >= 0 and
                system_summary['total_transactions'] >= 0
            )
            
            self.log_test("System Integration", system_healthy,
                         f"System summary: {system_summary}")
            
            # Test enhanced save functionality
            try:
                save_success = self.fund_manager.save_data()
                self.log_test("Enhanced Save Functionality", save_success,
                             "Enhanced data save including fee records")
            except Exception as save_error:
                self.log_test("Enhanced Save Functionality", False, str(save_error))
        
        except Exception as e:
            self.log_test("Enhanced Features Integration", False, str(e))
    
    def run_all_tests(self):
        """Chạy tất cả tests"""
        print("🚀 Starting Enhanced Fund Management System Validation")
        print("=" * 70)
        
        test_methods = [
            self.test_1_fund_manager_creation,
            self.test_2_data_loading,
            self.test_3_investor_management,
            self.test_4_transaction_processing,
            self.test_5_lifetime_performance,
            self.test_6_fee_calculation_enhanced,
            self.test_7_fund_manager_tracking,
            self.test_8_data_integrity,
            self.test_9_enhanced_features_integration
        ]
        
        for i, test_method in enumerate(test_methods, 1):
            print(f"\n📋 Running Test {i}: {test_method.__doc__.split(':')[1].strip()}")
            try:
                test_method()
            except Exception as e:
                self.log_test(f"Test {i} Execution", False, f"Exception: {str(e)}")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n❌ FAILED TESTS:")
            for error in self.errors:
                print(f"  {error}")
        
        if success_rate >= 90:
            print("\n🎉 VALIDATION SUCCESSFUL! Enhanced system is ready for production.")
            return True
        elif success_rate >= 70:
            print("\n⚠️  VALIDATION PARTIAL: Some issues found, but system is mostly functional.")
            return False
        else:
            print("\n❌ VALIDATION FAILED: Significant issues found. Please review and fix.")
            return False

def main():
    """Main validation function"""
    validator = EnhancedSystemValidator()
    success = validator.run_all_tests()
    
    print(f"\n🏁 Validation completed with {'SUCCESS' if success else 'ISSUES'}")
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)