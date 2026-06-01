---
name: lumenstone-db
description: >-
  Use when answering Lumen & Stone data questions through the FastAPI HTTP API
  at mock-backend, including employees, products, shoppers/customers,
  transactions, analytics, CRUD, lookup, ranking, totals, and joined records;
  not direct SQL or Postgres.
---

# Lumenstone Data API Access

> **This is a skill, not a tool.** Do not emit a tool call named `lumenstone-db`. To use this skill, invoke it through the agent's skill system (e.g. the `Skill` tool). To query data, use `curl`, the helper scripts, or Python HTTP requests as shown below.

All data access goes through the **HTTP API** (`mock-backend`). Do not connect to PostgreSQL, run SQL, or use `psql`. The API reads from the database behind the scenes.

## Base URL

| Environment | URL |
|-------------|-----|
| Local (default) | `http://localhost:8000/api/v1` |
| Override | Set `LUMENSTONE_API_URL` (no trailing slash) |

Check the service:

```bash
curl -s http://localhost:8000/api/v1/health
# {"status":"ok"}
```

OpenAPI docs (when server is running): `http://localhost:8000/docs`

## Complete Endpoint Map

All paths are under `BASE=http://localhost:8000/api/v1`.

### Employees

| Need | Method + path | Query/body |
|------|---------------|------------|
| List employees | `GET /employees` | `skip`, `limit`, `role`, `hire_date_after`, `hire_date_before`, `state`, `language`, `specialty`, `sort_by`, `order` |
| Employee detail | `GET /employees/{id}` | numeric `id`; adds address, languages, specialties, emergency contact |
| By business code | `GET /employees/by-employee-id/{employee_id}` | e.g. `E-0004` |
| By name | `GET /employees/by-name/{name}` | exact name, case-insensitive |
| Search | `GET /employees/search/?q={term}` | searches name, email, notes |
| Create employee | `POST /employees` | `EmployeeCreate` JSON |
| Update employee | `PUT /employees/{id}` | partial `EmployeeUpdate` JSON |
| Delete employee | `DELETE /employees/{id}` | numeric `id` |

### Products

| Need | Method + path | Query/body |
|------|---------------|------------|
| List products | `GET /products` | `skip`, `limit`, `category`, `metal`, `min_price`, `max_price`, `ethically_sourced`, `gemstone`, `in_stock_min`, `in_stock_max`, `sort_by`, `order` |
| Product detail | `GET /products/{id}` | numeric `id`; adds gemstones |
| By business code | `GET /products/by-product-id/{product_id}` | e.g. `P-0012` |
| By name | `GET /products/by-name/{name}` | exact name, case-insensitive |
| Search | `GET /products/search/?q={term}` | searches name, description, category |
| Create product | `POST /products` | `ProductCreate` JSON |
| Update product | `PUT /products/{id}` | partial `ProductUpdate` JSON |
| Delete product | `DELETE /products/{id}` | numeric `id` |

### Shoppers / Customers

| Need | Method + path | Query/body |
|------|---------------|------------|
| List shoppers | `GET /shoppers` | `skip`, `limit`, `loyalty_tier`, `allergy`, `communication_preference`, `marketing_opt_in`, `min_budget`, `max_budget`, `state`, `style`, `sort_by`, `order` |
| Shopper detail | `GET /shoppers/{id}` | numeric `id`; adds address, preferences, allergies, purchase history |
| By business code | `GET /shoppers/by-customer-id/{customer_id}` | e.g. `C-0025` |
| By name | `GET /shoppers/by-name/{name}` | exact name, case-insensitive |
| Search | `GET /shoppers/search/?q={term}` | searches name, email, notes |
| Create shopper | `POST /shoppers` | `ShopperCreate` JSON |
| Update shopper | `PUT /shoppers/{id}` | partial `ShopperUpdate` JSON |
| Delete shopper | `DELETE /shoppers/{id}` | numeric `id` |

### Transactions

