from typing import Any, Optional, TypeVar

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app import models

ModelType = TypeVar("ModelType", bound=models.Base)


# ---------- Generic helpers ----------

async def get_all(
    session: AsyncSession,
    model: type[ModelType],
    skip: int = 0,
    limit: int = 100,
) -> list[ModelType]:
    result = await session.execute(select(model).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_by_id(
    session: AsyncSession, model: type[ModelType], obj_id: int
) -> Optional[ModelType]:
    result = await session.execute(select(model).where(model.id == obj_id))
    return result.scalar_one_or_none()


async def create(session: AsyncSession, obj: ModelType) -> ModelType:
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def delete(session: AsyncSession, obj: ModelType) -> None:
    await session.delete(obj)
    await session.commit()


# ---------- Employees ----------

async def get_employees(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Employee]:
    result = await session.execute(select(models.Employee).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_employee(session: AsyncSession, employee_id: int) -> Optional[models.Employee]:
    result = await session.execute(
        select(models.Employee)
        .where(models.Employee.id == employee_id)
        .options(
            joinedload(models.Employee.address),
            joinedload(models.Employee.languages),
            joinedload(models.Employee.specialties),
            joinedload(models.Employee.emergency_contact),
        )
    )
    return result.scalar_one_or_none()


async def update_employee(
    session: AsyncSession, db_obj: models.Employee, update_data: dict[str, Any]
) -> models.Employee:
    for field, value in update_data.items():
        if value is not None:
            setattr(db_obj, field, value)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


# ---------- Products ----------

async def get_products(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Product]:
    result = await session.execute(select(models.Product).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_product(session: AsyncSession, product_id: int) -> Optional[models.Product]:
    result = await session.execute(
        select(models.Product)
        .where(models.Product.id == product_id)
        .options(joinedload(models.Product.gemstones))
    )
    return result.scalar_one_or_none()


async def update_product(
    session: AsyncSession, db_obj: models.Product, update_data: dict[str, Any]
) -> models.Product:
    for field, value in update_data.items():
        if value is not None:
            setattr(db_obj, field, value)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


# ---------- Shoppers ----------

async def get_shoppers(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Shopper]:
    result = await session.execute(select(models.Shopper).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_shopper(session: AsyncSession, shopper_id: int) -> Optional[models.Shopper]:
    result = await session.execute(
        select(models.Shopper)
        .where(models.Shopper.id == shopper_id)
        .options(
            joinedload(models.Shopper.address),
            joinedload(models.Shopper.preferences),
            joinedload(models.Shopper.preference_metals),
            joinedload(models.Shopper.preference_gemstones),
            joinedload(models.Shopper.preference_avoids),
            joinedload(models.Shopper.diamond_specs),
            joinedload(models.Shopper.allergies),
            joinedload(models.Shopper.purchase_history),
        )
    )
    return result.scalar_one_or_none()


async def update_shopper(
    session: AsyncSession, db_obj: models.Shopper, update_data: dict[str, Any]
) -> models.Shopper:
    for field, value in update_data.items():
        if value is not None:
            setattr(db_obj, field, value)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


# ---------- Transactions ----------

async def get_transactions(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    result = await session.execute(select(models.Transaction).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_transaction(session: AsyncSession, transaction_id: int) -> Optional[models.Transaction]:
    result = await session.execute(
        select(models.Transaction)
        .where(models.Transaction.id == transaction_id)
        .options(
            joinedload(models.Transaction.shopper),
            joinedload(models.Transaction.employee),
            joinedload(models.Transaction.product),
        )
    )
    return result.scalar_one_or_none()


async def update_transaction(
    session: AsyncSession, db_obj: models.Transaction, update_data: dict[str, Any]
) -> models.Transaction:
    for field, value in update_data.items():
        if value is not None:
            setattr(db_obj, field, value)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


# ---------- Analytics ----------

async def top_customers(session: AsyncSession, limit: int = 10) -> list[Any]:
    stmt = (
        select(
            models.Shopper.id,
            models.Shopper.customer_id,
            models.Shopper.name,
            func.coalesce(func.sum(models.Transaction.total_usd), 0).label("total_spent"),
        )
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .group_by(models.Shopper.id)
        .order_by(func.sum(models.Transaction.total_usd).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def top_employees(session: AsyncSession, limit: int = 10) -> list[Any]:
    stmt = (
        select(
            models.Employee.id,
            models.Employee.employee_id,
            models.Employee.name,
            func.coalesce(func.sum(models.Transaction.total_usd), 0).label("total_sales"),
        )
        .join(models.Transaction, models.Employee.id == models.Transaction.employee_id)
        .group_by(models.Employee.id)
        .order_by(func.sum(models.Transaction.total_usd).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def product_sales(session: AsyncSession, limit: int = 10) -> list[Any]:
    stmt = (
        select(
            models.Product.id,
            models.Product.product_id,
            models.Product.name,
            func.coalesce(func.sum(models.Transaction.quantity), 0).label("total_quantity"),
            func.coalesce(func.sum(models.Transaction.total_usd), 0).label("total_revenue"),
        )
        .join(models.Transaction, models.Product.id == models.Transaction.product_id)
        .group_by(models.Product.id)
        .order_by(func.sum(models.Transaction.total_usd).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def get_full_transactions(session: AsyncSession, skip: int = 0, limit: int = 100) -> list[models.Transaction]:
    result = await session.execute(
        select(models.Transaction)
        .options(
            joinedload(models.Transaction.shopper),
            joinedload(models.Transaction.employee),
            joinedload(models.Transaction.product),
        )
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ---------- Filtering helpers ----------

async def filter_employees(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    hire_date_after: Optional[str] = None,
    hire_date_before: Optional[str] = None,
    state: Optional[str] = None,
    language: Optional[str] = None,
    specialty: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
) -> list[models.Employee]:
    stmt = select(models.Employee)
    if role:
        stmt = stmt.where(models.Employee.role.ilike(f"%{role}%"))
    if hire_date_after:
        stmt = stmt.where(models.Employee.hire_date >= hire_date_after)
    if hire_date_before:
        stmt = stmt.where(models.Employee.hire_date <= hire_date_before)
    if state:
        stmt = stmt.join(models.EmployeeAddress).where(models.EmployeeAddress.state.ilike(f"%{state}%"))
    if language:
        stmt = stmt.join(models.EmployeeLanguage).where(models.EmployeeLanguage.language.ilike(f"%{language}%"))
    if specialty:
        stmt = stmt.join(models.EmployeeSpecialty).where(models.EmployeeSpecialty.specialty.ilike(f"%{specialty}%"))
    if sort_by:
        col = getattr(models.Employee, sort_by, models.Employee.id)
        if order == "desc":
            stmt = stmt.order_by(col.desc())
        else:
            stmt = stmt.order_by(col.asc())
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def filter_products(
    session: AsyncSession,
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
) -> list[models.Product]:
    stmt = select(models.Product)
    if category:
        stmt = stmt.where(models.Product.category.ilike(f"%{category}%"))
    if metal:
        stmt = stmt.where(models.Product.metal.ilike(f"%{metal}%"))
    if min_price is not None:
        stmt = stmt.where(models.Product.price_usd >= min_price)
    if max_price is not None:
        stmt = stmt.where(models.Product.price_usd <= max_price)
    if ethically_sourced is not None:
        stmt = stmt.where(models.Product.ethically_sourced == ethically_sourced)
    if gemstone:
        stmt = stmt.join(models.ProductGemstone).where(models.ProductGemstone.gemstone.ilike(f"%{gemstone}%"))
    if in_stock_min is not None:
        stmt = stmt.where(models.Product.in_stock >= in_stock_min)
    if in_stock_max is not None:
        stmt = stmt.where(models.Product.in_stock <= in_stock_max)
    if sort_by:
        col = getattr(models.Product, sort_by, models.Product.id)
        if order == "desc":
            stmt = stmt.order_by(col.desc())
        else:
            stmt = stmt.order_by(col.asc())
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def filter_shoppers(
    session: AsyncSession,
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
) -> list[models.Shopper]:
    stmt = select(models.Shopper)
    if loyalty_tier:
        stmt = stmt.where(models.Shopper.loyalty_tier.ilike(f"%{loyalty_tier}%"))
    if communication_preference:
        stmt = stmt.where(models.Shopper.communication_preference.ilike(f"%{communication_preference}%"))
    if marketing_opt_in is not None:
        stmt = stmt.where(models.Shopper.marketing_opt_in == marketing_opt_in)
    if state:
        stmt = stmt.join(models.ShopperAddress).where(models.ShopperAddress.state.ilike(f"%{state}%"))
    if style:
        stmt = stmt.join(models.ShopperPreferences).where(models.ShopperPreferences.style.ilike(f"%{style}%"))
    if min_budget is not None:
        stmt = stmt.join(models.ShopperPreferences).where(models.ShopperPreferences.budget_max >= min_budget)
    if max_budget is not None:
        stmt = stmt.join(models.ShopperPreferences).where(models.ShopperPreferences.budget_max <= max_budget)
    if allergy:
        stmt = stmt.join(models.ShopperAllergy).where(models.ShopperAllergy.allergy.ilike(f"%{allergy}%"))
    if sort_by:
        col = getattr(models.Shopper, sort_by, models.Shopper.id)
        if order == "desc":
            stmt = stmt.order_by(col.desc())
        else:
            stmt = stmt.order_by(col.asc())
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def filter_transactions(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    payment_method: Optional[str] = None,
    channel: Optional[str] = None,
    min_discount: Optional[float] = None,
    max_discount: Optional[float] = None,
    date_after: Optional[str] = None,
    date_before: Optional[str] = None,
    customer_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    product_id: Optional[int] = None,
    sort_by: Optional[str] = None,
    order: str = "asc",
) -> list[models.Transaction]:
    stmt = select(models.Transaction)
    if payment_method:
        stmt = stmt.where(models.Transaction.payment_method.ilike(f"%{payment_method}%"))
    if channel:
        stmt = stmt.where(models.Transaction.channel.ilike(f"%{channel}%"))
    if min_discount is not None:
        stmt = stmt.where(models.Transaction.discount_pct >= min_discount)
    if max_discount is not None:
        stmt = stmt.where(models.Transaction.discount_pct <= max_discount)
    if date_after:
        stmt = stmt.where(models.Transaction.date >= date_after)
    if date_before:
        stmt = stmt.where(models.Transaction.date <= date_before)
    if customer_id is not None:
        stmt = stmt.where(models.Transaction.customer_id == customer_id)
    if employee_id is not None:
        stmt = stmt.where(models.Transaction.employee_id == employee_id)
    if product_id is not None:
        stmt = stmt.where(models.Transaction.product_id == product_id)
    if sort_by:
        col = getattr(models.Transaction, sort_by, models.Transaction.id)
        if order == "desc":
            stmt = stmt.order_by(col.desc())
        else:
            stmt = stmt.order_by(col.asc())
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------- Search helpers ----------

async def search_employees(
    session: AsyncSession, q: str, skip: int = 0, limit: int = 100
) -> list[models.Employee]:
    stmt = select(models.Employee).where(
        or_(
            models.Employee.name.ilike(f"%{q}%"),
            models.Employee.notes.ilike(f"%{q}%"),
            models.Employee.email.ilike(f"%{q}%"),
        )
    ).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_products(
    session: AsyncSession, q: str, skip: int = 0, limit: int = 100
) -> list[models.Product]:
    stmt = select(models.Product).where(
        or_(
            models.Product.name.ilike(f"%{q}%"),
            models.Product.description.ilike(f"%{q}%"),
            models.Product.category.ilike(f"%{q}%"),
        )
    ).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_shoppers(
    session: AsyncSession, q: str, skip: int = 0, limit: int = 100
) -> list[models.Shopper]:
    stmt = select(models.Shopper).where(
        or_(
            models.Shopper.name.ilike(f"%{q}%"),
            models.Shopper.notes.ilike(f"%{q}%"),
            models.Shopper.email.ilike(f"%{q}%"),
        )
    ).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def search_transactions(
    session: AsyncSession, q: str, skip: int = 0, limit: int = 100
) -> list[models.Transaction]:
    stmt = select(models.Transaction).where(
        models.Transaction.notes.ilike(f"%{q}%")
    ).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


# ---------- Business key lookups ----------

async def get_employee_by_employee_id(session: AsyncSession, employee_id: str) -> Optional[models.Employee]:
    result = await session.execute(
        select(models.Employee)
        .where(models.Employee.employee_id == employee_id)
        .options(
            joinedload(models.Employee.address),
            joinedload(models.Employee.languages),
            joinedload(models.Employee.specialties),
            joinedload(models.Employee.emergency_contact),
        )
    )
    return result.scalar_one_or_none()


async def get_employee_by_name(session: AsyncSession, name: str) -> Optional[models.Employee]:
    result = await session.execute(
        select(models.Employee)
        .where(models.Employee.name.ilike(name))
        .options(
            joinedload(models.Employee.address),
            joinedload(models.Employee.languages),
            joinedload(models.Employee.specialties),
            joinedload(models.Employee.emergency_contact),
        )
    )
    return result.scalar_one_or_none()


async def get_product_by_product_id(session: AsyncSession, product_id: str) -> Optional[models.Product]:
    result = await session.execute(
        select(models.Product)
        .where(models.Product.product_id == product_id)
        .options(joinedload(models.Product.gemstones))
    )
    return result.scalar_one_or_none()


async def get_product_by_name(session: AsyncSession, name: str) -> Optional[models.Product]:
    result = await session.execute(
        select(models.Product)
        .where(models.Product.name.ilike(name))
        .options(joinedload(models.Product.gemstones))
    )
    return result.scalar_one_or_none()


async def get_shopper_by_customer_id(session: AsyncSession, customer_id: str) -> Optional[models.Shopper]:
    result = await session.execute(
        select(models.Shopper)
        .where(models.Shopper.customer_id == customer_id)
        .options(
            joinedload(models.Shopper.address),
            joinedload(models.Shopper.preferences),
            joinedload(models.Shopper.preference_metals),
            joinedload(models.Shopper.preference_gemstones),
            joinedload(models.Shopper.preference_avoids),
            joinedload(models.Shopper.diamond_specs),
            joinedload(models.Shopper.allergies),
            joinedload(models.Shopper.purchase_history),
        )
    )
    return result.scalar_one_or_none()


async def get_shopper_by_name(session: AsyncSession, name: str) -> Optional[models.Shopper]:
    result = await session.execute(
        select(models.Shopper)
        .where(models.Shopper.name.ilike(name))
        .options(
            joinedload(models.Shopper.address),
            joinedload(models.Shopper.preferences),
            joinedload(models.Shopper.preference_metals),
            joinedload(models.Shopper.preference_gemstones),
            joinedload(models.Shopper.preference_avoids),
            joinedload(models.Shopper.diamond_specs),
            joinedload(models.Shopper.allergies),
            joinedload(models.Shopper.purchase_history),
        )
    )
    return result.scalar_one_or_none()


async def get_transaction_by_transaction_id(session: AsyncSession, transaction_id: str) -> Optional[models.Transaction]:
    result = await session.execute(
        select(models.Transaction)
        .where(models.Transaction.transaction_id == transaction_id)
        .options(
            joinedload(models.Transaction.shopper),
            joinedload(models.Transaction.employee),
            joinedload(models.Transaction.product),
        )
    )
    return result.scalar_one_or_none()


# ---------- Aggregation helpers ----------

async def count_shoppers_by_tier(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Shopper.loyalty_tier, func.count(models.Shopper.id).label("count"))
        .where(models.Shopper.loyalty_tier.isnot(None))
        .group_by(models.Shopper.loyalty_tier)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def average_salary_by_role(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Employee.role, func.avg(models.Employee.salary_usd).label("average"))
        .where(models.Employee.role.isnot(None))
        .group_by(models.Employee.role)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def revenue_by_payment_method(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Transaction.payment_method, func.sum(models.Transaction.total_usd).label("total_revenue"))
        .where(models.Transaction.payment_method.isnot(None))
        .group_by(models.Transaction.payment_method)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def revenue_by_channel(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Transaction.channel, func.sum(models.Transaction.total_usd).label("total_revenue"))
        .where(models.Transaction.channel.isnot(None))
        .group_by(models.Transaction.channel)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def count_products_by_category(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Product.category, func.count(models.Product.id).label("count"))
        .where(models.Product.category.isnot(None))
        .group_by(models.Product.category)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def transaction_count_by_month(session: AsyncSession, year: int) -> list[Any]:
    stmt = (
        select(func.extract("month", models.Transaction.date).label("month"), func.count(models.Transaction.id).label("count"))
        .where(func.extract("year", models.Transaction.date) == year)
        .group_by(func.extract("month", models.Transaction.date))
        .order_by(func.extract("month", models.Transaction.date))
    )
    result = await session.execute(stmt)
    return list(result.all())


async def average_product_price_by_metal(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Product.metal, func.avg(models.Product.price_usd).label("average"))
        .where(models.Product.metal.isnot(None))
        .group_by(models.Product.metal)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def employee_total_revenue(session: AsyncSession) -> list[Any]:
    stmt = (
        select(
            models.Employee.id,
            models.Employee.employee_id,
            models.Employee.name,
            func.coalesce(func.sum(models.Transaction.total_usd), 0).label("total_revenue"),
        )
        .join(models.Transaction, models.Employee.id == models.Transaction.employee_id)
        .group_by(models.Employee.id)
        .order_by(func.sum(models.Transaction.total_usd).desc())
    )
    result = await session.execute(stmt)
    return list(result.all())


async def employee_transaction_counts(session: AsyncSession, year: Optional[int] = None) -> list[Any]:
    stmt = select(models.Employee.id, models.Employee.employee_id, models.Employee.name, func.count(models.Transaction.id).label("txn_count"))
    stmt = stmt.join(models.Transaction, models.Employee.id == models.Transaction.employee_id)
    if year:
        stmt = stmt.where(func.extract("year", models.Transaction.date) == year)
    stmt = stmt.group_by(models.Employee.id)
    result = await session.execute(stmt)
    return list(result.all())


async def customer_metal_preference_match(session: AsyncSession) -> list[Any]:
    stmt = (
        select(models.Shopper.id, models.Shopper.customer_id, models.Shopper.name)
        .join(models.ShopperPreferenceMetal, models.Shopper.id == models.ShopperPreferenceMetal.shopper_id)
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .join(models.Product, models.Transaction.product_id == models.Product.id)
        .where(models.ShopperPreferenceMetal.metal.ilike(models.Product.metal))
        .distinct()
    )
    result = await session.execute(stmt)
    return list(result.all())


async def validate_lifetime_spend(session: AsyncSession) -> list[Any]:
    stmt = (
        select(
            models.Shopper.id,
            models.Shopper.customer_id,
            models.Shopper.name,
            models.Shopper.lifetime_spend_usd.label("lifetime_spend"),
            func.coalesce(func.sum(models.ShopperPurchaseHistory.price_usd), 0).label("purchase_history_sum"),
        )
        .join(models.ShopperPurchaseHistory, models.Shopper.id == models.ShopperPurchaseHistory.shopper_id)
        .group_by(models.Shopper.id)
        .having(models.Shopper.lifetime_spend_usd != func.coalesce(func.sum(models.ShopperPurchaseHistory.price_usd), 0))
    )
    result = await session.execute(stmt)
    return list(result.all())


async def validate_transaction_totals(session: AsyncSession) -> list[Any]:
    stmt = select(models.Transaction)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def most_frequent_customer_employee_pair(session: AsyncSession) -> list[Any]:
    stmt = (
        select(
            models.Shopper.customer_id,
            models.Shopper.name.label("customer_name"),
            models.Employee.employee_id,
            models.Employee.name.label("employee_name"),
            func.count(models.Transaction.id).label("transaction_count"),
        )
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .join(models.Employee, models.Transaction.employee_id == models.Employee.id)
        .group_by(models.Shopper.id, models.Employee.id)
        .order_by(func.count(models.Transaction.id).desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def category_popularity(session: AsyncSession) -> list[Any]:
    stmt = (
        select(
            models.Product.category,
            func.count(models.Transaction.id).label("transaction_count"),
            func.coalesce(func.sum(models.Transaction.total_usd), 0).label("total_revenue"),
        )
        .join(models.Transaction, models.Product.id == models.Transaction.product_id)
        .where(models.Product.category.isnot(None))
        .group_by(models.Product.category)
        .order_by(func.count(models.Transaction.id).desc())
    )
    result = await session.execute(stmt)
    return list(result.all())


async def specialties_without_purchases(session: AsyncSession) -> list[Any]:
    subq = select(models.Product.category).join(models.Transaction, models.Product.id == models.Transaction.product_id).distinct().subquery()
    stmt = (
        select(models.Employee.id, models.Employee.employee_id, models.Employee.name, models.EmployeeSpecialty.specialty)
        .join(models.EmployeeSpecialty, models.Employee.id == models.EmployeeSpecialty.employee_id)
        .where(~models.EmployeeSpecialty.specialty.in_(subq))
    )
    result = await session.execute(stmt)
    return list(result.all())


async def get_shopper_transaction_totals(session: AsyncSession) -> list[Any]:
    stmt = (
        select(
            models.Shopper.id,
            models.Shopper.customer_id,
            models.Shopper.name,
            models.Shopper.lifetime_spend_usd,
            func.coalesce(func.sum(models.Transaction.total_usd), 0).label("transaction_total"),
        )
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .group_by(models.Shopper.id)
    )
    result = await session.execute(stmt)
    return list(result.all())


async def ethically_sourced_below_budget(session: AsyncSession) -> list[Any]:
    subq = select(func.avg(models.ShopperPreferences.budget_max)).join(models.Shopper, models.ShopperPreferences.shopper_id == models.Shopper.id).where(models.Shopper.loyalty_tier.ilike("bronze")).scalar_subquery()
    stmt = (
        select(models.Product)
        .where(models.Product.ethically_sourced == True)
        .where(models.Product.price_usd < subq)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_employee_by_transaction_and_customer_name(session: AsyncSession, transaction_id: str, customer_name: str) -> Optional[models.Employee]:
    result = await session.execute(
        select(models.Employee)
        .join(models.Transaction, models.Employee.id == models.Transaction.employee_id)
        .join(models.Shopper, models.Transaction.customer_id == models.Shopper.id)
        .where(models.Transaction.transaction_id == transaction_id)
        .where(models.Shopper.name.ilike(customer_name))
        .options(
            joinedload(models.Employee.languages),
            joinedload(models.Employee.specialties),
        )
    )
    return result.scalar_one_or_none()


async def get_product_by_customer_and_date(session: AsyncSession, customer_name: str, date: str) -> Optional[models.Product]:
    result = await session.execute(
        select(models.Product)
        .join(models.Transaction, models.Product.id == models.Transaction.product_id)
        .join(models.Shopper, models.Transaction.customer_id == models.Shopper.id)
        .where(models.Shopper.name.ilike(customer_name))
        .where(models.Transaction.date == date)
        .options(joinedload(models.Product.gemstones))
    )
    return result.scalar_one_or_none()


async def get_products_by_customer_name(session: AsyncSession, customer_name: str) -> list[models.Product]:
    result = await session.execute(
        select(models.Product)
        .join(models.Transaction, models.Product.id == models.Transaction.product_id)
        .join(models.Shopper, models.Transaction.customer_id == models.Shopper.id)
        .where(models.Shopper.name.ilike(customer_name))
        .distinct()
    )
    return list(result.scalars().all())


async def get_customers_by_employee_name(session: AsyncSession, employee_name: str) -> list[models.Shopper]:
    result = await session.execute(
        select(models.Shopper)
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .join(models.Employee, models.Transaction.employee_id == models.Employee.id)
        .where(models.Employee.name.ilike(employee_name))
        .distinct()
    )
    return list(result.scalars().all())
