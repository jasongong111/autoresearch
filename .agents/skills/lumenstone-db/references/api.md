# Lumenstone API Reference

Base: `{LUMENSTONE_API_URL}` or `http://localhost:8000/api/v1`.

Path IDs are numeric primary keys (`id`). Business codes (`employee_id`, `product_id`, `customer_id`, `transaction_id`) are JSON fields. Dedicated `by-*` endpoints exist for direct business-code and name lookups.

## Endpoint Matrix

### Core CRUD

| Method | Path | Params | Request body | Response |
|--------|------|--------|--------------|----------|
| `GET` | `/health` | none | none | `{ "status": "ok" }` |
| `GET` | `/employees` | `skip=0`, `limit=100`, `role`, `hire_date_after`, `hire_date_before`, `state`, `language`, `specialty`, `sort_by`, `order` | none | `EmployeeOut[]` |
| `GET` | `/employees/{id}` | numeric `id` | none | `EmployeeDetailOut` |
| `GET` | `/employees/by-employee-id/{employee_id}` | e.g. `E-0004` | none | `EmployeeDetailOut` |
| `GET` | `/employees/by-name/{name}` | exact name | none | `EmployeeDetailOut` |
| `GET` | `/employees/search/` | `q` | none | `EmployeeOut[]` |
| `POST` | `/employees` | none | `EmployeeCreate` | `EmployeeOut`, status 201 |
| `PUT` | `/employees/{id}` | numeric `id` | `EmployeeUpdate` partial | `EmployeeOut` |
| `DELETE` | `/employees/{id}` | numeric `id` | none | status 204 |
| `GET` | `/products` | `skip=0`, `limit=100`, `category`, `metal`, `min_price`, `max_price`, `ethically_sourced`, `gemstone`, `in_stock_min`, `in_stock_max`, `sort_by`, `order` | none | `ProductOut[]` |
| `GET` | `/products/{id}` | numeric `id` | none | `ProductDetailOut` |
| `GET` | `/products/by-product-id/{product_id}` | e.g. `P-0012` | none | `ProductDetailOut` |
| `GET` | `/products/by-name/{name}` | exact name | none | `ProductDetailOut` |
| `GET` | `/products/search/` | `q` | none | `ProductOut[]` |
| `POST` | `/products` | none | `ProductCreate` | `ProductOut`, status 201 |
| `PUT` | `/products/{id}` | numeric `id` | `ProductUpdate` partial | `ProductOut` |
| `DELETE` | `/products/{id}` | numeric `id` | none | status 204 |
| `GET` | `/shoppers` | `skip=0`, `limit=100`, `loyalty_tier`, `allergy`, `communication_preference`, `marketing_opt_in`, `min_budget`, `max_budget`, `state`, `style`, `sort_by`, `order` | none | `ShopperOut[]` |
| `GET` | `/shoppers/{id}` | numeric `id` | none | `ShopperDetailOut` |
| `GET` | `/shoppers/by-customer-id/{customer_id}` | e.g. `C-0025` | none | `ShopperDetailOut` |
| `GET` | `/shoppers/by-name/{name}` | exact name | none | `ShopperDetailOut` |
| `GET` | `/shoppers/search/` | `q` | none | `ShopperOut[]` |
| `POST` | `/shoppers` | none | `ShopperCreate` | `ShopperOut`, status 201 |
| `PUT` | `/shoppers/{id}` | numeric `id` | `ShopperUpdate` partial | `ShopperOut` |
| `DELETE` | `/shoppers/{id}` | numeric `id` | none | status 204 |
| `GET` | `/transactions` | `skip=0`, `limit=100`, `payment_method`, `channel`, `min_discount`, `max_discount`, `date_after`, `date_before`, `customer_id`, `employee_id`, `product_id`, `sort_by`, `order` | none | `TransactionOut[]` |
| `GET` | `/transactions/{id}` | numeric `id` | none | `TransactionFullOut` |
| `GET` | `/transactions/by-transaction-id/{transaction_id}` | e.g. `T-0031` | none | `TransactionFullOut` |
| `GET` | `/transactions/search/` | `q` | none | `TransactionOut[]` |
| `POST` | `/transactions` | none | `TransactionCreate` | `TransactionOut`, status 201 |
| `PUT` | `/transactions/{id}` | numeric `id` | `TransactionUpdate` partial | `TransactionOut` |
| `DELETE` | `/transactions/{id}` | numeric `id` | none | status 204 |

