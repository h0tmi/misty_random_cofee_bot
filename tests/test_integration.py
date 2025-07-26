import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from models import User, ParticipationStatus
from matching import MatchingService
from scheduler import MatchingScheduler

class TestIntegration:
    """Интеграционные тесты всей системы"""

    @pytest.mark.asyncio
    async def test_full_matching_cycle(self, populated_db):
        """Тест полного цикла мэтчинга"""
        # Создаем мок бота
        mock_bot = AsyncMock()

        # Создаем планировщик
        scheduler = MatchingScheduler(mock_bot, populated_db)

        # Запускаем мэтчинг
        await scheduler.start_weekly_matching()

        # Проверяем, что отправились уведомления
        assert mock_bot.send_message.call_count >= 1

        # Проверяем, что создались pending записи
        pending = await populated_db.get_pending_participants()
        assert len(pending) == 1  # Charlie

@pytest.mark.stress
class TestStressTests:
    """Стресс-тесты для больших объемов данных"""

    @pytest.mark.asyncio
    async def test_large_user_base_matching(self, temp_db):
        """Тест мэтчинга с большой базой пользователей"""
        # Создаем 20 пользователей (уменьшаем для быстрых тестов)
        users = []
        for i in range(1, 21):
            user = User(
                user_id=i,
                username=f"user{i}",
                first_name=f"User{i}",
                last_name=f"LastName{i}",
                bio=f"Bio of user {i}",
                interests=f"Interest {i % 10}",  # 10 разных интересов
                participation_status=ParticipationStatus.ALWAYS
            )
            users.append(user)
            await temp_db.create_or_update_user(user)

        matching_service = MatchingService(temp_db)

        # Засекаем время выполнения
        import time
        start_time = time.time()

        matches = await matching_service._create_matches_from_users(users)

        end_time = time.time()
        execution_time = end_time - start_time

        print(f"Matching 20 users took {execution_time:.2f} seconds")

        # Проверяем результаты
        assert len(matches) == 10  # 20 пользователей = 10 пар
        assert execution_time < 2.0  # Должно выполняться быстро

        # Проверяем уникальность пар
        matched_users = set()
        for user1, user2 in matches:
            assert user1.user_id not in matched_users
            assert user2.user_id not in matched_users
            matched_users.add(user1.user_id)
            matched_users.add(user2.user_id)

        assert len(matched_users) == 20
