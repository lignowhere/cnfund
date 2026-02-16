from fastapi import APIRouter, Depends

from ...api.deps import require_read_access
from ...core.config import get_settings
from ...schemas.common import ApiResponse
from ...schemas.system import FeatureFlagsDTO


router = APIRouter()
settings = get_settings()


@router.get("/feature-flags", response_model=ApiResponse[FeatureFlagsDTO])
def feature_flags(_user=Depends(require_read_access)):
    return ApiResponse(
        data=FeatureFlagsDTO(
            table_view=settings.feature_table_view,
            backup_restore=settings.feature_backup_restore,
            fee_safety=settings.feature_fee_safety,
            transactions_load_more=settings.feature_transactions_load_more,
        )
    )

