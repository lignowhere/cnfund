# test_suite.py (PHIÊN BẢN RÚT GỌN - CHỈ 3 TEST MỚI)
import os
import sys
from pathlib import Path
from datetime import datetime

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# --- CÁC HÀM TIỆN ÍCH CHO VIỆC TEST ---

def load_secrets_and_set_env():
    """Tìm và đọc file .streamlit/secrets.toml để thiết lập biến môi trường DATABASE_URL."""
    print("🔍 Đang tìm kiếm file secrets của Streamlit...")
    try:
        import toml
        secrets_path = project_root / ".streamlit" / "secrets.toml"
        if secrets_path.exists():
            secrets = toml.load(secrets_path)
            db_url = secrets.get("database_url")
            if db_url:
                os.environ['DATABASE_URL'] = db_url
                print("🔑 Đã tìm thấy và thiết lập DATABASE_URL từ secrets.toml.")
                return True
        else:
            print("ℹ️ Không tìm thấy file .streamlit/secrets.toml.")
    except Exception as e:
        print(f"💥 Lỗi khi đọc file secrets: {e}")
    return False

from services_enhanced import EnhancedFundManager
from maintenance_tool import get_data_handler, clear_data
from config import EPSILON
from decimal import Decimal, getcontext
getcontext().prec = 28

# Màu sắc cho output trên terminal
class bcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'

def assert_almost_equals(label, actual, expected, tolerance=1e-6):
    """So sánh hai số thực với một sai số cho phép."""
    if abs(Decimal(str(actual)) - Decimal(str(expected))) < Decimal(str(tolerance)):
        print(f"  {bcolors.OKGREEN}[PASS]{bcolors.ENDC} {label}: Expected ~{expected:.4f}, Got ~{actual:.4f}")
        return True
    else:
        print(f"  {bcolors.FAIL}[FAIL]{bcolors.ENDC} {label}: Expected ~{expected:.4f}, Got ~{actual:.4f}")
        return False

def assert_true(label, condition):
    """Kiểm tra một điều kiện là True."""
    if condition:
        print(f"  {bcolors.OKGREEN}[PASS]{bcolors.ENDC} {label}")
        return True
    else:
        print(f"  {bcolors.FAIL}[FAIL]{bcolors.ENDC} {label}")
        return False

# --- CÁC KỊCH BẢN TEST MỚI ---

def test_scenario_8_undo_nav_update(fm: EnhancedFundManager):
    """Kịch bản 8: Hoàn tác một giao dịch cập nhật NAV."""
    print(f"\n{bcolors.WARNING}--- SCENARIO 8: Undo NAV Update ---{bcolors.ENDC}")
    test_passed = True

    # 1. Arrange
    fm.add_investor("Mallory")
    mallory = fm.get_investor_by_id(1)
    fm.process_deposit(mallory.id, 100_000_000, 100_000_000, datetime(2024, 1, 1))
    
    fm.process_nav_update(110_000_000, datetime(2024, 2, 1)) # NAV_1
    nav_before_final_update = fm.get_latest_total_nav()

    fm.process_nav_update(120_000_000, datetime(2024, 3, 1)) # NAV_2 (sẽ bị undo)
    last_transaction_id = max(t.id for t in fm.transactions)

    # 2. Act
    undo_success = fm.undo_last_transaction(last_transaction_id)

    # 3. Assert
    final_nav = fm.get_latest_total_nav()
    test_passed &= assert_true("Undo operation reported success", undo_success)
    test_passed &= assert_almost_equals("Latest NAV reverted to previous value", final_nav, nav_before_final_update)

    return {"name": "Undo NAV Update", "passed": test_passed}


