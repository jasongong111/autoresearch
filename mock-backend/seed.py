import asyncio
import json
from datetime import date
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, create_tables
from app.models import (
    Employee,
    EmployeeAddress,
    EmployeeEmergencyContact,
    EmployeeLanguage,
    EmployeeSpecialty,
    Product,
    ProductGemstone,
    Shopper,
    ShopperAddress,
    ShopperAllergy,
    ShopperDiamondSpec,
    ShopperPreferenceAvoid,
    ShopperPreferenceGemstone,
    ShopperPreferenceMetal,
    ShopperPreferences,
    ShopperPurchaseHistory,
    Transaction,
)

DATA_DIR = Path(__file__).parent / "data"


def _parse_date(value: str | None) -> date | None:
    if value is None:
        return None
    return date.fromisoformat(value)


async def seed_employees(session: AsyncSession) -> dict[str, int]:
    path = DATA_DIR / "employees.json"
    with open(path) as f:
        data = json.load(f)

    mapping: dict[str, int] = {}
    for record in data["employees"]:
        emp = Employee(
            employee_id=record["employee_id"],
            name=record["name"],
            date_of_birth=_parse_date(record.get("date_of_birth")),
            gender=record.get("gender"),
            role=record.get("role"),
            email=record.get("email"),
            phone=record.get("phone"),
            hire_date=_parse_date(record.get("hire_date")),
            salary_usd=record.get("salary_usd"),
            notes=record.get("notes"),
        )
        session.add(emp)
        await session.flush()
        mapping[record["employee_id"]] = emp.id

        addr = record.get("address")
        if addr:
            session.add(
                EmployeeAddress(
                    employee_id=emp.id,
                    street=addr.get("street"),
                    city=addr.get("city"),
                    state=addr.get("state"),
                    zip=addr.get("zip"),
                    country=addr.get("country"),
                )
            )

        for lang in record.get("languages", []):
            session.add(EmployeeLanguage(employee_id=emp.id, language=lang))

        for spec in record.get("specialties", []):
            session.add(EmployeeSpecialty(employee_id=emp.id, specialty=spec))

        ec = record.get("emergency_contact")
        if ec:
            session.add(
                EmployeeEmergencyContact(
                    employee_id=emp.id,
                    name=ec.get("name"),
                    relation=ec.get("relationship"),
                    phone=ec.get("phone"),
                )
            )

    return mapping


async def seed_products(session: AsyncSession) -> dict[str, int]:
    path = DATA_DIR / "products.json"
    with open(path) as f:
        data = json.load(f)

    mapping: dict[str, int] = {}
    for record in data["products"]:
        prod = Product(
            product_id=record["product_id"],
            name=record["name"],
            category=record.get("category"),
            collection=record.get("collection"),
            metal=record.get("metal"),
            price_usd=record.get("price_usd"),
            weight_grams=record.get("weight_grams"),
            in_stock=record.get("in_stock"),
            ethically_sourced=record.get("ethically_sourced"),
            description=record.get("description"),
        )
        session.add(prod)
        await session.flush()
        mapping[record["product_id"]] = prod.id

        for gem in record.get("gemstones", []):
            session.add(ProductGemstone(product_id=prod.id, gemstone=gem))

    return mapping


async def seed_shoppers(session: AsyncSession) -> dict[str, int]:
    path = DATA_DIR / "shoppers.json"
    with open(path) as f:
        data = json.load(f)

    mapping: dict[str, int] = {}
    for record in data["shoppers"]:
        shopper = Shopper(
            customer_id=record["customer_id"],
            name=record["name"],
            age=record.get("age"),
            gender=record.get("gender"),
            email=record.get("email"),
            phone=record.get("phone"),
            ring_size=record.get("ring_size"),
            birthstone=record.get("birthstone"),
            anniversary=_parse_date(record.get("anniversary")),
            partner_name=record.get("partner_name"),
            loyalty_tier=record.get("loyalty_tier"),
            lifetime_spend_usd=record.get("lifetime_spend_usd"),
            communication_preference=record.get("communication_preference"),
            marketing_opt_in=record.get("marketing_opt_in"),
            notes=record.get("notes"),
        )
        session.add(shopper)
        await session.flush()
        mapping[record["customer_id"]] = shopper.id

        addr = record.get("address")
        if addr:
            session.add(
                ShopperAddress(
                    shopper_id=shopper.id,
                    street=addr.get("street"),
                    city=addr.get("city"),
                    state=addr.get("state"),
                    zip=addr.get("zip"),
                    country=addr.get("country"),
                )
            )

        prefs = record.get("preferences")
        if prefs:
            session.add(
                ShopperPreferences(
                    shopper_id=shopper.id,
                    style=prefs.get("style"),
                    ethical_only=prefs.get("ethical_only"),
                    budget_min=prefs.get("budget_usd", [None, None])[0],
                    budget_max=prefs.get("budget_usd", [None, None])[1],
                )
            )
            for metal in prefs.get("metal", []):
                session.add(
                    ShopperPreferenceMetal(shopper_id=shopper.id, metal=metal)
                )
            for gem in prefs.get("gemstone", []):
                session.add(
                    ShopperPreferenceGemstone(shopper_id=shopper.id, gemstone=gem)
                )
            for avoid in prefs.get("avoid", []):
                session.add(
                    ShopperPreferenceAvoid(shopper_id=shopper.id, avoid=avoid)
                )
            ds = prefs.get("diamond_specs")
            if ds:
                session.add(
                    ShopperDiamondSpec(
                        shopper_id=shopper.id,
                        cut=ds.get("cut"),
                        min_carat=ds.get("min_carat"),
                        min_clarity=ds.get("min_clarity"),
                        min_color=ds.get("min_color"),
                    )
                )

        for allergy in record.get("allergies", []):
            session.add(ShopperAllergy(shopper_id=shopper.id, allergy=allergy))

        for ph in record.get("purchase_history", []):
            session.add(
                ShopperPurchaseHistory(
                    shopper_id=shopper.id,
                    date=_parse_date(ph.get("date")),
                    item=ph.get("item"),
                    price_usd=ph.get("price_usd"),
                )
            )

    return mapping


async def seed_transactions(
    session: AsyncSession,
    shopper_map: dict[str, int],
    employee_map: dict[str, int],
    product_map: dict[str, int],
) -> None:
    path = DATA_DIR / "transactions.json"
    with open(path) as f:
        data = json.load(f)

    for record in data["transactions"]:
        session.add(
            Transaction(
                transaction_id=record["transaction_id"],
                date=_parse_date(record.get("date")),
                customer_id=shopper_map.get(record["customer_id"]),
                employee_id=employee_map.get(record["employee_id"]),
                product_id=product_map.get(record["product_id"]),
                quantity=record.get("quantity"),
                unit_price_usd=record.get("unit_price_usd"),
                discount_pct=record.get("discount_pct"),
                total_usd=record.get("total_usd"),
                payment_method=record.get("payment_method"),
                channel=record.get("channel"),
                notes=record.get("notes"),
            )
        )


async def main() -> None:
    await create_tables()
    async with AsyncSessionLocal() as session:
        employee_map = await seed_employees(session)
        product_map = await seed_products(session)
        shopper_map = await seed_shoppers(session)
        await seed_transactions(session, shopper_map, employee_map, product_map)
        await session.commit()
        print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(main())
