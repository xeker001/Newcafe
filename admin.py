import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="admin")


@router.message(Command("admin"))
async def admin_command(message: Message) -> None:
    admin_id = os.getenv("ADMIN_ID", "").strip()
    if not message.from_user or not admin_id or str(message.from_user.id) != admin_id:
        await message.answer("⛔ Bu buyruq faqat administrator uchun.")
        return

    await message.answer(
        "🛠 NEWCAFE administrator paneli\n\n"
        "Bot ishlayapti. Buyurtmalar mijozga tasdiq xabari sifatida bot ichida ko‘rsatiladi.\n"
        "Buyurtmalar doimiy saqlanmaydi; loyiha ma'lumotlar bazasidan foydalanmaydi."
    )
