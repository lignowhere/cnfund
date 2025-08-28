# maintenance_tool.py (PHIÊN BẢN SỬA LỖI NameError)
import os
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from sqlalchemy import text

# Thêm đường dẫn gốc của dự án vào sys.path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# +++++ PHẦN SỬA ĐỔI QUAN TRỌNG +++++
# Import các lớp cần thiết ở cấp độ module để tất cả các hàm đều có thể sử dụng
from supabase_data_handler import SupabaseDataHandler
from data_handler import EnhancedDataHandler

# --- CÁC HÀM TIỆN ÍCH ---

def load_secrets_and_set_env():
    """
    Tìm và đọc file .streamlit/secrets.toml để thiết lập biến môi trường DATABASE_URL.
    """
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
            else:
                print("⚠️ Tìm thấy secrets.toml nhưng không có key 'database_url'.")
        else:
            print("ℹ️ Không tìm thấy file .streamlit/secrets.toml.")
            
    except ImportError:
        print("⚠️ Thư viện 'toml' chưa được cài đặt. Vui lòng chạy 'pip install toml'.")
    except Exception as e:
        print(f"💥 Lỗi khi đọc file secrets: {e}")

def get_data_handler():
    """Xác định xem nên dùng Supabase hay CSV"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not found")
        
        handler = SupabaseDataHandler() # Bây giờ Python đã biết SupabaseDataHandler là gì
        
        if handler.connected:
            print("✅ Đã kết nối tới Supabase. Sẽ thao tác trên database.")
            return handler
        else:
            raise ConnectionError("Không thể kết nối Supabase.")
    except Exception as e:
        print(f"⚠️ {e}. Fallback về thao tác trên file CSV.")
        return EnhancedDataHandler() # Python cũng biết EnhancedDataHandler là gì

def confirm_action(prompt: str) -> bool:
    response = input(f"🚨 {prompt} Hành động này không thể hoàn tác. Nhập 'YES' để xác nhận: ")
    return response.strip().upper() == "YES"

# --- CÁC HÀM CHÍNH (Giữ nguyên) ---
def clear_data(handler):
    """Xóa toàn bộ dữ liệu hiện có bằng cách DROP TABLE."""
    if not confirm_action("BẠN CÓ CHẮC CHẮN MUỐN XÓA TOÀN BỘ CẤU TRÚC VÀ DỮ LIỆU?"):
        print("❌ Hành động đã bị hủy.")
        return

    print("\n🔥 Bắt đầu xóa triệt để cấu trúc và dữ liệu...")

    if isinstance(handler, SupabaseDataHandler):
        try:
            with handler.engine.connect() as conn:
                trans = conn.begin()
                # Sử dụng DROP TABLE để xóa hoàn toàn bảng và cấu trúc cũ
                # CASCADE sẽ xử lý các phụ thuộc
                tables_to_drop = ["fee_records", "transactions", "tranches", "investors"]
                for table in tables_to_drop:
                    print(f"   - Đang xóa bảng: {table}...")
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                trans.commit()
            print("✅ Đã xóa sạch cấu trúc và dữ liệu trên Supabase.")
            # Sau khi xóa, chúng ta cần kết nối lại để _create_tables chạy lại
            print("   - Đang kết nối lại để tạo cấu trúc bảng mới...")
            handler._connect()

        except Exception as e:
            print(f"💥 Lỗi khi xóa bảng trên Supabase: {e}")

    elif isinstance(handler, EnhancedDataHandler): # CSV handler
        from config import INVESTORS_FILE, TRANCHES_FILE, TRANSACTIONS_FILE, DATA_DIR
        files_to_delete = [INVESTORS_FILE, TRANCHES_FILE, TRANSACTIONS_FILE, DATA_DIR / "fee_records.csv"]
        for file_path in files_to_delete:
            if file_path.exists():
                os.remove(file_path)
                print(f"   - Đã xóa file: {file_path.name}")
        print("✅ Đã xóa sạch dữ liệu trên file CSV.")
    print("-" * 30)

def seed_data(handler):
    print("\n🌱 Bắt đầu tạo dữ liệu mẫu...")
    from models import Investor, Tranche, Transaction, FeeRecord
    from services_enhanced import EnhancedFundManager

    # Bước 1: Khởi tạo đối tượng FundManager
    fund_manager = EnhancedFundManager(handler)
    
    # Bước 2: Gọi các hàm khởi tạo một cách tường minh
    # fund_manager.load_data() # Không cần load vì chúng ta đang tạo mới từ đầu
    fund_manager._ensure_fund_manager_exists() # Chỉ tạo trong bộ nhớ

    # Bước 3: Tạo dữ liệu trong bộ nhớ (giữ nguyên như cũ)
    print("   - Tạo các nhà đầu tư...")
    fund_manager.add_investor("Nguyễn Văn An", "0901234567")
    fund_manager.add_investor("Trần Thị Bình", "0912345678")
    fund_manager.add_investor("Lê Minh Cường", "0987654321")
    
    investor_an = fund_manager.get_investor_by_id(1)
    investor_binh = fund_manager.get_investor_by_id(2)
    investor_cuong = fund_manager.get_investor_by_id(3)

    print("   - Thiết lập NAV ban đầu và các giao dịch...")
    total_nav = 1_000_000_000
    fund_manager.process_nav_update(total_nav, datetime(2024, 1, 1))
    
    an_deposit_1 = 200_000_000
    total_nav += an_deposit_1
    fund_manager.process_deposit(investor_an.id, an_deposit_1, total_nav, datetime(2024, 1, 15))
    
    binh_deposit_1 = 300_000_000
    total_nav += binh_deposit_1
    fund_manager.process_deposit(investor_binh.id, binh_deposit_1, total_nav, datetime(2024, 2, 1))

    total_nav *= 1.1
    fund_manager.process_nav_update(total_nav, datetime(2024, 6, 30))
    print(f"   - NAV tăng trưởng lên: {total_nav:,.0f} VND")

    cuong_deposit_1 = 150_000_000
    total_nav += cuong_deposit_1
    fund_manager.process_deposit(investor_cuong.id, cuong_deposit_1, total_nav, datetime(2024, 7, 5))

    an_withdraw_amount = 50_000_000
    total_nav *= 1.05
    fund_manager.process_nav_update(total_nav, datetime(2024, 10, 14))
    
    fee_info = fund_manager.calculate_investor_fee(investor_an.id, datetime(2024, 10, 15), total_nav)
    balance_before = fee_info['balance']
    fee_on_full = fee_info['total_fee']
    
    denom = balance_before - fee_on_full
    proportion = an_withdraw_amount / denom if denom > 0 else 1.0
    fee_on_withdrawal = fee_on_full * proportion
    gross_withdrawal = an_withdraw_amount + fee_on_withdrawal
    
    total_nav_after_withdraw = total_nav - gross_withdrawal
    fund_manager.process_withdrawal(investor_an.id, an_withdraw_amount, total_nav_after_withdraw, datetime(2024, 10, 15))
    total_nav = total_nav_after_withdraw
    print(f"   - {investor_an.name} đã rút {an_withdraw_amount:,.0f} VND")

    total_nav *= 1.08
    end_of_year_date = datetime(2024, 12, 31)
    
    fee_results = fund_manager.apply_year_end_fees_enhanced(end_of_year_date, total_nav)
    if fee_results.get('success'):
        print(f"   - Đã áp dụng phí cuối năm thành công. Tổng phí: {fee_results.get('total_fees', 0):,.0f} VND")
    else:
        print(f"   - Có lỗi khi tính phí cuối năm: {fee_results.get('errors')}")

    print("\n💾 Đang lưu dữ liệu mẫu...")
    success = fund_manager.save_data()
    
    if success:
        print("✅ Đã tạo và lưu dữ liệu mẫu thành công!")
    else:
        print("💥 Lỗi nghiêm trọng: Không thể lưu dữ liệu mẫu.")
    print("-" * 30)

def main():
    load_secrets_and_set_env()
    handler = get_data_handler()
    
    while True:
        print("\n--- 🛠️ CÔNG CỤ QUẢN LÝ DỮ LIỆU ---")
        print("1. Xóa trắng toàn bộ dữ liệu (Clear Data)")
        print("2. Tạo dữ liệu mẫu để test (Seed Data)")
        print("3. Xóa và tạo lại dữ liệu mẫu (Clear & Seed)")
        print("4. Thoát")
        choice = input("Vui lòng chọn một hành động (1-4): ")
        if choice == '1':
            clear_data(handler)
        elif choice == '2':
            seed_data(handler)
        elif choice == '3':
            clear_data(handler)
            seed_data(handler)
        elif choice == '4':
            print("👋 Tạm biệt!")
            break
        else:
            print("⚠️ Lựa chọn không hợp lệ, vui lòng thử lại.")

if __name__ == "__main__":
    main()