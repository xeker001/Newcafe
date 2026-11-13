import asyncio
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from admin import router as admin_router

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
INDEX_FILE = BASE_DIR / "index.html"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

PRODUCTS = {
    "classic": {"name": "NEWCAFE Classic", "description": "Klassik eruvchan qahva.", "price": 18000, "emoji": "☕"},
    "gold": {"name": "NEWCAFE Gold", "description": "Yumshoq ta'mli premium qahva.", "price": 30000, "emoji": "✨"},
    "latte": {"name": "NEWCAFE Latte", "description": "Sutli, mayin qahva ichimligi.", "price": 22000, "emoji": "🥛"},
    "americano": {"name": "Americano", "description": "Espresso va issiq suv — yengil, tetik ta'm.", "price": 16000, "emoji": "☕"},
    "espresso": {"name": "Espresso", "description": "Kichik finjonda kuchli qahva.", "price": 14000, "emoji": "⚡"},
    "cappuccino": {"name": "Cappuccino", "description": "Espresso, sut va yumshoq ko'pik.", "price": 23000, "emoji": "☁️"},
    "mocha": {"name": "Mocha", "description": "Qahva, sut va shokolad uyg'unligi.", "price": 27000, "emoji": "🍫"},
    "raf": {"name": "Raf Coffee", "description": "Qaymoqli, mayin va xushbo'y.", "price": 28000, "emoji": "🤎"},
    "iced_latte": {"name": "Iced Latte", "description": "Muzdek sutli qahva — issiq kunlar uchun.", "price": 24000, "emoji": "🧊"},
    "cold_brew": {"name": "Cold Brew", "description": "Sovuq usulda damlangan qahva.", "price": 25000, "emoji": "🥤"},
    "black_tea": {"name": "Qora choy", "description": "Limon bilan damlangan klassik choy.", "price": 8000, "emoji": "🍵"},
    "green_tea": {"name": "Ko'k choy", "description": "Yengil va yoqimli issiq choy.", "price": 8000, "emoji": "🍃"},
    "matcha": {"name": "Matcha Latte", "description": "Matcha va sutli zamonaviy ichimlik.", "price": 26000, "emoji": "🍵"},
    "croissant": {"name": "Kruassan", "description": "Qahva bilan mos, yangi pishiriq.", "price": 14000, "emoji": "🥐"},
    "cheesecake": {"name": "Cheesecake", "description": "Tanaffusga shirin qo'shimcha.", "price": 22000, "emoji": "🍰"},
    "student_combo": {"name": "Talaba seti", "description": "Americano + kruassan — dars oldidan qulay tanlov.", "price": 26000, "emoji": "🎓"},
}


def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " so'm"


def mini_app_url() -> str | None:
    configured_url = os.getenv("MINI_APP_URL", "").strip()
    if configured_url:
        return configured_url
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if railway_domain:
        return f"https://{railway_domain.removeprefix('https://')}"
    return None


def inline_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👇 Menyuni ochish", callback_data="products")],
            [InlineKeyboardButton(text="🛍 Savatcham", callback_data="cart"), InlineKeyboardButton(text="🎁 Aksiya", callback_data="promo")],
            [InlineKeyboardButton(text="ℹ️ Biz haqimizda", callback_data="about"), InlineKeyboardButton(text="📞 Aloqa", callback_data="contact")],
        ]
    )


def app_keyboard() -> ReplyKeyboardMarkup | None:
    url = mini_app_url()
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        logger.warning("MINI_APP_URL must be an absolute HTTPS URL; Mini App button is disabled.")
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🌐 NEWCAFE Mini App", web_app=WebAppInfo(url=url))]],
        resize_keyboard=True,
        is_persistent=True,
    )


def products_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f'{item["emoji"]} {item["name"]} — {money(item["price"])}', callback_data=f"product:{key}")]
        for key, item in PRODUCTS.items()
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def edit_message(message: Message, text: str, keyboard: InlineKeyboardMarkup | None = None) -> None:
    if message.photo:
        await message.edit_caption(caption=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.edit_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


async def show_products(message: Message) -> None:
    image = ASSETS_DIR / "newcafe_products.jpg"
    caption = "☕ *NEWCAFE mahsulotlari*\n\nMahsulotni tanlab, batafsil ma'lumot oling:"
    if image.is_file():
        await message.answer_photo(image, caption=caption, reply_markup=products_keyboard(), parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(caption, reply_markup=products_keyboard(), parse_mode=ParseMode.MARKDOWN)


async def show_cart(message: Message, cart: dict[str, int]) -> None:
    if not cart:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="☕ Mahsulotlarni ko'rish", callback_data="products")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")],
        ])
        await edit_message(message, "🛍 *Savatchangiz hozircha bo'sh.*\nMahsulotlar bo'limidan qahva tanlang.", keyboard)
        return
    lines = []
    total = 0
    for key, quantity in cart.items():
        item = PRODUCTS[key]
        subtotal = item["price"] * quantity
        total += subtotal
        lines.append(f'{item["emoji"]} {item["name"]} × {quantity} — {money(subtotal)}')
    text = "🛍 *Savatchangiz*\n\n" + "\n".join(lines) + f"\n\n*Jami: {money(total)}*"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Demo buyurtmani tasdiqlash", callback_data="checkout")],
        [InlineKeyboardButton(text="🗑 Savatchani tozalash", callback_data="clear")],
        [InlineKeyboardButton(text="☕ Yana mahsulot tanlash", callback_data="products")],
        [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")],
    ])
    await edit_message(message, text, keyboard)


