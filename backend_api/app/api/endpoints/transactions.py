from fastapi import APIRouter, Depends, HTTPException, Query

from ...api.deps import require_mutate_access, require_read_access
from ...schemas.common import ApiResponse, PaginatedResponse
from ...schemas.transactions import (
    TransactionCardDTO,
    TransactionCreateRequest,
    TransactionDTO,
)
from ...services.fund_runtime import runtime
from ...services.mappers import transaction_to_card_dto, transaction_to_dto


router = APIRouter()


def _investor_name_map(manager) -> dict[int, str]:
    names = {0: "Fund Manager"}
    for inv in manager.investors:
        names[inv.id] = inv.name
    return names


@router.get("", response_model=ApiResponse[PaginatedResponse[TransactionDTO]])
def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    _user=Depends(require_read_access),
):
    def _read(manager):
        name_map = _investor_name_map(manager)
        all_txs = sorted(
            manager.transactions,
            key=lambda tx: (tx.date, tx.id),
            reverse=True,
        )
        start = (page - 1) * page_size
        end = start + page_size
        items = [
            transaction_to_dto(tx, name_map.get(tx.investor_id, f"Investor {tx.investor_id}"))
            for tx in all_txs[start:end]
        ]
        return PaginatedResponse(items=items, total=len(all_txs), page=page, page_size=page_size)

    return ApiResponse(data=runtime.read(_read))


@router.get("/cards", response_model=ApiResponse[PaginatedResponse[TransactionCardDTO]])
def list_transaction_cards(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    _user=Depends(require_read_access),
):
    def _read(manager):
        name_map = _investor_name_map(manager)
        all_txs = sorted(
            manager.transactions,
            key=lambda tx: (tx.date, tx.id),
            reverse=True,
        )
        start = (page - 1) * page_size
        end = start + page_size
        items = [
            transaction_to_card_dto(tx, name_map.get(tx.investor_id, f"Investor {tx.investor_id}"))
            for tx in all_txs[start:end]
        ]
        return PaginatedResponse(items=items, total=len(all_txs), page=page, page_size=page_size)

    return ApiResponse(data=runtime.read(_read))


@router.post("", response_model=ApiResponse[dict])
def create_transaction(payload: TransactionCreateRequest, _user=Depends(require_mutate_access)):
    def _write(manager):
        tx_date = runtime.as_datetime(payload.transaction_date)
        tx_type = payload.transaction_type

        if tx_type == "nav_update":
            ok, message = manager.process_nav_update(payload.total_nav, tx_date)
            if not ok:
                raise HTTPException(status_code=400, detail=message)
            return {"success": True, "message": message}

        if payload.investor_id is None:
            raise HTTPException(status_code=422, detail="investor_id is required")
        if payload.amount is None:
            raise HTTPException(status_code=422, detail="amount is required")

        if tx_type == "deposit":
            ok, message = manager.process_deposit(
                payload.investor_id,
                payload.amount,
                payload.total_nav,
                tx_date,
            )
        elif tx_type == "withdraw":
            ok, message = manager.process_withdrawal(
                payload.investor_id,
                payload.amount,
                payload.total_nav,
                tx_date,
            )
        else:
            raise HTTPException(status_code=422, detail="Unsupported transaction type")

        if not ok:
            raise HTTPException(status_code=400, detail=message)
        return {"success": True, "message": message}

    return ApiResponse(message="Transaction processed", data=runtime.mutate(_write))


@router.delete("/{transaction_id}", response_model=ApiResponse[dict])
def delete_transaction(transaction_id: int, _user=Depends(require_mutate_access)):
    def _write(manager):
        ok = manager.delete_transaction(transaction_id)
        if not ok:
            raise HTTPException(status_code=400, detail="Delete failed")
        return {"deleted": True, "transaction_id": transaction_id}

    return ApiResponse(message="Transaction deleted", data=runtime.mutate(_write))


@router.post("/{transaction_id}/undo", response_model=ApiResponse[dict])
def undo_transaction(transaction_id: int, _user=Depends(require_mutate_access)):
    def _write(manager):
        ok = manager.undo_last_transaction(transaction_id)
        if not ok:
            raise HTTPException(status_code=400, detail="Undo failed")
        return {"undone": True, "transaction_id": transaction_id}

    return ApiResponse(message="Transaction undone", data=runtime.mutate(_write))

