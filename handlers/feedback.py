from aiogram import Router, F
from aiogram.types import CallbackQuery
import logging

from database import Database
from keyboards import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("feedback_met_"))
async def handle_meeting_confirmed(callback: CallbackQuery, db: Database):
    """Обработка подтверждения встречи"""
    try:
        match_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id

        success = await db.record_meeting_feedback(
            match_id, user_id, "meeting_confirmed"
        )

        if success:
            await callback.message.edit_text(
                "✅ Спасибо за обратную связь! "
                "Рады, что встреча состоялась.\n\n"
                "Это поможет нам улучшить алгоритм подбора пар для "
                "следующих матчингов. До свидания! ☕",
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.edit_text(
                "❌ Произошла ошибка при сохранении обратной связи. "
                "Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    except Exception as e:
        logger.error(f"Ошибка при обработке подтверждения встречи: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu()
        )

    await callback.answer()


@router.callback_query(F.data.startswith("feedback_not_met_"))
async def handle_meeting_not_confirmed(callback: CallbackQuery, db: Database):
    """Обработка отклонения встречи"""
    try:
        match_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id

        success = await db.record_meeting_feedback(
            match_id, user_id, "meeting_not_confirmed"
        )

        if success:
            await callback.message.edit_text(
                "📝 Спасибо за обратную связь! "
                "Жаль, что встреча не состоялась.\n\n"
                "Мы учтем это при следующем подборе пар. "
                "Надеемся, что в следующий раз все получится! 🤞",
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.edit_text(
                "❌ Произошла ошибка при сохранении обратной связи. "
                "Попробуйте позже.",
                reply_markup=get_main_menu()
            )

    except Exception as e:
        logger.error(f"Ошибка при обработке отклонения встречи: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка. Попробуйте позже.",
            reply_markup=get_main_menu()
        )

    await callback.answer()


@router.callback_query(F.data.startswith("feedback_later_"))
async def handle_feedback_later(callback: CallbackQuery):
    """Обработка отложенной обратной связи"""
    await callback.message.edit_text(
        "⏰ Хорошо, мы напомним вам о встрече через несколько дней.\n\n"
        "Вы также можете вернуться к этому сообщению позже и "
        "оставить обратную связь.",
        reply_markup=get_main_menu()
    )
    await callback.answer()