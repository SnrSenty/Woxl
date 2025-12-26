import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommandScopeDefault, BotCommand
from aiogram.filters import BaseFilter
from aiogram import types

from config import cfg
from db import init_db
from handlers.start_handler import router as start_router
from handlers.roles_handler import router as roles_router
from handlers.nicks_handler import router as nicks_router
from handlers.warns_handler import router as warns_router
from db import AsyncSessionLocal
from models import Chat, RoleAssignment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=cfg.BOT_TOKEN, parse_mode=cfg.PARSE_MODE)
dp = Dispatcher()


# Register routers
dp.include_router(start_router)
dp.include_router(roles_router)
dp.include_router(nicks_router)
dp.include_router(warns_router)


@dp.my_chat_member()
async def on_my_chat_member(update: types.ChatMemberUpdated):
    """
    Auto assign Owner role when bot is added to a chat.
    """
    # when bot becomes member or administrator in a group
    new = update.new_chat_member
    if new and new.status in ("member", "administrator"):
        chat = update.chat
        # find chat owner via get_chat_administrators and detect ChatMemberOwner
        try:
            admins = await bot.get_chat_administrators(chat.id)
            owner = None
            for a in admins:
                if a.status == "creator" or a.status == "administrator" and getattr(a, "is_owner", False):
                    # 'creator' indicates owner
                    owner = a.user
                    break
                if a.status == "creator":
                    owner = a.user
                    break
            if not owner:
                # fallback: pick first with status 'creator'
                for a in admins:
                    if a.status == "creator":
                        owner = a.user
                        break
            if owner:
                async with AsyncSessionLocal() as session:
                    q = await session.execute(select(Chat).where(Chat.id == chat.id))
                    ch = q.scalars().first()
                    if not ch:
                        ch = Chat(id=chat.id)
                        session.add(ch)
                        await session.commit()
                    # assign owner role (5)
                    q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id==chat.id, RoleAssignment.user_id==owner.id))
                    existing = q.scalars().first()
                    if existing:
                        existing.role_id = 5
                        session.add(existing)
                    else:
                        ra = RoleAssignment(chat_id=chat.id, user_id=owner.id, role_id=5, assigned_by=None)
                        session.add(ra)
                    await session.commit()
                    logger.info("Assigned owner role in chat %s to user %s", chat.id, owner.id)
        except Exception as e:
            logger.exception("Error assigning owner role: %s", e)


async def main():
    # init DB
    await init_db()

    # set bot commands
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="admins", description="Показать список админов"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

    # start polling
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())