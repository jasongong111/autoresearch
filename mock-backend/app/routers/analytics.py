from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-customers", response_model=List[schemas.TopCustomerOut])
async def top_customers(limit: int = 10, db: AsyncSession = Depends(get_db)):
    rows = await crud.top_customers(db, limit=limit)
    return [
        schemas.TopCustomerOut(
            shopper_id=r.id, customer_id=r.customer_id, name=r.name, total_spent=float(r.total_spent)
        )
        for r in rows
    ]


@router.get("/top-employees", response_model=List[schemas.TopEmployeeOut])
async def top_employees(limit: int = 10, db: AsyncSession = Depends(get_db)):
    rows = await crud.top_employees(db, limit=limit)
    return [
        schemas.TopEmployeeOut(
            employee_id=r.id,
            employee_id_code=r.employee_id,
            name=r.name,
            total_sales=float(r.total_sales),
        )
        for r in rows
    ]


@router.get("/product-sales", response_model=List[schemas.ProductSalesOut])
async def product_sales(limit: int = 10, db: AsyncSession = Depends(get_db)):
    rows = await crud.product_sales(db, limit=limit)
    return [
        schemas.ProductSalesOut(
            product_id=r.id,
            product_id_code=r.product_id,
            name=r.name,
            total_quantity=int(r.total_quantity),
            total_revenue=float(r.total_revenue),
        )
        for r in rows
    ]


