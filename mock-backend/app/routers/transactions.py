from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/", response_model=List[schemas.TransactionOut])
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    payment_method: Optional[str] = None,
    channel: Optional[str] = None,
    min_discount: Optional[float] = None,
    max_discount: Optional[float] = None,
    date_after: Optional[date] = None,
    date_before: Optional[date] = None,
    customer_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    product_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    db: AsyncSession = Depends(get_db),
):
    return await crud.filter_transactions(
        db,
        skip=skip,
        limit=limit,
        payment_method=payment_method,
        channel=channel,
        min_discount=min_discount,
        max_discount=max_discount,
        date_after=date_after,
        date_before=date_before,
        customer_id=customer_id,
        employee_id=employee_id,
        product_id=product_id,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{transaction_id}", response_model=schemas.TransactionFullOut)
async def get_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    txn = await crud.get_transaction(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.get("/by-transaction-id/{transaction_id}", response_model=schemas.TransactionFullOut)
async def get_transaction_by_transaction_id(transaction_id: str, db: AsyncSession = Depends(get_db)):
    txn = await crud.get_transaction_by_transaction_id(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.get("/search/", response_model=List[schemas.TransactionOut])
async def search_transactions(q: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.search_transactions(db, q, skip=skip, limit=limit)


@router.post("/", response_model=schemas.TransactionOut, status_code=201)
async def create_transaction(payload: schemas.TransactionCreate, db: AsyncSession = Depends(get_db)):
    txn = models.Transaction(
        transaction_id=payload.transaction_id,
        date=payload.date,
        customer_id=payload.customer_id,
        employee_id=payload.employee_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit_price_usd=payload.unit_price_usd,
        discount_pct=payload.discount_pct,
        total_usd=payload.total_usd,
        payment_method=payload.payment_method,
        channel=payload.channel,
        notes=payload.notes,
    )
    return await crud.create(db, txn)


@router.put("/{transaction_id}", response_model=schemas.TransactionOut)
async def update_transaction(
    transaction_id: int, payload: schemas.TransactionUpdate, db: AsyncSession = Depends(get_db)
):
    txn = await crud.get_transaction(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    update_data = payload.model_dump(exclude_unset=True)
    return await crud.update_transaction(db, txn, update_data)


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: int, db: AsyncSession = Depends(get_db)):
    txn = await crud.get_by_id(db, models.Transaction, transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    await crud.delete(db, txn)
