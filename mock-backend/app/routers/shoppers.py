from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/shoppers", tags=["shoppers"])


@router.get("/", response_model=List[schemas.ShopperOut])
async def list_shoppers(
    skip: int = 0,
    limit: int = 100,
    loyalty_tier: Optional[str] = None,
    allergy: Optional[str] = None,
    communication_preference: Optional[str] = None,
    marketing_opt_in: Optional[bool] = None,
    min_budget: Optional[float] = None,
    max_budget: Optional[float] = None,
    state: Optional[str] = None,
    style: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
    db: AsyncSession = Depends(get_db),
):
    return await crud.filter_shoppers(
        db,
        skip=skip,
        limit=limit,
        loyalty_tier=loyalty_tier,
        allergy=allergy,
        communication_preference=communication_preference,
        marketing_opt_in=marketing_opt_in,
        min_budget=min_budget,
        max_budget=max_budget,
        state=state,
        style=style,
        sort_by=sort_by,
        order=order,
    )


@router.get("/{shopper_id}", response_model=schemas.ShopperDetailOut)
async def get_shopper(shopper_id: int, db: AsyncSession = Depends(get_db)):
    shopper = await crud.get_shopper(db, shopper_id)
    if not shopper:
        raise HTTPException(status_code=404, detail="Shopper not found")
    return shopper


@router.get("/by-customer-id/{customer_id}", response_model=schemas.ShopperDetailOut)
async def get_shopper_by_customer_id(customer_id: str, db: AsyncSession = Depends(get_db)):
    shopper = await crud.get_shopper_by_customer_id(db, customer_id)
    if not shopper:
        raise HTTPException(status_code=404, detail="Shopper not found")
    return shopper


@router.get("/by-name/{name}", response_model=schemas.ShopperDetailOut)
async def get_shopper_by_name(name: str, db: AsyncSession = Depends(get_db)):
    shopper = await crud.get_shopper_by_name(db, name)
    if not shopper:
        raise HTTPException(status_code=404, detail="Shopper not found")
    return shopper


@router.get("/search/", response_model=List[schemas.ShopperOut])
async def search_shoppers(q: str, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.search_shoppers(db, q, skip=skip, limit=limit)


@router.post("/", response_model=schemas.ShopperOut, status_code=201)
async def create_shopper(payload: schemas.ShopperCreate, db: AsyncSession = Depends(get_db)):
    shopper = models.Shopper(
        customer_id=payload.customer_id,
        name=payload.name,
        age=payload.age,
        gender=payload.gender,
        email=payload.email,
        phone=payload.phone,
        ring_size=payload.ring_size,
        birthstone=payload.birthstone,
        anniversary=payload.anniversary,
        partner_name=payload.partner_name,
        loyalty_tier=payload.loyalty_tier,
        lifetime_spend_usd=payload.lifetime_spend_usd,
        communication_preference=payload.communication_preference,
        marketing_opt_in=payload.marketing_opt_in,
        notes=payload.notes,
    )
    await crud.create(db, shopper)

    if payload.address:
        db.add(
            models.ShopperAddress(
                shopper_id=shopper.id,
                street=payload.address.street,
                city=payload.address.city,
                state=payload.address.state,
                zip=payload.address.zip,
                country=payload.address.country,
            )
        )

    if payload.preferences:
        db.add(
            models.ShopperPreferences(
                shopper_id=shopper.id,
                style=payload.preferences.style,
                ethical_only=payload.preferences.ethical_only,
                budget_min=payload.preferences.budget_min,
                budget_max=payload.preferences.budget_max,
            )
        )
        for metal in payload.preference_metals:
            db.add(models.ShopperPreferenceMetal(shopper_id=shopper.id, metal=metal))
        for gem in payload.preference_gemstones:
            db.add(models.ShopperPreferenceGemstone(shopper_id=shopper.id, gemstone=gem))
        for avoid in payload.preference_avoids:
            db.add(models.ShopperPreferenceAvoid(shopper_id=shopper.id, avoid=avoid))
        if payload.diamond_specs:
            db.add(
                models.ShopperDiamondSpec(
                    shopper_id=shopper.id,
                    cut=payload.diamond_specs.cut,
                    min_carat=payload.diamond_specs.min_carat,
                    min_clarity=payload.diamond_specs.min_clarity,
                    min_color=payload.diamond_specs.min_color,
                )
            )

    for allergy in payload.allergies:
        db.add(models.ShopperAllergy(shopper_id=shopper.id, allergy=allergy))

    for ph in payload.purchase_history:
        db.add(
            models.ShopperPurchaseHistory(
                shopper_id=shopper.id,
                date=ph.date,
                item=ph.item,
                price_usd=ph.price_usd,
            )
        )

    await db.commit()
    await db.refresh(shopper)
    return shopper


@router.put("/{shopper_id}", response_model=schemas.ShopperOut)
async def update_shopper(
    shopper_id: int, payload: schemas.ShopperUpdate, db: AsyncSession = Depends(get_db)
):
    shopper = await crud.get_shopper(db, shopper_id)
    if not shopper:
        raise HTTPException(status_code=404, detail="Shopper not found")
    update_data = payload.model_dump(exclude_unset=True)
    return await crud.update_shopper(db, shopper, update_data)


@router.delete("/{shopper_id}", status_code=204)
async def delete_shopper(shopper_id: int, db: AsyncSession = Depends(get_db)):
    shopper = await crud.get_by_id(db, models.Shopper, shopper_id)
    if not shopper:
        raise HTTPException(status_code=404, detail="Shopper not found")
    await crud.delete(db, shopper)
