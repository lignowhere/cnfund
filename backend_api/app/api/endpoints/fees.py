import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ...api.deps import require_mutate_access, require_read_access
from ...schemas.common import ApiResponse
from ...schemas.fees import (
    FeeApplyRequest,
    FeePreviewBundleDTO,
    FeePreviewDTO,
    FeePreviewRequest,
    FeePreviewSummaryDTO,
    FeeRecordDTO,
)
from ...services.fund_runtime import runtime
from ...services.mappers import fee_record_to_dto


router = APIRouter()


def _build_preview(manager, end_date, total_nav: float) -> list[FeePreviewDTO]:
    previews: list[FeePreviewDTO] = []
    for inv in manager.get_regular_investors():
        result = manager.calculate_performance_fee(
            inv.id,
            end_date,
            end_date,
            total_nav,
        )
        fee_amount = float(result.get("fee", 0.0))
        excess_profit = float(result.get("excess_profit", 0.0))
        units = fee_amount / total_nav if total_nav > 0 else 0.0
        rate = (fee_amount / excess_profit * 100) if excess_profit > 0 else 0.0
        previews.append(
            FeePreviewDTO(
                investor_id=inv.id,
                investor_name=inv.name,
                fee_amount=fee_amount,
                fee_rate_percent=rate,
                units_to_transfer=units,
                excess_profit=excess_profit,
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
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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