@router.get("/transactions/full", response_model=List[schemas.TransactionFullOut])
async def full_transactions(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_full_transactions(db, skip=skip, limit=limit)


@router.get("/count-by-tier", response_model=List[schemas.CountOut])
async def count_by_tier(db: AsyncSession = Depends(get_db)):
    rows = await crud.count_shoppers_by_tier(db)
    return [schemas.CountOut(label=r.loyalty_tier, count=r.count) for r in rows]


@router.get("/average-salary-by-role", response_model=List[schemas.AverageOut])
async def average_salary_by_role(db: AsyncSession = Depends(get_db)):
    rows = await crud.average_salary_by_role(db)
    return [schemas.AverageOut(label=r.role, average=float(r.average)) for r in rows]


@router.get("/revenue-by-payment-method", response_model=List[schemas.RevenueOut])
async def revenue_by_payment_method(db: AsyncSession = Depends(get_db)):
    rows = await crud.revenue_by_payment_method(db)
    return [schemas.RevenueOut(label=r.payment_method, total_revenue=float(r.total_revenue)) for r in rows]


@router.get("/revenue-by-channel", response_model=List[schemas.RevenueOut])
async def revenue_by_channel(db: AsyncSession = Depends(get_db)):
    rows = await crud.revenue_by_channel(db)
    return [schemas.RevenueOut(label=r.channel, total_revenue=float(r.total_revenue)) for r in rows]


@router.get("/count-by-category", response_model=List[schemas.CountOut])
async def count_by_category(db: AsyncSession = Depends(get_db)):
    rows = await crud.count_products_by_category(db)
    return [schemas.CountOut(label=r.category, count=r.count) for r in rows]


@router.get("/transaction-count-by-month", response_model=List[schemas.MonthlyCountOut])
async def transaction_count_by_month(year: int, db: AsyncSession = Depends(get_db)):
    rows = await crud.transaction_count_by_month(db, year)
    return [schemas.MonthlyCountOut(month=int(r.month), count=r.count) for r in rows]


@router.get("/average-price-by-metal", response_model=List[schemas.AverageOut])
async def average_price_by_metal(db: AsyncSession = Depends(get_db)):
    rows = await crud.average_product_price_by_metal(db)
    return [schemas.AverageOut(label=r.metal, average=float(r.average)) for r in rows]


@router.get("/employee-revenue", response_model=List[schemas.EmployeeRevenueOut])
async def employee_revenue(db: AsyncSession = Depends(get_db)):
    rows = await crud.employee_total_revenue(db)
    return [
        schemas.EmployeeRevenueOut(
            employee_id=r.id,
            employee_id_code=r.employee_id,
            name=r.name,
            total_revenue=float(r.total_revenue),
        )
        for r in rows
    ]


@router.get("/employee-transaction-counts")
async def employee_transaction_counts(year: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    rows = await crud.employee_transaction_counts(db, year=year)
    return [
        {
            "employee_id": r.employee_id,
            "name": r.name,
            "transaction_count": r.txn_count,
        }
        for r in rows
    ]


@router.get("/customer-metal-preference-match", response_model=List[schemas.ShopperOut])
async def customer_metal_preference_match(db: AsyncSession = Depends(get_db)):
    rows = await crud.customer_metal_preference_match(db)
    return [schemas.ShopperOut.model_validate(r) for r in rows]


@router.get("/validate-lifetime-spend", response_model=List[schemas.ValidationIssueOut])
async def validate_lifetime_spend(db: AsyncSession = Depends(get_db)):
    rows = await crud.validate_lifetime_spend(db)
    return [
        schemas.ValidationIssueOut(
            shopper_id=r.id,
            customer_id=r.customer_id,
            name=r.name,
            lifetime_spend=float(r.lifetime_spend),
            purchase_history_sum=float(r.purchase_history_sum),
            difference=abs(float(r.lifetime_spend) - float(r.purchase_history_sum)),
        )
        for r in rows
    ]


@router.get("/validate-transaction-totals", response_model=List[schemas.TransactionValidationOut])
async def validate_transaction_totals(db: AsyncSession = Depends(get_db)):
    rows = await crud.validate_transaction_totals(db)
    issues = []
    for r in rows:
        if r.unit_price_usd is not None and r.quantity is not None and r.discount_pct is not None:
            computed = r.unit_price_usd * r.quantity * (1 - r.discount_pct / 100)
            if abs(computed - (r.total_usd or 0)) > 0.01:
                issues.append(
                    schemas.TransactionValidationOut(
                        transaction_id=r.transaction_id,
                        customer_id=None,
                        date=r.date,
                        unit_price_usd=float(r.unit_price_usd),
                        quantity=r.quantity,
                        discount_pct=float(r.discount_pct),
                        total_usd=float(r.total_usd) if r.total_usd else None,
                        computed_total=round(computed, 2),
                    )
                )
    return issues


@router.get("/most-frequent-customer-employee-pair", response_model=List[schemas.CustomerEmployeePairOut])
async def most_frequent_customer_employee_pair(db: AsyncSession = Depends(get_db)):
    rows = await crud.most_frequent_customer_employee_pair(db)
    return [
        schemas.CustomerEmployeePairOut(
            customer_id=r.customer_id,
            customer_name=r.customer_name,
            employee_id=r.employee_id,
            employee_name=r.employee_name,
            transaction_count=r.transaction_count,
        )
        for r in rows
    ]


@router.get("/category-popularity", response_model=List[schemas.CategoryPopularityOut])
async def category_popularity(db: AsyncSession = Depends(get_db)):
    rows = await crud.category_popularity(db)
    return [
        schemas.CategoryPopularityOut(
            category=r.category,
            transaction_count=r.transaction_count,
            total_revenue=float(r.total_revenue),
        )
        for r in rows
    ]


@router.get("/specialties-without-purchases")
async def specialties_without_purchases(db: AsyncSession = Depends(get_db)):
    rows = await crud.specialties_without_purchases(db)
    return [
        {
            "employee_id": r.employee_id,
            "name": r.name,
            "specialty": r.specialty,
        }
        for r in rows
    ]


@router.get("/shopper-transaction-totals")
async def shopper_transaction_totals(db: AsyncSession = Depends(get_db)):
    rows = await crud.get_shopper_transaction_totals(db)
    return [
        {
            "shopper_id": r.id,
            "customer_id": r.customer_id,
            "name": r.name,
            "lifetime_spend": float(r.lifetime_spend_usd) if r.lifetime_spend_usd else 0,
            "transaction_total": float(r.transaction_total),
            "difference": abs(float(r.lifetime_spend_usd or 0) - float(r.transaction_total)),
        }
        for r in rows
    ]


@router.get("/ethically-sourced-below-budget", response_model=List[schemas.ProductOut])
async def ethically_sourced_below_budget(db: AsyncSession = Depends(get_db)):
    rows = await crud.ethically_sourced_below_budget(db)
    return [schemas.ProductOut.model_validate(r) for r in rows]


@router.get("/low-stock")
async def low_stock(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = select(models.Product).where(models.Product.in_stock <= 1)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        schemas.LowStockOut(
            product_id=r.product_id,
            name=r.name,
            in_stock=r.in_stock,
            category=r.category,
        )
        for r in rows
    ]


@router.get("/employee-by-transaction-and-customer", response_model=schemas.EmployeeDetailOut)
async def employee_by_transaction_and_customer(transaction_id: str, customer_name: str, db: AsyncSession = Depends(get_db)):
    emp = await crud.get_employee_by_transaction_and_customer_name(db, transaction_id, customer_name)
    if not emp:
        raise HTTPException(status_code=404, detail="Not found")
    return emp


@router.get("/product-by-customer-and-date", response_model=schemas.ProductDetailOut)
async def product_by_customer_and_date(customer_name: str, date: str, db: AsyncSession = Depends(get_db)):
    prod = await crud.get_product_by_customer_and_date(db, customer_name, date)
    if not prod:
        raise HTTPException(status_code=404, detail="Not found")
    return prod


@router.get("/customers-by-employee-name", response_model=List[schemas.ShopperOut])
async def customers_by_employee_name(employee_name: str, db: AsyncSession = Depends(get_db)):
    rows = await crud.get_customers_by_employee_name(db, employee_name)
    return [schemas.ShopperOut.model_validate(r) for r in rows]


@router.get("/products-by-customer-name", response_model=List[schemas.ProductOut])
async def products_by_customer_name(customer_name: str, db: AsyncSession = Depends(get_db)):
    rows = await crud.get_products_by_customer_name(db, customer_name)
    return [schemas.ProductOut.model_validate(r) for r in rows]


@router.get("/customer-by-purchase-price", response_model=List[schemas.ShopperOut])
async def customer_by_purchase_price(price_usd: float, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = (
        select(models.Shopper)
        .join(models.ShopperPurchaseHistory, models.Shopper.id == models.ShopperPurchaseHistory.shopper_id)
        .where(models.ShopperPurchaseHistory.price_usd == price_usd)
        .distinct()
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.ShopperOut.model_validate(r) for r in rows]


@router.get("/platinum-instore-customers", response_model=List[schemas.ShopperOut])
async def platinum_instore_customers(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = (
        select(models.Shopper)
        .where(models.Shopper.loyalty_tier.ilike("platinum"))
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .where(models.Transaction.channel.ilike("in-store"))
        .distinct()
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.ShopperOut.model_validate(r) for r in rows]


@router.get("/gemologist-most-transactions")
async def gemologist_most_transactions(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = (
        select(models.Employee.id, models.Employee.employee_id, models.Employee.name, func.count(models.Transaction.id).label("txn_count"))
        .join(models.Transaction, models.Employee.id == models.Transaction.employee_id)
        .where(models.Employee.role.ilike("%gemologist%"))
        .group_by(models.Employee.id)
        .order_by(func.count(models.Transaction.id).desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return []
    return [{"employee_id": row.employee_id, "name": row.name, "transaction_count": row.txn_count}]


@router.get("/employees-no-private-appointments", response_model=List[schemas.EmployeeOut])
async def employees_no_private_appointments(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    subq = select(models.Transaction.employee_id).where(models.Transaction.channel.ilike("private appointment")).distinct().subquery()
    stmt = select(models.Employee).where(~models.Employee.id.in_(subq))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.EmployeeOut.model_validate(r) for r in rows]


@router.get("/purchase-on-anniversary", response_model=List[schemas.ShopperOut])
async def purchase_on_anniversary(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, extract
    from app import models
    stmt = (
        select(models.Shopper)
        .join(models.Transaction, models.Shopper.id == models.Transaction.customer_id)
        .where(
            extract("month", models.Shopper.anniversary) == extract("month", models.Transaction.date),
            extract("day", models.Shopper.anniversary) == extract("day", models.Transaction.date),
        )
        .distinct()
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.ShopperOut.model_validate(r) for r in rows]


@router.get("/transactions-with-quantity")
async def transactions_with_quantity(min_quantity: int = 2, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = select(models.Transaction).where(models.Transaction.quantity >= min_quantity)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.TransactionOut.model_validate(r) for r in rows]


@router.get("/shoppers-anniversary-month", response_model=List[schemas.ShopperOut])
async def shoppers_anniversary_month(month: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, extract
    from app import models
    stmt = select(models.Shopper).where(extract("month", models.Shopper.anniversary) == month)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.ShopperOut.model_validate(r) for r in rows]


@router.get("/days-between-transactions")
async def days_between_transactions(transaction_id_a: str, transaction_id_b: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    result = await db.execute(
        select(models.Transaction).where(models.Transaction.transaction_id.in_([transaction_id_a, transaction_id_b]))
    )
    rows = list(result.scalars().all())
    if len(rows) != 2:
        raise HTTPException(status_code=404, detail="One or both transactions not found")
    dates = sorted([r.date for r in rows if r.date])
    if len(dates) != 2:
        raise HTTPException(status_code=400, detail="Missing dates on transactions")
    delta = (dates[1] - dates[0]).days
    return {"transaction_a": transaction_id_a, "transaction_b": transaction_id_b, "days": delta}


@router.get("/employees-born-in-decade", response_model=List[schemas.EmployeeOut])
async def employees_born_in_decade(start_year: int, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, extract
    from app import models
    stmt = select(models.Employee).where(
        extract("year", models.Employee.date_of_birth) >= start_year,
        extract("year", models.Employee.date_of_birth) < start_year + 10,
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [schemas.EmployeeOut.model_validate(r) for r in rows]


@router.get("/employee-age-at-hire")
async def employee_age_at_hire(name: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    result = await db.execute(select(models.Employee).where(models.Employee.name.ilike(name)))
    emp = result.scalar_one_or_none()
    if not emp or not emp.date_of_birth or not emp.hire_date:
        raise HTTPException(status_code=404, detail="Employee or dates not found")
    age = emp.hire_date.year - emp.date_of_birth.year
    if (emp.hire_date.month, emp.hire_date.day) < (emp.date_of_birth.month, emp.date_of_birth.day):
        age -= 1
    return {"name": emp.name, "hire_date": str(emp.hire_date), "age_at_hire": age}


@router.get("/customer-most-purchase-years")
async def customer_most_purchase_years(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, extract, func
    from app import models
    stmt = (
        select(
            models.Shopper.id,
            models.Shopper.customer_id,
            models.Shopper.name,
            func.count(func.distinct(extract("year", models.ShopperPurchaseHistory.date))).label("year_count"),
        )
        .join(models.ShopperPurchaseHistory, models.Shopper.id == models.ShopperPurchaseHistory.shopper_id)
        .group_by(models.Shopper.id)
        .order_by(func.count(func.distinct(extract("year", models.ShopperPurchaseHistory.date))).desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        return []
    return [{"customer_id": row.customer_id, "name": row.name, "distinct_years": row.year_count}]


@router.get("/existence/products-with-gemstones")
async def products_with_gemstones(gemstones: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    gems = [g.strip() for g in gemstones.split(",")]
    stmt = (
        select(models.Product.id)
        .join(models.ProductGemstone, models.Product.id == models.ProductGemstone.product_id)
        .where(models.ProductGemstone.gemstone.ilike(gems[0]))
    )
    for gem in gems[1:]:
        stmt = stmt.where(
            models.Product.id.in_(
                select(models.ProductGemstone.product_id)
                .where(models.ProductGemstone.gemstone.ilike(gem))
            )
        )
    result = await db.execute(stmt)
    rows = result.all()
    return schemas.ExistenceOut(exists=len(rows) > 0)


@router.get("/existence/shopper-metals")
async def shopper_metals(metals: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    ms = [m.strip() for m in metals.split(",")]
    stmt = (
        select(models.Shopper.id)
        .join(models.ShopperPreferenceMetal, models.Shopper.id == models.ShopperPreferenceMetal.shopper_id)
        .where(models.ShopperPreferenceMetal.metal.ilike(ms[0]))
    )
    for metal in ms[1:]:
        stmt = stmt.where(
            models.Shopper.id.in_(
                select(models.ShopperPreferenceMetal.shopper_id)
                .where(models.ShopperPreferenceMetal.metal.ilike(metal))
            )
        )
    result = await db.execute(stmt)
    rows = result.all()
    return schemas.ExistenceOut(exists=len(rows) > 0)


@router.get("/existence/zero-gemstones-above-price")
async def zero_gemstones_above_price(price: float = 500, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    subq = select(models.ProductGemstone.product_id).distinct().subquery()
    stmt = select(models.Product).where(~models.Product.id.in_(subq)).where(models.Product.price_usd > price)
    result = await db.execute(stmt)
    row = result.first()
    return schemas.ExistenceOut(exists=row is not None)


@router.get("/existence/transaction-discount")
async def transaction_discount_exact(discount_pct: float, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = select(models.Transaction).where(models.Transaction.discount_pct == discount_pct)
    result = await db.execute(stmt)
    row = result.first()
    return schemas.ExistenceOut(exists=row is not None)


@router.get("/existence/emergency-contact-relation")
async def emergency_contact_relation(relation: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from app import models
    stmt = select(models.EmployeeEmergencyContact).where(models.EmployeeEmergencyContact.relation.ilike(relation))
    result = await db.execute(stmt)
    row = result.first()
    return schemas.ExistenceOut(exists=row is not None)
