### **HƯỚNG DẪN VẬN HÀNH HỆ THỐNG QUẢN LÝ QUỸ ĐẦU TƯ**

#### **1. Giới thiệu**

Chào mừng bạn đến với Hệ thống Quản lý Quỹ. Công cụ này được thiết kế để giúp bạn tự động hóa và đơn giản hóa toàn bộ quy trình quản lý một quỹ đầu tư, từ việc theo dõi nhà đầu tư, ghi nhận giao dịch, cho đến việc tính toán phí hiệu suất một cách chính xác và minh bạch.

**Các lợi ích chính:**

- **Tập trung dữ liệu:** Mọi thông tin về nhà đầu tư, giao dịch, và các kỳ tính phí đều được lưu trữ an toàn ở một nơi duy nhất.
- **Tính toán tự động:** Giảm thiểu sai sót của con người bằng cách tự động hóa các phép tính phức tạp như giá mỗi đơn vị quỹ (NAV/unit) và phí hiệu suất.
- **Minh bạch:** Cung cấp các báo cáo chi tiết về hiệu suất đầu tư và lịch sử phí cho từng nhà đầu tư.
- **Bảo mật:** Phân quyền truy cập rõ ràng, yêu cầu đăng nhập cho các thao tác quan trọng.

#### **2. Bắt đầu & Các Khái Niệm Cốt Lõi**

##### **2.1. Chế độ truy cập**

Hệ thống có hai chế độ:

- **Chế độ Chỉ xem (Viewer):** Khi chưa đăng nhập, bạn có thể xem tất cả các báo cáo, thống kê, lịch sử phí và hiệu suất đầu tư. Bạn không thể thay đổi hay thêm mới bất kỳ dữ liệu nào.
- **Chế độ Quản trị (Admin):** Để thực hiện các thao tác thêm, sửa, xóa dữ liệu (như thêm nhà đầu tư, ghi nhận giao dịch, tính phí), bạn cần phải đăng nhập.
  1.  Chọn một trang yêu cầu quyền chỉnh sửa (ví dụ: "💸 Thêm Giao Dịch").
  2.  Nhập mật khẩu quản trị đã được cung cấp.
  3.  Nhấn nút **"🚀 Đăng nhập"**.

##### **2.2. Các thuật ngữ cần nắm**

- **Tổng NAV (Total Net Asset Value):** Là tổng giá trị tài sản ròng của quỹ tại một thời điểm nhất định. Đây là con số quan trọng nhất để xác định giá trị của quỹ.
- **Đơn vị quỹ (Units):** Giống như "cổ phần" của quỹ. Khi một nhà đầu tư nạp tiền, họ sẽ "mua" một số lượng đơn vị quỹ nhất định. Tổng số đơn vị quỹ của một người thể hiện tỷ lệ sở hữu của họ trong quỹ.
- **Giá mỗi Đơn vị (Price per Unit):** Được tính bằng công thức: `Tổng NAV / Tổng số Đơn vị quỹ đang lưu hành`.
- **High-Water Mark (HWM):** Là "mốc giá cao nhất" mà một lô giao dịch đã từng đạt được. Phí hiệu suất chỉ được tính trên phần lợi nhuận vượt qua mốc HWM này, đảm bảo nhà đầu tư không phải trả phí hai lần cho cùng một mức lợi nhuận.
- **Hiệu suất Trọn đời (Lifetime Performance):** Phân tích hiệu suất đầu tư tính từ **lúc bắt đầu** thay vì chỉ trong một kỳ, có tính đến cả các khoản phí đã trả.

#### **3. Hướng Dẫn Chi Tiết Các Chức Năng**

##### **3.1. Quản lý Nhà đầu tư (NĐT)**

- **Trang: `👥 Thêm Nhà Đầu Tư`**

  1.  Điền tên (bắt buộc) và các thông tin liên hệ khác (số điện thoại, email, địa chỉ).
  2.  Nhấn nút **"➕ Thêm Nhà Đầu Tư"**.

- **Trang: `✏️ Sửa Thông Tin NĐT`**
  - **Phần 1: Sửa thông tin**
    1.  Một bảng tính chứa toàn bộ danh sách NĐT sẽ hiện ra.
    2.  Bạn có thể **sửa trực tiếp** trên các ô của bảng (Tên, SĐT, Địa chỉ, Email, Ngày tham gia).
    3.  Sau khi chỉnh sửa xong, nhấn nút **"💾 Lưu Thay Đổi"** để cập nhật.
  - **Phần 2: Xem Tình Trạng Nhà Đầu Tư**
    1.  Chọn một nhà đầu tư từ danh sách.
    2.  Nhập **Total NAV Hiện Tại** để hệ thống tính toán.
    3.  Xem nhanh các chỉ số quan trọng: Số dư, Lãi/Lỗ, và Tỷ lệ Lãi/Lỗ hiện tại.

