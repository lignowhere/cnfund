# CNFund Cutover And Rollback Playbook

This playbook defines release steps from Streamlit UI to the new Next.js frontend.

## Cutover prerequisites

- Backend API and frontend passed:
  - `npm run lint`
  - `npm run build`
  - `npm run test:e2e`
  - `python -m compileall backend_api/app`
- Internal UAT score >= 4.2/5 for current phase.
- Feature flags verified in target environment.

## Feature flags (backend env)

- `API_FEATURE_TABLE_VIEW`
- `API_FEATURE_BACKUP_RESTORE`
- `API_FEATURE_FEE_SAFETY`
- `API_FEATURE_TRANSACTIONS_LOAD_MORE`

## Deployment order

1. Deploy backend API (Railway).
2. Validate health and OpenAPI.
3. Deploy frontend (Vercel).
4. Smoke test critical paths on mobile + desktop.
5. Route internal users to new frontend by default.
6. Keep Streamlit as read-only fallback for 1 week.

## Smoke checklist (release gate)

1. Login and refresh token flow works.
2. Create investor works.
3. Add transaction (deposit/withdraw/nav_update) works.
4. Fee preview/apply works with safety controls.
5. Backup manual + restore confirmation works.
6. Reports page loads (transaction + investor report).

## Rollback (<15 minutes)

1. Switch users back to Streamlit URL immediately.
2. Keep backend API running (no schema rollback required).
3. Disable risky flags if needed:
   - `API_FEATURE_BACKUP_RESTORE=false`
   - `API_FEATURE_FEE_SAFETY=true` (keep on)
4. Investigate issue using:
   - API audit logs table
   - Railway logs
   - Vercel logs
5. Fix in hotpatch branch and redeploy.

## Decommission checklist (post-stability)

1. No blocker defects for 7 consecutive days.
2. All core workflows executed only on new frontend.
3. Streamlit routes disabled for end users.
4. Keep Python core services and data handlers for API runtime.
