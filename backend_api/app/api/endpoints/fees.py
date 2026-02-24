import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ...api.deps import require_mutate_access, require_read_access
from ...schemas.common import ApiResponse
from ...schemas.fees import (
    FeeConfigBundleDTO,
    FeeApplyRequest,
    FeeGlobalConfigDTO,
    FeeGlobalConfigUpdateRequest,
    FeeInvestorOverrideDTO,
    FeeInvestorOverrideUpsertRequest,
    FeePreviewBundleDTO,
    FeePreviewDTO,
    FeePreviewRequest,
    FeePreviewSummaryDTO,
    FeeRecordDTO,
)
from ...services.fund_runtime import runtime
from ...services.mappers import fee_record_to_dto


router = APIRouter()


def _to_global_config_dto(payload: dict) -> FeeGlobalConfigDTO:
    return FeeGlobalConfigDTO(
        performance_fee_rate=float(payload.get("performance_fee_rate", 0.0)),
        hurdle_rate_annual=float(payload.get("hurdle_rate_annual", 0.0)),
        updated_at=payload.get("updated_at"),
    )


def _to_override_dto(payload: dict) -> FeeInvestorOverrideDTO:
    return FeeInvestorOverrideDTO(
        investor_id=int(payload["investor_id"]),
        performance_fee_rate=(
            float(payload["performance_fee_rate"])
            if payload.get("performance_fee_rate") is not None
            else None
        ),
        hurdle_rate_annual=(
            float(payload["hurdle_rate_annual"])
            if payload.get("hurdle_rate_annual") is not None
            else None
        ),
        updated_at=payload.get("updated_at"),
    )


def _read_fee_config_bundle(manager) -> FeeConfigBundleDTO:
    bundle = manager.get_fee_config_bundle()
    return FeeConfigBundleDTO(
        global_config=_to_global_config_dto(bundle["global_config"]),
        overrides=[_to_override_dto(item) for item in bundle["overrides"]],
    )


def _build_preview(manager, end_date, total_nav: float) -> list[FeePreviewDTO]:
    previews: list[FeePreviewDTO] = []
    for inv in manager.get_regular_investors():
        result = manager.calculate_performance_fee(
            inv.id,
            end_date,
            end_date,
            total_nav,
        )
        fee_amount = float(result.get("total_fee", result.get("fee", 0.0)))
        excess_profit = float(result.get("excess_profit", 0.0))
        current_price = float(result.get("current_price", 0.0))
        units = float(
            result.get(
                "units_to_transfer",
                (fee_amount / current_price) if current_price > 0 else 0.0,
            )
        )
        rate = (fee_amount / excess_profit * 100) if excess_profit > 0 else 0.0
        resolved_config = manager.resolve_fee_config_for_investor(inv.id)
        previews.append(
            FeePreviewDTO(
                investor_id=inv.id,
                investor_name=inv.name,
                fee_amount=fee_amount,
                fee_rate_percent=rate,
                units_to_transfer=units,
                excess_profit=excess_profit,
                applied_performance_fee_rate=float(
                    result.get("applied_performance_fee_rate", resolved_config["performance_fee_rate"])
                ),
                applied_hurdle_rate=float(
                    result.get("applied_hurdle_rate", resolved_config["hurdle_rate_annual"])
                ),
                fee_source=str(result.get("fee_source", resolved_config["fee_source"])),
            )
        )
    return previews


