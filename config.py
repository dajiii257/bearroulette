# -*- coding: utf-8 -*-
"""
Единый конфиг проекта Bear Bot.
Все настройки здесь — без .env.
"""

# ═══════════════════════════════════════════════════════════
# TELEGRAM BOT
# ═══════════════════════════════════════════════════════════
BOT_TOKEN = "9166521409:AAERkF2DZNqjlBfz5ekiylllLuXRvbjHMUw"
BOT_USERNAME = "BearRouletteBot"

# Админы (telegram user id). Несколько штук.
ADMIN_IDS = [
    52841421,
    8307076618,
    8941580208,  # замени на свои
    # 987654321,
]

# ═══════════════════════════════════════════════════════════
# WEBAPP / API
# ═══════════════════════════════════════════════════════════
# Публичный URL, по которому открывается Mini App (без слэша в конце)
WEBAPP_URL = "https://your.domain"

# Хост/порт API+статики (для запуска)
API_HOST = "0.0.0.0"
API_PORT = 8080

# ═══════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════
# SQLite для старта. Для продакшена замени на PostgreSQL:
# DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/bearbot"
DATABASE_URL = "sqlite+aiosqlite:///./bearbot.db"

# ═══════════════════════════════════════════════════════════
# USERBOT (отправка подарков)
# ═══════════════════════════════════════════════════════════
# На первом этапе можно оставить заглушку (USERBOT_ENABLED = False)
USERBOT_ENABLED = False
USERBOT_API_ID = 0
USERBOT_API_HASH = ""
USERBOT_SESSION = ""          # строка StringSession
USERBOT_USERNAME = "BearsRelayer2"

# ═══════════════════════════════════════════════════════════
# СПОНСОР-КАНАЛЫ / ЧАТЫ
# type: "channel" | "group"
# join: "public" | "private" | "request"   (открытый / инвайт / по заявкам)
# url:  ссылка для кнопки (t.me/... или https://t.me/+)
# chat_id: числовой id ИЛИ @username — для проверки подписки
# ═══════════════════════════════════════════════════════════
SPONSOR_CHANNELS = [
    {
        "title": "Канал спонсора #1",
        "chat_id": "@your_channel",      # или -1001234567890
        "url": "https://t.me/your_channel",
        "type": "channel",
        "join": "public",
    },
    {
        "title": "Канал спонсора #2",
        "chat_id": "@another_channel",
        "url": "https://t.me/another_channel",
        "type": "channel",
        "join": "public",
    },
    # Пример закрытого чата по заявкам:
    # {
    #     "title": "Закрытый чат",
    #     "chat_id": -1001234567890,
    #     "url": "https://t.me/+AbCdEfGhIjK",
    #     "type": "group",
    #     "join": "request",
    # },
]

# После проигрыша — доп. оффер «+N прокрутов за подписку на партнёров»
PARTNER_SPIN_BONUS = 5
PARTNER_CHANNELS = [
    {
        "title": "Партнёр #1",
        "chat_id": "@partner_one",
        "url": "https://t.me/partner_one",
        "type": "channel",
        "join": "public",
    },
    {
        "title": "Партнёр #2",
        "chat_id": "@partner_two",
        "url": "https://t.me/partner_two",
        "type": "channel",
        "join": "public",
    },
]

# ═══════════════════════════════════════════════════════════
# ИГРОВАЯ ЛОГИКА
# ═══════════════════════════════════════════════════════════
PAID_SPIN_STARS = 5
COOLDOWN_HOURS = 24
BASE_CHANCE = 1
CHANCE_PER_FRIEND = 1
CHANCE_CAP = 10
CHANCE_STEPS = [
    {"friends": 1, "chance": 2},
    {"friends": 2, "chance": 3},
    {"friends": 15, "chance": 10},
]
PITY_DAY = 21
RARE_GAP_DAYS = 14
REF_ACTIVE_DAYS = 5
REF_BONUS_EVERY = 3
REF_BONUS_SPINS = 2
PAWS_NEED = 15
PAW_CHANCE = 5.0
FRIEND_PARTNER = {"spins": 1, "day": 2}
EXCHANGE_SPINS = 7
GIFT_SENDER = "userbot"
START_SPINS = 1  # спинов после прохождения спонсоров

WHEEL_LAYOUT = 12
WHEEL_ID = "12-e1026fda"
WHEEL_SECTORS = [
    {"a": 0.0, "half": 15.0, "type": "bear"},
    {"a": 30.0, "half": 15.0, "type": "premium"},
    {"a": 60.0, "half": 15.0, "type": "paw"},
    {"a": 90.0, "half": 15.0, "type": "nothing"},
    {"a": 120.0, "half": 15.0, "type": "skin", "slot": 0},
    {"a": 150.0, "half": 15.0, "type": "nothing"},
    {"a": 180.0, "half": 15.0, "type": "skin", "slot": 1},
    {"a": 210.0, "half": 15.0, "type": "nft"},
    {"a": 240.0, "half": 15.0, "type": "paw"},
    {"a": 270.0, "half": 15.0, "type": "nothing"},
    {"a": 300.0, "half": 15.0, "type": "skin", "slot": 2},
    {"a": 330.0, "half": 15.0, "type": "nothing"},
]
WHEEL_PAWS = [
    {"a": 49.28, "half": 6.0},
    {"a": 84.0, "half": 6.0},
    {"a": 229.28, "half": 6.0},
    {"a": 264.0, "half": 6.0},
]

PRIZES = [
    {"gift_id": "5170233102089322756", "tier": "bear", "stars": 15, "name": "Мишка"},
    {"gift_id": "5170145012310081615", "tier": "bear", "stars": 15, "name": "Сердце"},
    {"gift_id": "5170250947678437525", "tier": "skin", "stars": 25, "name": "Подарок"},
    {"gift_id": "5168103777563050263", "tier": "skin", "stars": 25, "name": "Роза"},
    {"gift_id": "5170144170496491616", "tier": "skin", "stars": 50, "name": "Торт"},
    {"gift_id": "5170314324215857265", "tier": "skin", "stars": 50, "name": "Букет"},
    {"gift_id": "5170564780938756245", "tier": "skin", "stars": 50, "name": "Ракета"},
    {"gift_id": "6028601630662853006", "tier": "skin", "stars": 50, "name": "Шампанское"},
    {"gift_id": "5168043875654172773", "tier": "skin", "stars": 100, "name": "Кубок"},
    {"gift_id": "5170690322832818290", "tier": "skin", "stars": 100, "name": "Кольцо"},
    {"gift_id": "5170521118301225164", "tier": "skin", "stars": 100, "name": "Алмаз"},
    {"gift_id": "nft_vice_cream", "tier": "nft", "stars": 0, "name": "Vice Cream NFT"},
]
PREMIUM_PRIZE = True
SHARE_TEXT = "🧸 У меня для тебя подарок! Забирай бесплатно"

# ═══════════════════════════════════════════════════════════
# КАПЧА
# ═══════════════════════════════════════════════════════════
# Папка с картинками капчи. Имя файла = ответ (без расширения).
# Пример: assets/captcha/7K2P.png  → правильный ответ "7K2P" (регистр не важен)
CAPTCHA_DIR = "assets/captcha"
CAPTCHA_LENGTH = 4  # если генерируем на лету
CAPTCHA_TTL_SECONDS = 300

# ═══════════════════════════════════════════════════════════
# ПРОЧЕЕ
# ═══════════════════════════════════════════════════════════
SPIN_RATE_LIMIT_SECONDS = 2
LOG_LEVEL = "INFO"
