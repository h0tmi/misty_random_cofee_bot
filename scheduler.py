import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import Database
from matching import MatchingService, format_user_profile
from handlers.matching import get_participation_keyboard

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
        """Начать еженедельный мэтчинг"""
        try:
            logger.info("Начинаем еженедельный мэтчинг...")

            # Создаем автоматические пары и запросы на подтверждение
            auto_matches = await self.matching_service.create_weekly_matches()

            # Отправляем автоматические пары
            for user1, user2 in auto_matches:
                await self._send_match_notification(user1, user2)
                await self._send_match_notification(user2, user1)

            # Отправляем запросы на подтверждение участия
            pending_users = await self.matching_service.process_pending_confirmations()
            for user in pending_users:
                await self._send_participation_request(user)

            logger.info(f"Мэтчинг завершен. Автоматических пар: {len(auto_matches)}, "
                       f"запросов на подтверждение: {len(pending_users)}")

        except Exception as e:
            logger.error(f"Ошибка при еженедельном мэтчинге: {e}")

    async def create_confirmed_matches(self):
        """Создать пары из подтвердивших участие пользователей"""
        try:
            logger.info("Создаем пары из подтвердивших участие...")

            confirmed_matches = await self.matching_service.create_matches_from_confirmed_participants()

            # Отправляем уведомления о парах
            for user1, user2 in confirmed_matches:
                await self._send_match_notification(user1, user2)
                await self._send_match_notification(user2, user1)

            logger.info(f"Создано {len(confirmed_matches)} пар из подтвердивших участие")

        except Exception as e:
            logger.error(f"Ошибка при создании подтвержденных пар: {e}")

    async def _send_match_notification(self, user: object, partner: object):
        """Отправить уведомление о паре"""
        try:
            profile_text = format_user_profile(partner)
            await self.bot.send_message(
                chat_id=user.user_id,
                text=profile_text,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user.user_id}: {e}")

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
