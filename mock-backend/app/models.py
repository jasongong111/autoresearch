from typing import List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[Optional[str]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    hire_date: Mapped[Optional[str]] = mapped_column(Date)
    salary_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    address: Mapped[Optional["EmployeeAddress"]] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    languages: Mapped[List["EmployeeLanguage"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    specialties: Mapped[List["EmployeeSpecialty"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    emergency_contact: Mapped[Optional["EmployeeEmergencyContact"]] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="employee")


class EmployeeAddress(Base):
    __tablename__ = "employee_addresses"

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True
    )
    street: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    zip: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(100))

    employee: Mapped["Employee"] = relationship(back_populates="address")


class EmployeeLanguage(Base):
    __tablename__ = "employee_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE")
    )
    language: Mapped[str] = mapped_column(String(50))

    employee: Mapped["Employee"] = relationship(back_populates="languages")


class EmployeeSpecialty(Base):
    __tablename__ = "employee_specialties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE")
    )
    specialty: Mapped[str] = mapped_column(String(100))

    employee: Mapped["Employee"] = relationship(back_populates="specialties")


class EmployeeEmergencyContact(Base):
    __tablename__ = "employee_emergency_contacts"

    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True
    )
    name: Mapped[Optional[str]] = mapped_column(String(255))
    relation: Mapped[Optional[str]] = mapped_column(String(50))
    phone: Mapped[Optional[str]] = mapped_column(String(50))

    employee: Mapped["Employee"] = relationship(back_populates="emergency_contact")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    collection: Mapped[Optional[str]] = mapped_column(String(100))
    metal: Mapped[Optional[str]] = mapped_column(String(100))
    price_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    weight_grams: Mapped[Optional[float]] = mapped_column(Numeric(8, 2))
    in_stock: Mapped[Optional[int]] = mapped_column(Integer)
    ethically_sourced: Mapped[Optional[bool]] = mapped_column(Boolean)
    description: Mapped[Optional[str]] = mapped_column(Text)

    gemstones: Mapped[List["ProductGemstone"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="product")


class ProductGemstone(Base):
    __tablename__ = "product_gemstones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE")
    )
    gemstone: Mapped[str] = mapped_column(String(100))

    product: Mapped["Product"] = relationship(back_populates="gemstones")


class Shopper(Base):
    __tablename__ = "shoppers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[Optional[int]] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    ring_size: Mapped[Optional[float]] = mapped_column(Numeric(4, 1))
    birthstone: Mapped[Optional[str]] = mapped_column(String(50))
    anniversary: Mapped[Optional[str]] = mapped_column(Date)
    partner_name: Mapped[Optional[str]] = mapped_column(String(255))
    loyalty_tier: Mapped[Optional[str]] = mapped_column(String(20))
    lifetime_spend_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    communication_preference: Mapped[Optional[str]] = mapped_column(String(20))
    marketing_opt_in: Mapped[Optional[bool]] = mapped_column(Boolean)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    address: Mapped[Optional["ShopperAddress"]] = relationship(
        back_populates="shopper", uselist=False, cascade="all, delete-orphan"
    )
    preferences: Mapped[Optional["ShopperPreferences"]] = relationship(
        back_populates="shopper", uselist=False, cascade="all, delete-orphan"
    )
    preference_metals: Mapped[List["ShopperPreferenceMetal"]] = relationship(
        back_populates="shopper", cascade="all, delete-orphan"
    )
    preference_gemstones: Mapped[List["ShopperPreferenceGemstone"]] = relationship(
        back_populates="shopper", cascade="all, delete-orphan"
    )
    preference_avoids: Mapped[List["ShopperPreferenceAvoid"]] = relationship(
        back_populates="shopper", cascade="all, delete-orphan"
    )
    diamond_specs: Mapped[Optional["ShopperDiamondSpec"]] = relationship(
        back_populates="shopper", uselist=False, cascade="all, delete-orphan"
    )
    allergies: Mapped[List["ShopperAllergy"]] = relationship(
        back_populates="shopper", cascade="all, delete-orphan"
    )
    purchase_history: Mapped[List["ShopperPurchaseHistory"]] = relationship(
        back_populates="shopper", cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(back_populates="shopper")


class ShopperAddress(Base):
    __tablename__ = "shopper_addresses"

    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE"), primary_key=True
    )
    street: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    zip: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(100))

    shopper: Mapped["Shopper"] = relationship(back_populates="address")


class ShopperPreferences(Base):
    __tablename__ = "shopper_preferences"

    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE"), primary_key=True
    )
    style: Mapped[Optional[str]] = mapped_column(String(100))
    ethical_only: Mapped[Optional[bool]] = mapped_column(Boolean)
    budget_min: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    budget_max: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    shopper: Mapped["Shopper"] = relationship(back_populates="preferences")


class ShopperPreferenceMetal(Base):
    __tablename__ = "shopper_preference_metals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE")
    )
    metal: Mapped[str] = mapped_column(String(50))

    shopper: Mapped["Shopper"] = relationship(back_populates="preference_metals")


class ShopperPreferenceGemstone(Base):
    __tablename__ = "shopper_preference_gemstones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE")
    )
    gemstone: Mapped[str] = mapped_column(String(50))

    shopper: Mapped["Shopper"] = relationship(back_populates="preference_gemstones")


class ShopperPreferenceAvoid(Base):
    __tablename__ = "shopper_preference_avoids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE")
    )
    avoid: Mapped[str] = mapped_column(String(50))

    shopper: Mapped["Shopper"] = relationship(back_populates="preference_avoids")


class ShopperDiamondSpec(Base):
    __tablename__ = "shopper_diamond_specs"

    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE"), primary_key=True
    )
    cut: Mapped[Optional[str]] = mapped_column(String(50))
    min_carat: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    min_clarity: Mapped[Optional[str]] = mapped_column(String(20))
    min_color: Mapped[Optional[str]] = mapped_column(String(20))

    shopper: Mapped["Shopper"] = relationship(back_populates="diamond_specs")


class ShopperAllergy(Base):
    __tablename__ = "shopper_allergies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE")
    )
    allergy: Mapped[str] = mapped_column(String(50))

    shopper: Mapped["Shopper"] = relationship(back_populates="allergies")


class ShopperPurchaseHistory(Base):
    __tablename__ = "shopper_purchase_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shopper_id: Mapped[int] = mapped_column(
        ForeignKey("shoppers.id", ondelete="CASCADE")
    )
    date: Mapped[Optional[str]] = mapped_column(Date)
    item: Mapped[Optional[str]] = mapped_column(String(255))
    price_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))

    shopper: Mapped["Shopper"] = relationship(back_populates="purchase_history")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    date: Mapped[Optional[str]] = mapped_column(Date)
    customer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("shoppers.id", ondelete="SET NULL")
    )
    employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id", ondelete="SET NULL")
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("products.id", ondelete="SET NULL")
    )
    quantity: Mapped[Optional[int]] = mapped_column(Integer)
    unit_price_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    discount_pct: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    total_usd: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    payment_method: Mapped[Optional[str]] = mapped_column(String(50))
    channel: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    shopper: Mapped[Optional["Shopper"]] = relationship(back_populates="transactions")
    employee: Mapped[Optional["Employee"]] = relationship(back_populates="transactions")
    product: Mapped[Optional["Product"]] = relationship(back_populates="transactions")