| Need | Method + path | Query/body |
|------|---------------|------------|
| List transactions | `GET /transactions` | `skip`, `limit`, `payment_method`, `channel`, `min_discount`, `max_discount`, `date_after`, `date_before`, `customer_id`, `employee_id`, `product_id`, `sort_by`, `order` |
| Transaction detail | `GET /transactions/{id}` | numeric `id`; nested shopper, employee, product |
| By business code | `GET /transactions/by-transaction-id/{transaction_id}` | e.g. `T-0031` |
| Search | `GET /transactions/search/?q={term}` | searches notes |
| Create transaction | `POST /transactions` | `TransactionCreate` JSON; FK ids are numeric ids |
| Update transaction | `PUT /transactions/{id}` | partial `TransactionUpdate` JSON |
| Delete transaction | `DELETE /transactions/{id}` | numeric `id` |

### Analytics

| Need | Method + path | Query/body |
|------|---------------|------------|
| Top customers by spend | `GET /analytics/top-customers` | `limit` |
| Top employees by sales | `GET /analytics/top-employees` | `limit` |
| Product sales by revenue | `GET /analytics/product-sales` | `limit` |
| Joined transaction list | `GET /analytics/transactions/full` | `skip`, `limit`; nested shopper, employee, product |
| Count shoppers by tier | `GET /analytics/count-by-tier` | none |
| Average salary by role | `GET /analytics/average-salary-by-role` | none |
| Revenue by payment method | `GET /analytics/revenue-by-payment-method` | none |
| Revenue by channel | `GET /analytics/revenue-by-channel` | none |
| Count products by category | `GET /analytics/count-by-category` | none |
| Transaction count by month | `GET /analytics/transaction-count-by-month` | `year` |
| Average price by metal | `GET /analytics/average-price-by-metal` | none |
| Employee total revenue | `GET /analytics/employee-revenue` | none |
| Employee transaction counts | `GET /analytics/employee-transaction-counts` | `year` (optional) |
| Customer metal preference match | `GET /analytics/customer-metal-preference-match` | none |
| Validate lifetime spend | `GET /analytics/validate-lifetime-spend` | none |
| Validate transaction totals | `GET /analytics/validate-transaction-totals` | none |
| Most frequent customer-employee pair | `GET /analytics/most-frequent-customer-employee-pair` | none |
| Category popularity | `GET /analytics/category-popularity` | none |
| Specialties without purchases | `GET /analytics/specialties-without-purchases` | none |
| Shopper transaction totals | `GET /analytics/shopper-transaction-totals` | none |
| Ethically sourced below bronze budget | `GET /analytics/ethically-sourced-below-budget` | none |
| Low stock products | `GET /analytics/low-stock` | none |
| Employee by transaction + customer | `GET /analytics/employee-by-transaction-and-customer` | `transaction_id`, `customer_name` |
| Product by customer + date | `GET /analytics/product-by-customer-and-date` | `customer_name`, `date` |
| Customers by employee name | `GET /analytics/customers-by-employee-name` | `employee_name` |
| Products by customer name | `GET /analytics/products-by-customer-name` | `customer_name` |
| Customer by purchase price | `GET /analytics/customer-by-purchase-price` | `price_usd` |
| Platinum in-store customers | `GET /analytics/platinum-instore-customers` | none |
| Gemologist most transactions | `GET /analytics/gemologist-most-transactions` | none |
| Employees no private appointments | `GET /analytics/employees-no-private-appointments` | none |
| Purchase on anniversary | `GET /analytics/purchase-on-anniversary` | none |
| Transactions with quantity | `GET /analytics/transactions-with-quantity` | `min_quantity` |
| Shoppers by anniversary month | `GET /analytics/shoppers-anniversary-month` | `month` |
| Days between transactions | `GET /analytics/days-between-transactions` | `transaction_id_a`, `transaction_id_b` |
| Employees born in decade | `GET /analytics/employees-born-in-decade` | `start_year` |
| Employee age at hire | `GET /analytics/employee-age-at-hire` | `name` |
| Customer most purchase years | `GET /analytics/customer-most-purchase-years` | none |
| Existence: products with gemstones | `GET /analytics/existence/products-with-gemstones` | `gemstones` (comma-separated) |
| Existence: shopper metals | `GET /analytics/existence/shopper-metals` | `metals` (comma-separated) |
| Existence: zero gemstones above price | `GET /analytics/existence/zero-gemstones-above-price` | `price` |
| Existence: transaction discount exact | `GET /analytics/existence/transaction-discount` | `discount_pct` |
| Existence: emergency contact relation | `GET /analytics/existence/emergency-contact-relation` | `relation` |

