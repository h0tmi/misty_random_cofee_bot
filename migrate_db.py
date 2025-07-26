#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления новых функций:
1. Поле meeting_feedback в таблице matches
2. Таблица matching_sessions для отслеживания сессий матчинга
"""

import sqlite3
import sys
from config import load_config


def migrate_database():
    """Выполнить миграцию базы данных"""
    config = load_config()
    conn = sqlite3.connect(config.database_path)
    cursor = conn.cursor()

    try:
        print("Начинаем миграцию базы данных...")

        # Проверяем, есть ли поле meeting_feedback в таблице matches
        cursor.execute("PRAGMA table_info(matches)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'meeting_feedback' not in columns:
            print("Добавляем поле meeting_feedback в таблицу matches...")
            cursor.execute("""
                ALTER TABLE matches
                ADD COLUMN meeting_feedback TEXT DEFAULT NULL
            """)
            print("✅ Поле meeting_feedback добавлено")
        else:
            print("ℹ️ Поле meeting_feedback уже существует")

        # Проверяем, существует ли таблица matching_sessions
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='matching_sessions'
        """)

        if not cursor.fetchone():
            print("Создаем таблицу matching_sessions...")
            cursor.execute("""
                CREATE TABLE matching_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT DEFAULT 'collecting',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deadline TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT NULL,
                    forced_completion BOOLEAN DEFAULT 0
                )
            """)
            print("✅ Таблица matching_sessions создана")
        else:
            print("ℹ️ Таблица matching_sessions уже существует")

        conn.commit()
        print("✅ Миграция завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

    return True


if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)