async def start(message: Message) -> None:
    banner = ASSETS_DIR / "newcafe_banner.jpg"
    text = (
        "☕ Assalomu alaykum!\n\n"
        "NEWCAFE botiga xush kelibsiz! 👑\n\n"
        "Bu yerda siz:\n"
        "☕ Mazali kofelar menyusini ko'rishingiz;\n"
        "🛒 O'zingizga yoqqan ichimlikni tanlashingiz;\n"
        "✨ Yangi ta'mlardan bahramand bo'lishingiz mumkin.\n\n"
        "NEWCAFE — Good Coffee, Good Mood!\n\n"
        "👇 Menyuni ochish uchun tugmani bosing."
    )
    if banner.is_file():
        await message.answer_photo(banner, caption=text, reply_markup=inline_menu(), parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer(text, reply_markup=inline_menu(), parse_mode=ParseMode.MARKDOWN)
    web_keyboard = app_keyboard()
    if web_keyboard:
        await message.answer(
            "Mini App orqali demo buyurtma yuborishingiz mumkin. Buyurtmani botga qaytarish uchun Mini App ichidagi tugmadan foydalaning.",
            reply_markup=web_keyboard,
        )
    else:
        await message.answer("Mini App tugmasini yoqish uchun MINI_APP_URL muhit o'zgaruvchisini sozlang.")


async def help_command(message: Message) -> None:
    await message.answer("Buyruqlar: /start — bosh menyu, /help — yordam, /admin — administrator ma'lumoti.")


async def callback_handler(message: Message, callback_data: str, bot: Bot) -> None:
    user_id = message.from_user.id if message.from_user else 0
    user_data = bot
    del user_id, callback_data, user_data


async def handle_callback(callback, dispatcher: Dispatcher, bot: Bot) -> None:
    await callback.answer()
    message = callback.message
    if not isinstance(message, Message):
        return
    user_id = callback.from_user.id
    user_data = dispatcher.workflow_data.setdefault("user_data", {})
    cart = user_data.setdefault(user_id, {})
    data = callback.data or ""
    if data == "home":
        await edit_message(message, "☕ *NEWCAFE bosh sahifasi*\n\nKerakli bo'limni tanlang:", inline_menu())
    elif data == "products":
        await show_products(message)
    elif data.startswith("product:"):
        key = data.partition(":")[2]
        item = PRODUCTS.get(key)
        if not item:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Savatchaga qo'shish", callback_data=f"add:{key}")],
            [InlineKeyboardButton(text="⬅️ Mahsulotlarga qaytish", callback_data="products")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home")],
        ])
        text = f'{item["emoji"]} *{item["name"]}*\n\n{item["description"]}\n\n*Narxi: {money(item["price"])}*\n\n_Narxlar demo uchun kiritilgan._'
        await edit_message(message, text, keyboard)
    elif data.startswith("add:"):
        key = data.partition(":")[2]
        if key not in PRODUCTS:
            await callback.answer("Mahsulot topilmadi.", show_alert=True)
            return
        cart[key] = min(cart.get(key, 0) + 1, 99)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍 Savatchani ko'rish", callback_data="cart")],
            [InlineKeyboardButton(text="☕ Davom etish", callback_data="products")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")],
        ])
        await edit_message(message, f'✅ {PRODUCTS[key]["name"]} savatchaga qo‘shildi.', keyboard)
    elif data == "cart":
        await show_cart(message, cart)
    elif data == "clear":
        cart.clear()
        await edit_message(message, "🗑 Savatcha tozalandi.", inline_menu())
    elif data == "checkout":
        if not cart:
            await show_cart(message, cart)
            return
        total = sum(PRODUCTS[key]["price"] * quantity for key, quantity in cart.items())
        await edit_message(
            message,
            f"🎉 *Demo buyurtma tayyor!*\n\nBuyurtma summasi: *{money(total)}*\n\nBu faqat namoyish. To'lov yoki haqiqiy yetkazib berish amalga oshirilmaydi.",
            InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="home")],
                [InlineKeyboardButton(text="☕ Yangi buyurtma", callback_data="products")],
            ]),
        )
        cart.clear()
    elif data == "promo":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="☕ Mahsulotlarni ko'rish", callback_data="products")],
            [InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")],
        ])
        await edit_message(message, "🎁 *NEWCAFE aksiyalari*\n\nBu demo loyihada aksiya va chegirmalar namunaviy.", keyboard)
    elif data == "about":
        await edit_message(
            message,
            "ℹ️ *NEWCAFE haqida*\n\nNEWCAFE — o'quv loyihasi uchun yaratilgan zamonaviy qahva brendi konsepsiyasi.\nBizning shiorimiz: *A New Taste. A New Energy.*\n\n_Bu bot demo maqsadida yaratilgan._",
            InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")]]),
        )
    elif data == "contact":
        await edit_message(
            message,
            "📞 *Aloqa*\n\nDemo loyiha uchun:\nTelegram: @newcafe_demo\nEmail: hello@newcafe.example\n\n_Bu kontaktlar namunaviy._",
            InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data="home")]]),
        )
    else:
        await callback.answer("Noma'lum tugma.", show_alert=True)