Prefer **GET** for lookups unless the task explicitly requires writes. For write body fields, read [references/api.md](references/api.md) before sending the request.

## ID fields (important)

| In API path `{id}` | In JSON body | Meaning |
|--------------------|--------------|---------|
| Numeric `id` | `id` | Primary key — **use this in URLs** |
| — | `employee_id` | Business code, e.g. `E-0004` |
| — | `product_id` | Business code, e.g. `P-0012` |
| — | `customer_id` | Business code, e.g. `C-0025` |
| — | `transaction_id` | Business code, e.g. `T-0031` |

`GET /employees/E-0004` returns **404**. Use `GET /employees/by-employee-id/E-0004` instead, or resolve via list + match.

## How to query

### 1. curl (preferred)

```bash
BASE=http://localhost:8000/api/v1

# list and detail
curl -s "$BASE/employees?limit=100"
curl -s "$BASE/employees/4"
curl -s "$BASE/products?skip=0&limit=100"
curl -s "$BASE/shoppers/25"
curl -s "$BASE/transactions/12"

# business code lookups
curl -s "$BASE/employees/by-employee-id/E-0004"
curl -s "$BASE/products/by-product-id/P-0012"
curl -s "$BASE/shoppers/by-customer-id/C-0025"
curl -s "$BASE/transactions/by-transaction-id/T-0031"

# filtering
curl -s "$BASE/products?category=ring&sort_by=price_usd&order=desc"
curl -s "$BASE/shoppers?loyalty_tier=platinum&sort_by=lifetime_spend_usd&order=desc"
curl -s "$BASE/transactions?payment_method=financing&date_after=2024-01-01"

# search
curl -s "$BASE/products/search/?q=gold"
curl -s "$BASE/employees/search/?q=VIP"

# analytics
curl -s "$BASE/analytics/top-customers?limit=5"
curl -s "$BASE/analytics/top-employees?limit=5"
curl -s "$BASE/analytics/product-sales?limit=5"
curl -s "$BASE/analytics/transactions/full?limit=50"
curl -s "$BASE/analytics/count-by-tier"
curl -s "$BASE/analytics/employee-revenue"
curl -s "$BASE/analytics/low-stock"

# write example: update one field
curl -s -X PUT "$BASE/products/12" \
  -H "Content-Type: application/json" \
  -d '{"in_stock": 7}'
```

### 2. Helper script (stdlib only)

```bash
# GET any path (leading slash optional)
python .claude/skills/lumenstone-db/scripts/api_get.py employees
python .claude/skills/lumenstone-db/scripts/api_get.py /analytics/top-customers --query limit=3

# Find one record by business code or exact field value
python .claude/skills/lumenstone-db/scripts/api_find.py employees --by employee_id --value E-0004 --detail
python .claude/skills/lumenstone-db/scripts/api_find.py products --by name --value "Celestial Halo Ring" --detail
python .claude/skills/lumenstone-db/scripts/api_find.py shoppers --by customer_id --value C-0025 --detail
python .claude/skills/lumenstone-db/scripts/api_find.py transactions --by transaction_id --value T-0007 --detail
```

Stdout is JSON. Exit `1` if not found or API unreachable.

### 3. Python (httpx / requests)

