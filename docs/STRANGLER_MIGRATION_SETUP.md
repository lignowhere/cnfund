# CNFund Strangler Migration Setup

Run new frontend + new backend API in parallel with existing Streamlit UI.

## 1. Install dependencies

From repo root:

```powershell
.\.venv\Scripts\python -m pip install -r backend_api/requirements.txt
cd frontend_app
npm install
cd ..
```

Optional for e2e:

```powershell
cd frontend_app
npx playwright install
cd ..
```

## 2. Configure environment

Backend:

```powershell
Copy-Item backend_api/.env.example .env -Force
```

Frontend:

```powershell
Copy-Item frontend_app/.env.example frontend_app/.env.local -Force
```

Default local URLs:

- API: `http://127.0.0.1:8001`
- Frontend: `http://localhost:3000`

## 3. Start backend API

```powershell
.\.venv\Scripts\python -m uvicorn backend_api.app.main:app --reload --host 127.0.0.1 --port 8001
```

Or run both backend + frontend automatically:

```powershell
.\scripts\start_new_stack.ps1 -InstallDeps
```

Default seeded admin:

- Username: `admin`
- Password: `1997`

## 4. Start frontend app

Open another terminal:

```powershell
cd frontend_app
npm run dev
```

## 5. Open and verify

- Frontend: `http://localhost:3000/login`
- Swagger: `http://127.0.0.1:8001/docs`
- Health: `http://127.0.0.1:8001/health`

Quick mobile-first checklist:

- Login -> Dashboard loads KPI cards.
- Transactions add NAV update.
- Fees preview/apply requires safety acknowledgements.
- Backup restore requires typing `RESTORE`.
- Reports page opens from drawer.

## 6. Run regression checks

```powershell
.\.venv\Scripts\python -m compileall backend_api/app
cd frontend_app
npm run lint
npm run build
npm run test:e2e
cd ..
```

## 7. Keep Streamlit in parallel

Old UI still runs for side-by-side comparison:

```powershell
streamlit run app.py
```

This supports strangler rollout and quick rollback if needed.

## 8. Demo data

Project includes cleaned demo dataset (Vietnamese UTF-8, non-E2E noise):

- `data/*.csv`
- `backend_api/data/*.csv`

If your local run modifies demo data, copy root dataset back:

```powershell
Copy-Item data\\*.csv backend_api\\data -Force
```
