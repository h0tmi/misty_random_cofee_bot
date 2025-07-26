import random
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

from models import User, ParticipationStatus
from database import Database

logger = logging.getLogger(__name__)

class MatchingService:
    def __init__(self, database: Database):
        self.db = database

    async def create_weekly_matches(self) -> List[Tuple[User, User]]:
        """Создать пары для еженедельного мэтчинга"""
        # Получаем всех участников со статусом "всегда участвовать"
        always_participants = await self.db.get_users_by_participation_status(
            ParticipationStatus.ALWAYS
        )

        # Получаем участников со статусом "спрашивать каждый раз"
        ask_participants = await self.db.get_users_by_participation_status(
            ParticipationStatus.ASK_EACH_TIME
        )

        # Для участников "спрашивать каждый раз" создаем записи в таблице pending_matches
        await self._create_pending_matches(ask_participants)

        # Создаем пары из участников "всегда участвовать"
        matches = await self._create_matches_from_users(always_participants)

        logger.info(f"Создано {len(matches)} пар для автоматического мэтчинга")
        logger.info(f"Создано {len(ask_participants)} запросов на подтверждение участия")

        return matches

    async def _create_pending_matches(self, users: List[User]):
        """Создать записи ожидающих подтверждения участников"""
        for user in users:
            await self.db.create_pending_match(user.user_id)

    async def _create_matches_from_users(self, users: List[User]) -> List[Tuple[User, User]]:
        """Создать пары из списка пользователей"""
        if len(users) < 2:
            return []

        # Перемешиваем пользователей для случайности
        shuffled_users = users.copy()
        random.shuffle(shuffled_users)

        matches = []

        # Создаем пары
        for i in range(0, len(shuffled_users) - 1, 2):
            user1 = shuffled_users[i]
            user2 = shuffled_users[i + 1]

            # Проверяем, не были ли эти пользователи в паре недавно
            if not await self._were_matched_recently(user1.user_id, user2.user_id):
                # Сохраняем пару в базу данных
                await self.db.create_match(user1.user_id, user2.user_id)
                matches.append((user1, user2))

        # Если остался один пользователь, добавляем его к случайной паре (группа из 3 человек)
        if len(shuffled_users) % 2 == 1:
            if matches:
                last_user = shuffled_users[-1]
                # Добавляем к последней паре (создаем группу из 3 человек)
                random_match_index = random.randint(0, len(matches) - 1)
                logger.info(f"Пользователь {last_user.first_name} добавлен к существующей паре (группа из 3 человек)")

        return matches

    async def _were_matched_recently(self, user1_id: int, user2_id: int, days: int = 30) -> bool:
        """Проверить, были ли пользователи в паре недавно"""
        return await self.db.check_recent_match(user1_id, user2_id, days)

    async def process_pending_confirmations(self) -> List[User]:
        """Получить список пользователей, которым нужно отправить запрос на участие"""
        return await self.db.get_pending_participants()

    async def confirm_participation(self, user_id: int, wants_to_participate: bool):
        """Подтвердить или отклонить участие пользователя"""
        if wants_to_participate:
            await self.db.confirm_pending_participation(user_id)
        else:
            await self.db.decline_pending_participation(user_id)

    async def create_matches_from_confirmed_participants(self) -> List[Tuple[User, User]]:
        """Создать пары из подтвердивших участие пользователей"""
        confirmed_users = await self.db.get_confirmed_participants()
        matches = await self._create_matches_from_users(confirmed_users)

        # Очищаем таблицу pending_matches после создания пар
        await self.db.clear_pending_matches()

        return matches

def format_user_profile(user: User) -> str:
    """Форматировать анкету пользователя для отправки"""
    profile_text = f"👤 Ваша пара на эту неделю:\n\n"
    profile_text += f"**{user.first_name}"

    if user.last_name:
        profile_text += f" {user.last_name}"

    if user.username:
        profile_text += f"** (@{user.username})"
    else:
        profile_text += "**"

    profile_text += f"\n\n"

    if user.bio:
        profile_text += f"📝 О себе: {user.bio}\n\n"

    if user.interests:
        profile_text += f"🎯 Интересы: {user.interests}\n\n"

    profile_text += f"💬 Напишите друг другу и договоритесь о встрече!\n"
    profile_text += f"☕ Удачного знакомства!"

    return profile_text
