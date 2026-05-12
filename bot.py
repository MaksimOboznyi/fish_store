import os
from functools import partial
from io import BytesIO

import redis
import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    Filters,
)
from strapi_api import (
    fetch_products,
    fetch_product,
    fetch_product_image,
    fetch_cart_with_items,
    create_cart_item,
    delete_cart_item,
    create_customer,
)


START = "START"
HANDLE_MENU = "HANDLE_MENU"
HANDLE_DESCRIPTION = "HANDLE_DESCRIPTION"
HANDLE_CART = "HANDLE_CART"
WAITING_EMAIL = "WAITING_EMAIL"


def fetch_cart_by_telegram_id(strapi_base_url, telegram_id):
    response = requests.get(
        f"{strapi_base_url}/api/carts",
        params={
            "filters[telegram_id][$eq]": str(telegram_id),
        },
    )
    response.raise_for_status()

    carts = response.json()["data"]

    if not carts:
        return None

    return carts[0]


def create_cart(strapi_base_url, telegram_id):
    response = requests.post(
        f"{strapi_base_url}/api/carts",
        json={
            "data": {
                "telegram_id": str(telegram_id),
            }
        },
    )
    response.raise_for_status()

    return response.json()["data"]


def get_or_create_cart(strapi_base_url, telegram_id):
    cart = fetch_cart_by_telegram_id(strapi_base_url, telegram_id)

    if cart:
        return cart

    return create_cart(strapi_base_url, telegram_id)


def format_cart(cart):
    if not cart:
        return "Ваша корзина пока пустая."

    cart_items = cart.get("cart_items", [])

    if not cart_items:
        return "Ваша корзина пока пустая."

    message_lines = ["Ваша корзина:\n"]
    total_price = 0

    for cart_item in cart_items:
        quantity_kg = cart_item["quantity_kg"]
        product = cart_item["product"]

        title = product["title"]
        price = product["price"]

        item_total_price = price * quantity_kg
        total_price += item_total_price

        message_lines.append(
            f"• {title}\n"
            f"  Количество: {quantity_kg} кг\n"
            f"  Цена: {price} руб./кг\n"
            f"  Сумма: {item_total_price} руб.\n"
        )

    message_lines.append(f"\nИтого: {total_price} руб.")

    return "\n".join(message_lines)


def get_state(redis_client, user_id):
    state = redis_client.get(f"user:{user_id}:state")

    if state is None:
        return START

    return state.decode("utf-8")


def set_state(redis_client, user_id, state):
    redis_client.set(f"user:{user_id}:state", state)


