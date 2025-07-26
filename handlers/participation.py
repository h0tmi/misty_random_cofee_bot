from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import Database
from models import ParticipationStatus
from keyboards import get_participation_menu, get_main_menu

router = Router()

@router.callback_query(F.data == "participation_menu")
async def participation_menu(callback: CallbackQuery, db: Database):
    user = await db.get_user(callback.from_user.id)

    if not user:
        await callback.answer("❌ Сначала создайте анкету", show_alert=True)
        return

    status_text = {
        ParticipationStatus.ALWAYS: "✅ Всегда участвую",
        ParticipationStatus.ASK_EACH_TIME: "❓ Спрашивать каждый раз",
        ParticipationStatus.NEVER: "❌ Не участвую"
    }

    await callback.message.edit_text(
        f"☕ Управление участием в Random Coffee\n\n"
        f"Текущий статус: {status_text[user.participation_status]}\n\n"
        f"Выберите новый статус:",
        reply_markup=get_participation_menu()
    )

@router.callback_query(F.data.startswith("participation_"))
async def change_participation(callback: CallbackQuery, db: Database):
    user = await db.get_user(callback.from_user.id)

    if not user:
        await callback.answer("❌ Сначала создайте анкету", show_alert=True)
        return

    status_map = {
        "participation_always": ParticipationStatus.ALWAYS,
        "participation_ask": ParticipationStatus.ASK_EACH_TIME,
        "participation_never": ParticipationStatus.NEVER
    }

    new_status = status_map[callback.data]
    user.participation_status = new_status

    await db.create_or_update_user(user)

    status_text = {
        ParticipationStatus.ALWAYS: "✅ Всегда участвовать",
        ParticipationStatus.ASK_EACH_TIME: "❓ Спрашивать каждый раз",
        ParticipationStatus.NEVER: "❌ Не участвовать"
    }

    await callback.message.edit_text(
        f"✅ Статус участия изменен на: {status_text[new_status]}",
        reply_markup=get_main_menu()
    )