```python
import os
import httpx

base = os.getenv("LUMENSTONE_API_URL", "http://localhost:8000/api/v1")

# by business code
detail = httpx.get(f"{base}/employees/by-employee-id/E-0004").json()

# filter + sort
products = httpx.get(f"{base}/products", params={
    "category": "ring",
    "min_price": 1000,
    "sort_by": "price_usd",
    "order": "desc"
}).json()

# analytics
revenue = httpx.get(f"{base}/analytics/revenue-by-payment-method").json()
```

## Query Recipe Index

**By business code** (`E-*`, `P-*`, `C-*`, `T-*`):

Use the dedicated `by-{code}` endpoints:
- `GET /employees/by-employee-id/E-0004`
- `GET /products/by-product-id/P-0012`
- `GET /shoppers/by-customer-id/C-0025`
- `GET /transactions/by-transaction-id/T-0031`

**By person or product name:**

Use the dedicated `by-name` endpoints:
- `GET /employees/by-name/Beatrice%20Lindgren`
- `GET /products/by-name/Solstice%20Moonstone%20Ring`
- `GET /shoppers/by-name/Marcus%20Okonkwo`

**Rankings / totals:**

- Top spenders → `GET /analytics/top-customers`
- Top sellers → `GET /analytics/top-employees`
- Product revenue → `GET /analytics/product-sales`
- Employee total revenue → `GET /analytics/employee-revenue`
- Full sale context → `GET /analytics/transactions/full` or `GET /transactions/{id}`

**Filtering:**

Use server-side query parameters on list endpoints instead of fetching everything:
- Employees by role, hire date, state, language, specialty → `GET /employees?role=...&state=...`
- Products by category, metal, price range, ethically sourced, gemstone, stock → `GET /products?category=...&min_price=...`
- Shoppers by tier, allergy, communication preference, budget, state, style → `GET /shoppers?loyalty_tier=...&allergy=...`
- Transactions by payment method, channel, discount range, date range, FKs → `GET /transactions?payment_method=...&date_after=...`

**Search:**

- Text search in names, descriptions, notes → `GET /{resource}/search/?q=...`

**By nested detail:**

- Employee address/languages/specialties/emergency contact → `GET /employees/{id}`
- Product gemstones → `GET /products/{id}`
- Shopper preferences, metals, gemstones, avoids, diamond specs, allergies, purchase history → `GET /shoppers/{id}`
- Transaction shopper/employee/product names → `GET /transactions/{id}` or `GET /analytics/transactions/full`

**Date-based queries:**

- Hire date range → `GET /employees?hire_date_after=2021-01-01`
- Transactions by year/month → `GET /analytics/transaction-count-by-month?year=2024`
- Days between two transactions → `GET /analytics/days-between-transactions?transaction_id_a=T-100001&transaction_id_b=T-100030`
- Employees born in a decade → `GET /analytics/employees-born-in-decade?start_year=1970`
- Age at hire → `GET /analytics/employee-age-at-hire?name=Beatrice%20Lindgren`
- Anniversary month → `GET /analytics/shoppers-anniversary-month?month=6`
- Purchase on anniversary → `GET /analytics/purchase-on-anniversary`

**Boolean / existence checks:**

- Product with multiple gemstones → `GET /analytics/existence/products-with-gemstones?gemstones=sapphire,diamond`
- Shopper with multiple metal preferences → `GET /analytics/existence/shopper-metals?metals=yellow%20gold,platinum`
- Zero gemstones above price → `GET /analytics/existence/zero-gemstones-above-price?price=500`
- Exact discount → `GET /analytics/existence/transaction-discount?discount_pct=10`
- Emergency contact relation → `GET /analytics/existence/emergency-contact-relation?relation=sister`

**Cross-table lookups:**

