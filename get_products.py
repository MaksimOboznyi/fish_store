import requests

STRAPI_PRODUCTS_URL = "http://localhost:1337/api/products"

def fetch_products():
    response = requests	.get(STRAPI_PRODUCTS_URL)
    response.raise_for_status()
    return response.json()

def main():
    products = fetch_products()
    print(products)


if __name__ == "__main__":
    main()
        
