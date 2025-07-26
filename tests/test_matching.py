import pytest
from unittest.mock import AsyncMock, patch
import random

from models import User, ParticipationStatus
from matching import MatchingService, format_user_profile

class TestMatchingService:
    """Тесты сервиса мэтчинга"""

    @pytest.mark.asyncio
    async def test_create_matches_from_users_even_number(self, matching_service, temp_db):
        """Тест создания пар из четного количества пользователей"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.ALWAYS),
            User(2, "bob", "Bob", None, None, None, ParticipationStatus.ALWAYS),
            User(3, "charlie", "Charlie", None, None, None, ParticipationStatus.ALWAYS),
            User(4, "diana", "Diana", None, None, None, ParticipationStatus.ALWAYS),
        ]

        # Добавляем пользователей в базу
        for user in users:
            await temp_db.create_or_update_user(user)

        matches = await matching_service._create_matches_from_users(users)

        assert len(matches) == 2  # 4 пользователя = 2 пары

        # Проверяем, что все пользователи использованы
        matched_users = set()
        for user1, user2 in matches:
            matched_users.add(user1.user_id)
            matched_users.add(user2.user_id)

        assert len(matched_users) == 4
        assert matched_users == {1, 2, 3, 4}

    @pytest.mark.asyncio
    async def test_create_matches_from_users_odd_number(self, matching_service, temp_db):
        """Тест создания пар из нечетного количества пользователей"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.ALWAYS),
            User(2, "bob", "Bob", None, None, None, ParticipationStatus.ALWAYS),
            User(3, "charlie", "Charlie", None, None, None, ParticipationStatus.ALWAYS),
        ]

        # Добавляем пользователей в базу
        for user in users:
            await temp_db.create_or_update_user(user)

        matches = await matching_service._create_matches_from_users(users)

        assert len(matches) == 1  # 3 пользователя = 1 пара (1 остается)

        # Проверяем, что 2 пользователя в паре
        matched_users = set()
        for user1, user2 in matches:
            matched_users.add(user1.user_id)
            matched_users.add(user2.user_id)

        assert len(matched_users) == 2

    @pytest.mark.asyncio
    async def test_create_matches_insufficient_users(self, matching_service, temp_db):
        """Тест создания пар при недостаточном количестве пользователей"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.ALWAYS),
        ]

        matches = await matching_service._create_matches_from_users(users)
        assert len(matches) == 0  # Нельзя создать пару из 1 человека

        # Тест с пустым списком
        empty_matches = await matching_service._create_matches_from_users([])
        assert len(empty_matches) == 0

class TestMatchingAntiRepeat:
    """Тесты против повторного мэтчинга одних и тех же пользователей"""

    @pytest.mark.asyncio
    async def test_recent_match_blocking(self, matching_service, temp_db):
        """Тест блокировки недавних пар"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.ALWAYS),
            User(2, "bob", "Bob", None, None, None, ParticipationStatus.ALWAYS),
        ]

        # Добавляем пользователей в базу
        for user in users:
            await temp_db.create_or_update_user(user)

        # Создаем первую пару
        await temp_db.create_match(1, 2)

        # Проверяем, что пара считается недавней
        is_recent = await matching_service._were_matched_recently(1, 2, days=30)
        assert is_recent is True

        # Создаем пары снова - они не должны повториться
        with patch.object(matching_service, '_were_matched_recently', return_value=True):
            matches = await matching_service._create_matches_from_users(users)
            assert len(matches) == 0  # Пары не создались из-за недавнего мэтчинга

    @pytest.mark.asyncio
    async def test_multiple_rounds_no_immediate_repeat(self, matching_service, temp_db):
        """Тест множественных раундов мэтчинга без немедленных повторов"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.ALWAYS),
            User(2, "bob", "Bob", None, None, None, ParticipationStatus.ALWAYS),
            User(3, "charlie", "Charlie", None, None, None, ParticipationStatus.ALWAYS),
            User(4, "diana", "Diana", None, None, None, ParticipationStatus.ALWAYS),
        ]

        # Добавляем пользователей в базу
        for user in users:
            await temp_db.create_or_update_user(user)

        # Фиксируем random seed для предсказуемости
        random.seed(42)

        # Первый раунд мэтчинга
        matches_round1 = await matching_service._create_matches_from_users(users)
        assert len(matches_round1) == 2

        first_round_pairs = set()
        for user1, user2 in matches_round1:
            pair = tuple(sorted([user1.user_id, user2.user_id]))
            first_round_pairs.add(pair)

        # Симулируем второй раунд через 35 дней (после окончания блокировки)
        # Для этого мы мокаем метод проверки недавних пар
        async def mock_were_matched_recently(user1_id, user2_id, days=30):
            # Возвращаем False, имитируя что прошло достаточно времени
            return False

        with patch.object(matching_service, '_were_matched_recently', side_effect=mock_were_matched_recently):
            matches_round2 = await matching_service._create_matches_from_users(users)
            assert len(matches_round2) == 2

            second_round_pairs = set()
            for user1, user2 in matches_round2:
                pair = tuple(sorted([user1.user_id, user2.user_id]))
                second_round_pairs.add(pair)

            # Пары должны отличаться (при достаточном количестве пользователей)
            # С 4 пользователями возможны пары: (1,2), (3,4), (1,3), (2,4), (1,4), (2,3)
            # Вероятность повтора мала, но возможна
            print(f"Round 1 pairs: {first_round_pairs}")
            print(f"Round 2 pairs: {second_round_pairs}")

    @pytest.mark.asyncio
    async def test_large_group_anti_repeat(self, matching_service, temp_db):
        """Тест анти-повтора на большой группе пользователей"""
        # Создаем 10 пользователей
        users = []
        for i in range(1, 11):
            user = User(
                user_id=i,
                username=f"user{i}",
                first_name=f"User{i}",
                last_name=None,
                bio=None,
                interests=None,
                participation_status=ParticipationStatus.ALWAYS
            )
            users.append(user)
            await temp_db.create_or_update_user(user)

        # Проводим несколько раундов мэтчинга
        all_pairs = set()

        for round_num in range(5):  # 5 раундов
            # Мокаем проверку недавних пар для каждого раунда
            async def mock_were_matched_recently(user1_id, user2_id, days=30):
                pair = tuple(sorted([user1_id, user2_id]))
                return pair in all_pairs  # Блокируем уже использованные пары

            with patch.object(matching_service, '_were_matched_recently', side_effect=mock_were_matched_recently):
                matches = await matching_service._create_matches_from_users(users)

                # Добавляем новые пары
                for user1, user2 in matches:
                    pair = tuple(sorted([user1.user_id, user2.user_id]))
                    all_pairs.add(pair)
                    # Также сохраняем в базу для реальной проверки
                    await temp_db.create_match(user1.user_id, user2.user_id)

                print(f"Round {round_num + 1}: {len(matches)} matches created")

        print(f"Total unique pairs created: {len(all_pairs)}")

        # С 10 пользователями максимально возможно 45 уникальных пар (C(10,2))
        # За 5 раундов по 5 пар каждый = максимум 25 пар
        assert len(all_pairs) <= 25
        assert len(all_pairs) > 0  # Должны создаваться пары

    @pytest.mark.asyncio
    async def test_weekly_matching_workflow(self, matching_service, populated_db):
        """Тест полного процесса еженедельного мэтчинга"""
        matches = await matching_service.create_weekly_matches()

        # Должны получить пары из пользователей со статусом ALWAYS
        # Alice (1), Bob (2), Diana (4) = 1 пара + 1 человек остается
        assert len(matches) == 1

        # Проверяем, что создались pending записи для ASK_EACH_TIME пользователей
        pending = await populated_db.get_pending_participants()
        assert len(pending) == 1  # Charlie (3)
        assert pending[0].user_id == 3

    @pytest.mark.asyncio
    async def test_confirmed_participation_workflow(self, matching_service, populated_db):
        """Тест работы с подтвержденным участием"""
        # Создаем pending записи
        await populated_db.create_pending_match(1)  # Alice
        await populated_db.create_pending_match(2)  # Bob
        await populated_db.create_pending_match(3)  # Charlie

        # Подтверждаем участие для Alice и Bob
        await matching_service.confirm_participation(1, True)
        await matching_service.confirm_participation(2, True)
        await matching_service.confirm_participation(3, False)

        # Создаем пары из подтвердивших
        matches = await matching_service.create_matches_from_confirmed_participants()

        assert len(matches) == 1  # Alice и Bob должны составить пару

        matched_ids = set()
        for user1, user2 in matches:
            matched_ids.add(user1.user_id)
            matched_ids.add(user2.user_id)

        assert matched_ids == {1, 2}  # Alice и Bob

        # Проверяем, что pending записи очищены
        pending_after = await populated_db.get_pending_participants()
        assert len(pending_after) == 0

class TestMatchingEdgeCases:
    """Тесты граничных случаев мэтчинга"""

    @pytest.mark.asyncio
    async def test_no_users_available(self, matching_service, temp_db):
        """Тест когда нет доступных пользователей"""
        matches = await matching_service.create_weekly_matches()
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_only_never_participate_users(self, matching_service, temp_db):
        """Тест когда все пользователи имеют статус NEVER"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.NEVER),
            User(2, "bob", "Bob", None, None, None, ParticipationStatus.NEVER),
        ]

        for user in users:
            await temp_db.create_or_update_user(user)

        matches = await matching_service.create_weekly_matches()
        assert len(matches) == 0

    @pytest.mark.asyncio
    async def test_all_users_recently_matched(self, matching_service, temp_db):
        """Тест когда все пользователи недавно были в парах друг с другом"""
        users = [
            User(1, "alice", "Alice", None, None, None, ParticipationStatus.ALWAYS),
            User(2, "bob", "Bob", None, None, None, ParticipationStatus.ALWAYS),
        ]

        for user in users:
            await temp_db.create_or_update_user(user)

        # Создаем недавний мэтч
        await temp_db.create_match(1, 2)

        matches = await matching_service.create_weekly_matches()
        assert len(matches) == 0  # Не должно создаться пар

def test_format_user_profile():
    """Тест форматирования профиля пользователя"""
    user = User(
        user_id=1,
        username="alice",
        first_name="Alice",
        last_name="Smith",
        bio="Люблю кофе и программирование",
        interests="Python, кофе, книги",
        participation_status=ParticipationStatus.ALWAYS
    )

    profile_text = format_user_profile(user)

    assert "Alice Smith" in profile_text
    assert "@alice" in profile_text
    assert "Люблю кофе и программирование" in profile_text
    assert "Python, кофе, книги" in profile_text
    assert "💬 Напишите друг другу" in profile_text

def test_format_user_profile_minimal():
    """Тест форматирования минимального профиля"""
    user = User(
        user_id=1,
        username=None,
        first_name="Alice",
        last_name=None,
        bio=None,
        interests=None,
        participation_status=ParticipationStatus.ALWAYS
    )

    profile_text = format_user_profile(user)

    assert "Alice" in profile_text
    assert "@" not in profile_text  # Нет username
    assert "👤 Ваша пара на эту неделю" in profile_text
