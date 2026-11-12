import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ASSETS = Path(__file__).parent / "assets"

# Demo mahsulotlar. Narxlar namunaviy, haqiqiy savdo amalga oshirilmaydi.
PRODUCTS = {
    "classic": {"name": "NEWCAFE Classic", "description": "Klassik eruvchan qahva.", "price": 25000, "emoji": "☕"},
    "gold": {"name": "NEWCAFE Gold", "description": "Yumshoq ta'mli premium qahva.", "price": 35000, "emoji": "✨"},
    "latte": {"name": "NEWCAFE Latte", "description": "Sutli qahva ichimligi.", "price": 18000, "emoji": "🥛"},
}

def money(value: int) -> str:
    return f"{value:,}".replace(",", " ") + " so'm"

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("☕ Mahsulotlar", callback_data="products")],
        [InlineKeyboardButton("🛍 Savatcham", callback_data="cart"),
         InlineKeyboardButton("🎁 Aksiya", callback_data="promo")],
        [InlineKeyboardButton("ℹ️ Biz haqimizda", callback_data="about"),
         InlineKeyboardButton("📞 Aloqa", callback_data="contact")],
    ])

def products_keyboard():
    rows = []
    for key, item in PRODUCTS.items():
        rows.append([InlineKeyboardButton(
            f'{item["emoji"]} {item["name"]} — {money(item["price"])}',
            callback_data=f"product:{key}"
        )])
    rows.append([InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")])
    return InlineKeyboardMarkup(rows)

async def edit_text(query, text, reply_markup=None, parse_mode=None):
    """Matnli ham, rasmli Telegram xabarlarini ham mos ravishda tahrirlaydi."""
    if query.message and query.message.photo:
        await query.edit_message_caption(
            caption=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    else:
        await query.edit_message_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )

async def send_visual(query, image_name, caption, keyboard, parse_mode=None):
    image_path = ASSETS / image_name
    with image_path.open("rb") as photo:
        await query.message.reply_photo(
            photo=photo, caption=caption,
            reply_markup=keyboard, parse_mode=parse_mode
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("cart", {})
    text = (
        "☕ *NEWCAFE ga xush kelibsiz!*\n\n"
        "Yangi ta'm. Yangi energiya.\n"
        "Mahsulotlarimiz bilan tanishing yoki demo buyurtma yarating.\n\n"
        "_Bu o'quv loyiha uchun namoyish botidir._"
    )
    image_path = ASSETS / "newcafe_banner.jpg"
    with image_path.open("rb") as photo:
        await update.message.reply_photo(
            photo=photo, caption=text,
            reply_markup=main_keyboard(), parse_mode="Markdown"
        )

async def show_home(query):
    await edit_text(
        query,
        "☕ *NEWCAFE bosh sahifasi*\n\nKerakli bo'limni tanlang:",
        reply_markup=main_keyboard(),
        parse_mode="Markdown"
    )

async def show_products(query):
    await send_visual(
        query, "newcafe_products.jpg",
        "☕ *NEWCAFE mahsulotlari*\n\nMahsulotni tanlab, batafsil ma'lumot oling:",
        products_keyboard(), parse_mode="Markdown"
    )

async def show_cart(query, context):
    cart = context.user_data.setdefault("cart", {})
    if not cart:
        text = "🛍 *Savatchangiz hozircha bo'sh.*\nMahsulotlar bo'limidan qahva tanlang."
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("☕ Mahsulotlarni ko'rish", callback_data="products")],
            [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")]
        ])
    else:
        lines, total = [], 0
        for key, qty in cart.items():
            item = PRODUCTS[key]
            subtotal = item["price"] * qty
            total += subtotal
            lines.append(f'{item["emoji"]} {item["name"]} × {qty} — {money(subtotal)}')
        text = "🛍 *Savatchangiz*\n\n" + "\n".join(lines) + f"\n\n*Jami: {money(total)}*"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Demo buyurtmani tasdiqlash", callback_data="checkout")],
            [InlineKeyboardButton("🗑 Savatchani tozalash", callback_data="clear")],
            [InlineKeyboardButton("☕ Yana mahsulot tanlash", callback_data="products")],
            [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")],
        ])
    await edit_text(query, text, reply_markup=keyboard, parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "home":
        await show_home(query)
    elif data == "products":
        await show_products(query)
    elif data.startswith("product:"):
        key = data.split(":", 1)[1]
        item = PRODUCTS[key]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Savatchaga qo'shish", callback_data=f"add:{key}")],
            [InlineKeyboardButton("⬅️ Mahsulotlarga qaytish", callback_data="products")],
            [InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")],
        ])
        text = (
            f'{item["emoji"]} *{item["name"]}*\n\n'
            f'{item["description"]}\n\n'
            f'*Narxi: {money(item["price"])}*\n\n'
            "_Narxlar demo uchun kiritilgan._"
        )
        await send_visual(query, "newcafe_products.jpg", text, keyboard, parse_mode="Markdown")
    elif data.startswith("add:"):
        key = data.split(":", 1)[1]
        cart = context.user_data.setdefault("cart", {})
        cart[key] = cart.get(key, 0) + 1
        await edit_text(
            query, f'✅ {PRODUCTS[key]["name"]} savatchaga qo‘shildi.',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍 Savatchani ko'rish", callback_data="cart")],
                [InlineKeyboardButton("☕ Davom etish", callback_data="products")],
                [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")],
            ])
        )
    elif data == "cart":
        await show_cart(query, context)
    elif data == "clear":
        context.user_data["cart"] = {}
        await edit_text(query, "🗑 Savatcha tozalandi.", reply_markup=main_keyboard())
    elif data == "checkout":
        cart = context.user_data.setdefault("cart", {})
        if not cart:
            await show_cart(query, context)
            return
        total = sum(PRODUCTS[k]["price"] * q for k, q in cart.items())
        await edit_text(
            query,
            f"🎉 *Demo buyurtma tayyor!*\n\nBuyurtma summasi: *{money(total)}*\n\n"
            "Bu faqat namoyish. To'lov yoki haqiqiy yetkazib berish amalga oshirilmaydi.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Bosh menyu", callback_data="home")],
                [InlineKeyboardButton("☕ Yangi buyurtma", callback_data="products")],
            ]),
            parse_mode="Markdown"
        )
        context.user_data["cart"] = {}
    elif data == "promo":
        await send_visual(
            query, "newcafe_promo.jpg",
            "🎁 *NEWCAFE aksiyalari*\n\nBu demo loyihada aksiya banneri namoyish qilinadi. "
            "Chegirma va takliflar namunaviy.",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("☕ Mahsulotlarni ko'rish", callback_data="products")],
                [InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")],
            ]),
            parse_mode="Markdown"
        )
    elif data == "about":
        await edit_text(
            query,
            "ℹ️ *NEWCAFE haqida*\n\n"
            "NEWCAFE — o'quv loyihasi uchun yaratilgan zamonaviy qahva brendi konsepsiyasi.\n"
            "Bizning shiorimiz: *A New Taste. A New Energy.*\n\n"
            "_Bu bot demo maqsadida ishlaydi._",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")]]),
            parse_mode="Markdown"
        )
    elif data == "contact":
        await edit_text(
            query,
            "📞 *Aloqa*\n\n"
            "Demo loyiha uchun:\n"
            "Telegram: @newcafe_demo\n"
            "Email: hello@newcafe.example\n\n"
            "_Bu kontaktlar namunaviy. Haqiqiy aloqa ma'lumotlari emas._",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bosh menyu", callback_data="home")]]),
            parse_mode="Markdown"
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Botdan foydalanish uchun /start buyrug'ini yuboring.")

def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN topilmadi. BotFather tokenini BOT_TOKEN muhit o'zgaruvchisiga kiriting."
        )
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("NEWCAFE demo bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
