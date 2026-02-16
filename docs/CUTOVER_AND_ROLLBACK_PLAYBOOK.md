# CNFund Cutover And Rollback Playbook

Playbook cho release pipeline hiện tại: Next.js + FastAPI + PostgreSQL.

## Cutover prerequisites

- Frontend passed:
  - `cd frontend_app`
  - `npm run lint`
  - `npm run build`
- Backend passed:
  - `.\.venv\Scripts\python -m compileall backend_api/app`
  - `.\.venv\Scripts\python -m pytest tests/test_math_audit.py`
  - `.\.venv\Scripts\python -m pytest tests/test_backend_smoke.py`
- UAT nội bộ đạt ngưỡng.

## Feature flags (backend env)

- `API_FEATURE_TABLE_VIEW`
- `API_FEATURE_BACKUP_RESTORE`
- `API_FEATURE_FEE_SAFETY`
- `API_FEATURE_TRANSACTIONS_LOAD_MORE`
- `API_AUTO_BACKUP_ON_NEW_TRANSACTION`

## Deployment order

1. Deploy backend API (Railway).
2. Verify `/health` và `/docs`.
3. Deploy frontend (Vercel).
4. Smoke test mobile + desktop các luồng chính.
5. Mở traffic production sang frontend mới.

## Smoke checklist (release gate)

1. Login + refresh token hoạt động.
2. Create investor hoạt động.
3. Add transaction (deposit/withdraw/nav_update) hoạt động.
4. Fee preview/apply hoạt động với safety controls.
5. Backup manual + restore confirmation hoạt động.
6. Reports page load ổn định.

## Rollback (<15 minutes)

1. Rollback frontend về deployment trước trên Vercel.
2. Nếu cần, rollback backend về deployment trước trên Railway.
3. Tạm tắt các flag rủi ro cao:
   - `API_FEATURE_BACKUP_RESTORE=false`
   - giữ `API_FEATURE_FEE_SAFETY=true`
4. Điều tra qua:
   - API audit logs
   - Railway logs
   - Vercel logs
5. Fix ở hotpatch branch và redeploy.

## Post-release stability checklist

1. Không có blocker defect trong 7 ngày liên tiếp.
2. Backup/restore drill pass.
3. Mọi workflow cốt lõi chạy ổn định trên stack mới.
