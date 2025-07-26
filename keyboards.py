from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Моя анкета",
            callback_data="profile_menu"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="☕ Участие",
            callback_data="participation_menu"
        )
    )
    return builder.as_markup()


def get_profile_menu() -> InlineKeyboardMarkup:
    """Меню анкеты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📝 Создать/Изменить анкету",
            callback_data="edit_profile"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👁 Посмотреть анкету",
            callback_data="view_profile"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить анкету",
            callback_data="delete_profile"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="main_menu"
        )
    )
    return builder.as_markup()


def get_participation_menu() -> InlineKeyboardMarkup:
    """Меню участия"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Всегда участвовать",
            callback_data="participation_always"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❓ Спрашивать каждый раз",
            callback_data="participation_ask"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Не участвовать",
            callback_data="participation_never"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data="main_menu"
        )
    )
    return builder.as_markup()


def get_confirm_delete() -> InlineKeyboardMarkup:
    """Подтверждение удаления"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data="confirm_delete"
        ),
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="profile_menu"
        )
    )
    return builder.as_markup()


def get_admin_menu() -> InlineKeyboardMarkup:
    """Админское меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="👥 Список пользователей",
            callback_data="admin_users"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Статистика мэтчинга",
            callback_data="admin_stats"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Запустить мэтчинг",
            callback_data="admin_manual_matching"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="⏹ Завершить мэтчинг принудительно",
            callback_data="admin_force_complete"
        )
    )
    return builder.as_markup()


def get_users_list_keyboard(
    users_count: int, page: int = 0, page_size: int = 10
) -> InlineKeyboardMarkup:
    """Клавиатура для списка пользователей с пагинацией"""
    builder = InlineKeyboardBuilder()

    # Кнопки навигации по страницам
    total_pages = (users_count + page_size - 1) // page_size

    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"users_page_{page-1}"
            ))

        nav_buttons.append(InlineKeyboardButton(
            text=f"{page+1}/{total_pages}",
            callback_data="current_page"
        ))

        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"users_page_{page+1}"
            ))

        if nav_buttons:
            builder.row(*nav_buttons)

    # Кнопка возврата в админ меню
    builder.row(
        InlineKeyboardButton(
            text="⬅️ В админ меню",
            callback_data="admin_menu"
        )
    )

    return builder.as_markup()


def get_participation_selection() -> InlineKeyboardMarkup:
    """Выбор статуса участия при создании анкеты"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Всегда участвовать",
            callback_data="force_participation_always"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❓ Спрашивать каждый раз",
            callback_data="force_participation_ask"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Не участвовать",
            callback_data="force_participation_never"
        )
    )
    return builder.as_markup()


def get_back_to_admin() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ меню"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="⬅️ В админ меню",
            callback_data="admin_menu"
        )
    )
    return builder.as_markup()


def get_meeting_feedback_keyboard(match_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для обратной связи о встрече"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Мы встретились",
            callback_data=f"feedback_met_{match_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Встреча не состоялась",
            callback_data=f"feedback_not_met_{match_id}"
        )
    )
    return builder.as_markup()


def get_match_with_feedback_keyboard(
    partner_name: str, match_id: int
) -> InlineKeyboardMarkup:
    """Клавиатура с анкетой партнера и кнопкой обратной связи"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Мы встретились",
            callback_data=f"feedback_met_{match_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Встреча не состоялась",
            callback_data=f"feedback_not_met_{match_id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📅 Напомнить позже",
            callback_data=f"feedback_later_{match_id}"
        )
    )
    return builder.as_markup()


def get_force_complete_confirmation() -> InlineKeyboardMarkup:
    """Подтверждение принудительного завершения матчинга"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅ Да, завершить принудительно",
            callback_data="confirm_force_complete"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="admin_menu"
        )
    )
    return builder.as_markup()
