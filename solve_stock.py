import os
import httpx
import json

base = os.getenv("LUMENSTONE_API_URL", "http://localhost:8000/api/v1")
search_term = "Solstice Moonstone Ring"

try:
    response = httpx.get(f"{base}/products/search/?q={search_term}")
    response.raise_for_status()
    products = response.json()

    found_product = None
    for product in products:
        # Assuming 'name' field exists and checking for an 'in_stock' field
        if product.get('name') == search_term:
            found_product = product
            break

    if found_product:
        stock = found_product.get('in_stock', 'N/A')
        print(f"Stock for {search_term}: {stock}")
    else:
        print(f"Product '{search_term}' not found in search results.")

except httpx.HTTPStatusError as e:
    print(f"HTTP error occurred: {e}")
except httpx.RequestError as e:
    print(f"An error occurred while requesting {e.request.url!r}: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")