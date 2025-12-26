from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def page_kb(page: int, prefix: str = "page"):
    prev = InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{max(1, page-1)}")
    nxt = InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{page+1}")
    # Two buttons in one row
    kb = InlineKeyboardMarkup(inline_keyboard=[[prev, nxt]])
    return kb