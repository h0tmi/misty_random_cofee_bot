import random
import logging
from typing import List, Tuple, Set

from models import User, ParticipationStatus
from database import Database

logger = logging.getLogger(__name__)


class MatchingResult:
    """Результат матчинга"""
    def __init__(self):
        self.matches: List[Tuple[User, User]] = []
        self.unmatched_users: List[User] = []
        self.users_with_recent_matches: List[User] = []


class MatchingService:
    def __init__(self, database: Database):
        self.db = database

    async def start_weekly_matching_session(self, deadline_hours: int = 24) -> int:
        """Начать новую сессию матчинга с дедлайном для сбора участников"""
        # Создаем новую сессию матчинга
        session_id = await self.db.create_matching_session(deadline_hours)

        # Получаем участников со статусом "спрашивать каждый раз"
        ask_participants = await self.db.get_users_by_participation_status(
            ParticipationStatus.ASK_EACH_TIME
        )

        # Для участников "спрашивать каждый раз" создаем записи
        # в таблице pending_matches
        await self._create_pending_matches(ask_participants)

        logger.info(f"Начата сессия матчинга #{session_id}")
        logger.info(f"Создано {len(ask_participants)} запросов на "
                    f"подтверждение участия")
        logger.info(f"Дедлайн для подтверждения: {deadline_hours} часов")

        return session_id

    async def create_weekly_matches(self) -> MatchingResult:
        """Создать пары для еженедельного мэтчинга из всех участников"""
        # Получаем всех участников со статусом "всегда участвовать"
        always_participants = await self.db.get_users_by_participation_status(
            ParticipationStatus.ALWAYS
        )

        # Получаем участников, подтвердивших участие
        confirmed_participants = await self.db.get_confirmed_participants()

        # Объединяем всех участников
        all_participants = always_participants + confirmed_participants

        # Создаем пары из всех участников
        result = await self._create_matches_from_users(all_participants)

        # Очищаем таблицу pending_matches после создания пар
        await self.db.clear_pending_matches()

        logger.info(f"Создано {len(result.matches)} пар для матчинга")
        logger.info(f"Участников 'всегда': {len(always_participants)}")
        logger.info(f"Подтвердивших участие: {len(confirmed_participants)}")
        logger.info(f"Не нашлось пары для {len(result.unmatched_users)} "
                    f"пользователей")
        logger.info(f"Пропущено из-за недавних матчей: "
                    f"{len(result.users_with_recent_matches)} пользователей")

        return result

    async def _create_pending_matches(self, users: List[User]):
        """Создать записи ожидающих подтверждения участников"""
        for user in users:
            await self.db.create_pending_match(user.user_id)

    async def _create_matches_from_users(self, users: List[User]) -> MatchingResult:
        """Создать пары из списка пользователей"""
        result = MatchingResult()

        if len(users) < 2:
            # Если пользователей меньше 2, никого нельзя сматчить
            result.unmatched_users = users
            return result

        # Перемешиваем пользователей для случайности
        shuffled_users = users.copy()
        random.shuffle(shuffled_users)

        matched_user_ids: Set[int] = set()

        # Создаем пары
        for i in range(0, len(shuffled_users) - 1, 2):
            user1 = shuffled_users[i]
            user2 = shuffled_users[i + 1]

            # Проверяем, не были ли эти пользователи в паре недавно
            if not await self._were_matched_recently(user1.user_id, user2.user_id):
                # Сохраняем пару в базу данных
                await self.db.create_match(user1.user_id, user2.user_id)
                result.matches.append((user1, user2))
                matched_user_ids.add(user1.user_id)
                matched_user_ids.add(user2.user_id)
            else:
                # Пользователи недавно были в паре, добавляем их в список с недавними матчами
                result.users_with_recent_matches.extend([user1, user2])

        # Обрабатываем пользователей, которые не были сматчены
        for user in shuffled_users:
            if user.user_id not in matched_user_ids:
                # Если остался один пользователь и есть существующие пары,
                # можно добавить его к случайной паре (группа из 3 человек)
                if (len(shuffled_users) % 2 == 1 and result.matches and
                    user == shuffled_users[-1]):
                    # Это случай с нечетным количеством - добавляем в группу из 3 человек
                    random_match_index = random.randint(0, len(result.matches) - 1)
                    logger.info(f"Пользователь {user.first_name} добавлен к "
                               f"существующей паре (группа из 3 человек)")
                    # Можно расширить логику для групп из 3 человек в будущем
                    result.unmatched_users.append(user)
                else:
                    result.unmatched_users.append(user)

        return result

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

    async def create_matches_from_confirmed_participants(self) -> MatchingResult:
        """Создать пары из подтвердивших участие пользователей"""
        confirmed_users = await self.db.get_confirmed_participants()
        result = await self._create_matches_from_users(confirmed_users)

        # Очищаем таблицу pending_matches после создания пар
        await self.db.clear_pending_matches()

        return result


def format_user_profile(user: User, match_id: int = None) -> str:
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
    profile_text += f"☕ Удачного знакомства!\n\n"

    if match_id:
        profile_text += (
            f"📋 После встречи, пожалуйста, отметьте состоялась ли она, "
            f"это поможет улучшить алгоритм подбора пар."
        )

    return profile_text


def format_no_match_message(user: User) -> str:
    """Форматировать сообщение для пользователя без пары"""
    message_text = f"☕ Привет, {user.first_name}!\n\n"
    message_text += f"К сожалению, на этой неделе мы не смогли подобрать вам "
    message_text += f"пару для Random Coffee.\n\n"
    message_text += f"Это могло произойти по одной из причин:\n"
    message_text += f"• Недостаточное количество участников\n"
    message_text += f"• Вы недавно встречались с доступными участниками\n\n"
    message_text += f"Не расстраивайтесь! Мы обязательно найдем вам "
    message_text += f"интересного собеседника на следующей неделе! 😊\n\n"
    message_text += f"Приглашайте друзей в Random Coffee - чем больше "
    message_text += f"участников, тем больше интересных знакомств!"

    return message_text
