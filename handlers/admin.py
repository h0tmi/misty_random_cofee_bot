import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command

from config import load_config
from keyboards import (
    get_admin_menu,
    get_users_list_keyboard,
    get_back_to_admin,
    get_force_complete_confirmation
)
from models import ParticipationStatus
from database import Database

router = Router()
logger = logging.getLogger(__name__)

# Загружаем конфиг для проверки админских прав
config = load_config()


def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом"""
    return user_id in config.admin_ids


@router.message(Command("admin"))
async def admin_command(message: Message):
    """Админская команда"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return

    await message.answer(
        "🔧 Админская панель\n\n"
        "Доступные функции:",
        reply_markup=get_admin_menu()
    )


@router.callback_query(F.data == "admin_menu")
async def admin_menu_callback(callback: CallbackQuery):
    """Обработчик кнопки админ меню"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🔧 Админская панель\n\n"
        "Доступные функции:",
        reply_markup=get_admin_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery, db: Database):
    """Показать список пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await _show_users_page(callback, db, page=0)


@router.callback_query(F.data.startswith("users_page_"))
async def users_page_callback(callback: CallbackQuery, db: Database):
    """Обработчик пагинации списка пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    page = int(callback.data.split("_")[-1])
    await _show_users_page(callback, db, page)


async def _show_users_page(callback: CallbackQuery, db, page: int = 0):
    """Показать страницу со списком пользователей"""
    page_size = 10
    offset = page * page_size

    try:
        users = await db.get_all_users(limit=page_size, offset=offset)
        total_users = await db.get_users_count()

        if not users and page > 0:
            # Если страница пустая, переходим на первую страницу
            await _show_users_page(callback, db, page=0)
            return

        text = f"👥 <b>Список пользователей</b> (всего: {total_users})\n\n"

        if not users:
            text += "📭 Пользователей пока нет"
        else:
            for i, user in enumerate(users, start=offset + 1):
                status_emoji = {
                    ParticipationStatus.ALWAYS: "✅",
                    ParticipationStatus.ASK_EACH_TIME: "❓",
                    ParticipationStatus.NEVER: "❌"
                }.get(user.participation_status, "❓")

                # Экранируем HTML символы для безопасности
                from html import escape
                first_name = escape(user.first_name or "")
                last_name = escape(user.last_name or "")
                username_text = (
                    f"@{escape(user.username)}" if user.username
                    else "без username"
                )
                active_text = "✅" if user.is_active else "❌"

                created_date = (
                    user.created_at[:10] if user.created_at else 'неизвестно'
                )

                text += (
                    f"{i}. <b>{first_name}</b> "
                    f"{last_name}\n"
                    f"   ID: <code>{user.user_id}</code> | {username_text}\n"
                    f"   Участие: {status_emoji} | Активен: {active_text}\n"
                    f"   Создан: {created_date}\n\n"
                )

        await callback.message.edit_text(
            text,
            reply_markup=get_users_list_keyboard(total_users, page, page_size),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении списка пользователей",
            reply_markup=get_back_to_admin()
        )

    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery, db: Database):
    """Показать статистику мэтчинга"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    try:
        stats = await db.get_matching_statistics()

        # Форматируем статистику участия
        participation_text = ""
        participation_stats = stats.get('participation_stats', {})

        status_names = {
            'always': 'Всегда участвуют',
            'ask_each_time': 'Спрашивать каждый раз',
            'never': 'Не участвуют'
        }

        for status, count in participation_stats.items():
            status_name = status_names.get(status, status)
            participation_text += f"• {status_name}: {count}\n"

        if not participation_text:
            participation_text = "• Нет данных\n"

        text = (
            "📊 <b>Статистика мэтчинга</b>\n\n"

            "👥 <b>Пользователи:</b>\n"
            f"• Всего активных: {stats['active_users']}\n"
            f"• Ожидают подтверждения: {stats['pending_users']}\n"
            f"• Подтвердили участие: {stats['confirmed_users']}\n\n"

            "🎯 <b>Статусы участия:</b>\n"
            f"{participation_text}\n"

            "💫 <b>Мэтчи:</b>\n"
            f"• Всего создано: {stats['total_matches']}\n"
            f"• За последние 30 дней: {stats['recent_matches']}\n\n"

            f"📅 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_back_to_admin(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при получении статистики",
            reply_markup=get_back_to_admin()
        )

    await callback.answer()


