# Code Standards

_Last updated: 2026-03-13_

Tài liệu này mô tả các patterns thực tế đang dùng trong codebase, không phải aspirational standards.

---

## Python (backend_api + core)

### Style
- Python 3.11+ features: union types `X | Y`, `match` statements
- Không dùng `from __future__ import annotations`
- Type hints đầy đủ cho function signatures trong `backend_api/`; ít hơn trong `core/`
- `core/services_enhanced.py` dùng `Dict[str, Any]`, `List[Investor]` (typing module, không phải built-in generics)

### Imports
- Standard library trước, third-party sau, local last — nhưng không enforce bằng linter
- `core/` và `utils/` được bootstrap vào `sys.path` tại runtime bởi `FundRuntime._bootstrap_sys_path()`
- Pattern import trong endpoints: relative imports (`from ...services.fund_runtime import runtime`)

### Naming
- Classes: `PascalCase` — `EnhancedFundManager`, `PostgresDataHandler`, `FundRuntime`
- Functions/methods: `snake_case` — `get_investor_by_id`, `calculate_investor_fee`
- Constants: `UPPER_SNAKE_CASE` — `HURDLE_RATE_ANNUAL`, `PERFORMANCE_FEE_RATE`
- Private methods: `_leading_underscore` — `_build_manager`, `_apply_fee_to_investor_tranches`
- SQLAlchemy models: `PascalCase` — `User`, `RefreshToken`, `AuditLog`
- Pydantic schemas: `PascalCase` + `DTO` suffix cho response types — `InvestorCardDTO`, `FeePreviewDTO`

### Error handling
- FastAPI endpoints raise `HTTPException` với status codes cụ thể
- Business logic trong `core/` trả về `bool` hoặc dict thay vì raise exceptions
- `try/except Exception as e: logging.error(...)` dùng nhiều trong `services_enhanced.py`
- Endpoint pattern:
```python
def _write(manager):
    try:
        result = manager.do_something(...)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed: {exc}") from exc
    return result

return ApiResponse(data=runtime.mutate(_write))
```

### Response format
Tất cả API responses wrap trong `ApiResponse[T]`:
```python
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str | None = None
    data: T
```

### Configuration (env vars)
- `pydantic-settings` với prefix `API_`
- Tất cả settings trong `backend_api/app/core/config.py`
- Secrets validation tại startup: `jwt_secret_key` required, `admin_password` weak check
- `.env` file ở repo root, đọc bởi `SettingsConfigDict(env_file=".env", env_prefix="API_")`

### Datetime
- `datetime.now(timezone.utc)` thay vì `datetime.utcnow()` (deprecated)
- Tuy nhiên: vẫn còn 7 occurrences của `datetime.utcnow()` trong `core/` — legacy code
- DB columns lưu naive datetime (UTC) — `_utcnow()` helper: `datetime.now(timezone.utc).replace(tzinfo=None)`

### Security
- Passwords: `pbkdf2_sha256` qua `passlib`
- JWT: `python-jose`, HS256 algorithm
- Refresh token: stored hashed (`sha256`) trong DB, `jti` field để revoke
- Path traversal protection trong backup restore:
```python
target = (EXPORT_DIR / backup_id).resolve()
if not target.is_relative_to(EXPORT_DIR.resolve()):
    raise ValueError(f"Invalid backup_id: {backup_id}")
```

### Concurrency
- `FundRuntime` dùng `threading.Lock()` để serialize read/mutate operations
- `EnhancedFundManager.load_data()` dùng `ThreadPoolExecutor(max_workers=4)` để load parallel từ DB

---

## TypeScript (frontend_app)

### Style
- TypeScript strict mode (inferred từ tsconfig)
- `"use client"` directive ở đầu mọi component/hook dùng browser APIs
- No `any` type ngoài các điểm explicit với `// type: ignore[...]` comment

### Naming
- Components: `PascalCase` — `ConfirmDialog`, `ToastViewport`
- Hooks: `camelCase` bắt đầu bằng `use` — `useAuthStore`
- Types/interfaces: `PascalCase` + `DTO` suffix cho API response shapes — `InvestorCardDTO`
- API client methods: `camelCase` — `investorCards`, `createTransaction`
- Route constants: kebab-case trong URL — `/investors`, `/fees`
- Constants: `UPPER_SNAKE_CASE` (hiếm, mostly trong query-keys)

### Imports
- Path alias `@/` maps to `src/` — dùng nhất quán
- Không có barrel exports (index.ts files) — import trực tiếp từ file
- Type-only imports: `import type { ... }` cho TypeScript types

### State Management
- **Server state:** TanStack Query (`@tanstack/react-query`) — fetch, cache, invalidate
- **Auth state:** Zustand `persist` middleware → `localStorage` (key `cnfund-auth`)
- **Local UI state:** `useState` / `useReducer`

### API Calls
- Tất cả qua `apiClient` object trong `src/lib/api.ts`
- Auto token refresh khi 401: deduplicated via `refreshInFlight` promise
- Error messages được parse từ `ApiResponse.detail` (string hoặc `ValidationErrorPayload`)
- Không dùng SWR hay axios

### Components
- shadcn/ui components ở `src/components/ui/` — wrapper với custom variants
- `cn()` utility = `clsx` + `tailwind-merge` — dùng nhất quán cho class concatenation
- Không dùng CSS modules hay styled-components
- Tailwind classes trực tiếp trên elements

### Forms
- Không dùng react-hook-form hay formik — forms được xử lý với `useState` + controlled inputs
- VND amounts dùng `NumberInput` wrapper (`src/lib/number-input.ts`) format `xxx.xxx` → numeric

### Error handling
- API errors hiển thị qua toast notification
- Không có error boundary — lỗi crash page
- Network errors được format bởi `buildNetworkError()` với user-friendly Vietnamese messages

---

## Database Schema Conventions

### SQLAlchemy (auth tables)
- `mapped_column()` với explicit types
- `Mapped[T]` type annotations
- `DateTime` columns lưu naive UTC (`_utcnow()` default)
- Table names: `snake_case` — `users`, `refresh_tokens`, `audit_logs`

### Fund tables (PostgreSQL, managed by core/)
- Table prefix: `fund_` — `fund_investors`, `fund_tranches`, etc.
- Columns: `snake_case`
- JSON columns cho fee configs

---

## API Design Conventions

### URL Structure
```
/api/v1/{resource}           GET list, POST create
/api/v1/{resource}/{id}      GET one, PUT/PATCH update, DELETE
/api/v1/{resource}/{id}/action   POST for actions (undo, reset-password)
/api/v1/{resource}/action    POST for collection actions (preview, apply, manual)
```

### Response Shape
```json
{
  "success": true,
  "message": "Optional message",
  "data": { ... }
}
```

Paginated responses:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### HTTP Status Codes dùng trong project
- `200` — success
- `400` — bad request / validation error / business rule violation
- `401` — unauthenticated
- `403` — unauthorized (wrong role)
- `404` — not found
- `422` — Pydantic validation error (FastAPI default)
