import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage

from config import load_config
from database import Database
from keyboards import get_main_menu
from scheduler import MatchingScheduler
from handlers import profile, participation, matching

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация
config = load_config()
bot = Bot(token=config.bot_token)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Создаем экземпляр базы данных без инициализации
db = Database(config.database_path)

# Создаем планировщик
scheduler = MatchingScheduler(bot, db)

# Регистрация роутеров
dp.include_router(profile.router)
dp.include_router(participation.router)
dp.include_router(matching.router)

@dp.message(CommandStart())
async def start_command(message: Message):
    """Обработчик команды /start"""
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Я бот для Random Coffee - помогаю людям знакомиться и общаться за чашкой кофе ☕\n\n"
        f"Что я умею:\n"
        f"• Создавать и управлять анкетами\n"
        f"• Подбирать пары для встреч каждую неделю\n"
        f"• Управлять участием в мэтчинге\n\n"
        f"🗓 Мэтчинг происходит каждый понедельник!\n\n"
        f"Выберите действие:",
        reply_markup=get_main_menu()
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = """
🤖 Команды бота:

/start - Запустить бота
/help - Показать справку
/menu - Главное меню

📝 Как пользоваться:
1. Создайте анкету с информацией о себе
2. Выберите статус участия
3. Ждите уведомлений о новых знакомствах!

🗓 Расписание мэтчинга:
• Понедельник 10:00 - начало мэтчинга
• Вторник 10:00 - создание пар из подтвердивших участие

Статусы участия:
• ✅ Всегда участвовать - автоматическое участие в мэтчинге
• ❓ Спрашивать каждый раз - бот будет спрашивать перед каждым мэтчингом
• ❌ Не участвовать - отключить участие
    """
    await message.answer(help_text)

@dp.message(Command("menu"))
async def menu_command(message: Message):
    """Обработчик команды /menu"""
    await message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_menu()
    )

# Админские команды
@dp.message(Command("start_matching"))
async def manual_start_matching(message: Message):
    """Ручной запуск мэтчинга (только для админов)"""
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return

    await message.answer("🔄 Запускаю мэтчинг...")
    await scheduler.manual_start_matching()
    await message.answer("✅ Мэтчинг запущен!")

@dp.message(Command("create_confirmed_matches"))
async def manual_create_confirmed_matches(message: Message):
    """Ручное создание подтвержденных пар (только для админов)"""
    if message.from_user.id not in config.admin_ids:
        await message.answer("❌ У вас нет прав для выполнения этой команды")
        return

    await message.answer("🔄 Создаю пары из подтвердивших участие...")
    await scheduler.manual_create_confirmed_matches()
    await message.answer("✅ Пары созданы!")

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "🏠 Главное меню:",
        reply_markup=get_main_menu()
    )

# Middleware для передачи database в хендлеры
class DatabaseMiddleware:
    def __init__(self, database: Database):
        self.database = database

    async def __call__(self, handler, event, data):
        data['db'] = self.database
        return await handler(event, data)

async def main():
    """Запуск бота"""
    try:
        # Инициализируем базу данных после запуска event loop
        await db.init_db()

        # Регистрируем middleware
        db_middleware = DatabaseMiddleware(db)
        dp.message.middleware(db_middleware)
        dp.callback_query.middleware(db_middleware)

        # Запускаем планировщик
        scheduler.start()

        logger.info("🤖 Бот запущен!")
        logger.info("📅 Планировщик мэтчинга активен")

        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
    finally:
        scheduler.stop()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
