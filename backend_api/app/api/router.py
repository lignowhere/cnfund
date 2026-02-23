from fastapi import APIRouter

from .endpoints import accounts, auth, backups, fees, investors, nav, reports, system, transactions


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(investors.router, prefix="/investors", tags=["investors"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(nav.router, prefix="/nav", tags=["nav"])
api_router.include_router(fees.router, prefix="/fees", tags=["fees"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(backups.router, prefix="/backups", tags=["backups"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
