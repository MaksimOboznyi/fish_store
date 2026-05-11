# Fish Store Bot

Telegram-бот для магазина рыбы.

Бот получает товары из CMS Strapi, показывает пользователю список товаров, позволяет открыть карточку товара, добавить товар в корзину, посмотреть корзину, удалить товар из корзины и оставить email для оформления заказа.

## Возможности

- Получение товаров из Strapi CMS через API
- Отображение списка товаров в Telegram
- Отображение карточки товара с фото, описанием и ценой
- Добавление товара в корзину
- Просмотр корзины
- Удаление товара из корзины
- Запрос email пользователя
- Сохранение контактов клиента в CMS

## Технологии

- Python 3.9+
- python-telegram-bot
- Redis
- Strapi CMS
- requests
- python-dotenv

## Переменные окружения

Для запуска проекта создайте файл `.env` в корне проекта.

Пример `.env`:

```env
TG_BOT_TOKEN=your_telegram_bot_token
REDIS_URL=redis://default:your_password@your_redis_host:your_redis_port/0
STRAPI_BASE_URL=http://localhost:1337
```

Описание переменных:

- `TG_BOT_TOKEN` — токен Telegram-бота от BotFather
- `REDIS_URL` — адрес подключения к Redis
- `STRAPI_BASE_URL` — адрес Strapi CMS

Если Strapi запущен локально, значение обычно такое:

```env
STRAPI_BASE_URL=http://localhost:1337
```

## Установка

Клонируйте репозиторий:

```bash
git clone https://github.com/MaksimOboznyi/fish_store.git
cd fish_store
```

Создайте виртуальное окружение:

```bash
python3 -m venv venv
```

Активируйте виртуальное окружение:

```bash
source venv/bin/activate
```

Установите зависимости:

```bash
pip install -r requirements.txt
```

## Запуск

Перед запуском убедитесь, что:

- создан файл `.env`;
- Redis доступен;
- Strapi CMS запущена;
- в Strapi добавлены товары;
- у Public Role в Strapi настроены права доступа к API.

Запустите бота:

```bash
python3 bot.py
```

После запуска отправьте боту команду:

```text
/start
```

## Настройка Strapi

Strapi используется как внешняя CMS для хранения товаров, корзин и контактов клиентов.

В Strapi должны быть созданы следующие Content Types:

### Product

Поля:

- `title` — название товара
- `description` — описание товара
- `picture` — изображение товара
- `price` — цена товара

### Cart

Поля:

- `telegram_id` — Telegram ID пользователя
- `cart_items` — связь с товарами в корзине

### CartItem

Поля:

- `quantity_kg` — количество килограммов
- `product` — связь с товаром
- `cart` — связь с корзиной

### Customer

Поля:

- `telegram_id` — Telegram ID пользователя
- `email` — email пользователя

## Права доступа в Strapi

В Strapi откройте:

```text
Settings → Users & Permissions Plugin → Roles → Public
```

Для `Product` включите:

```text
find
findOne
```

Для `Cart` включите:

```text
find
findOne
create
update
```

Для `CartItem` включите:

```text
find
findOne
create
update
delete
```

Для `Customer` включите:

```text
find
findOne
create
update
```

## Как работает бот

1. Пользователь отправляет `/start`
2. Бот показывает список товаров
3. Пользователь выбирает товар
4. Бот показывает карточку товара
5. Пользователь добавляет товар в корзину
6. Пользователь открывает корзину
7. Пользователь может удалить товар из корзины
8. Пользователь нажимает «Оплатить»
9. Бот просит email
10. Email сохраняется в CMS

## Проверка API Strapi

Получить список товаров:

```bash
curl http://localhost:1337/api/products
```

Получить товары с изображениями:

```bash
curl "http://localhost:1337/api/products?populate=picture"
```

Получить корзины с товарами:

```bash
curl "http://localhost:1337/api/carts?populate[cart_items][populate]=product"
```

