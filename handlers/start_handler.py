from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from db import AsyncSessionLocal
from models import Chat
from sqlalchemy import select
from config import cfg

router = Router()


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message):
    nickname = message.from_user.full_name
    text = (
        f"🍊 Привет, {nickname}. Вы подключились к Woxl -- Чат менеджер.\n"
        "Я Вокс, бот для поддержки порядка, контроля нарушений и администрирования."
    )
    await message.answer(text, parse_mode=cfg.PARSE_MODE)

    # Ensure chat exists in DB (for private chat this adds too)
    async with AsyncSessionLocal() as session:
        if message.chat:
            q = await session.execute(select(Chat).where(Chat.id == message.chat.id))
            chat = q.scalars().first()
            if not chat:
                chat = Chat(id=message.chat.id)
                session.add(chat)
                await session.commit()