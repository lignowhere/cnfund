# Project Roadmap

_Last updated: 2026-03-13_

Dựa trên code review March 2026. Ưu tiên: Critical → High → Medium → Low.

---

## Critical — Security (Fix ngay trước production)

### C1. Token Storage in localStorage
**File:** `frontend_app/src/store/auth-store.ts`
**Vấn đề:** Access token và refresh token lưu trong `localStorage` via Zustand `persist`. Dễ bị XSS lấy cắp.
**Fix:** Chuyển refresh token sang `httpOnly` cookie. Access token có thể giữ in-memory.
**Effort:** ~1 ngày

### C2. Thiếu Rate Limiting
**Vấn đề:** Không có rate limiting ở application layer. `POST /auth/login` có thể bị brute-force không giới hạn.
**Fix:** Thêm `slowapi` (FastAPI rate limiter) cho auth endpoints. Minimum: 5 req/min trên `/auth/login`.
**Effort:** ~2 giờ

### C3. Weak Default Password Warning không đủ
**File:** `backend_api/app/core/config.py`
**Vấn đề:** `admin_password` trong `_KNOWN_BAD_PASSWORDS` chỉ log warning, không raise exception. Password "1997" vẫn được chấp nhận trong production.
**Fix:** Raise `RuntimeError` nếu `environment=production` và password yếu. Hoặc enforce minimum length/complexity.
**Effort:** ~1 giờ

### C4. Google OAuth Token Handling
**File:** `token.pickle` ở root
**Vấn đề:** `token.pickle` file chứa OAuth credentials committed ở root (nếu chưa gitignore). Kể cả encode thành base64 thì vẫn là cleartext credentials.
**Fix:** Xác nhận `token.pickle` trong `.gitignore`; rotate credentials nếu đã expose; document rõ process encode token.
**Effort:** ~1 giờ review + potential credential rotation

---

## High Priority

### H1. Refactor God Class services_enhanced.py
**File:** `core/services_enhanced.py` (~2200 lines)
**Vấn đề:** Một class chứa: load/save, investor management, transaction processing, NAV, fee calculation, backup stubs, validation, reporting. Khó test, khó maintain.
**Proposed split:**
- `FeeCalculator` — fee math (HWM, hurdle, crystallization)
- `TransactionProcessor` — deposit, withdraw, undo, delete
- `NavManager` — NAV history, price_per_unit
- `InvestorManager` — CRUD investors/tranches
- `DataValidator` — integrity validation
- Keep `EnhancedFundManager` as thin orchestrator
**Effort:** ~3-5 ngày, cần test coverage trước khi refactor

### H2. Unit Test Coverage cho backend_api/
**Vấn đề:** Không có tests trong `backend_api/app/`. Tests chỉ tồn tại ở root `tests/` dùng SQLite.
**Fix:** Thêm pytest + `TestClient` fixtures cho endpoints, mock `FundRuntime`. Target: ≥70% coverage trên endpoints.
**Effort:** ~3 ngày

### H3. datetime.utcnow() Deprecation
**Files:** `core/services_enhanced.py` (2 occurrences), `core/postgres_data_handler.py` (5 occurrences)
**Vấn đề:** `datetime.utcnow()` deprecated trong Python 3.12+. Sẽ gây warnings và eventual removal.
**Fix:** Replace với `datetime.now(timezone.utc)` (hoặc `_utcnow()` helper đã có trong backend).
**Effort:** ~1 giờ

### H4. Frontend Error Boundaries
**Vấn đề:** Không có React error boundary. Lỗi runtime (network, unhandled exceptions) crash toàn bộ page thay vì show error UI.
**Fix:** Thêm `ErrorBoundary` component wrap các page sections. Minimal: 1 root-level error boundary trong `(app)/layout.tsx`.
**Effort:** ~2 giờ

### H5. Backup File Path Validation — Tăng cường
**File:** `backend_api/app/services/backup_service.py`
**Hiện trạng:** Có path traversal check (`is_relative_to`). Tốt.
**Cải thiện:** Thêm whitelist regex cho `backup_id` filename format (`Fund_Export_*.xlsx`) trước khi resolve path. Defense in depth.
**Effort:** ~1 giờ

---

## Medium Priority

### M1. API Versioning Strategy
**Vấn đề:** Hiện tại `/api/v1/` prefix nhưng không có actual versioning strategy. Breaking changes không được document.
**Fix:** Định nghĩa rõ deprecation policy. Bắt đầu dùng `CHANGELOG.md` cho API changes.
**Effort:** ~1 ngày planning

