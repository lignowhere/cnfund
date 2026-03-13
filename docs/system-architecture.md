# System Architecture

_Last updated: 2026-03-13_

---

## 1. Deployment Topology

```
┌──────────────────────────────────────────────────────────────┐
│                        Internet                              │
└──────────┬───────────────────────────────┬───────────────────┘
           │                               │
    ┌──────▼──────┐                 ┌──────▼──────┐
    │   Vercel    │                 │   Railway   │
    │  (Frontend) │                 │  (Backend)  │
    │             │                 │             │
    │ Next.js 16  │◄───── HTTPS ───►│  FastAPI    │
    │ TypeScript  │   /api/v1/*     │  Python 3.11│
    │ Port: 443   │                 │  Port: 8001 │
    └─────────────┘                 └──────┬──────┘
                                           │ SQLAlchemy
                                    ┌──────▼──────┐
                                    │   Railway   │
                                    │ PostgreSQL  │
                                    │  Port: 5432 │
                                    └─────────────┘
                                           │
                                    ┌──────▼──────┐
                                    │ Google Drive│
                                    │  (Backup)   │
                                    └─────────────┘
```

---

## 2. Internal Architecture

### Backend Layer Diagram

```
HTTP Request
     │
     ▼
FastAPI CORS Middleware
     │
     ▼
Audit Middleware (log every request to audit_logs table)
     │
     ▼
API Router (/api/v1)
     │
     ├── /auth/*       → auth.py endpoints
     ├── /investors/*  → investors.py endpoints
     ├── /transactions/* → transactions.py endpoints
     ├── /nav/*        → nav.py endpoints
     ├── /fees/*       → fees.py endpoints
     ├── /reports/*    → reports.py endpoints
     ├── /backups/*    → backups.py endpoints
     ├── /accounts/*   → accounts.py endpoints
     └── /system/*     → system.py endpoints
                │
                ▼
        Dependency Injection (deps.py)
        get_current_user → decode JWT → lookup User in DB
        require_read_access / require_mutate_access / require_admin_access
                │
                ▼
        ┌───────────────────────────────────┐
        │         FundRuntime               │
        │  (singleton, thread-safe lock)    │
        │                                   │
        │  runtime.read(callback)           │
        │  runtime.mutate(callback)         │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │      EnhancedFundManager          │
        │  (core/services_enhanced.py)      │
        │                                   │
        │  - investors, tranches,           │
        │  - transactions, fee_records      │
        │  - fee_global_config              │
        │  - fee_investor_overrides         │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │     PostgresDataHandler           │
        │  (core/postgres_data_handler.py)  │
        │                                   │
        │  fund_investors                   │
        │  fund_tranches                    │
        │  fund_transactions                │
        │  fund_fee_records                 │
        │  fund_fee_global_config           │
        │  fund_fee_investor_overrides      │
        └───────────────────────────────────┘
```

**Hai loại database access tồn tại song song:**
1. **SQLAlchemy ORM** (auth tables: `users`, `refresh_tokens`, `investor_accounts`, `audit_logs`) — được quản lý bởi `backend_api/app/models/auth.py`
2. **Raw SQL / pandas** (fund tables: `fund_*`) — được quản lý bởi `core/postgres_data_handler.py`

---

## 3. Authentication Flow

```
Client                    Frontend               Backend
  │                           │                     │
  │──── login(user/pass) ────►│                     │
  │                           │─── POST /auth/login ►│
  │                           │                     │ verify password (pbkdf2_sha256)
  │                           │                     │ create access_token (JWT, 30min)
  │                           │                     │ create refresh_token (JWT, 7d)
  │                           │                     │ store refresh token hash in DB
  │                           │◄── {access, refresh} │
  │                           │ store in localStorage│
  │                           │  (Zustand persist)  │
  │                           │                     │
  │ (30 min later)            │                     │
  │──── request ─────────────►│                     │
  │                           │── GET /data + Bearer►│
  │                           │                     │ decode JWT → 401 (expired)
  │                           │◄──── 401 ───────────│
  │                           │                     │
  │                           │─ POST /auth/refresh ►│
  │                           │  {refresh_token}    │ verify JTI not revoked
  │                           │                     │ verify token hash matches DB
  │                           │                     │ revoke old refresh token
  │                           │                     │ issue new token pair
  │                           │◄── new {access, refresh}
  │                           │ retry original request
  │                           │                     │
  │ logout                    │                     │
  │──────────────────────────►│                     │
  │                           │── POST /auth/logout ►│
  │                           │  {refresh_token}    │ revoke_at = now()
  │                           │◄── 200 ─────────────│
  │                           │ clear localStorage  │
```

**Token storage:** Zustand `persist` middleware → `localStorage` key `cnfund-auth`. Cả `access_token` và `refresh_token` được persist.

---

## 4. Data Flow: Transaction (Deposit)

