import pytest
import pytest_asyncio
import tempfile
import os

from database import Database
from models import User, ParticipationStatus
from matching import MatchingService


@pytest_asyncio.fixture(scope="function")
async def temp_db():
    """Временная база данных для тестов"""
    # Создаем временный файл базы данных
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    db = Database(temp_file.name)
    await db.init_db()

    yield db

    # Удаляем временный файл после теста
    try:
        os.unlink(temp_file.name)
    except OSError:
        pass


@pytest_asyncio.fixture(scope="function")
async def matching_service(temp_db):
    """Сервис мэтчинга для тестов"""
    return MatchingService(temp_db)


@pytest.fixture(scope="function")
def sample_users():
    """Примеры пользователей для тестов"""
    return [
        User(
            user_id=1,
            username="alice",
            first_name="Alice",
            last_name="Smith",
            bio="Люблю кофе и книги",
            interests="Чтение, программирование",
            participation_status=ParticipationStatus.ALWAYS
        ),
        User(
            user_id=2,
            username="bob",
            first_name="Bob",
            last_name="Johnson",
            bio="Разработчик и путешественник",
            interests="IT, путешествия",
            participation_status=ParticipationStatus.ALWAYS
        ),
        User(
            user_id=3,
            username="charlie",
            first_name="Charlie",
            last_name="Brown",
            bio="Дизайнер и художник",
            interests="Дизайн, искусство",
            participation_status=ParticipationStatus.ASK_EACH_TIME
        ),
        User(
            user_id=4,
            username="diana",
            first_name="Diana",
            last_name="Wilson",
            bio="Маркетолог",
            interests="Маркетинг, психология",
            participation_status=ParticipationStatus.ALWAYS
        ),
        User(
            user_id=5,
            username="eve",
            first_name="Eve",
            last_name="Davis",
            bio="Учитель",
            interests="Образование, музыка",
            participation_status=ParticipationStatus.NEVER
        )
    ]


@pytest_asyncio.fixture(scope="function")
async def populated_db(temp_db, sample_users):
    """База данных с тестовыми пользователями"""
    for user in sample_users:
        await temp_db.create_or_update_user(user)
    yield temp_db
