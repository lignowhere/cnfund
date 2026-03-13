# Codebase Summary

_Last updated: 2026-03-13_

---

## Repository Root Layout

```
CNFund/
├── backend_api/          # FastAPI application (Railway deploy)
├── core/                 # Shared business logic (Python)
├── frontend_app/         # Next.js application (Vercel deploy)
├── utils/                # Shared Python utilities
├── scripts/              # One-off migration/setup scripts
├── tests/                # Integration & smoke tests
├── data/                 # Local CSV seed data
├── exports/              # Backup Excel files (gitignored)
├── docs/                 # Documentation
├── config.py             # Fund constants (HURDLE_RATE, PERFORMANCE_FEE_RATE, etc.)
├── helpers.py            # Shared helpers (validate_phone, validate_email, format_currency)
├── railway.toml          # Railway build config
├── Dockerfile            # Backend Docker image
├── requirements.txt      # Root-level Python deps (for scripts/tests)
└── package.json          # npm scripts for dev (concurrently runs both stacks)
```

---

## backend_api/

FastAPI application. All runtime logic lives here when running in production.

```
backend_api/
├── app/
│   ├── main.py               # App factory, CORS, audit middleware, lifespan
│   ├── api/
│   │   ├── router.py         # Mounts all endpoint routers under /api/v1
│   │   ├── deps.py           # DI: get_db, get_current_user, require_*_access
│   │   └── endpoints/
│   │       ├── auth.py           # POST /login /refresh /logout; GET /me
│   │       ├── accounts.py       # Investor account management (admin only)
│   │       ├── investors.py      # CRUD investors + cards/paginated
│   │       ├── transactions.py   # CRUD + undo transactions
│   │       ├── nav.py            # GET /nav/history
│   │       ├── fees.py           # Preview, apply, history, config
│   │       ├── reports.py        # Dashboard, investor report, transactions report, export
│   │       ├── backups.py        # List, manual backup, restore
│   │       └── system.py         # Feature flags, location catalog
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings, env prefix API_)
│   │   ├── database.py       # SQLAlchemy engine + SessionLocal
│   │   ├── security.py       # JWT create/decode, pbkdf2_sha256 password hashing
│   │   └── rbac.py           # Role sets: READ_ROLES, MUTATE_ROLES, ADMIN_ONLY_ROLES
│   ├── models/
│   │   └── auth.py           # SQLAlchemy models: User, RefreshToken, InvestorAccount, AuditLog
│   ├── schemas/
│   │   ├── common.py         # ApiResponse[T], generic wrapper
│   │   ├── auth.py           # LoginRequest, TokenPair, UserInfo, etc.
│   │   ├── investors.py      # InvestorCardDTO, CreateInvestorRequest, etc.
│   │   ├── transactions.py   # TransactionCardDTO, CreateTransactionRequest
│   │   ├── nav.py            # NavPointDTO
│   │   ├── fees.py           # FeePreviewDTO, FeeApplyRequest, FeeConfigBundleDTO, etc.
│   │   ├── reports.py        # DashboardDTO, InvestorReportDTO, TransactionsReportDTO
│   │   ├── backups.py        # BackupListItemDTO, RestoreBackupRequest
│   │   ├── accounts.py       # InvestorAccountAdminItemDTO
│   │   └── system.py         # FeatureFlagsDTO, LocationProvinceDTO, LocationWardDTO
│   ├── services/
│   │   ├── fund_runtime.py   # Thread-safe singleton wrapping EnhancedFundManager
│   │   ├── backup_service.py # list_local_backups, trigger_manual_backup, restore_from_local_backup
│   │   ├── export_service.py # Excel/CSV/PDF export logic
│   │   ├── location_catalog.py # Province/ward lookup from embedded JSON
│   │   └── mappers.py        # fee_record_to_dto, investor_to_dto, etc.
│   └── data/                 # Embedded location catalog JSON
├── requirements.txt          # Backend-specific deps
└── start.sh                  # Uvicorn startup script
```

**Điểm quan trọng:**
- `fund_runtime.py` là cầu nối giữa FastAPI endpoints và `core/services_enhanced.py`. Mọi operation đều đi qua `runtime.read()` hoặc `runtime.mutate()`.
- Tất cả business logic thực sự nằm ở `core/` không phải trong `backend_api/`.
- SQLAlchemy models chỉ quản lý auth tables; fund data (investors, tranches, etc.) được lưu trong bảng `fund_*` do `core/postgres_data_handler.py` quản lý.

---

## core/

Shared business logic. Được dùng bởi cả `backend_api/` và scripts migration.

```
core/
├── models.py                  # Dataclasses: Investor, Tranche, Transaction, FeeRecord
├── services_enhanced.py       # EnhancedFundManager — god class (~2200 lines)
│                              # Chứa: load/save, investors, transactions, NAV,
│                              # fee calculation (HWM, hurdle, performance fee),
│                              # backup stubs, validation, reports
└── postgres_data_handler.py   # PostgresDataHandler — SQL queries cho fund_* tables
```

**Database tables (fund data):**
- `fund_investors` — investor records
- `fund_tranches` — investment tranches per investor
- `fund_transactions` — all transactions
- `fund_fee_records` — fee application history
- `fund_fee_global_config` — global fee configuration
- `fund_fee_investor_overrides` — per-investor fee overrides