##### **3.2. Quản lý Giao dịch & NAV**

- **Trang: `📈 Thêm Total NAV`**

  - **Mục đích:** Cập nhật giá trị hiện tại của quỹ. Nên thực hiện định kỳ (cuối ngày/tuần) hoặc khi có biến động lớn.

  1.  Chọn ngày cập nhật.
  2.  Nhập giá trị **Total NAV mới** của quỹ.
  3.  Nhấn **"✅ Cập nhật NAV"**.

- **Trang: `💸 Thêm Giao Dịch` (Nạp/Rút tiền cho NĐT)**

  1.  Chọn nhà đầu tư và loại giao dịch (Nạp/Rút).
  2.  Nhập số tiền và ngày giao dịch.
  3.  **Quan trọng:** Nhập **Tổng NAV Mới của Quỹ (SAU KHI đã cộng/trừ số tiền giao dịch)**.
  4.  Nhấn **"✅ Thực hiện giao dịch"**.

- **Trang: `🛒 Fund Manager Withdrawal` (Rút tiền cho Quản lý Quỹ)**

  - **Mục đích:** Trang **chuyên biệt** để Fund Manager rút tiền lời của mình (từ các khoản phí đã nhận).

  1.  Hệ thống sẽ tự động hiển thị số dư hiện tại của Fund Manager.
  2.  Chọn loại rút: "Rút một phần" hoặc "Rút toàn bộ".
  3.  Nhập số tiền nếu rút một phần.
  4.  Xem trước số units bị trừ và NAV còn lại của quỹ.
  5.  Nhấn **"💸 Xác Nhận Fund Manager Withdrawal"** để hoàn tất.

- **Trang: `🔧 Quản Lý Giao Dịch`**
  - **Tab 1 - 📋 Danh Sách Giao Dịch:**
    - Xem lại toàn bộ lịch sử giao dịch.
    - Sử dụng các bộ lọc theo: Loại giao dịch, Nhà đầu tư, và Khoảng thời gian.
  - **Tab 3 - 🗑️ Xóa Giao Dịch:**
    1.  **Cảnh báo:** Hành động này rất nguy hiểm và có thể làm sai lệch toàn bộ dữ liệu.
    2.  Chọn một giao dịch từ danh sách 20 giao dịch gần nhất.
    3.  Kiểm tra lại thông tin.
    4.  Tick vào ô xác nhận và nhấn nút **"🗑️ XÓA GIAO DỊCH"**.

##### **3.3. Tính toán & Quản lý Phí**

- **Trang: `🧮 Tính Toán Phí` (Chốt phí cuối kỳ)**

  - **Mục đích:** Chức năng quan trọng nhất, thực hiện cuối kỳ (cuối năm) để tính và thu phí hiệu suất.

  1.  Nhập **Năm**, **Ngày Kết Thúc**, và **Total NAV Kết Thúc** của kỳ tính phí.
  2.  **Tab 1 - 🧮 Tính Phí Enhanced (Xem trước):**
      - Đây là bảng xem trước quan trọng nhất. Nó cho bạn thấy: Phí mới của mỗi NĐT, số Units sẽ bị trừ và chuyển cho Fund Manager, và số Units còn lại.
      - Kiểm tra kỹ lưỡng tổng phí và tổng units sẽ được chuyển.
  3.  **Tab 2 & 3 (Phí Chi Tiết & Chi Tiết Tranches):** Cung cấp các bảng tính chi tiết hơn về cách phí được tạo ra.
  4.  **Hành động cuối cùng - Áp dụng phí:**
      - Sau khi đã kiểm tra kỹ lưỡng bản xem trước, tick vào ô **"✅ Tôi chắc chắn muốn áp dụng phí"**.
      - Nhấn nút **"🚀 Áp Dụng Phí"**.
      - ⚠️ **CẢNH BÁO:** Hành động này là **KHÔNG THỂ HOÀN TÁC**. Hệ thống sẽ trừ Units của NĐT, cộng Units cho Fund Manager và ghi lại lịch sử phí vĩnh viễn.