### Analytics

| Method | Path | Params | Response |
|--------|------|--------|----------|
| `GET` | `/analytics/top-customers` | `limit=10` | `TopCustomerOut[]` |
| `GET` | `/analytics/top-employees` | `limit=10` | `TopEmployeeOut[]` |
| `GET` | `/analytics/product-sales` | `limit=10` | `ProductSalesOut[]` |
| `GET` | `/analytics/transactions/full` | `skip=0`, `limit=100` | `TransactionFullOut[]` |
| `GET` | `/analytics/count-by-tier` | none | `CountOut[]` |
| `GET` | `/analytics/average-salary-by-role` | none | `AverageOut[]` |
| `GET` | `/analytics/revenue-by-payment-method` | none | `RevenueOut[]` |
| `GET` | `/analytics/revenue-by-channel` | none | `RevenueOut[]` |
| `GET` | `/analytics/count-by-category` | none | `CountOut[]` |
| `GET` | `/analytics/transaction-count-by-month` | `year` | `MonthlyCountOut[]` |
| `GET` | `/analytics/average-price-by-metal` | none | `AverageOut[]` |
| `GET` | `/analytics/employee-revenue` | none | `EmployeeRevenueOut[]` |
| `GET` | `/analytics/employee-transaction-counts` | `year` (optional) | `{ employee_id, name, transaction_count }[]` |
| `GET` | `/analytics/customer-metal-preference-match` | none | `ShopperOut[]` |
| `GET` | `/analytics/validate-lifetime-spend` | none | `ValidationIssueOut[]` |
| `GET` | `/analytics/validate-transaction-totals` | none | `TransactionValidationOut[]` |
| `GET` | `/analytics/most-frequent-customer-employee-pair` | none | `CustomerEmployeePairOut[]` |
| `GET` | `/analytics/category-popularity` | none | `CategoryPopularityOut[]` |
| `GET` | `/analytics/specialties-without-purchases` | none | `{ employee_id, name, specialty }[]` |
| `GET` | `/analytics/shopper-transaction-totals` | none | `{ shopper_id, customer_id, name, lifetime_spend, transaction_total, difference }[]` |
| `GET` | `/analytics/ethically-sourced-below-budget` | none | `ProductOut[]` |
| `GET` | `/analytics/low-stock` | none | `LowStockOut[]` |
| `GET` | `/analytics/employee-by-transaction-and-customer` | `transaction_id`, `customer_name` | `EmployeeDetailOut` |
| `GET` | `/analytics/product-by-customer-and-date` | `customer_name`, `date` | `ProductDetailOut` |
| `GET` | `/analytics/customers-by-employee-name` | `employee_name` | `ShopperOut[]` |
| `GET` | `/analytics/products-by-customer-name` | `customer_name` | `ProductOut[]` |
| `GET` | `/analytics/customer-by-purchase-price` | `price_usd` | `ShopperOut[]` |
| `GET` | `/analytics/platinum-instore-customers` | none | `ShopperOut[]` |
| `GET` | `/analytics/gemologist-most-transactions` | none | `{ employee_id, name, transaction_count }[]` |
| `GET` | `/analytics/employees-no-private-appointments` | none | `EmployeeOut[]` |
| `GET` | `/analytics/purchase-on-anniversary` | none | `ShopperOut[]` |
| `GET` | `/analytics/transactions-with-quantity` | `min_quantity=2` | `TransactionOut[]` |
| `GET` | `/analytics/shoppers-anniversary-month` | `month` | `ShopperOut[]` |
| `GET` | `/analytics/days-between-transactions` | `transaction_id_a`, `transaction_id_b` | `{ transaction_a, transaction_b, days }` |
| `GET` | `/analytics/employees-born-in-decade` | `start_year` | `EmployeeOut[]` |
| `GET` | `/analytics/employee-age-at-hire` | `name` | `{ name, hire_date, age_at_hire }` |
| `GET` | `/analytics/customer-most-purchase-years` | none | `{ customer_id, name, distinct_years }[]` |
| `GET` | `/analytics/existence/products-with-gemstones` | `gemstones` (comma-separated) | `ExistenceOut` |
| `GET` | `/analytics/existence/shopper-metals` | `metals` (comma-separated) | `ExistenceOut` |
| `GET` | `/analytics/existence/zero-gemstones-above-price` | `price` | `ExistenceOut` |
| `GET` | `/analytics/existence/transaction-discount` | `discount_pct` | `ExistenceOut` |
| `GET` | `/analytics/existence/emergency-contact-relation` | `relation` | `ExistenceOut` |

