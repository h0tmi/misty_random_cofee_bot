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
                meeting_feedback TEXT DEFAULT NULL,
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

        # Таблица для отслеживания сессий матчинга
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matching_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT DEFAULT 'collecting',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deadline TIMESTAMP,
                completed_at TIMESTAMP DEFAULT NULL,
                forced_completion BOOLEAN DEFAULT 0
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

    # Админские методы
    async def get_all_users(self, limit: int = None, offset: int = 0) -> List[User]:
        """Получить всех пользователей (с пагинацией)"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM users ORDER BY created_at DESC"
        params = ()

        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params = (limit, offset)

        cursor.execute(query, params)
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

    async def get_users_count(self) -> int:
        """Получить общее количество пользователей"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()

        return count

    async def get_matching_statistics(self) -> dict:
        """Получить статистику мэтчинга"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Общее количество мэтчей
        cursor.execute("SELECT COUNT(*) FROM matches")
        total_matches = cursor.fetchone()[0]

        # Количество мэтчей за последние 30 дней
        cursor.execute("""
            SELECT COUNT(*) FROM matches
            WHERE created_at >= datetime('now', '-30 days')
        """)
        recent_matches = cursor.fetchone()[0]

        # Количество пользователей по статусам участия
        cursor.execute("""
            SELECT participation_status, COUNT(*) FROM users
            WHERE is_active = 1
            GROUP BY participation_status
        """)
        participation_stats = dict(cursor.fetchall())

        # Количество активных пользователей
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]

        # Количество пользователей, ожидающих подтверждения
        cursor.execute("SELECT COUNT(*) FROM pending_matches WHERE confirmed IS NULL")
        pending_users = cursor.fetchone()[0]

        # Количество подтвердивших участие
        cursor.execute("SELECT COUNT(*) FROM pending_matches WHERE confirmed = 1")
        confirmed_users = cursor.fetchone()[0]

        conn.close()

        return {
            'total_matches': total_matches,
            'recent_matches': recent_matches,
            'participation_stats': participation_stats,
            'active_users': active_users,
            'pending_users': pending_users,
            'confirmed_users': confirmed_users
        }

    # Методы для работы с обратной связью о встречах
    async def record_meeting_feedback(self, match_id: int, user_id: int, feedback: str) -> bool:
        """Записать обратную связь о встрече"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Проверяем, что пользователь участвует в этом матче
        cursor.execute("""
            SELECT id FROM matches
            WHERE id = ? AND (user1_id = ? OR user2_id = ?)
        """, (match_id, user_id, user_id))

        match = cursor.fetchone()
        if not match:
            conn.close()
            return False

        # Записываем обратную связь
        cursor.execute("""
            UPDATE matches
            SET meeting_feedback = ?
            WHERE id = ?
        """, (feedback, match_id))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def get_user_recent_matches(self, user_id: int, days: int = 7) -> List[dict]:
        """Получить недавние матчи пользователя для отправки обратной связи"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        date_threshold = datetime.now() - timedelta(days=days)

        cursor.execute("""
            SELECT m.id, m.user1_id, m.user2_id, m.created_at, m.meeting_feedback,
                   u1.first_name as user1_name, u1.last_name as user1_lastname,
                   u2.first_name as user2_name, u2.last_name as user2_lastname
            FROM matches m
            JOIN users u1 ON m.user1_id = u1.user_id
            JOIN users u2 ON m.user2_id = u2.user_id
            WHERE (m.user1_id = ? OR m.user2_id = ?)
            AND m.created_at >= ?
            AND m.meeting_feedback IS NULL
            ORDER BY m.created_at DESC
        """, (user_id, user_id, date_threshold.isoformat()))

        rows = cursor.fetchall()
        conn.close()

        matches = []
        for row in rows:
            partner_name = (
                f"{row[5]} {row[6] or ''}".strip() if user_id == row[2]
                else f"{row[7]} {row[8] or ''}".strip()
            )
            matches.append({
                'match_id': row[0],
                'partner_name': partner_name,
                'created_at': row[3],
                'feedback': row[4]
            })

        return matches

    # Методы для работы с сессиями матчинга
    async def create_matching_session(self, deadline_hours: int = 24) -> int:
        """Создать новую сессию матчинга"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        deadline = datetime.now() + timedelta(hours=deadline_hours)

        cursor.execute("""
            INSERT INTO matching_sessions (deadline)
            VALUES (?)
        """, (deadline.isoformat(),))

        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id

    async def get_current_matching_session(self) -> Optional[dict]:
        """Получить текущую активную сессию матчинга"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, status, started_at, deadline, completed_at, forced_completion
            FROM matching_sessions
            WHERE status IN ('collecting', 'pairing')
            ORDER BY started_at DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'status': row[1],
                'started_at': row[2],
                'deadline': row[3],
                'completed_at': row[4],
                'forced_completion': bool(row[5])
            }
        return None

    async def update_matching_session_status(self, session_id: int, status: str, forced: bool = False) -> bool:
        """Обновить статус сессии матчинга"""
        await self._ensure_initialized()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if status == 'completed':
            cursor.execute("""
                UPDATE matching_sessions
                SET status = ?, completed_at = CURRENT_TIMESTAMP, forced_completion = ?
                WHERE id = ?
            """, (status, forced, session_id))
        else:
            cursor.execute("""
                UPDATE matching_sessions
                SET status = ?
                WHERE id = ?
            """, (status, session_id))

        conn.commit()
        result = cursor.rowcount > 0
        conn.close()
        return result

    async def force_complete_matching_session(self) -> bool:
        """Принудительно завершить текущую сессию матчинга"""
        session = await self.get_current_matching_session()
        if not session:
            return False

        return await self.update_matching_session_status(
            session['id'], 'completed', forced=True
        )