def send_products_menu(bot, chat_id, strapi_base_url):
    products = fetch_products(strapi_base_url)

    keyboard = []

    for product in products:
        product_document_id = product["documentId"]
        title = product["title"]

        keyboard.append([
            InlineKeyboardButton(
                title,
                callback_data=f"product_{product_document_id}",
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "Моя корзина",
            callback_data="show_cart",
        )
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=chat_id,
        text="Please choose:",
        reply_markup=reply_markup,
    )


def send_cart(bot, chat_id, strapi_base_url, telegram_id):
    cart = fetch_cart_with_items(strapi_base_url, telegram_id)
    cart_text = format_cart(cart)

    keyboard = []

    if cart:
        cart_items = cart.get("cart_items", [])

        for cart_item in cart_items:
            cart_item_document_id = cart_item["documentId"]
            product = cart_item["product"]
            title = product["title"]

            keyboard.append([
                InlineKeyboardButton(
                    f"Убрать: {title}",
                    callback_data=f"remove_cart_item_{cart_item_document_id}",
                )
            ])

    keyboard.append([
        InlineKeyboardButton(
            "Оплатить",
            callback_data="checkout",
        )
    ])

    keyboard.append([
        InlineKeyboardButton(
            "В меню",
            callback_data="back_to_menu",
        )
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(
        chat_id=chat_id,
        text=cart_text,
        reply_markup=reply_markup,
    )


def handle_start(update, context, redis_client, strapi_base_url):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id

    set_state(redis_client, user_id, HANDLE_MENU)

    send_products_menu(
        bot=context.bot,
        chat_id=chat_id,
        strapi_base_url=strapi_base_url,
    )


def handle_button(update, context, redis_client, strapi_base_url):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    chat_id = query.message.chat_id
    callback_data = query.data

    state = get_state(redis_client, user_id)

    if callback_data == "back_to_menu":
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
        )

        set_state(redis_client, user_id, HANDLE_MENU)

        send_products_menu(
            bot=context.bot,
            chat_id=chat_id,
            strapi_base_url=strapi_base_url,
        )
        return

    if callback_data == "show_cart":
        send_cart(
            bot=context.bot,
            chat_id=chat_id,
            strapi_base_url=strapi_base_url,
            telegram_id=user_id,
        )

        set_state(redis_client, user_id, HANDLE_CART)
        return

    if callback_data == "checkout":
        context.bot.send_message(
            chat_id=chat_id,
            text="Введите ваш email для оформления заказа:",
        )

        set_state(redis_client, user_id, WAITING_EMAIL)
        return

    if callback_data.startswith("remove_cart_item_"):
        cart_item_document_id = callback_data.replace("remove_cart_item_", "")

        delete_cart_item(
            strapi_base_url=strapi_base_url,
            cart_item_document_id=cart_item_document_id,
        )

        context.bot.delete_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
        )

        send_cart(
            bot=context.bot,
            chat_id=chat_id,
            strapi_base_url=strapi_base_url,
            telegram_id=user_id,
        )

        set_state(redis_client, user_id, HANDLE_CART)
        return

    if callback_data.startswith("add_to_cart_"):
        product_document_id = callback_data.replace("add_to_cart_", "")

        cart = get_or_create_cart(
            strapi_base_url=strapi_base_url,
            telegram_id=user_id,
        )
        cart_document_id = cart["documentId"]

        create_cart_item(
            strapi_base_url=strapi_base_url,
            cart_document_id=cart_document_id,
            product_document_id=product_document_id,
            quantity_kg=1,
        )

        context.bot.send_message(
            chat_id=chat_id,
            text="Товар добавлен в корзину.",
        )

        set_state(redis_client, user_id, HANDLE_DESCRIPTION)
        return

    if state != HANDLE_MENU:
        query.edit_message_text("Сначала нажмите /start")
        set_state(redis_client, user_id, START)
        return

    if callback_data.startswith("product_"):
        product_id = callback_data.replace("product_", "")

        product = fetch_product(
            strapi_base_url=strapi_base_url,
            product_id=product_id,
        )

        title = product["title"]
        description = product["description"]
        price = product["price"]

        caption = (
            f"{title} ({price} руб. за кг)\n\n"
            f"{description}"
        )

        image_file = fetch_product_image(
            strapi_base_url=strapi_base_url,
            product=product,
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Добавить в корзину",
                    callback_data=f"add_to_cart_{product_id}",
                )
            ],
            [
                InlineKeyboardButton(
                    "Моя корзина",
                    callback_data="show_cart",
                )
            ],
            [
                InlineKeyboardButton(
                    "Назад",
                    callback_data="back_to_menu",
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.delete_message(
            chat_id=chat_id,
            message_id=query.message.message_id,
        )

        context.bot.send_photo(
            chat_id=chat_id,
            photo=image_file,
            caption=caption,
            reply_markup=reply_markup,
        )

        set_state(redis_client, user_id, HANDLE_DESCRIPTION)
        return

    query.edit_message_text("Неизвестная команда.")
    set_state(redis_client, user_id, START)


def handle_message(update, context, redis_client, strapi_base_url):
    user_id = update.effective_user.id
    text = update.message.text

    state = get_state(redis_client, user_id)

    if state == WAITING_EMAIL:
        email = text.strip()

        customer = create_customer(
            strapi_base_url=strapi_base_url,
            telegram_id=user_id,
            email=email,
        )

        print(f"Создан клиент в Strapi: {customer}")

        update.message.reply_text(
            f"Спасибо! Мы получили вашу почту: {email}"
        )

        set_state(redis_client, user_id, START)
        return

    update.message.reply_text(
        f"Ваше сообщение: {text}\nТекущее состояние: {state}"
    )


def main():
    load_dotenv()

    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    redis_url = os.getenv("REDIS_URL")
    strapi_base_url = os.getenv("STRAPI_BASE_URL")

    if not tg_bot_token:
        raise RuntimeError("Не найден TG_BOT_TOKEN в .env")

    if not redis_url:
        raise RuntimeError("Не найден REDIS_URL в .env")

    if not strapi_base_url:
        raise RuntimeError("Не найден STRAPI_BASE_URL в .env")

    redis_client = redis.from_url(redis_url)
    redis_client.ping()

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(
        CommandHandler(
            "start",
            partial(
                handle_start,
                redis_client=redis_client,
                strapi_base_url=strapi_base_url,
            ),
        )
    )

    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(
                handle_button,
                redis_client=redis_client,
                strapi_base_url=strapi_base_url,
            )
        )
    )

    dispatcher.add_handler(
        MessageHandler(
            Filters.text & ~Filters.command,
            partial(
                handle_message,
                redis_client=redis_client,
                strapi_base_url=strapi_base_url,
            ),
        )
    )

    print("Бот запущен")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()