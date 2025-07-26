from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Моя анкета", callback_data="profile_menu")
    )
    builder.row(
        InlineKeyboardButton(text="☕ Участие", callback_data="participation_menu")
    )
    return builder.as_markup()


def get_profile_menu() -> InlineKeyboardMarkup:
    """Меню анкеты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Создать/Изменить анкету", callback_data="edit_profile")
    )
    builder.row(
        InlineKeyboardButton(text="👁 Посмотреть анкету", callback_data="view_profile")
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить анкету", callback_data="delete_profile")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_participation_menu() -> InlineKeyboardMarkup:
    """Меню участия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Всегда участвовать", callback_data="participation_always")
    )
    builder.row(
        InlineKeyboardButton(text="❓ Спрашивать каждый раз", callback_data="participation_ask")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Не участвовать", callback_data="participation_never")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")
    )
    return builder.as_markup()


def get_confirm_delete() -> InlineKeyboardMarkup:
    """Подтверждение удаления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="profile_menu")
    )
    return builder.as_markup()
