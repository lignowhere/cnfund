# Hướng Dẫn Quản Lý Nhà Đầu Tư

## Tổng Quan

Quản lý nhà đầu tư là chức năng cốt lõi của hệ thống, cho phép bạn:
- ➕ Thêm nhà đầu tư mới
- ✏️ Chỉnh sửa thông tin nhà đầu tư
- 👁️ Theo dõi tình trạng đầu tư
- 📊 Xem thống kê chi tiết

---

## 1. Thêm Nhà Đầu Tư Mới

### Truy cập trang

Từ menu bên trái, chọn **"👥 Thêm Nhà Đầu Tư"**

### Điền thông tin

![Add Investor Form](../assets/add-investor-form.png)

#### Thông tin bắt buộc:
- **Tên nhà đầu tư** ✅: Không được để trống, không được trùng lặp

#### Thông tin tùy chọn:
- **Số điện thoại**: Format hợp lệ (`+84` hoặc `0` + 9-10 số)
- **Địa chỉ**: Địa chỉ liên hệ
- **Email**: Email hợp lệ

### Xác nhận thêm

1. Kiểm tra lại thông tin
2. Nhấn nút **"➕ Thêm Nhà Đầu Tư"**
3. Hệ thống sẽ hiển thị thông báo thành công/lỗi

### Ví dụ thêm nhà đầu tư

```
✅ Thành công:
Tên: "Nguyễn Văn A"
SĐT: "0901234567"
Email: "nva@email.com"
➡️ Kết quả: "Đã thêm Nguyễn Văn A (ID: 15)"

❌ Lỗi phổ biến:
- "Tên không được để trống"
- "Nhà đầu tư 'Nguyễn Văn A' đã tồn tại"
- "SĐT không hợp lệ"
- "Email không hợp lệ"
```

---

## 2. Sửa Thông Tin Nhà Đầu Tư

### Truy cập trang

Từ menu bên trái, chọn **"✏️ Sửa Thông Tin NĐT"**

### Phần 1: Chỉnh sửa thông tin

#### Bảng tính tương tác
- Hệ thống hiển thị bảng tính chứa tất cả nhà đầu tư
- Bạn có thể **edit trực tiếp** trên các ô trong bảng
- Các trường có thể chỉnh sửa: Tên, SĐT, Địa chỉ, Email, Ngày tham gia

![Edit Investor Table](../assets/edit-investor-table.png)

#### Cách chỉnh sửa:
1. **Click đúp** vào ô cần sửa
2. **Nhập** giá trị mới
3. **Enter** để xác nhận thay đổi
4. Ô sẽ được highlight khi có thay đổi

#### Lưu thay đổi:
1. Sau khi chỉnh sửa xong tất cả
2. Nhấn nút **"💾 Lưu Thay Đổi"**
3. Hệ thống sẽ validate và lưu về database

### Validation khi sửa

- **Tên**: Không được trống, không trùng lặp
- **SĐT**: Phải đúng format nếu có nhập
- **Email**: Phải hợp lệ nếu có nhập
- **Ngày tham gia**: Phải là ngày hợp lệ

### Xử lý lỗi

```
✅ Thành công: "Đã cập nhật thông tin 3 nhà đầu tư"

❌ Lỗi validation:
- "Tên 'Nguyễn Văn B' đã tồn tại ở investor ID 5"  
- "SĐT '123456' không hợp lệ cho investor ID 3"
- "Email 'invalid-email' không hợp lệ cho investor ID 7"
```

---

## 3. Xem Tình Trạng Nhà Đầu Tư

### Phần 2: Tình trạng chi tiết

Sau phần chỉnh sửa, bạn sẽ thấy phần **"Xem Tình Trạng Nhà Đầu Tư"**

#### Bước 1: Chọn nhà đầu tư
- Dropdown list chứa tất cả nhà đầu tư
- Format: "Tên (ID: X)"

#### Bước 2: Nhập Total NAV hiện tại
- Nhập giá trị Total NAV để tính toán
- Đây là tổng giá trị tài sản ròng của quỹ hiện tại

#### Bước 3: Xem kết quả

Hệ thống sẽ hiển thị:

![Investor Status](../assets/investor-status.png)

##### Thông tin cơ bản:
- **Tên và ID**: Định danh nhà đầu tư
- **Ngày tham gia**: Lần đầu join quỹ
- **Thông tin liên hệ**: SĐT, email, địa chỉ

##### Số liệu tài chính:

| Chỉ số | Mô tả | Cách tính |
|--------|-------|-----------|
| **Tổng đã nạp** | Tổng tiền đã đầu tư | Sum của tất cả giao dịch deposit |
| **Tổng đã rút** | Tổng tiền đã rút ra | Sum của tất cả giao dịch withdrawal |
| **Vốn ròng** | Vốn thực tế trong quỹ | Tổng nạp - Tổng rút |
| **Units hiện tại** | Số đơn vị quỹ đang sở hữu | Sum của tất cả tranche units |
| **Giá trị hiện tại** | Giá trị thị trường hiện tại | Units × Price per Unit |
| **Lãi/Lỗ** | Chênh lệch so với vốn ròng | Giá trị hiện tại - Vốn ròng |
| **% Lãi/Lỗ** | Tỷ lệ phần trăm | (Lãi/Lỗ ÷ Vốn ròng) × 100% |
| **Tổng phí đã trả** | Phí hiệu suất đã nộp | Sum từ tất cả fee records |

### Ví dụ cụ thể

```
👤 Nguyễn Văn A (ID: 1)
📅 Ngày tham gia: 15/01/2024
📞 SĐT: 0901234567

💰 Tình trạng tài chính:
- Tổng đã nạp:     100,000,000 VND
- Tổng đã rút:      20,000,000 VND  
- Vốn ròng:         80,000,000 VND
- Units hiện tại:   75,000.50 units
- Giá trị hiện tại: 95,000,000 VND
- Lãi/Lỗ:          +15,000,000 VND (+18.75%)
- Tổng phí đã trả:   2,800,000 VND
```

---

## 4. Tính Năng Đặc Biệt

### Fund Manager

Hệ thống tự động tạo và quản lý **Fund Manager** (ID: 0):
- Không hiển thị trong danh sách investor thường
- Nhận units từ phí hiệu suất
- Có quyền rút tiền đặc biệt

### ID Assignment

- ID được assign tự động tăng dần từ 1
- ID: 0 reserved cho Fund Manager
- ID không thể thay đổi sau khi tạo
- ID bị xóa không được tái sử dụng

### Data Integrity

- Foreign key constraints đảm bảo data consistency
- Không thể xóa investor nếu còn có tranches/transactions
- Tên investor phải unique (case-insensitive)

---

## 5. Tips & Best Practices

### Quy tắc đặt tên

✅ **Nên**:
- "Nguyễn Văn A"
- "Công ty ABC"  
- "Mrs. Nguyen"

❌ **Không nên**:
- "" (trống)
- "   " (chỉ có spaces)
- Trùng với tên đã có

### Thông tin liên hệ

✅ **SĐT hợp lệ**:
- "0901234567"
- "+84901234567"
- "84901234567"

❌ **SĐT không hợp lệ**:
- "123456"
- "abcdef"  
- "090-123-4567"

✅ **Email hợp lệ**:
- "user@domain.com"
- "name.surname@company.vn"

❌ **Email không hợp lệ**:
- "invalid-email"
- "@domain.com"
- "user@"

### Backup trước khi sửa

Trước khi chỉnh sửa hàng loạt:
1. **Export Excel** để backup data hiện tại
2. **Test** với 1-2 investor trước
3. **Double-check** validation messages

### Troubleshooting

#### Không lưu được thay đổi
- Kiểm tra kết nối database (sidebar status)
- Xem console log (F12) để debug
- Thử refresh page và làm lại

#### Tên bị trùng lặp
- Hệ thống check tên case-insensitive
- "Nguyen Van A" = "nguyen van a"
- Thêm số hoặc ký tự phân biệt

#### Validation errors
- Đọc kỹ error message để biết trường nào lỗi
- Fix từng trường một, không rush
- Save thường xuyên để không mất công

---

## 6. Workflow Thực Tế

### Onboard nhà đầu tư mới

1. **Thu thập thông tin**:
   - CCCD/Passport để verify tên
   - SĐT và email chính thức
   - Địa chỉ liên hệ

2. **Thêm vào hệ thống**:
   - Dùng tên chính thức từ giấy tờ
   - Double-check không trùng lặp
   - Test call/email để verify contact info

3. **Xác nhận với nhà đầu tư**:
   - Show màn hình tình trạng
   - Confirm tất cả info đúng
   - Explain cách tracking performance

### Maintain data quality

1. **Review định kỳ** (tháng 1 lần):
   - Check thông tin liên hệ còn chính xác không
   - Update địa chỉ mới nếu có
   - Clean up data inconsistencies

2. **Audit trail**:
   - Mọi thay đổi được log
   - Backup trước major changes
   - Keep paper trail cho legal compliance

### Handle edge cases

- **Nhà đầu tư đổi tên**: Thêm note về tên cũ
- **Thông tin liên hệ mất**: Mark as inactive, keep records
- **Duplicate entries**: Merge data carefully, update transactions