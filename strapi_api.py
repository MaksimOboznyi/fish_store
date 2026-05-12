import requests
from io import BytesIO


def fetch_products(strapi_base_url):
    response = requests.get(f"{strapi_base_url}/api/products")
    response.raise_for_status()
    return response.json()["data"]


def fetch_product(strapi_base_url, product_id):
    response = requests.get(
        f"{strapi_base_url}/api/products/{product_id}?populate=picture"
    )
    response.raise_for_status()
    return response.json()["data"]


def fetch_product_image(strapi_base_url, product):
    picture = product["picture"]
    image_url = picture["url"]
    full_image_url = f"{strapi_base_url}{image_url}"

    response = requests.get(full_image_url)
    response.raise_for_status()

    image_file = BytesIO(response.content)
    image_file.name = "product.jpg"

    return image_file


def fetch_cart_with_items(strapi_base_url, telegram_id):
    response = requests.get(
        f"{strapi_base_url}/api/carts",
        params={
            "filters[telegram_id][$eq]": str(telegram_id),
            "populate[cart_items][populate]": "product",
        },
    )
    response.raise_for_status()

    carts = response.json()["data"]

    if not carts:
        return None

    return carts[0]


def create_cart_item(
    strapi_base_url,
    cart_document_id,
    product_document_id,
    quantity_kg=1,
):
    response = requests.post(
        f"{strapi_base_url}/api/cart-items",
        json={
            "data": {
                "quantity_kg": quantity_kg,
                "cart": {
                    "connect": [cart_document_id],
                },
                "product": {
                    "connect": [product_document_id],
                },
            }
        },
    )
    response.raise_for_status()

    return response.json()["data"]


def delete_cart_item(strapi_base_url, cart_item_document_id):
    response = requests.delete(
        f"{strapi_base_url}/api/cart-items/{cart_item_document_id}"
    )
    response.raise_for_status()


def create_customer(strapi_base_url, telegram_id, email):
    response = requests.post(
        f"{strapi_base_url}/api/clients",
        json={
            "data": {
                "telegram_id": str(telegram_id),
                "email": email,
            }
        },
    )
    response.raise_for_status()

    return response.json()["data"]