- Employee who served a customer on a transaction → `GET /analytics/employee-by-transaction-and-customer?transaction_id=T-100009&customer_name=Marcus%20Okonkwo`
- Product bought by customer on date → `GET /analytics/product-by-customer-and-date?customer_name=Amelia%20Hartwell&date=2024-08-19`
- Customers of an employee → `GET /analytics/customers-by-employee-name?employee_name=Yasmin%20Haddad`
- Products purchased by a customer → `GET /analytics/products-by-customer-name?customer_name=Asha%20Mensah`
- Customer by exact purchase price → `GET /analytics/customer-by-purchase-price?price_usd=6200`
- Platinum customers with in-store purchases → `GET /analytics/platinum-instore-customers`
- Gemologist with most transactions → `GET /analytics/gemologist-most-transactions`
- Employees never handling private appointments → `GET /analytics/employees-no-private-appointments`

**Validation / complex reasoning:**

- Lifetime spend vs purchase history mismatch → `GET /analytics/validate-lifetime-spend`
- Transaction total math errors → `GET /analytics/validate-transaction-totals`
- Customer metal preference matching purchased product → `GET /analytics/customer-metal-preference-match`
- Low or out-of-stock products → `GET /analytics/low-stock`
- Most frequent customer-employee pair → `GET /analytics/most-frequent-customer-employee-pair`
- Category popularity → `GET /analytics/category-popularity`

**Create/update/delete:**

Only write when the user asks to mutate data. Use `POST` to create, `PUT /{id}` for partial top-level updates, and `DELETE /{id}` to delete. Nested child records can be supplied on create; the current update schemas only update top-level fields. Transaction FK fields (`customer_id`, `employee_id`, `product_id`) expect numeric primary keys, not business codes.

## Response shapes (summary)

List endpoints return arrays of flat records. Detail endpoints add nested objects:

- **Employee detail:** `address`, `languages[]`, `specialties[]`, `emergency_contact`
- **Product detail:** `gemstones[]`
- **Shopper detail:** `address`, `preferences`, `preference_metals[]`, `preference_gemstones[]`, `preference_avoids[]`, `diamond_specs`, `allergies[]`, `purchase_history[]`
- **Transaction detail:** `shopper`, `employee`, `product` (each flat `*Out` shape)

Field reference: [references/api.md](references/api.md)

## Rules for agents

1. **This is a skill, not a tool.** Never emit a `lumenstone-db` tool call. Query data with `curl`, the helper scripts, or Python HTTP clients only.
2. **Only use the HTTP API** — never SQL, asyncpg, or direct DB URLs.
3. Confirm **`/health`** returns `ok` before querying.
4. Path parameters are **numeric `id`**, not business codes — except for the dedicated `by-employee-id`, `by-product-id`, `by-customer-id`, `by-transaction-id`, and `by-name` endpoints.
5. Use **analytics** endpoints for rankings/totals when one exists; avoid manual aggregation over full lists for top customers, top employees, product revenue, employee revenue, category popularity, etc.
6. Use **server-side query parameters** for filtering (`role=`, `category=`, `loyalty_tier=`, `payment_method=`, `date_after=`, etc.) instead of fetching entire collections and filtering client-side.
7. Use **dedicated lookup endpoints** (`by-employee-id`, `by-name`, etc.) instead of listing and scanning client-side.
8. Use **search endpoints** (`/search/?q=`) for text matching instead of listing and scanning.
9. Paginate large lists with `skip` and `limit` (default `skip=0`, `limit=100` for lists; default analytics `limit=10`).
10. For nested data, call the **detail** endpoint or `/analytics/transactions/full`, not the flat list endpoint.
11. For date-based queries, use the **analytics date endpoints** when available instead of fetching all records and filtering client-side.
12. For existence checks, use the **analytics existence endpoints** when available.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Connection refused :8000 | `docker compose up -d mock-backend` from repo root |
| `{"detail":"Employee not found"}` | Wrong numeric id; use `by-employee-id` or list + match business code |
| Empty `[]` | Run `docker compose exec mock-backend python seed.py` |
| 404 with code in URL | Use `by-employee-id`, `by-product-id`, etc., or numeric `id` in path |