def _build_confirm_token(manager, end_date, total_nav: float, previews: list[FeePreviewDTO]) -> str:
    tx_count = len(manager.transactions)
    last_tx_id = max([tx.id for tx in manager.transactions], default=0)
    payload = {
        "end_date": str(end_date),
        "total_nav": round(total_nav, 2),
        "total_fee_amount": round(sum(item.fee_amount for item in previews), 2),
        "total_units_to_transfer": round(sum(item.units_to_transfer for item in previews), 6),
        "tx_count": tx_count,
        "last_tx_id": last_tx_id,
        "fee_config_snapshot": manager.get_fee_config_snapshot(),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@router.get("/config", response_model=ApiResponse[FeeConfigBundleDTO])
def get_fee_config(_user=Depends(require_read_access)):
    return ApiResponse(data=runtime.read(_read_fee_config_bundle))


@router.patch("/config/global", response_model=ApiResponse[FeeGlobalConfigDTO])
def update_global_fee_config(
    payload: FeeGlobalConfigUpdateRequest,
    _user=Depends(require_mutate_access),
):
    if payload.performance_fee_rate is None and payload.hurdle_rate_annual is None:
        raise HTTPException(status_code=400, detail="No updates provided")

    def _write(manager):
        updated = manager.update_global_fee_config(
            performance_fee_rate=payload.performance_fee_rate,
            hurdle_rate_annual=payload.hurdle_rate_annual,
        )
        return _to_global_config_dto(updated)

    return ApiResponse(message="Global fee config updated", data=runtime.mutate(_write))


@router.put("/config/overrides/{investor_id}", response_model=ApiResponse[FeeInvestorOverrideDTO])
def upsert_fee_override(
    investor_id: int,
    payload: FeeInvestorOverrideUpsertRequest,
    _user=Depends(require_mutate_access),
):
    if payload.performance_fee_rate is None and payload.hurdle_rate_annual is None:
        raise HTTPException(status_code=400, detail="At least one override value is required")

    def _write(manager):
        investor = manager.get_investor_by_id(investor_id)
        if investor is None or investor.is_fund_manager:
            raise HTTPException(status_code=404, detail="Investor not found")
        updated = manager.upsert_investor_fee_override(
            investor_id,
            performance_fee_rate=payload.performance_fee_rate,
            hurdle_rate_annual=payload.hurdle_rate_annual,
        )
        return _to_override_dto(updated)

    return ApiResponse(message="Investor fee override updated", data=runtime.mutate(_write))


@router.delete("/config/overrides/{investor_id}", response_model=ApiResponse[dict])
def delete_fee_override(
    investor_id: int,
    _user=Depends(require_mutate_access),
):
    def _write(manager):
        deleted = manager.delete_investor_fee_override(investor_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Investor fee override not found")
        return {"deleted": True}

    return ApiResponse(message="Investor fee override deleted", data=runtime.mutate(_write))


@router.post("/preview", response_model=ApiResponse[FeePreviewBundleDTO])
def preview_fees(payload: FeePreviewRequest, _user=Depends(require_read_access)):
    def _read(manager):
        previews = _build_preview(manager, payload.end_date, payload.total_nav)
        summary = FeePreviewSummaryDTO(
            total_fee_amount=sum(item.fee_amount for item in previews),
            total_units_to_transfer=sum(item.units_to_transfer for item in previews),
            investor_count=len(previews),
        )
        token = _build_confirm_token(manager, payload.end_date, payload.total_nav, previews)
        return FeePreviewBundleDTO(
            items=previews,
            summary=summary,
            confirm_token=token,
            generated_at=datetime.utcnow().isoformat(),
        )

    return ApiResponse(data=runtime.read(_read))


@router.post("/apply", response_model=ApiResponse[dict])
def apply_fees(payload: FeeApplyRequest, _user=Depends(require_mutate_access)):
    def _write(manager):
        if not payload.acknowledge_risk or not payload.acknowledge_backup:
            raise HTTPException(status_code=400, detail="Missing safety acknowledgements")

        previews = _build_preview(manager, payload.end_date, payload.total_nav)
        expected_token = _build_confirm_token(manager, payload.end_date, payload.total_nav, previews)
        if payload.confirm_token != expected_token:
            raise HTTPException(
                status_code=409,
                detail="Fee preview token mismatch. Please preview again before applying fees.",
            )

        results = manager.apply_year_end_fees_enhanced(
            runtime.as_datetime(payload.end_date),
            payload.total_nav,
        )
        if not isinstance(results, dict):
            raise HTTPException(status_code=400, detail="Unexpected fee response")
        return results

    return ApiResponse(message="Fees applied", data=runtime.mutate(_write))


@router.get("/history", response_model=ApiResponse[list[FeeRecordDTO]])
def fee_history(_user=Depends(require_read_access)):
    def _read(manager):
        return [fee_record_to_dto(item) for item in manager.get_fee_history()]

    return ApiResponse(data=runtime.read(_read))
