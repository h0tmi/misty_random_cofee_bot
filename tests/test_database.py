import pytest
from datetime import datetime, timedelta

from models import User, ParticipationStatus

class TestDatabase:
    """Тесты для работы с базой данных"""

    @pytest.mark.asyncio
    async def test_create_user(self, temp_db):
        """Тест создания пользователя"""
        user = User(
            user_id=123,
            username="testuser",
            first_name="Test",
            last_name="User",
            bio="Test bio",
            interests="Testing",
            participation_status=ParticipationStatus.ALWAYS
        )

        result = await temp_db.create_or_update_user(user)
        assert result is True

        # Проверяем, что пользователь создан
        retrieved_user = await temp_db.get_user(123)
        assert retrieved_user is not None
        assert retrieved_user.username == "testuser"
        assert retrieved_user.first_name == "Test"
        assert retrieved_user.bio == "Test bio"

    @pytest.mark.asyncio
    async def test_update_user(self, temp_db):
        """Тест обновления пользователя"""
        user = User(
            user_id=123,
            username="testuser",
            first_name="Test",
            last_name="User",
            bio="Original bio",
            interests="Testing",
            participation_status=ParticipationStatus.ALWAYS
        )

        await temp_db.create_or_update_user(user)

        # Обновляем пользователя
        user.bio = "Updated bio"
        user.participation_status = ParticipationStatus.ASK_EACH_TIME

        result = await temp_db.create_or_update_user(user)
        assert result is True

        # Проверяем обновление
        retrieved_user = await temp_db.get_user(123)
        assert retrieved_user.bio == "Updated bio"
        assert retrieved_user.participation_status == ParticipationStatus.ASK_EACH_TIME

    @pytest.mark.asyncio
    async def test_delete_user(self, temp_db):
        """Тест удаления пользователя"""
        user = User(
            user_id=123,
            username="testuser",
            first_name="Test",
            last_name="User",
            bio="Test bio",
            interests="Testing",
            participation_status=ParticipationStatus.ALWAYS
        )

        await temp_db.create_or_update_user(user)

        # Удаляем пользователя
        result = await temp_db.delete_user(123)
        assert result is True

        # Проверяем, что пользователь удален
        retrieved_user = await temp_db.get_user(123)
        assert retrieved_user is None

    @pytest.mark.asyncio
    async def test_get_users_by_participation_status(self, populated_db, sample_users):
        """Тест получения пользователей по статусу участия"""
        always_users = await populated_db.get_users_by_participation_status(
            ParticipationStatus.ALWAYS
        )
        ask_users = await populated_db.get_users_by_participation_status(
            ParticipationStatus.ASK_EACH_TIME
        )
        never_users = await populated_db.get_users_by_participation_status(
            ParticipationStatus.NEVER
        )

        assert len(always_users) == 3  # Alice, Bob, Diana
        assert len(ask_users) == 1     # Charlie
        assert len(never_users) == 1   # Eve

        always_ids = [user.user_id for user in always_users]
        assert 1 in always_ids  # Alice
        assert 2 in always_ids  # Bob
        assert 4 in always_ids  # Diana

    @pytest.mark.asyncio
    async def test_create_match(self, temp_db):
        """Тест создания пары"""
        result = await temp_db.create_match(1, 2)
        assert result is True

        # Проверяем, что пара была недавно
        recent = await temp_db.check_recent_match(1, 2, days=1)
        assert recent is True

        # Проверяем обратную пару
        recent_reverse = await temp_db.check_recent_match(2, 1, days=1)
        assert recent_reverse is True

    @pytest.mark.asyncio
    async def test_check_recent_match_expired(self, temp_db):
        """Тест проверки устаревших пар"""
        # Создаем пару
        await temp_db.create_match(1, 2)

        # Проверяем, что пара не считается недавней для большого периода
        recent = await temp_db.check_recent_match(1, 2, days=0)
        assert recent is False  # Должно быть False, так как мы ищем за 0 дней

    @pytest.mark.asyncio
    async def test_pending_matches_workflow(self, populated_db):
        """Тест работы с ожидающими подтверждения участниками"""
        # Создаем записи для ожидающих
        await populated_db.create_pending_match(1)
        await populated_db.create_pending_match(2)

        # Получаем список ожидающих
        pending = await populated_db.get_pending_participants()
        assert len(pending) == 2

        # Подтверждаем участие одного
        await populated_db.confirm_pending_participation(1)

        # Отклоняем участие другого
        await populated_db.decline_pending_participation(2)

        # Проверяем подтвердивших
        confirmed = await populated_db.get_confirmed_participants()
        assert len(confirmed) == 1
        assert confirmed[0].user_id == 1

        # Очищаем ожидающих
        await populated_db.clear_pending_matches()
        pending_after_clear = await populated_db.get_pending_participants()
        assert len(pending_after_clear) == 0