def test_scenario_9_fee_fails_if_no_fund_manager(fm: EnhancedFundManager):
    """Kịch bản 9: Áp dụng phí thất bại nếu không có Fund Manager."""
    print(f"\n{bcolors.WARNING}--- SCENARIO 9: Fee Application Fails Gracefully if No FM ---{bcolors.ENDC}")
    
    # 1. Arrange
    # CỐ TÌNH KHÔNG GỌI _ensure_fund_manager_exists()
    fm.add_investor("Nemo")
    nemo = fm.get_investor_by_id(1)
    fm.process_deposit(nemo.id, 100_000_000, 100_000_000, datetime(2024, 1, 1))
    fm.process_nav_update(120_000_000, datetime(2024, 12, 30))

    # 2. Act
    results = fm.apply_year_end_fees_enhanced(datetime(2024, 12, 31), 120_000_000)

    # 3. Assert
    # Mong đợi: hàm thất bại VÀ có thông báo lỗi đúng
    passed = (not results["success"]) and ("Fund Manager not found" in results["errors"])
    
    return {"name": "Fee Fails Gracefully if No FM", "passed": passed}


def test_scenario_10_full_withdrawal_with_no_profit(fm: EnhancedFundManager):
    """Kịch bản 10: Rút toàn bộ vốn khi không có lãi."""
    print(f"\n{bcolors.WARNING}--- SCENARIO 10: Full Withdrawal with No Profit ---{bcolors.ENDC}")
    test_passed = True
    
    # 1. Arrange
    fm._ensure_fund_manager_exists()
    fm.add_investor("Oscar")
    oscar = fm.get_investor_by_id(1)
    fm.process_deposit(oscar.id, 100_000_000, 100_000_000, datetime(2024, 1, 1))
    fm.process_nav_update(90_000_000, datetime(2024, 6, 1)) # Lỗ 10%
    
    # 2. Act
    # Yêu cầu rút 100M (lớn hơn số dư 90M) để kích hoạt rút toàn bộ
    success, message = fm.process_withdrawal(oscar.id, 100_000_000, 0, datetime(2024, 6, 2))

    # 3. Assert
    fm_units = fm.get_investor_units(0)
    test_passed &= assert_true("Withdrawal operation should succeed", success)
    test_passed &= assert_almost_equals("Oscar's final units is zero", fm.get_investor_units(oscar.id), 0)
    test_passed &= assert_true("Oscar has no remaining tranches", not fm.get_investor_tranches(oscar.id))
    test_passed &= assert_almost_equals("Fund Manager units unchanged", fm_units, 0)
    
    # Kiểm tra số tiền thực nhận có đúng là 90M không
    test_passed &= assert_true("Message contains correct net amount (90,000,000)", "90,000,000" in message)

    return {"name": "Full Withdrawal with No Profit", "passed": test_passed}


def print_summary(results):
    """In báo cáo tóm tắt kết quả test."""
    print("\n" + "="*50)
    print(" " * 14 + "TEST SUITE SUMMARY")
    print("="*50)
    passed_count = sum(1 for r in results if r["passed"])
    for result in results:
        status_text = f"{bcolors.OKGREEN}PASSED{bcolors.ENDC}" if result["passed"] else f"{bcolors.FAIL}FAILED{bcolors.ENDC}"
        print(f"Test: {result['name']:<40} | Status: {status_text}")
    print("-"*50)
    final_color = bcolors.OKGREEN if passed_count == len(results) else bcolors.FAIL
    print(f"{final_color}SUMMARY: {passed_count}/{len(results)} tests passed.{bcolors.ENDC}")
    print("="*50)

# --- HÀM CHẠY CHÍNH ---

def main():
    """Hàm chính để điều phối và chạy các bài test."""
    print("--- RUNNING FOCUSED VALIDATION SUITE ---")
    load_secrets_and_set_env()
    
    handler = get_data_handler()
    if not handler:
        print(f"{bcolors.FAIL}Could not initialize data handler. Aborting tests.{bcolors.ENDC}")
        return
    
    test_results = []
    
    # Danh sách các kịch bản test mới
    scenarios = [
        test_scenario_8_undo_nav_update,
        test_scenario_9_fee_fails_if_no_fund_manager,
        test_scenario_10_full_withdrawal_with_no_profit
    ]

    for i, scenario_func in enumerate(scenarios):
        print(f"\n[TEST {i+1}] Preparing environment for '{scenario_func.__name__}'...")
        clear_data(handler)
        
        fm_instance = EnhancedFundManager(handler)
        
        test_results.append(scenario_func(fm_instance))
        
    print_summary(test_results)
    
if __name__ == "__main__":
    main()