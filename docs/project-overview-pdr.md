# CNFund — Project Overview & Product Development Requirements

_Last updated: 2026-03-13_

---

## 1. Tổng quan hệ thống

CNFund là hệ thống quản lý quỹ đầu tư nội bộ (private investment fund) dành cho nhóm nhà đầu tư cá nhân tại Việt Nam. Hệ thống theo dõi: vốn góp, NAV, lợi nhuận, phí quản lý/performance, và báo cáo cho từng nhà đầu tư.

**Stack hiện tại:**
- Frontend: Next.js 16 + TypeScript + Tailwind + shadcn/ui → deploy Vercel
- Backend: FastAPI (Python 3.11+) → deploy Railway
- Database: PostgreSQL (Railway managed)
- Backup: local Excel export + Google Drive upload

**Đã loại bỏ:** Streamlit UI, Supabase.

---

## 2. Người dùng & Vai trò (RBAC)

| Role | Quyền | Mô tả |
|------|-------|-------|
| `admin` | Read + Write + Admin | Quản lý toàn bộ hệ thống, tài khoản người dùng |
| `fund_manager` | Read + Write | Giao dịch, NAV, phí. Không quản lý accounts |
| `investor` | Read (chỉ dữ liệu của mình) | Xem báo cáo cá nhân, lịch sử giao dịch |
| `viewer` | Read | Chỉ đọc, không thay đổi dữ liệu |

Role được kiểm tra tại `backend_api/app/core/rbac.py`:
- `READ_ROLES = {viewer, admin, fund_manager}`
- `MUTATE_ROLES = {admin, fund_manager}`
- `ADMIN_ONLY_ROLES = {admin}`

---

## 3. Tính năng chính

### 3.1 Quản lý nhà đầu tư
- Thêm/sửa investor với thông tin: tên, phone, email, địa chỉ (tỉnh/huyện chuẩn hóa theo catalog)
- Mỗi investor có thể có tài khoản đăng nhập (linked `InvestorAccount`)
- Fund Manager là investor đặc biệt (`is_fund_manager=True`), nhận phí từ các investor khác

### 3.2 Giao dịch (Transactions)
Ba loại giao dịch:
- **deposit**: Nhà đầu tư nạp vốn → tạo tranche mới với `entry_nav` hiện tại
- **withdraw**: Rút vốn (một phần hoặc toàn bộ) → giảm units theo tỉ lệ
- **nav_update**: Cập nhật tổng NAV quỹ → tính lại `price_per_unit`

Hỗ trợ undo transaction và delete transaction với kiểm tra integrity.

### 3.3 NAV Tracking
- Lưu lịch sử NAV theo thời gian
- `price_per_unit = total_nav / total_units`
- Hiển thị biểu đồ NAV history trên frontend

### 3.4 Tính phí (Fee Calculation)

#### Performance Fee
- **Mặc định:** 20% (`PERFORMANCE_FEE_RATE = 0.20`)
- **Hurdle Rate:** 6%/năm (`HURDLE_RATE_ANNUAL = 0.06`)
- **High Water Mark (HWM):** Mỗi tranche có HWM riêng. Phí chỉ tính trên lợi nhuận vượt HWM VÀ vượt hurdle rate.
- **Crystallization:** Khi apply fee, HWM được nâng lên giá hiện tại; `entry_nav` và `invested_value` của tranche được cập nhật.

#### Cơ chế tính phí theo tranche
```
excess_profit_per_tranche = (current_price - hurdle_price) * units
hurdle_price = entry_nav * (1 + hurdle_rate_annual) ^ years_held
performance_fee = sum(excess_profit_per_tranche) * performance_fee_rate
```

Phí được trừ vào units của investor và chuyển sang tranche của Fund Manager.

#### Fee Configuration
- Global config: áp dụng cho toàn bộ quỹ
- Per-investor override: ghi đè global cho từng investor
- API: `GET/PATCH /fees/config/global`, `PUT/DELETE /fees/config/overrides/{investor_id}`

### 3.5 Báo cáo
- **Dashboard:** KPIs (total NAV, số investors, tổng units, tổng phí, fund manager value, gross return), top investors
- **Investor report:** Chi tiết từng investor — balance, P&L, lifetime performance, fee details, tranches, transaction history
- **Transactions report:** Lọc theo ngày, investor, loại giao dịch; xuất CSV hoặc PDF

### 3.6 Backup & Restore
- Auto backup sau mỗi giao dịch mới (nếu `API_AUTO_BACKUP_ON_NEW_TRANSACTION=true`)
- Manual backup qua API → tạo file `.xlsx` ở `exports/`
- Restore từ backup với xác nhận phrase "RESTORE"
- Upload lên Google Drive (nếu cấu hình `GOOGLE_OAUTH_TOKEN_BASE64`)

### 3.7 Accounts Management
- Admin quản lý tài khoản đăng nhập cho investors
- Reset password cho investor accounts
- Liên kết `User` ↔ `InvestorAccount` (1-1)

---

## 4. Business Rules

### 4.1 Quy tắc giao dịch
- Deposit phải có `amount > 0` và `total_nav > 0`
- Withdraw không được vượt quá số units hiện có
- NAV update phải có `total_nav >= 0`
- Mỗi giao dịch được audit log (user, method, path, status code)

### 4.2 Quy tắc phí
- Phí chỉ áp dụng với investors thường (không áp dụng cho Fund Manager)
- Preview phí trước khi apply — yêu cầu `confirm_token` và hai acknowledge flags
- Khi apply phí: tạo `FeeRecord`, giảm units investor, tăng units Fund Manager
- Không apply phí cho tranche có `excess_profit <= EPSILON` (1e-6)

### 4.3 Quy tắc undo/delete
- Undo hoạt động khác delete: undo reverses về trạng thái trước, delete chỉ xóa record
- Undo deposit: giảm units tương ứng, xóa tranche liên quan
- Undo withdrawal: restore units đã rút

### 4.4 Tính toàn vẹn dữ liệu
- `validate_data_integrity()` kiểm tra: investors, tranches, transactions, fee_records, cross-references
- Thread-safe thông qua `FundRuntime._lock` — mỗi read/mutate đều acquire lock

---

## 5. Yêu cầu phi chức năng

| Yêu cầu | Hiện trạng |
|---------|-----------|
| Authentication | JWT access token (30 min) + refresh token (7 days), revocation qua DB |
| Authorization | RBAC 4 roles, kiểm tra tại mọi endpoint |
| Audit trail | Mọi HTTP request được log vào `audit_logs` |
| Concurrency | Thread-safe via `threading.Lock` trong `FundRuntime` |
| Backup | Auto backup + manual backup + Google Drive |
| PWA | Service worker, web manifest, installable |
| Dark mode | CSS variables, `[data-theme="dark"]` |
| Responsive | Mobile-first, Tailwind breakpoints |

---

## 6. Ràng buộc kỹ thuật

- Python 3.11+ (dùng `match`, union type `X | Y`)
- Node.js 20+, Next.js 16 (App Router)
- PostgreSQL là database duy nhất được hỗ trợ trong production
- `core/services_enhanced.py` là god class (~2200 dòng) — cần refactor dài hạn
- Không có rate limiting tại application layer
- Tokens lưu trong `localStorage` (qua Zustand persist)
