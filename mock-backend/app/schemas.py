from datetime import date as DateType
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# ---------- Shared ----------

class AddressBase(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None


class AddressCreate(AddressBase):
    pass


class AddressOut(AddressBase):
    model_config = ConfigDict(from_attributes=True)


# ---------- Employees ----------

class EmployeeLanguageBase(BaseModel):
    language: str


class EmployeeLanguageOut(EmployeeLanguageBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EmployeeSpecialtyBase(BaseModel):
    specialty: str


class EmployeeSpecialtyOut(EmployeeSpecialtyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EmployeeEmergencyContactBase(BaseModel):
    name: Optional[str] = None
    relation: Optional[str] = None
    phone: Optional[str] = None


class EmployeeEmergencyContactOut(EmployeeEmergencyContactBase):
    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    employee_id: str
    name: str
    date_of_birth: Optional[DateType] = None
    gender: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    hire_date: Optional[DateType] = None
    salary_usd: Optional[float] = None
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    address: Optional[AddressCreate] = None
    languages: List[str] = []
    specialties: List[str] = []
    emergency_contact: Optional[EmployeeEmergencyContactBase] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[DateType] = None
    gender: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    hire_date: Optional[DateType] = None
    salary_usd: Optional[float] = None
    notes: Optional[str] = None


class EmployeeOut(EmployeeBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EmployeeDetailOut(EmployeeOut):
    address: Optional[AddressOut] = None
    languages: List[EmployeeLanguageOut] = []
    specialties: List[EmployeeSpecialtyOut] = []
    emergency_contact: Optional[EmployeeEmergencyContactOut] = None


# ---------- Products ----------

class ProductGemstoneBase(BaseModel):
    gemstone: str


class ProductGemstoneOut(ProductGemstoneBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    product_id: str
    name: str
    category: Optional[str] = None
    collection: Optional[str] = None
    metal: Optional[str] = None
    price_usd: Optional[float] = None
    weight_grams: Optional[float] = None
    in_stock: Optional[int] = None
    ethically_sourced: Optional[bool] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    gemstones: List[str] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    collection: Optional[str] = None
    metal: Optional[str] = None
    price_usd: Optional[float] = None
    weight_grams: Optional[float] = None
    in_stock: Optional[int] = None
    ethically_sourced: Optional[bool] = None
    description: Optional[str] = None


class ProductOut(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ProductDetailOut(ProductOut):
    gemstones: List[ProductGemstoneOut] = []


# ---------- Shoppers ----------

class ShopperPreferenceMetalBase(BaseModel):
    metal: str


class ShopperPreferenceMetalOut(ShopperPreferenceMetalBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShopperPreferenceGemstoneBase(BaseModel):
    gemstone: str


class ShopperPreferenceGemstoneOut(ShopperPreferenceGemstoneBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShopperPreferenceAvoidBase(BaseModel):
    avoid: str


class ShopperPreferenceAvoidOut(ShopperPreferenceAvoidBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShopperDiamondSpecBase(BaseModel):
    cut: Optional[str] = None
    min_carat: Optional[float] = None
    min_clarity: Optional[str] = None
    min_color: Optional[str] = None


class ShopperDiamondSpecOut(ShopperDiamondSpecBase):
    model_config = ConfigDict(from_attributes=True)


class ShopperPreferencesBase(BaseModel):
    style: Optional[str] = None
    ethical_only: Optional[bool] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None


class ShopperPreferencesOut(ShopperPreferencesBase):
    model_config = ConfigDict(from_attributes=True)


class ShopperAllergyBase(BaseModel):
    allergy: str


class ShopperAllergyOut(ShopperAllergyBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShopperPurchaseHistoryBase(BaseModel):
    date: Optional[DateType] = None
    item: Optional[str] = None
    price_usd: Optional[float] = None


class ShopperPurchaseHistoryOut(ShopperPurchaseHistoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShopperBase(BaseModel):
    customer_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ring_size: Optional[float] = None
    birthstone: Optional[str] = None
    anniversary: Optional[DateType] = None
    partner_name: Optional[str] = None
    loyalty_tier: Optional[str] = None
    lifetime_spend_usd: Optional[float] = None
    communication_preference: Optional[str] = None
    marketing_opt_in: Optional[bool] = None
    notes: Optional[str] = None


class ShopperCreate(ShopperBase):
    address: Optional[AddressCreate] = None
    preferences: Optional[ShopperPreferencesBase] = None
    preference_metals: List[str] = []
    preference_gemstones: List[str] = []
    preference_avoids: List[str] = []
    diamond_specs: Optional[ShopperDiamondSpecBase] = None
    allergies: List[str] = []
    purchase_history: List[ShopperPurchaseHistoryBase] = []


class ShopperUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ring_size: Optional[float] = None
    birthstone: Optional[str] = None
    anniversary: Optional[DateType] = None
    partner_name: Optional[str] = None
    loyalty_tier: Optional[str] = None
    lifetime_spend_usd: Optional[float] = None
    communication_preference: Optional[str] = None
    marketing_opt_in: Optional[bool] = None
    notes: Optional[str] = None


class ShopperOut(ShopperBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ShopperDetailOut(ShopperOut):
    address: Optional[AddressOut] = None
    preferences: Optional[ShopperPreferencesOut] = None
    preference_metals: List[ShopperPreferenceMetalOut] = []
    preference_gemstones: List[ShopperPreferenceGemstoneOut] = []
    preference_avoids: List[ShopperPreferenceAvoidOut] = []
    diamond_specs: Optional[ShopperDiamondSpecOut] = None
    allergies: List[ShopperAllergyOut] = []
    purchase_history: List[ShopperPurchaseHistoryOut] = []


# ---------- Transactions ----------

class TransactionBase(BaseModel):
    transaction_id: str
    date: Optional[DateType] = None
    customer_id: Optional[int] = None
    employee_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price_usd: Optional[float] = None
    discount_pct: Optional[float] = None
    total_usd: Optional[float] = None
    payment_method: Optional[str] = None
    channel: Optional[str] = None
    notes: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    date: Optional[DateType] = None
    customer_id: Optional[int] = None
    employee_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price_usd: Optional[float] = None
    discount_pct: Optional[float] = None
    total_usd: Optional[float] = None
    payment_method: Optional[str] = None
    channel: Optional[str] = None
    notes: Optional[str] = None


class TransactionOut(TransactionBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class TransactionFullOut(BaseModel):
    id: int
    transaction_id: str
    date: Optional[DateType] = None
    quantity: Optional[int] = None
    unit_price_usd: Optional[float] = None
    discount_pct: Optional[float] = None
    total_usd: Optional[float] = None
    payment_method: Optional[str] = None
    channel: Optional[str] = None
    notes: Optional[str] = None
    shopper: Optional[ShopperOut] = None
    employee: Optional[EmployeeOut] = None
    product: Optional[ProductOut] = None
    model_config = ConfigDict(from_attributes=True)


# ---------- Analytics ----------

class TopCustomerOut(BaseModel):
    shopper_id: int
    customer_id: str
    name: str
    total_spent: float


class TopEmployeeOut(BaseModel):
    employee_id: int
    employee_id_code: str
    name: str
    total_sales: float


class ProductSalesOut(BaseModel):
    product_id: int
    product_id_code: str
    name: str
    total_quantity: int
    total_revenue: float


class CountOut(BaseModel):
    label: str
    count: int


class AverageOut(BaseModel):
    label: Optional[str] = None
    average: float


class SumOut(BaseModel):
    label: Optional[str] = None
    total: float


class RevenueOut(BaseModel):
    label: str
    total_revenue: float


class EmployeeRevenueOut(BaseModel):
    employee_id: int
    employee_id_code: str
    name: str
    total_revenue: float


class MonthlyCountOut(BaseModel):
    month: int
    count: int


class ValidationIssueOut(BaseModel):
    shopper_id: int
    customer_id: str
    name: str
    lifetime_spend: float
    purchase_history_sum: float
    difference: float


class TransactionValidationOut(BaseModel):
    transaction_id: str
    customer_id: Optional[str] = None
    date: Optional[DateType] = None
    unit_price_usd: Optional[float] = None
    quantity: Optional[int] = None
    discount_pct: Optional[float] = None
    total_usd: Optional[float] = None
    computed_total: float


class CustomerEmployeePairOut(BaseModel):
    customer_id: str
    customer_name: str
    employee_id: str
    employee_name: str
    transaction_count: int


class CategoryPopularityOut(BaseModel):
    category: str
    transaction_count: int
    total_revenue: float


class LowStockOut(BaseModel):
    product_id: str
    name: str
    in_stock: Optional[int] = None
    category: Optional[str] = None


class ExistenceOut(BaseModel):
    exists: bool