## Shared Shapes

`Address`: `{ street?, city?, state?, zip?, country? }`

Dates are ISO strings (`YYYY-MM-DD`). Optional fields may be `null`.

## Employees

`EmployeeOut` fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Numeric primary key for paths |
| `employee_id` | string | Business code like `E-0004` |
| `name` | string | |
| `date_of_birth` | date/null | |
| `gender` | string/null | |
| `role` | string/null | |
| `email` | string/null | |
| `phone` | string/null | |
| `hire_date` | date/null | |
| `salary_usd` | number/null | Annual salary |
| `notes` | string/null | |

`EmployeeDetailOut` adds:

- `address`: `Address | null`
- `languages`: `[{ id, language }]`
- `specialties`: `[{ id, specialty }]`
- `emergency_contact`: `{ name?, relation?, phone? } | null`

`EmployeeCreate` body:

```json
{
  "employee_id": "E-0101",
  "name": "Avery Stone",
  "date_of_birth": "1990-01-15",
  "gender": "Nonbinary",
  "role": "Sales Associate",
  "email": "avery@example.com",
  "phone": "555-0101",
  "hire_date": "2024-04-01",
  "salary_usd": 72000,
  "notes": "Optional notes",
  "address": { "street": "1 Main St", "city": "New York", "state": "NY", "zip": "10001", "country": "USA" },
  "languages": ["English", "Spanish"],
  "specialties": ["Diamonds"],
  "emergency_contact": { "name": "Jordan Stone", "relation": "Sibling", "phone": "555-0102" }
}
```

Required on create: `employee_id`, `name`. `EmployeeUpdate` supports only these top-level fields: `name`, `date_of_birth`, `gender`, `role`, `email`, `phone`, `hire_date`, `salary_usd`, `notes`.

## Products

`ProductOut` fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Numeric primary key for paths |
| `product_id` | string | Business code like `P-0012` |
| `name` | string | |
| `category` | string/null | |
| `collection` | string/null | |
| `metal` | string/null | |
| `price_usd` | number/null | |
| `weight_grams` | number/null | |
| `in_stock` | int/null | |
| `ethically_sourced` | bool/null | |
| `description` | string/null | |

`ProductDetailOut` adds `gemstones`: `[{ id, gemstone }]`.

`ProductCreate` body:

```json
{
  "product_id": "P-0101",
  "name": "Celestial Halo Ring",
  "category": "Ring",
  "collection": "Celestial",
  "metal": "Platinum",
  "price_usd": 2400,
  "weight_grams": 4.2,
  "in_stock": 5,
  "ethically_sourced": true,
  "description": "Optional description",
  "gemstones": ["Diamond", "Sapphire"]
}
```

