from fastapi import APIRouter, Depends, HTTPException

from ...api.deps import require_mutate_access, require_read_access
from ...schemas.common import ApiResponse
from ...schemas.nav import NavPointDTO, NavUpdateRequest
from ...services.fund_runtime import runtime
from ...services.mappers import nav_point_to_dto


router = APIRouter()


@router.post("/update", response_model=ApiResponse[dict])
def update_nav(payload: NavUpdateRequest, _user=Depends(require_mutate_access)):
    def _write(manager):
        ok, message = manager.process_nav_update(
            payload.total_nav, runtime.as_datetime(payload.transaction_date)
        )
        if not ok:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    return ApiResponse(message="NAV updated", data=runtime.mutate(_write))


@router.get("/history", response_model=ApiResponse[list[NavPointDTO]])
def nav_history(_user=Depends(require_read_access)):
    def _read(manager):
        return [nav_point_to_dto(point) for point in manager.get_nav_history()]

    return ApiResponse(data=runtime.read(_read))