**Key classes:**
- `EnhancedFundManager`: orchestrates all business operations. Không thread-safe natively — được wrap bởi `FundRuntime`.
- `PostgresDataHandler`: raw SQL load/save. `connected` property = True khi DB available.
- `Tranche`: dataclass với HWM, `invested_value` property/setter, `calculate_excess_profit()`, `calculate_hurdle_price()`.

---

## utils/

```
utils/
├── datetime_utils.py       # safe_days_between, safe_total_seconds_between
├── timezone_manager.py     # TimezoneManager — parse timezone-aware datetimes
└── type_safety_fixes.py    # safe_int_conversion, safe_float_conversion
```

---

## frontend_app/

Next.js 16 App Router. TypeScript strict mode.

```
frontend_app/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout: fonts (Manrope + Noto Sans), PWA, QueryProvider
│   │   ├── globals.css             # CSS custom properties (design tokens, dark mode)
│   │   ├── manifest.ts             # PWA manifest
│   │   ├── login/page.tsx          # Login page (public)
│   │   └── (app)/                  # Auth-protected route group
│   │       ├── layout.tsx          # App shell: sidebar nav, auth guard
│   │       ├── dashboard/page.tsx  # KPIs + charts
│   │       ├── investors/page.tsx  # Investor list + create
│   │       ├── transactions/page.tsx
│   │       ├── fees/page.tsx       # Preview + apply fees
│   │       ├── reports/page.tsx    # Transaction reports
│   │       ├── backup/page.tsx     # Backup + restore
│   │       └── accounts/page.tsx   # Investor account management
│   ├── components/
│   │   ├── ui/                     # shadcn/ui wrappers
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── confirm-dialog.tsx
│   │   │   ├── input.tsx
│   │   │   ├── select.tsx
│   │   │   ├── states.tsx          # Loading/empty/error state components
│   │   │   └── toast-viewport.tsx
│   │   ├── charts/                 # Recharts-based chart components
│   │   ├── form/                   # Form helper components
│   │   ├── layout/                 # Sidebar, navigation
│   │   └── pwa/sw-register.tsx     # Service worker registration
│   ├── lib/
│   │   ├── types.ts                # All TypeScript DTO types
│   │   ├── api.ts                  # Main API client (apiClient object)
│   │   ├── auth-api.ts             # Auth-specific API (no auth required)
│   │   ├── api-base.ts             # URL builders
│   │   ├── network-error.ts        # Network error formatting
│   │   ├── query-keys.ts           # TanStack Query key constants
│   │   ├── utils.ts                # cn() (clsx + tailwind-merge)
│   │   ├── number-input.ts         # VND number input formatting
│   │   └── theme.ts                # Theme boot script (prevents FOUC)
│   ├── providers/
│   │   └── query-provider.tsx      # TanStack Query provider
│   └── store/
│       └── auth-store.ts           # Zustand store (persisted to localStorage)
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

**Điểm quan trọng:**
- Auth state (access token, refresh token, user info) lưu trong `localStorage` qua Zustand `persist`.
- API requests dùng `fetch` với auto-refresh token khi nhận 401.
- TanStack Query dùng cho tất cả server state, không dùng React Server Components.
- Không có error boundary component — lỗi runtime sẽ crash toàn bộ page.

---

## scripts/

```
scripts/
├── migrate_drive_latest_to_postgres.py    # Import .xlsx backup vào PostgreSQL
├── backfill_investor_contact_address.py   # Backfill address fields cho existing investors
├── encode_oauth_token.py                  # Encode token.pickle → base64 string cho env var
├── verify_timezone.py                     # Kiểm tra timezone consistency
├── railway_bootstrap_postgres_once.ps1    # PowerShell: one-time bootstrap CSV → PostgreSQL
└── start_new_stack.ps1                    # PowerShell: khởi động local dev stack
```

---

## tests/

```
tests/
├── test_math_audit.py                    # Unit tests cho fee math calculations
├── test_backend_smoke.py                 # Smoke tests với SQLite in-memory
├── test_fees_config.py                   # Fee config API tests
├── test_investor_accounts_portal.py      # Investor portal tests
├── test_investor_contact_and_locations.py
└── test_reports_transactions.py
```

Tests dùng SQLite in-memory database. **Không có tests trong `backend_api/app/` directory.**

---

## Key Files (Quick Reference)

| File | Vai trò |
|------|---------|
| `config.py` | Constants: `HURDLE_RATE_ANNUAL=0.06`, `PERFORMANCE_FEE_RATE=0.20`, `DEFAULT_UNIT_PRICE=10000.0` |
| `core/services_enhanced.py` | God class ~2200 lines — tất cả business logic |
| `backend_api/app/services/fund_runtime.py` | Thread-safe wrapper, singleton |
| `backend_api/app/core/config.py` | Env vars với prefix `API_` |
| `backend_api/app/core/security.py` | JWT + password hashing |
| `frontend_app/src/store/auth-store.ts` | Auth state in localStorage |
| `frontend_app/src/lib/api.ts` | Tất cả API calls |
| `frontend_app/src/lib/types.ts` | Tất cả TypeScript types |
