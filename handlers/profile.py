from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter

from database import Database
from models import User, ParticipationStatus
from keyboards import get_profile_menu, get_main_menu, get_confirm_delete

router = Router()

class ProfileStates(StatesGroup):
    waiting_for_bio = State()
    waiting_for_interests = State()

@router.callback_query(F.data == "profile_menu")
async def profile_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "📝 Управление анкетой:",
        reply_markup=get_profile_menu()
    )

@router.callback_query(F.data == "view_profile")
async def view_profile(callback: CallbackQuery, db: Database):
    user = await db.get_user(callback.from_user.id)

    if not user:
        await callback.answer("❌ У вас нет анкеты", show_alert=True)
        return

    profile_text = f"👤 Ваша анкета:\n\n"
    profile_text += f"Имя: {user.first_name}"
    if user.last_name:
        profile_text += f" {user.last_name}"
    if user.username:
        profile_text += f" (@{user.username})"
    profile_text += f"\n\n"

    if user.bio:
        profile_text += f"О себе: {user.bio}\n\n"

    if user.interests:
        profile_text += f"Интересы: {user.interests}\n\n"

    status_text = {
        ParticipationStatus.ALWAYS: "✅ Всегда участвую",
        ParticipationStatus.ASK_EACH_TIME: "❓ Спрашивать каждый раз",
        ParticipationStatus.NEVER: "❌ Не участвую"
    }
    profile_text += f"Статус участия: {status_text[user.participation_status]}"

    await callback.message.edit_text(profile_text, reply_markup=get_profile_menu())

@router.callback_query(F.data == "edit_profile")
async def start_edit_profile(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📝 Расскажите немного о себе (или отправьте /skip чтобы пропустить):"
    )
    await state.set_state(ProfileStates.waiting_for_bio)

@router.message(StateFilter(ProfileStates.waiting_for_bio))
async def process_bio(message: Message, state: FSMContext):
    bio = None if message.text == "/skip" else message.text
    await state.update_data(bio=bio)

    await message.answer(
        "🎯 Укажите ваши интересы и хобби (или отправьте /skip чтобы пропустить):"
    )
    await state.set_state(ProfileStates.waiting_for_interests)

@router.message(StateFilter(ProfileStates.waiting_for_interests))
async def process_interests(message: Message, state: FSMContext, db: Database):
    interests = None if message.text == "/skip" else message.text
    data = await state.get_data()

    user = User(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        bio=data.get('bio'),
        interests=interests,
        participation_status=ParticipationStatus.ASK_EACH_TIME
    )

    await db.create_or_update_user(user)
    await state.clear()

    await message.answer(
        "✅ Анкета успешно создана/обновлена!",
        reply_markup=get_main_menu()
    )

@router.callback_query(F.data == "delete_profile")
async def confirm_delete_profile(callback: CallbackQuery):
    await callback.message.edit_text(
        "⚠️ Вы действительно хотите удалить свою анкету?\n"
        "Это действие нельзя отменить.",
        reply_markup=get_confirm_delete()
    )

@router.callback_query(F.data == "confirm_delete")
async def delete_profile(callback: CallbackQuery, db: Database):
    success = await db.delete_user(callback.from_user.id)

    if success:
        await callback.message.edit_text(
            "✅ Анкета успешно удалена.",
            reply_markup=get_main_menu()
        )
    else:
        await callback.answer("❌ Ошибка при удалении анкеты", show_alert=True)