@router.callback_query(F.data == "admin_manual_matching")
async def admin_manual_matching_callback(callback: CallbackQuery):
    """Ручной запуск мэтчинга"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "🔄 Запускаю мэтчинг...",
        reply_markup=get_back_to_admin()
    )

    # Получаем планировщик
    import shared
    scheduler = shared.get_scheduler()
    if scheduler:
        try:
            await scheduler.manual_start_matching()
            await callback.message.edit_text(
                "✅ Мэтчинг успешно запущен!",
                reply_markup=get_back_to_admin()
            )
        except Exception as e:
            logger.error(f"Ошибка при запуске мэтчинга: {e}")
            await callback.message.edit_text(
                f"❌ Ошибка при запуске мэтчинга: {str(e)}",
                reply_markup=get_back_to_admin()
            )
    else:
        await callback.message.edit_text(
            "❌ Планировщик недоступен",
            reply_markup=get_back_to_admin()
        )

    await callback.answer()


@router.callback_query(F.data == "current_page")
async def current_page_callback(callback: CallbackQuery):
    """Обработчик нажатия на текущую страницу (ничего не делаем)"""
    await callback.answer()


@router.callback_query(F.data == "admin_force_complete")
async def admin_force_complete_callback(callback: CallbackQuery, db: Database):
    """Обработчик принудительного завершения матчинга"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    # Проверяем, есть ли активная сессия матчинга
    session = await db.get_current_matching_session()

    if not session:
        await callback.message.edit_text(
            "❌ Нет активной сессии матчинга для завершения.",
            reply_markup=get_back_to_admin()
        )
        await callback.answer()
        return

    if session['status'] == 'collecting':
        await callback.message.edit_text(
            f"⚠️ Принудительное завершение матчинга\n\n"
            f"Текущий статус: Сбор участников\n"
            f"Дедлайн: {session['deadline'][:16]}\n\n"
            f"Вы уверены, что хотите завершить матчинг принудительно? "
            f"Это создаст пары из уже подтвердивших участие пользователей.",
            reply_markup=get_force_complete_confirmation()
        )
    else:
        await callback.message.edit_text(
            f"❌ Сессия матчинга уже в процессе создания пар или завершена.\n"
            f"Статус: {session['status']}",
            reply_markup=get_back_to_admin()
        )

    await callback.answer()


@router.callback_query(F.data == "confirm_force_complete")
async def confirm_force_complete_callback(
    callback: CallbackQuery, db: Database
):
    """Подтверждение принудительного завершения матчинга"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    try:
        # Завершаем сессию принудительно
        success = await db.force_complete_matching_session()

        if success:
            # Получаем планировщик и запускаем создание пар
            import shared
            scheduler = shared.get_scheduler()
            if scheduler:
                await scheduler.manual_create_confirmed_matches()

                await callback.message.edit_text(
                    "✅ Матчинг завершен принудительно!\n\n"
                    "Пары созданы из участников, которые успели "
                    "подтвердить свое участие.",
                    reply_markup=get_back_to_admin()
                )
            else:
                await callback.message.edit_text(
                    "❌ Планировщик недоступен.",
                    reply_markup=get_back_to_admin()
                )
        else:
            await callback.message.edit_text(
                "❌ Не удалось завершить матчинг. "
                "Возможно, нет активной сессии.",
                reply_markup=get_back_to_admin()
            )

    except Exception as e:
        logger.error(f"Ошибка при принудительном завершении матчинга: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при завершении матчинга: {str(e)}",
            reply_markup=get_back_to_admin()
        )

    await callback.answer()