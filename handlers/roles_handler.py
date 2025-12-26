import re
from datetime import datetime
from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select, delete
from db import AsyncSessionLocal
from models import RoleAssignment, Chat, ROLE_MAP
from config import cfg

router = Router()

# Helpers
async def get_role_assignments(session, chat_id):
    q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id))
    return q.scalars().all()


def role_name(role_id: int) -> str:
    return ROLE_MAP.get(role_id, ("Неизвестно", ""))[0]


async def parse_target_user_from_message(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.full_name
    parts = message.text.strip().split()
    # try numeric id
    for p in parts[1:]:
        if p.isdigit():
            return int(p), p
        if p.startswith("@"):
            return None, p
    return None, None


@router.message(lambda message: message.text and re.match(r"^(админы|\?админ)$", message.text.strip(), re.IGNORECASE))
async def cmd_list_admins(message: Message):
    async with AsyncSessionLocal() as session:
        assigns = await get_role_assignments(session, message.chat.id)
    # group by role
    roles_map = {}
    for a in assigns:
        roles_map.setdefault(a.role_id, []).append(a)
    text_lines = ["🍊 Список администраторов\n"]
    for rid in sorted(ROLE_MAP.keys(), reverse=True):
        title = ROLE_MAP[rid][0]
        members = roles_map.get(rid, [])
        text_lines.append(f"[{rid}] {title}")
        if members:
            for m in members:
                # try to show nick if available; fallback to user id
                text_lines.append(f"{m.user_id}")
        else:
            text_lines.append("(пусто)")
        text_lines.append("")  # spacer
    await message.answer("\n".join(text_lines), parse_mode=cfg.PARSE_MODE)


# Assign role command: +админ / +модер / выдать
@router.message(lambda message: message.text and re.match(r"^(\+админ|\+модер|выдать)\b", message.text.strip(), re.IGNORECASE))
async def cmd_assign(message: Message):
    caller_id = message.from_user.id
    chat_id = message.chat.id
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == caller_id))
        caller_assign = q.scalars().first()
        # check if caller is owner (role_id==5)
        if not caller_assign or caller_assign.role_id != 5:
            await message.reply("Только Владелец может выдавать админов.", parse_mode=cfg.PARSE_MODE)
            return

        target_user_id, target_display = await parse_target_user_from_message(message)
        # default role to id 4 (Администратор)
        role_id = 4
        # optional reason: text after username/id
        reason = None
        parts = message.text.strip().split()
        if len(parts) >= 2:
            # find index of target token (if it's in text)
            if target_display and isinstance(target_display, str) and target_display.startswith("@"):
                try:
                    idx = message.text.index(target_display) + len(target_display)
                    rest = message.text[idx:].strip()
                    if rest:
                        reason = rest
                except ValueError:
                    reason = None
            else:
                # if reply, reason is after first token
                rest = " ".join(parts[1:])
                if rest:
                    reason = rest

        if not target_user_id:
            await message.reply("Не удалось определить пользователя. Ответьте на сообщение пользователя или укажите id.", parse_mode=cfg.PARSE_MODE)
            return

        # upsert assignment
        q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == target_user_id))
        existing = q.scalars().first()
        if existing:
            existing.role_id = role_id
            existing.assigned_by = caller_id
            existing.reason = reason
            existing.assigned_at = datetime.utcnow()
            session.add(existing)
        else:
            ra = RoleAssignment(chat_id=chat_id, user_id=target_user_id, role_id=role_id, assigned_by=caller_id, reason=reason)
            session.add(ra)
        await session.commit()
    await message.reply(f"➕ {target_display or target_user_id} назначен на роль: {role_name(role_id)} [{role_id}]\nС большой силой приходит большая ответственность.", parse_mode=cfg.PARSE_MODE)


# Remove admin: -админ / снять
@router.message(lambda message: message.text and re.match(r"^(-админ|снять)\b", message.text.strip(), re.IGNORECASE))
async def cmd_remove_admin(message: Message):
    caller_id = message.from_user.id
    chat_id = message.chat.id
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == caller_id))
        caller_assign = q.scalars().first()
        if not caller_assign or caller_assign.role_id != 5:
            await message.reply("Только Владелец может снимать админов.", parse_mode=cfg.PARSE_MODE)
            return

        target_user_id, target_display = await parse_target_user_from_message(message)
        if not target_user_id:
            await message.reply("Не удалось определить пользователя. Ответьте на сообщение пользователя или укажите id.", parse_mode=cfg.PARSE_MODE)
            return

        q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == target_user_id))
        existing = q.scalars().first()
        if not existing:
            await message.reply("У пользователя нет роли в этой группе.", parse_mode=cfg.PARSE_MODE)
            return
        roleid = existing.role_id
        await session.execute(delete(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == target_user_id))
        await session.commit()
    await message.reply(f"➖ {target_display or target_user_id} снят с роли: {role_name(roleid)} [{roleid}]\nСпасибо за вклад в управление чатом.", parse_mode=cfg.PARSE_MODE)


# Promote / demote (only one step)
@router.message(lambda message: message.text and re.match(r"^(повысить|повышение|понизить|понижение)\b", message.text.strip(), re.IGNORECASE))
async def cmd_promote_demote(message: Message):
    caller_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip().split()[0].lower()
    is_promote = text.startswith("повыш")
    async with AsyncSessionLocal() as session:
        q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == caller_id))
        caller_assign = q.scalars().first()
        if not caller_assign or caller_assign.role_id != 5:
            await message.reply("Только Владелец может повышать/понижать.", parse_mode=cfg.PARSE_MODE)
            return
        target_user_id, target_display = await parse_target_user_from_message(message)
        if not target_user_id:
            await message.reply("Не удалось определить пользователя. Ответьте на сообщение пользователя или укажите id.", parse_mode=cfg.PARSE_MODE)
            return
        q = await session.execute(select(RoleAssignment).where(RoleAssignment.chat_id == chat_id, RoleAssignment.user_id == target_user_id))
        existing = q.scalars().first()
        if not existing:
            await message.reply("У пользователя нет назначенной роли.", parse_mode=cfg.PARSE_MODE)
            return
        old = existing.role_id
        if is_promote:
            new = min(5, old + 1)
            if new == old:
                await message.reply("Нельзя повысить выше существующей роли.", parse_mode=cfg.PARSE_MODE)
                return
            existing.role_id = new
            session.add(existing)
            await session.commit()
            await message.reply(f"⬆️ {target_display or target_user_id} повышен до: {role_name(new)} [{new}]\nДоверие растёт — ответственность тоже.", parse_mode=cfg.PARSE_MODE)
        else:
            new = max(1, old - 1)
            if new == old:
                await message.reply("Нельзя понизить ниже минимальной роли.", parse_mode=cfg.PARSE_MODE)
                return
            existing.role_id = new
            session.add(existing)
            await session.commit()
            await message.reply(f"⬇️ {target_display or target_user_id} понижен до: {role_name(new)} [{new}]\nРоль изменена, но вклад всё ещё ценится.", parse_mode=cfg.PARSE_MODE)