```
User clicks "Nạp vốn"
        │
        ▼
Frontend validates input
POST /api/v1/transactions
{transaction_type: "deposit", investor_id: X, amount: Y, total_nav: Z, transaction_date: "..."}
        │
        ▼
deps.py: require_mutate_access → role must be in {admin, fund_manager}
        │
        ▼
runtime.mutate(callback):
  1. Acquire threading.Lock()
  2. manager.refresh() — reload from PostgreSQL
  3. callback(manager):
     manager.process_deposit(investor_id, amount, total_nav, date)
       → calculate units = amount / price_per_unit
       → create Tranche(entry_nav=current_price, units=units, hwm=current_price)
       → create Transaction(type="deposit", ...)
  4. manager.save_data() → write all fund_* tables back to PostgreSQL
  5. Release lock
        │
        ▼
if API_AUTO_BACKUP_ON_NEW_TRANSACTION=true:
  trigger backup → write Fund_Export_*.xlsx to exports/
  upload to Google Drive (if configured)
        │
        ▼
Return ApiResponse{data: transaction_card}
        │
        ▼
Frontend invalidates TanStack Query caches → refetch dashboard, investor cards
```

---

## 5. API Endpoint Map

| Method | Path | Role Required | Description |
|--------|------|---------------|-------------|
| POST | `/auth/login` | None | Login, returns token pair |
| POST | `/auth/refresh` | None | Refresh tokens |
| POST | `/auth/logout` | None | Revoke refresh token |
| GET | `/auth/me` | Any authenticated | Current user info |
| GET | `/investors` | read | List investors |
| GET | `/investors/cards` | read | Investor cards with portfolio |
| GET | `/investors/cards/paginated` | read | Paginated investor cards |
| POST | `/investors` | mutate | Create investor |
| PUT | `/investors/{id}` | mutate | Update investor |
| GET | `/transactions/cards` | read | Paginated transactions |
| POST | `/transactions` | mutate | Create transaction |
| DELETE | `/transactions/{id}` | mutate | Delete transaction |
| POST | `/transactions/{id}/undo` | mutate | Undo transaction |
| GET | `/nav/history` | read | NAV history |
| GET | `/fees/config` | read | Fee config bundle |
| PATCH | `/fees/config/global` | mutate | Update global fee config |
| PUT | `/fees/config/overrides/{investor_id}` | mutate | Upsert investor fee override |
| DELETE | `/fees/config/overrides/{investor_id}` | mutate | Delete investor fee override |
| POST | `/fees/preview` | read | Preview fee calculation |
| POST | `/fees/apply` | mutate | Apply year-end fees |
| GET | `/fees/history` | read | Fee application history |
| GET | `/reports/dashboard` | read | Dashboard KPIs + top investors |
| GET | `/reports/investor/{id}` | read | Investor report |
| GET | `/reports/me` | investor | Own investor report |
| GET | `/reports/transactions` | read | Transactions report |
| GET | `/reports/me/transactions` | investor | Own transactions |
| GET | `/reports/transactions/export` | read | Export CSV/PDF |
| GET | `/backups` | read | List backups |
| POST | `/backups/manual` | mutate | Create manual backup |
| POST | `/backups/restore` | mutate | Restore from backup |
| GET | `/accounts/investors` | admin | List investor accounts |
| POST | `/accounts/investors` | admin | Create investor account |
| PATCH | `/accounts/investors/{id}` | admin | Update investor account |
| POST | `/accounts/investors/{id}/reset-password` | admin | Reset password |
| GET | `/system/feature-flags` | read | Feature flags |
| GET | `/system/locations/provinces` | read | Province catalog |
| GET | `/system/locations/wards` | read | Ward catalog by province |
| GET | `/health` | None | Health check |

---

## 6. Database Schema

### Auth Tables (SQLAlchemy managed)

```sql
users (id, username, password_hash, role, is_active, created_at)
refresh_tokens (id, user_id→users, jti, token_hash, expires_at, revoked_at, created_at)
investor_accounts (id, user_id→users, investor_id, created_at)
audit_logs (id, username, action, method, path, status_code, details, created_at)
```

### Fund Tables (postgres_data_handler managed)

```sql
fund_investors (id, name, phone, email, address, province_code, province_name,
               ward_code, ward_name, address_line, join_date, is_fund_manager)

fund_tranches (investor_id, tranche_id, entry_date, entry_nav, units,
              original_invested_value, hwm, original_entry_date,
              original_entry_nav, cumulative_fees_paid)

fund_transactions (id, investor_id, type, amount, total_nav, units_change,
                  transaction_date, description)

fund_fee_records (id, period, investor_id, fee_amount, fee_units,
                 calculation_date, description)

fund_fee_global_config (id, data JSONB)
fund_fee_investor_overrides (investor_id, data JSONB)
```

---

## 7. Frontend Architecture

```
app/layout.tsx              ← Root: fonts, QueryProvider, PWA
  │
  ├── app/login/page.tsx    ← Public, redirects to / if logged in
  │
  └── app/(app)/layout.tsx  ← Auth guard + App shell (sidebar)
        │
        ├── dashboard/page.tsx
        ├── investors/page.tsx
        ├── transactions/page.tsx
        ├── fees/page.tsx
        ├── reports/page.tsx
        ├── backup/page.tsx
        └── accounts/page.tsx
```

**State layers:**
- `useAuthStore` (Zustand, persisted) → tokens + user info
- TanStack Query → server data cache per-page
- `useState` → local form/UI state
