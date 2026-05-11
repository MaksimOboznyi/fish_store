import os
import requests 
from dotenv import load_dotenv


load_dotenv()

STRAPI_BASE_URL = os.getenv("STRAPI_BASE_URL")
STRAPI_PRODUCTS_URL = f"{STRAPI_BASE_URL}/api/products"

def fetch_products():
    response = requests	.get(STRAPI_PRODUCTS_URL)
    response.raise_for_status()
    return response.json()

def main():
    if not STRAPI_BASE_URL:
        raise RuntimeError("Не найден STRAPI_BASE_URL в .env")
    products = fetch_products()
    print(products)


if __name__ == "__main__":
    main()
        
