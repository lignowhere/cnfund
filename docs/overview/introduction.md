# Giới Thiệu Hệ Thống Quản Lý Quỹ Đầu Tư

## Tổng Quan

Hệ Thống Quản Lý Quỹ Đầu Tư là một ứng dụng web được phát triển bằng Streamlit, được thiết kế để tự động hóa và đơn giản hóa toàn bộ quy trình quản lý một quỹ đầu tư. Hệ thống cung cấp các chức năng từ việc theo dõi nhà đầu tư, ghi nhận giao dịch, cho đến việc tính toán phí hiệu suất một cách chính xác và minh bạch.

## Tính Năng Chính

### 1. 👥 Quản Lý Nhà Đầu Tư (NĐT)
- **Thêm nhà đầu tư mới**: Tạo hồ sơ chi tiết cho từng nhà đầu tư
- **Cập nhật thông tin**: Chỉnh sửa thông tin liên hệ, địa chỉ
- **Theo dõi trạng thái**: Xem tình trạng đầu tư và số dư hiện tại
- **Phân quyền**: Hỗ trợ Fund Manager với quyền đặc biệt

### 2. 💸 Quản Lý Giao Dịch & NAV
- **Giao dịch nạp/rút**: Xử lý giao dịch của nhà đầu tư
- **Cập nhật NAV**: Theo dõi giá trị tài sản ròng của quỹ
- **Fund Manager Withdrawal**: Chức năng rút tiền chuyên biệt cho người quản lý
- **Lịch sử giao dịch**: Theo dõi và quản lý toàn bộ giao dịch

### 3. 🧮 Tính Toán & Quản Lý Phí
- **Tính phí hiệu suất**: Tự động tính phí dựa trên High Water Mark
- **Preview trước khi áp dụng**: Xem trước chi tiết trước khi chốt phí
- **Tính phí cá nhân**: Công cụ tính phí cho từng nhà đầu tư
- **Lịch sử phí**: Theo dõi toàn bộ lịch sử phí đã thu

### 4. 📊 Báo Cáo & Phân Tích
- **Dashboard tổng hợp**: Thống kê tổng quan về quỹ
- **Lifetime Performance**: Phân tích hiệu suất đầu tư trọn đời
- **Báo cáo chi tiết**: Export Excel và lưu trên Google Drive
- **Biểu đồ trực quan**: Hiển thị dữ liệu dưới dạng biểu đồ

## Lợi Ích Chính

### 🎯 **Tập trung dữ liệu**
Mọi thông tin về nhà đầu tư, giao dịch, và các kỳ tính phí đều được lưu trữ an toàn ở một nơi duy nhất trong cơ sở dữ liệu Supabase PostgreSQL.

### 🤖 **Tính toán tự động**
Giảm thiểu sai sót của con người bằng cách tự động hóa các phép tính phức tạp như:
- Giá mỗi đơn vị quỹ (NAV/unit)
- Phí hiệu suất dựa trên High Water Mark
- Phân bổ units khi có giao dịch

### 🔍 **Minh bạch**
Cung cấp các báo cáo chi tiết về:
- Hiệu suất đầu tư của từng nhà đầu tư
- Lịch sử phí đã thu
- Lifetime performance với phân tích gross/net returns

### 🔒 **Bảo mật**
- Phân quyền truy cập rõ ràng
- Yêu cầu đăng nhập cho các thao tác quan trọng
- Backup dữ liệu tự động
- Audit trail cho mọi thay đổi

## Khái Niệm Cốt Lõi

### 📈 **NAV (Net Asset Value)**
Tổng giá trị tài sản ròng của quỹ tại một thời điểm nhất định. Đây là con số quan trọng nhất để xác định giá trị của quỹ.

### 🪙 **Units (Đơn vị quỹ)**
Giống như "cổ phần" của quỹ. Khi một nhà đầu tư nạp tiền, họ sẽ "mua" một số lượng đơn vị quỹ nhất định.

### 💰 **Price per Unit**
Được tính bằng công thức: `Tổng NAV / Tổng số Đơn vị quỹ đang lưu hành`

### 🏔️ **High-Water Mark (HWM)**
Mốc giá cao nhất mà một lô giao dịch đã từng đạt được. Phí hiệu suất chỉ được tính trên phần lợi nhuận vượt qua mốc HWM này.

### 📊 **Tranches**
Các "lô giao dịch" đại diện cho từng lần nạp tiền của nhà đầu tư. Mỗi tranche có:
- Entry date và Entry NAV riêng
- High Water Mark riêng
- Theo dõi phí đã trả riêng

## Công Nghệ Sử Dụng

- **Frontend**: Streamlit
- **Backend**: Python 3.8+
- **Database**: Supabase PostgreSQL
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, Altair
- **File Storage**: Google Drive API
- **Authentication**: Streamlit built-in

## Mô Hình Hoạt Động

Hệ thống hoạt động theo mô hình web application với:

1. **Frontend**: Streamlit UI cho người dùng tương tác
2. **Business Logic**: Services layer xử lý logic nghiệp vụ
3. **Data Layer**: PostgreSQL database thông qua Supabase
4. **File Storage**: Google Drive để lưu trữ reports
5. **Security**: Authentication và authorization layers

## Người Dùng Mục Tiêu

- **Fund Managers**: Người quản lý quỹ cần theo dõi và báo cáo
- **Investors**: Nhà đầu tư muốn theo dõi performance
- **Auditors**: Người kiểm toán cần xem báo cáo chi tiết
- **Compliance Teams**: Đội compliance cần đảm bảo minh bạch