### M2. Structured Logging
**Vấn đề:** Logging hiện tại dùng `print()` statements mix với `logging.info/error`. Không có request ID correlation.
**Fix:** Standardize trên `logging` module. Thêm request ID vào audit log và propagate qua service calls.
**Effort:** ~1 ngày

### M3. Database Migration Tool
**Vấn đề:** Không có Alembic hoặc migration tracking. Schema changes phải làm thủ công. `Base.metadata.create_all()` chỉ tạo bảng mới, không alter existing.
**Fix:** Thêm Alembic cho auth tables. Fund tables đang dùng raw SQL — document migration process.
**Effort:** ~1 ngày setup

### M4. FundRuntime Memory Model
**Vấn đề:** `FundRuntime` load toàn bộ fund data vào memory khi startup và sau mỗi mutate. Với số lượng giao dịch lớn, này sẽ tăng memory footprint và reload latency.
**Fix:** Xem xét lazy loading hoặc caching với invalidation. Hiện tại với scale nhỏ (< vài nghìn records) chưa cần thiết.
**Effort:** Medium — architecture decision required

### M5. Frontend Form Validation
**Vấn đề:** Không dùng form library (react-hook-form, zod). Validation trải rác trong event handlers.
**Fix:** Thêm zod schemas cho API request types + react-hook-form. Types đã có sẵn trong `lib/types.ts`.
**Effort:** ~2 ngày

### M6. Environment Variable Documentation
**Vấn đề:** Một số env vars trong settings (`access_token_expire_minutes`, `refresh_token_expire_days`) không được document trong deployment guide.
**Fix:** Update `.env.example` và `docs/deployment-guide.md` với full env var list.
**Effort:** ~1 giờ (đã được xử lý trong `deployment-guide.md`)

### M7. Investor Role — Read Access Scope
**Vấn đề:** `investor` role hiện không có trong `READ_ROLES`. Investor chỉ có thể access `/reports/me` và `/reports/me/transactions`. Nếu cần xem NAV history hay investor list, sẽ bị 403.
**Fix:** Review xem investor cần read gì. Update `READ_ROLES` nếu cần hoặc tạo `INVESTOR_ROLES` set riêng.
**Effort:** ~2 giờ

---

## Low Priority / Technical Debt

### L1. `core/services_enhanced.py` — Print statements
**Vấn đề:** Nhiều `print()` statements với emoji (encoding issues trên Windows/logs).
**Fix:** Replace với `logging.info/debug`.

### L2. Legacy Backup Stubs trong services_enhanced.py
**Vấn đề:** Nhiều backup-related methods return empty/stub values vì backup đã được moved sang API. Gây confusion.
**Fix:** Xóa stub methods hoặc document rõ deprecated.

### L3. Token Deduplication trong Auth Store
**Vấn đề:** `refreshInFlight` deduplication chỉ hoạt động trong single tab. Multiple tabs có thể trigger concurrent refreshes.
**Fix:** Xem xét `BroadcastChannel` API hoặc `SharedWorker` cho cross-tab token sync.

### L4. PDF Export Quality
**File:** `backend_api/app/services/export_service.py`
**Vấn đề:** Dùng `reportlab` trực tiếp — PDF output cơ bản, không có template. Khó customize.
**Fix:** Xem xét `WeasyPrint` hoặc HTML template → PDF approach.

### L5. Missing .env.example
**Vấn đề:** `backend_api/.env.example` được reference trong README nhưng cần verify tồn tại và đầy đủ.
**Fix:** Ensure `.env.example` có tất cả required vars với placeholder values.

---

## Documentation Debt (Resolved with this sprint)

Các docs được tạo trong sprint 2026-03-13:
- [x] `docs/project-overview-pdr.md`
- [x] `docs/codebase-summary.md`
- [x] `docs/code-standards.md`
- [x] `docs/system-architecture.md`
- [x] `docs/project-roadmap.md` (tài liệu này)
- [x] `docs/deployment-guide.md`
- [x] `docs/design-guidelines.md`
- [x] `docs/README.md` (index)

---

## Metrics to Track

| Metric | Hiện tại | Target |
|--------|----------|--------|
| Backend unit test coverage (backend_api/) | 0% | ≥70% |
| `datetime.utcnow()` occurrences | 7 | 0 |
| Token storage security | localStorage | httpOnly cookie |
| Rate limiting | None | ≥ 5 req/min on auth |
| services_enhanced.py lines | ~2200 | <500 per module |
| Error boundary coverage | 0 | ≥1 root boundary |
