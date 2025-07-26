import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Database
from matching import MatchingService, format_user_profile, format_no_match_message
from handlers.matching import get_participation_keyboard
from keyboards import get_match_with_feedback_keyboard

logger = logging.getLogger(__name__)

class MatchingScheduler:
    def __init__(self, bot, database: Database):
        self.bot = bot
        self.db = database
        self.matching_service = MatchingService(database)
        self.scheduler = AsyncIOScheduler()

    def start(self):
        """Запустить планировщик"""
        # Запускаем мэтчинг каждый понедельник в 10:00
        self.scheduler.add_job(
            self.start_weekly_matching,
            CronTrigger(day_of_week=0, hour=10, minute=0),  # 0 = понедельник
            id='weekly_matching'
        )

        # Создаем пары из подтвердивших участие каждый вторник в 10:00
        self.scheduler.add_job(
            self.create_confirmed_matches,
            CronTrigger(day_of_week=1, hour=10, minute=0),  # 1 = вторник
            id='confirmed_matching'
        )

        # Для тестирования - можно добавить задачу каждые 5 минут
        # self.scheduler.add_job(
        #     self.start_weekly_matching,
        #     'interval',
        #     minutes=5,
        #     id='test_matching'
        # )

        self.scheduler.start()
        logger.info("Планировщик мэтчинга запущен")

    def stop(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        logger.info("Планировщик мэтчинга остановлен")

    async def start_weekly_matching(self):
        """Начать еженедельный мэтчинг - фаза 1: сбор участников"""
        try:
            logger.info("Начинаем еженедельный мэтчинг (фаза 1: сбор участников)...")

            # Начинаем сессию матчинга с дедлайном 24 часа
            session_id = await self.matching_service.start_weekly_matching_session(24)

            # Отправляем запросы на подтверждение участия
            pending_users = await self.matching_service.process_pending_confirmations()
            for user in pending_users:
                await self._send_participation_request(user)

            logger.info(f"Сессия матчинга #{session_id} начата. "
                       f"Запросов на подтверждение: {len(pending_users)}")

        except Exception as e:
            logger.error(f"Ошибка при запуске сессии матчинга: {e}")

    async def create_confirmed_matches(self):
        """Создать пары из всех участников - фаза 2: создание пар"""
        try:
            logger.info("Создаем пары из всех участников (фаза 2)...")

            # Проверяем, есть ли активная сессия матчинга
            session = await self.db.get_current_matching_session()
            if not session or session['status'] != 'collecting':
                logger.warning("Нет активной сессии сбора участников")
                return

            # Переводим сессию в статус создания пар
            await self.db.update_matching_session_status(session['id'], 'pairing')

            # Создаем пары из всех участников
            matching_result = await self.matching_service.create_weekly_matches()

            # Отправляем уведомления о парах с кнопками обратной связи
            for user1, user2 in matching_result.matches:
                # Получаем ID матча для обратной связи
                recent_matches = await self.db.get_user_recent_matches(user1.user_id, 1)
                match_id = recent_matches[0]['match_id'] if recent_matches else None

                await self._send_match_notification_with_feedback(user1, user2, match_id)
                await self._send_match_notification_with_feedback(user2, user1, match_id)

            # Отправляем уведомления пользователям без пары
            for user in matching_result.unmatched_users:
                await self._send_no_match_notification(user)

            # Отправляем уведомления пользователям с недавними матчами
            for user in matching_result.users_with_recent_matches:
                await self._send_no_match_notification(user)

            # Завершаем сессию матчинга
            await self.db.update_matching_session_status(session['id'], 'completed')

            logger.info(f"Создано {len(matching_result.matches)} пар из всех участников, "
                       f"пользователей без пары: {len(matching_result.unmatched_users)}")

        except Exception as e:
            logger.error(f"Ошибка при создании пар: {e}")

    async def _send_match_notification(self, user: object, partner: object):
        """Отправить уведомление о паре"""
        try:
            profile_text = format_user_profile(partner)
            await self.bot.send_message(
                chat_id=user.user_id,
                text=profile_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user.user_id}: {e}")

    async def _send_match_notification_with_feedback(self, user: object, partner: object, match_id: int):
        """Отправить уведомление о паре с кнопками обратной связи"""
        try:
            profile_text = format_user_profile(partner, match_id)
            await self.bot.send_message(
                chat_id=user.user_id,
                text=profile_text,
                reply_markup=get_match_with_feedback_keyboard(partner.first_name, match_id),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user.user_id}: {e}")

    async def _send_no_match_notification(self, user: object):
        """Отправить уведомление о том, что пара не найдена"""
        try:
            no_match_text = format_no_match_message(user)
            await self.bot.send_message(
                chat_id=user.user_id,
                text=no_match_text
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления об отсутствии пары пользователю {user.user_id}: {e}")

    async def _send_participation_request(self, user: object):
        """Отправить запрос на участие в мэтчинге"""
        try:
            message_text = (
                f"☕ Привет, {user.first_name}!\n\n"
                f"Наступило время еженедельного Random Coffee!\n"
                f"Хотите участвовать в мэтчинге на этой неделе?\n\n"
                f"Если да, завтра мы подберем вам интересного собеседника для встречи за кофе."
            )

            await self.bot.send_message(
                chat_id=user.user_id,
                text=message_text,
                reply_markup=get_participation_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке запроса участия пользователю {user.user_id}: {e}")

    # Методы для ручного запуска (для админов)
    async def manual_start_matching(self):
        """Ручной запуск мэтчинга"""
        await self.start_weekly_matching()

    async def manual_create_confirmed_matches(self):
        """Ручное создание подтвержденных пар"""
        await self.create_confirmed_matches()
