from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def page_kb(page: int, prefix: str = "page"):
    kb = InlineKeyboardMarkup(row_width=2)
    prev = InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{page-1}")
    nxt = InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page+1}")
    kb.add(prev, nxt)
    return kb