- **Trang: `🔍 Tính Phí Riêng`**
  - **Mục đích:** Công cụ xem nhanh phí tạm tính cho một NĐT bất kỳ mà không ảnh hưởng đến dữ liệu. Rất hữu ích khi NĐT muốn hỏi về phí trước khi rút tiền giữa kỳ.
  1.  Chọn nhà đầu tư, ngày tính và Total NAV.
  2.  Nhấn **"🧮 Tính Toán"**.
  3.  Kết quả sẽ hiển thị cả **Hiệu suất Hiện tại** và **Hiệu suất Trọn đời**, cùng với chi tiết cách tính phí.

##### **3.4. Báo cáo & Phân Tích**

- **Trang: `📊 Báo Cáo & Thống Kê`** (Trang tổng hợp nhiều loại báo cáo)

  - **Tab 1 - 📊 Thống Kê Giá Trị:** Xem tổng quan số dư, vốn, lãi/lỗ của các nhà đầu tư tại một thời điểm NAV nhất định.
  - **Tab 2 - 📈 Lifetime Performance:** (Xem thêm trang riêng bên dưới)
  - **Tab 3 - 💰 Lịch Sử Phí:** (Xem thêm trang riêng bên dưới)
  - **Tab 4 - 📋 Lịch Sử Giao Dịch:** Bảng ghi lại toàn bộ giao dịch của quỹ.
  - **Tab 5 - 🏛️ Fund Manager Dashboard:** Bảng điều khiển dành riêng cho người quản lý, theo dõi tài sản và thu nhập từ phí.

- **Trang: `📈 Lifetime Performance`**

  - Đây là báo cáo giá trị nhất, cho thấy hiệu quả đầu tư thực sự của NĐT.
  - Nó phân biệt rõ **Vốn Gốc**, **Tổng Phí Đã Trả**, và từ đó tính ra **Lợi nhuận Gross** (trước phí) và **Lợi nhuận Net** (sau phí).
  - Sử dụng biểu đồ để so sánh và phân tích tác động của phí.

- **Trang: `💰 Lịch Sử Phí`**
  - Xem lại chi tiết tất cả các lần thu phí trong quá khứ.
  - Lọc theo kỳ hoặc theo từng nhà đầu tư.
  - Bao gồm các biểu đồ tổng kết phí theo từng kỳ.

#### **4. Quy trình làm việc mẫu**

1.  **NĐT mới tham gia:** Dùng chức năng `👥 Thêm Nhà Đầu Tư` để tạo hồ sơ.
2.  **NĐT nạp tiền:** Dùng chức năng `💸 Thêm Giao Dịch` để ghi nhận số tiền và cập nhật NAV mới.
3.  **Quỹ hoạt động:** Cập nhật NAV định kỳ bằng chức năng `📈 Thêm Total NAV`.
4.  **NĐT rút tiền:** Dùng chức năng `💸 Thêm Giao Dịch` với loại "Rút".
5.  **Cuối kỳ (Cuối năm):**
    - Cập nhật NAV cuối cùng của kỳ.
    - Vào `🧮 Tính Toán Phí`, xem trước kỹ lưỡng, và xác nhận áp dụng phí.
6.  **Bất cứ lúc nào:** Sử dụng các trang báo cáo (`📊 Báo Cáo & Thống Kê`, `📈 Lifetime Performance`, `💰 Lịch Sử Phí`) để theo dõi tình hình hoạt động của quỹ.

#### **5. Câu hỏi thường gặp (FAQ)**

- **Câu hỏi: Tôi nhập sai một giao dịch, làm thế nào để sửa?**

  - **Trả lời:** Hãy vào trang `🔧 Quản Lý Giao Dịch`, vào tab `🗑️ Xóa Giao Dịch` để xóa giao dịch sai đi. Sau đó, bạn cần vào trang `💸 Thêm Giao Dịch` để tạo lại giao dịch đó cho đúng. Hãy thật cẩn thận vì việc này có thể ảnh hưởng đến các tính toán sau thời điểm đó.

- **Câu hỏi: Nút "Export Excel" để làm gì?**

  - **Trả lời:** Nút này sẽ tạo một file báo cáo tổng hợp dưới dạng Excel và tự động tải nó lên Google Drive đã được cấu hình, giúp bạn dễ dàng lưu trữ và chia sẻ báo cáo.

- **Câu hỏi: Sự khác biệt giữa `💸 Thêm Giao Dịch` và `🛒 Fund Manager Withdrawal` là gì?**
  - **Trả lời:** `💸 Thêm Giao Dịch` dùng cho các giao dịch nạp/rút tiền của **nhà đầu tư thông thường**. `🛒 Fund Manager Withdrawal` là trang **chuyên biệt** để **người quản lý quỹ** rút số tiền lời (đến từ phí) mà mình đã tích lũy được.