async def handle_web_app_data(message: Message, bot: Bot) -> None:
    raw_data = message.web_app_data.data if message.web_app_data else ""
    if len(raw_data) > 4096:
        await message.answer("Buyurtma ma'lumoti juda katta yoki noto'g'ri.")
        return
    try:
        payload = json.loads(raw_data)
    except (json.JSONDecodeError, TypeError):
        await message.answer("Buyurtma ma'lumotini o'qib bo'lmadi. Iltimos, qayta urinib ko'ring.")
        return
    if not isinstance(payload, dict) or payload.get("type") != "demo_order":
        await message.answer("Noma'lum Mini App so'rovi.")
        return
    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items or len(raw_items) > len(PRODUCTS):
        await message.answer("Savatchada mahsulot yo'q yoki buyurtma noto'g'ri.")
        return
    quantities: dict[str, int] = {}
    for row in raw_items:
        if not isinstance(row, dict):
            await message.answer("Buyurtma tarkibi noto'g'ri.")
            return
        key = row.get("id")
        quantity = row.get("qty")
        if key not in PRODUCTS or not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 99:
            await message.answer("Buyurtmada noma'lum mahsulot yoki miqdor bor.")
            return
        quantities[key] = quantities.get(key, 0) + quantity
        if quantities[key] > 99:
            await message.answer("Mahsulot miqdori ruxsat etilgan chegaradan oshdi.")
            return
    total = sum(PRODUCTS[key]["price"] * quantity for key, quantity in quantities.items())
    details = "\n".join(f'{PRODUCTS[key]["name"]} × {quantity} — {money(PRODUCTS[key]["price"] * quantity)}' for key, quantity in quantities.items())
    user = message.from_user
    username = f"@{user.username}" if user and user.username else (user.full_name if user else "Unknown")
    admin_id = int(os.environ["ADMIN_ID"])
    try:
        await bot.send_message(
            admin_id,
            f"🧾 Yangi demo buyurtma\nFoydalanuvchi: {username} (ID: {user.id if user else 'unknown'})\n\n{details}\n\nJami: {money(total)}",
        )
    except Exception:
        logger.exception("Could not notify ADMIN_ID about a Mini App demo order")
    await message.answer(
        f"✅ Demo buyurtmangiz qabul qilindi!\n\n{details}\n\nJami: {money(total)}\n\nBu namoyish buyurtmasi; ma'lumotlar bazasida saqlanmaydi."
    )


async def index_handler(_: web.Request) -> web.FileResponse:
    return web.FileResponse(INDEX_FILE)


async def health_handler(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})


async def run() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_value = os.getenv("ADMIN_ID", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required. Set it in your environment; never commit it to GitHub.")
    if not admin_id_value:
        raise RuntimeError("ADMIN_ID is required. Set it to the numeric Telegram user ID of the bot administrator.")
    try:
        int(admin_id_value)
    except ValueError as exc:
        raise RuntimeError("ADMIN_ID must be a numeric Telegram user ID.") from exc
    if not INDEX_FILE.is_file():
        raise RuntimeError(f"Mini App file not found: {INDEX_FILE}")
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/health", health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info("Mini App and health endpoint listening on port %s", port)
    bot = Bot(token=token)
    dispatcher = Dispatcher()
    dispatcher.include_router(admin_router)
    dispatcher.workflow_data["user_data"] = {}
    dispatcher.message.register(start, CommandStart())
    dispatcher.message.register(help_command, Command("help"))
    dispatcher.message.register(handle_web_app_data, F.web_app_data)
    dispatcher.callback_query.register(lambda callback: handle_callback(callback, dispatcher, bot))
    if not mini_app_url():
        logger.warning("MINI_APP_URL is not set; the Mini App is served, but its Telegram button will not be shown.")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
