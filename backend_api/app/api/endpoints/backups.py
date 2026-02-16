from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.deps import require_mutate_access, require_read_access
from ...schemas.backups import BackupListItemDTO, RestoreBackupRequest
from ...schemas.common import ApiResponse
from ...services.fund_runtime import runtime
from ...services.backup_service import (
    list_local_backups,
    restore_from_local_backup,
    trigger_manual_backup,
)


router = APIRouter()


@router.get("", response_model=ApiResponse[list[BackupListItemDTO]])
def list_backups(days: int = Query(default=30, ge=1, le=365), _user=Depends(require_read_access)):
    def _read(_manager):
        items = list_local_backups(days=days)
        return [
            BackupListItemDTO(
                backup_id=str(row.get("backup_id", "")),
                backup_type=str(row.get("backup_type", "unknown")),
                created_at=str(row.get("created_at", "")),
                metadata=row,
            )
            for row in items
        ]

    return ApiResponse(data=runtime.read(_read))


@router.post("/manual", response_model=ApiResponse[dict])
def create_manual_backup(_user=Depends(require_mutate_access)):
    def _write(manager):
        backup = trigger_manual_backup(manager, description="api_manual")
        return {"backup_id": backup["backup_id"], "created_at": backup["created_at"]}

    return ApiResponse(message="Manual backup created", data=runtime.mutate(_write))


@router.post("/restore", response_model=ApiResponse[dict])
def restore_backup(payload: RestoreBackupRequest, _user=Depends(require_mutate_access)):
    def _write(manager):
        if payload.confirm_phrase.strip().upper() != "RESTORE":
            raise HTTPException(status_code=400, detail="Invalid restore confirmation phrase")
        try:
            result = restore_from_local_backup(
                manager,
                payload.backup_id,
                create_safety_backup=payload.create_safety_backup,
            )
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Restore failed: {exc}") from exc
        return result

    return ApiResponse(message="Backup restored", data=runtime.mutate(_write))
