from fastapi import APIRouter, Depends, Query

from ...api.deps import require_read_access
from ...core.config import get_settings
from ...schemas.common import ApiResponse
from ...schemas.system import FeatureFlagsDTO, LocationProvinceDTO, LocationWardDTO
from ...services.location_catalog import get_provinces, get_wards


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


@router.get("/locations/provinces", response_model=ApiResponse[list[LocationProvinceDTO]])
def location_provinces(_user=Depends(require_read_access)):
    return ApiResponse(data=[LocationProvinceDTO(**row) for row in get_provinces()])


@router.get("/locations/wards", response_model=ApiResponse[list[LocationWardDTO]])
def location_wards(
    province_code: str = Query(min_length=1),
    _user=Depends(require_read_access),
):
    return ApiResponse(
        data=[LocationWardDTO(**row) for row in get_wards(province_code)]
    )
