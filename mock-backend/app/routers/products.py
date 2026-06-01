from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[schemas.ProductOut])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    metal: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    ethically_sourced: Optional[bool] = None,
    gemstone: Optional[str] = None,
    in_stock_min: Optional[int] = None,
    in_stock_max: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    db: AsyncSession = Depends(get_db),
):
    return await crud.filter_products(
        db,
        skip=skip,
        limit=limit,
        category=category,
        metal=metal,
        min_price=min_price,
        max_price=max_price,
        ethically_sourced=ethically_sourced,
        gemstone=gemstone,
        in_stock_min=in_stock_min,
        in_stock_max=in_stock_max,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{product_id}", response_model=schemas.ProductDetailOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    prod = await crud.get_product(db, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod


@router.get("/by-product-id/{product_id}", response_model=schemas.ProductDetailOut)
async def get_product_by_product_id(product_id: str, db: AsyncSession = Depends(get_db)):
    prod = await crud.get_product_by_product_id(db, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod


@router.get("/by-name/{name}", response_model=schemas.ProductDetailOut)
async def get_product_by_name(name: str, db: AsyncSession = Depends(get_db)):
    prod = await crud.get_product_by_name(db, name)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod


@router.get("/search/", response_model=List[schemas.ProductOut])
async def search_products(q: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.search_products(db, q, skip=skip, limit=limit)


@router.post("/", response_model=schemas.ProductOut, status_code=201)
async def create_product(payload: schemas.ProductCreate, db: AsyncSession = Depends(get_db)):
    prod = models.Product(
        product_id=payload.product_id,
        name=payload.name,
        category=payload.category,
        collection=payload.collection,
        metal=payload.metal,
        price_usd=payload.price_usd,
        weight_grams=payload.weight_grams,
        in_stock=payload.in_stock,
        ethically_sourced=payload.ethically_sourced,
        description=payload.description,
    )
    await crud.create(db, prod)
    for gem in payload.gemstones:
        db.add(models.ProductGemstone(product_id=prod.id, gemstone=gem))
    await db.commit()
    await db.refresh(prod)
    return prod


@router.put("/{product_id}", response_model=schemas.ProductOut)
async def update_product(
    product_id: int, payload: schemas.ProductUpdate, db: AsyncSession = Depends(get_db)
):
    prod = await crud.get_product(db, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    update_data = payload.model_dump(exclude_unset=True)
    return await crud.update_product(db, prod, update_data)


@router.delete("/{product_id}", status_code=204)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    prod = await crud.get_by_id(db, models.Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    await crud.delete(db, prod)