Required on create: `product_id`, `name`. `ProductUpdate` supports only these top-level fields: `name`, `category`, `collection`, `metal`, `price_usd`, `weight_grams`, `in_stock`, `ethically_sourced`, `description`.

## Shoppers / Customers

The API path is `/shoppers`; user questions may say "customers". `customer_id` is the business code.

`ShopperOut` fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Numeric primary key for paths |
| `customer_id` | string | Business code like `C-0025` |
| `name` | string | |
| `age` | int/null | |
| `gender` | string/null | |
| `email` | string/null | |
| `phone` | string/null | |
| `ring_size` | number/null | |
| `birthstone` | string/null | |
| `anniversary` | date/null | |
| `partner_name` | string/null | |
| `loyalty_tier` | string/null | |
| `lifetime_spend_usd` | number/null | |
| `communication_preference` | string/null | |
| `marketing_opt_in` | bool/null | |
| `notes` | string/null | |

`ShopperDetailOut` adds:

- `address`: `Address | null`
- `preferences`: `{ style?, ethical_only?, budget_min?, budget_max? } | null`
- `preference_metals`: `[{ id, metal }]`
- `preference_gemstones`: `[{ id, gemstone }]`
- `preference_avoids`: `[{ id, avoid }]`
- `diamond_specs`: `{ cut?, min_carat?, min_clarity?, min_color? } | null`
- `allergies`: `[{ id, allergy }]`
- `purchase_history`: `[{ id, date?, item?, price_usd? }]`

`ShopperCreate` body:

```json
{
  "customer_id": "C-0101",
  "name": "Mina Patel",
  "age": 34,
  "gender": "Female",
  "email": "mina@example.com",
  "phone": "555-0201",
  "ring_size": 6.5,
  "birthstone": "Emerald",
  "anniversary": "2020-06-10",
  "partner_name": "Sam Patel",
  "loyalty_tier": "Gold",
  "lifetime_spend_usd": 3500,
  "communication_preference": "email",
  "marketing_opt_in": true,
  "notes": "Optional notes",
  "address": { "street": "2 Market St", "city": "San Francisco", "state": "CA", "zip": "94105", "country": "USA" },
  "preferences": { "style": "Minimal", "ethical_only": true, "budget_min": 1000, "budget_max": 5000 },
  "preference_metals": ["Gold", "Platinum"],
  "preference_gemstones": ["Emerald"],
  "preference_avoids": ["Nickel"],
  "diamond_specs": { "cut": "Round", "min_carat": 1.0, "min_clarity": "VS1", "min_color": "G" },
  "allergies": ["Nickel"],
  "purchase_history": [{ "date": "2025-02-14", "item": "Bracelet", "price_usd": 450 }]
}
```

Required on create: `customer_id`, `name`. `ShopperUpdate` supports only these top-level fields: `name`, `age`, `gender`, `email`, `phone`, `ring_size`, `birthstone`, `anniversary`, `partner_name`, `loyalty_tier`, `lifetime_spend_usd`, `communication_preference`, `marketing_opt_in`, `notes`.

## Transactions

`TransactionOut` fields:

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | Numeric primary key for paths |
| `transaction_id` | string | Business code like `T-0031` |
| `date` | date/null | |
| `customer_id` | int/null | FK to `shoppers.id`, not `C-*` |
| `employee_id` | int/null | FK to `employees.id`, not `E-*` |
| `product_id` | int/null | FK to `products.id`, not `P-*` |
| `quantity` | int/null | |
| `unit_price_usd` | number/null | |
| `discount_pct` | number/null | `10` means 10% |
| `total_usd` | number/null | Post-discount total |
| `payment_method` | string/null | |
| `channel` | string/null | |
| `notes` | string/null | |

`TransactionFullOut` replaces flat FK ids with:

- `shopper`: `ShopperOut | null`
- `employee`: `EmployeeOut | null`
- `product`: `ProductOut | null`

`TransactionCreate` body:

```json
{
  "transaction_id": "T-0101",
  "date": "2026-05-29",
  "customer_id": 25,
  "employee_id": 4,
  "product_id": 12,
  "quantity": 1,
  "unit_price_usd": 2400,
  "discount_pct": 10,
  "total_usd": 2160,
  "payment_method": "card",
  "channel": "in-store",
  "notes": "Optional notes"
}
```

Required on create: `transaction_id`; FK fields are optional in schema but should be valid numeric ids when supplied. `TransactionUpdate` supports all fields except `transaction_id`.

## Analytics Response Shapes

`GET /analytics/top-customers?limit=10` returns:

```json
[
  { "shopper_id": 25, "customer_id": "C-0025", "name": "William Chen", "total_spent": 12345.67 }
]
```

`GET /analytics/top-employees?limit=10` returns:

```json
[
  { "employee_id": 4, "employee_id_code": "E-0004", "name": "Riley Brooks", "total_sales": 9876.54 }
]
```

`GET /analytics/product-sales?limit=10` returns:

```json
[
  { "product_id": 12, "product_id_code": "P-0012", "name": "Celestial Halo Ring", "total_quantity": 8, "total_revenue": 19200.0 }
]
```

`GET /analytics/employee-revenue` returns:

```json
[
  { "employee_id": 4, "employee_id_code": "E-0004", "name": "Riley Brooks", "total_revenue": 9876.54 }
]
```

`GET /analytics/count-by-tier` returns `CountOut[]`:

```json
[
  { "label": "platinum", "count": 12 }
]
```

`GET /analytics/average-salary-by-role` returns `AverageOut[]`:

```json
[
  { "label": "Sales Associate", "average": 52000.0 }
]
```

`GET /analytics/revenue-by-payment-method` and `revenue-by-channel` return `RevenueOut[]`:

```json
[
  { "label": "card", "total_revenue": 456000.0 }
]
```

`GET /analytics/transaction-count-by-month?year=2024` returns `MonthlyCountOut[]`:

```json
[
  { "month": 1, "count": 23 }
]
```

`GET /analytics/validate-lifetime-spend` returns `ValidationIssueOut[]`:

```json
[
  { "shopper_id": 5, "customer_id": "C-0005", "name": "Alice", "lifetime_spend": 1000.0, "purchase_history_sum": 950.0, "difference": 50.0 }
]
```

`GET /analytics/validate-transaction-totals` returns `TransactionValidationOut[]`:

```json
[
  { "transaction_id": "T-0001", "date": "2024-01-15", "unit_price_usd": 1000.0, "quantity": 1, "discount_pct": 10.0, "total_usd": 800.0, "computed_total": 900.0 }
```

`GET /analytics/low-stock` returns `LowStockOut[]`:

```json
[
  { "product_id": "P-0012", "name": "Celestial Halo Ring", "in_stock": 0, "category": "Ring" }
]
```

`GET /analytics/existence/*` endpoints return `ExistenceOut`:

```json
{ "exists": true }
```

`GET /analytics/days-between-transactions` returns:

```json
{ "transaction_a": "T-100001", "transaction_b": "T-100030", "days": 45 }
```

`GET /analytics/employee-age-at-hire` returns:

```json
{ "name": "Beatrice Lindgren", "hire_date": "2014-06-01", "age_at_hire": 28 }
```

## Common Query Patterns

- **Find by business code:** use `GET /{resource}/by-{code}/{value}`
- **Find by name:** use `GET /{resource}/by-name/{name}`
- **Filter lists:** use query parameters on `GET /{resource}` instead of listing everything
- **Text search:** use `GET /{resource}/search/?q={term}`
- **Rankings:** use analytics endpoints when available
- **Cross-table lookups:** use dedicated analytics endpoints (`employee-by-transaction-and-customer`, `products-by-customer-name`, etc.)
- **Date queries:** use date filter params on lists or dedicated analytics date endpoints
- **Existence checks:** use `GET /analytics/existence/*` endpoints
