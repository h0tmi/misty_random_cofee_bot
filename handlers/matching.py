from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from matching import MatchingService
from keyboards import get_main_menu

router = Router()

@router.callback_query(F.data.startswith("participate_"))
async def handle_participation_response(callback: CallbackQuery, db: Database):
    """Обработка ответа на участие в мэтчинге"""
    user_id = callback.from_user.id
    wants_to_participate = callback.data == "participate_yes"

    matching_service = MatchingService(db)
    await matching_service.confirm_participation(user_id, wants_to_participate)

    if wants_to_participate:
        await callback.message.edit_text(
            "✅ Отлично! Вы участвуете в мэтчинге этой недели.\n"
            "Ожидайте уведомления о вашей паре!",
            reply_markup=get_main_menu()
        )
    else:
        await callback.message.edit_text(
            "❌ Понятно, в этот раз вы не участвуете.\n"
            "Увидимся на следующей неделе!",
            reply_markup=get_main_menu()
        )

def get_participation_keyboard():
    """Клавиатура для подтверждения участия"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, участвую!", callback_data="participate_yes"),
        InlineKeyboardButton(text="❌ Нет, пропускаю", callback_data="participate_no")
    )
    return builder.as_markup()
