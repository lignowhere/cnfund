#!/usr/bin/env python3
"""
Quick Test Script cho Enhanced Fund Management System
Kiểm tra nhanh các tính năng enhanced đã hoạt động chưa
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

def test_imports():
    """Test basic imports"""
    print("🔍 Testing imports...")
    try:
        from services_enhanced import EnhancedFundManager
        from models import Investor, Tranche, Transaction, FeeRecord
        from data_handler import EnhancedDataHandler
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_enhanced_fund_manager():
    """Test enhanced fund manager creation"""
    print("🔍 Testing Enhanced Fund Manager...")
    try:
        from services_enhanced import EnhancedFundManager
        fm = EnhancedFundManager()
        
        # Test fund manager creation
        fund_manager = fm.get_fund_manager()
        if fund_manager:
            print(f"✅ Fund Manager found: {fund_manager.display_name}")
        else:
            print("❌ Fund Manager not found")
            return False
        
        # Test regular investors
        regular_investors = fm.get_regular_investors()
        print(f"✅ Regular investors: {len(regular_investors)}")
        
        # Test data loading
        print(f"✅ Loaded: {len(fm.investors)} investors, {len(fm.tranches)} tranches, {len(fm.transactions)} transactions, {len(fm.fee_records)} fee records")
        
        return True
    except Exception as e:
        print(f"❌ Enhanced Fund Manager error: {e}")
        return False

def test_enhanced_features():
    """Test enhanced features"""
    print("🔍 Testing Enhanced Features...")
    try:
        from services_enhanced import EnhancedFundManager
        fm = EnhancedFundManager()
        
        # Test lifetime performance
        regular_investors = fm.get_regular_investors()
        if regular_investors:
            test_investor = regular_investors[0]
            performance = fm.get_investor_lifetime_performance(test_investor.id, 1000000)
            
            required_fields = ['original_invested', 'current_value', 'total_fees_paid', 'gross_return', 'net_return']
            has_all_fields = all(field in performance for field in required_fields)
            
            if has_all_fields:
                print("✅ Lifetime performance calculation working")
            else:
                print("❌ Lifetime performance missing fields")
                return False
        
        # Test fee history
        fee_records = fm.get_fee_history()
        print(f"✅ Fee history: {len(fee_records)} records")
        
        # Test enhanced tranche fields
        if fm.tranches:
            sample_tranche = fm.tranches[0]
            has_enhanced = (hasattr(sample_tranche, 'original_entry_date') and 
                           hasattr(sample_tranche, 'original_entry_nav') and
                           hasattr(sample_tranche, 'cumulative_fees_paid'))
            
            if has_enhanced:
                print("✅ Enhanced tranche fields present")
            else:
                print("❌ Enhanced tranche fields missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Enhanced features error: {e}")
        return False

def test_data_files():
    """Test data files exist and readable"""
    print("🔍 Testing data files...")
    try:
        from pathlib import Path
        import pandas as pd
        
        data_dir = Path("data")
        required_files = ["investors.csv", "tranches.csv", "transactions.csv", "fee_records.csv"]
        
        for file_name in required_files:
            file_path = data_dir / file_name
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    print(f"✅ {file_name}: {len(df)} records")
                except Exception as e:
                    print(f"❌ {file_name}: Error reading - {e}")
                    return False
            else:
                if file_name == "fee_records.csv":
                    print(f"⚠️  {file_name}: Not found (will be created)")
                else:
                    print(f"❌ {file_name}: Not found")
                    return False
        
        return True
    except Exception as e:
        print(f"❌ Data files error: {e}")
        return False

def test_streamlit_compatibility():
    """Test streamlit compatibility"""
    print("🔍 Testing Streamlit compatibility...")
    try:
        import streamlit as st
        print("✅ Streamlit import successful")
        
        # Test if enhanced pages can be imported
        try:
            from fee_page_enhanced import EnhancedFeePage
            print("✅ Enhanced Fee Page import successful")
        except ImportError:
            print("⚠️  Enhanced Fee Page not found (using fallback)")
        
        try:
            from report_page_enhanced import EnhancedReportPage
            print("✅ Enhanced Report Page import successful")
        except ImportError:
            print("⚠️  Enhanced Report Page not found (using fallback)")
        
        return True
    except ImportError as e:
        print(f"❌ Streamlit compatibility error: {e}")
        return False

def run_quick_test():
    """Run all quick tests"""
    print("🚀 Enhanced Fund Management System - Quick Test")
    print("=" * 60)
    
    tests = [
        ("Basic Imports", test_imports),
        ("Enhanced Fund Manager", test_enhanced_fund_manager),
        ("Enhanced Features", test_enhanced_features),
        ("Data Files", test_data_files),
        ("Streamlit Compatibility", test_streamlit_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("\n🎉 ALL TESTS PASSED! Enhanced system is ready.")
        print("\nNext steps:")
        print("1. 🚀 Run app: streamlit run app.py")
        print("2. 🧪 Full validation: python test_enhanced_system.py")
        print("3. 📊 Generate demo data: python generate_demo_data.py")
        return True
    elif success_rate >= 80:
        print("\n⚠️  MOSTLY WORKING with minor issues.")
        print("System should be functional with some features missing.")
        return True
    else:
        print("\n❌ SIGNIFICANT ISSUES FOUND")
        print("Please fix the failed tests before proceeding.")
        return False

if __name__ == "__main__":
    success = run_quick_test()
    sys.exit(0 if success else 1)