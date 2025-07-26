import sqlite3
from typing import Optional, List
from datetime import datetime, timedelta
from models import User, ParticipationStatus


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False

    async def init_db(self):
        """Инициализация базы данных"""
        if self._initialized:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                bio TEXT,
                interests TEXT,
                participation_status TEXT DEFAULT 'ask_each_time',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER,
                user2_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (user1_id) REFERENCES users (user_id),
                FOREIGN KEY (user2_id) REFERENCES users (user_id)
            )
        """)

        # Новая таблица для ожидающих подтверждения участников
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pending_matches (
                user_id INTEGER PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed BOOLEAN DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        conn.commit()
        conn.close()
        self._initialized = True

    async def _ensure_initialized(self):
        """Убедиться, что база данных инициализирована"""
        if not self._initialized:
            await self.init_db()

    # ... (предыдущие методы остаются без изменений)
    async def create_or_update_user(self, user: User) -> bool:
        """Создать или обновить пользователя"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO users
            (user_id, username, first_name, last_name, bio, interests, participation_status, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user.user_id, user.username, user.first_name, user.last_name,
            user.bio, user.interests, user.participation_status.value, user.is_active
        ))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def get_user(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return User(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                last_name=row[3],
                bio=row[4],
                interests=row[5],
                participation_status=ParticipationStatus(row[6]),
                is_active=bool(row[7]),
                created_at=row[8]
            )
        return None

    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def get_participants(self) -> List[User]:
        """Получить всех активных участников"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE is_active = 1 AND participation_status IN ('always', 'ask_each_time')
        """)

        rows = cursor.fetchall()
        conn.close()

        users = []
        for row in rows:
            users.append(User(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                last_name=row[3],
                bio=row[4],
                interests=row[5],
                participation_status=ParticipationStatus(row[6]),
                is_active=bool(row[7]),
                created_at=row[8]
            ))

        return users

    # Новые методы для мэтчинга
    async def get_users_by_participation_status(self, status: ParticipationStatus) -> List[User]:
        """Получить пользователей по статусу участия"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE is_active = 1 AND participation_status = ?
        """, (status.value,))

        rows = cursor.fetchall()
        conn.close()

        users = []
        for row in rows:
            users.append(User(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                last_name=row[3],
                bio=row[4],
                interests=row[5],
                participation_status=ParticipationStatus(row[6]),
                is_active=bool(row[7]),
                created_at=row[8]
            ))

        return users

    async def create_match(self, user1_id: int, user2_id: int) -> bool:
        """Создать пару пользователей"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO matches (user1_id, user2_id)
            VALUES (?, ?)
        """, (user1_id, user2_id))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def check_recent_match(self, user1_id: int, user2_id: int, days: int = 30) -> bool:
        """Проверить, были ли пользователи в паре недавно"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_threshold = datetime.now() - timedelta(days=days)

        cursor.execute("""
            SELECT COUNT(*) FROM matches
            WHERE ((user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?))
            AND created_at > ?
        """, (user1_id, user2_id, user2_id, user1_id, date_threshold.isoformat()))

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    async def create_pending_match(self, user_id: int) -> bool:
        """Создать запись ожидающего подтверждения участника"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO pending_matches (user_id, confirmed)
            VALUES (?, NULL)
        """, (user_id,))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def get_pending_participants(self) -> List[User]:
        """Получить список участников, ожидающих подтверждения"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.* FROM users u
            JOIN pending_matches pm ON u.user_id = pm.user_id
            WHERE pm.confirmed IS NULL
        """)

        rows = cursor.fetchall()
        conn.close()

        users = []
        for row in rows:
            users.append(User(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                last_name=row[3],
                bio=row[4],
                interests=row[5],
                participation_status=ParticipationStatus(row[6]),
                is_active=bool(row[7]),
                created_at=row[8]
            ))

        return users

    async def confirm_pending_participation(self, user_id: int) -> bool:
        """Подтвердить участие пользователя"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pending_matches
            SET confirmed = 1
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def decline_pending_participation(self, user_id: int) -> bool:
        """Отклонить участие пользователя"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE pending_matches
            SET confirmed = 0
            WHERE user_id = ?
        """, (user_id,))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def get_confirmed_participants(self) -> List[User]:
        """Получить список подтвердивших участие пользователей"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.* FROM users u
            JOIN pending_matches pm ON u.user_id = pm.user_id
            WHERE pm.confirmed = 1
        """)

        rows = cursor.fetchall()
        conn.close()

        users = []
        for row in rows:
            users.append(User(
                user_id=row[0],
                username=row[1],
                first_name=row[2],
                last_name=row[3],
                bio=row[4],
                interests=row[5],
                participation_status=ParticipationStatus(row[6]),
                is_active=bool(row[7]),
                created_at=row[8]
            ))

        return users

    async def clear_pending_matches(self) -> bool:
        """Очистить таблицу ожидающих подтверждения"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM pending_matches")

        conn.commit()
        result = cursor.rowcount >= 0
        conn.close()
        return result
