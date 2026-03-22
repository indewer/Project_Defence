import os
import asyncio
import sqlite3
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

# --- КОНФИГУРАЦИЯ ---
# Токен берется из переменных окружения Windows
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Твоя вечная ссылка на GitHub Pages
WEB_APP_URL = "https://indewer.github.io/Project_Defence/"
DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "press.db")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    """Создает базу и колонки для ресурсов королевства"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Основная таблица логов
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  name TEXT, 
                  date TEXT, 
                  reps INTEGER, 
                  wood INTEGER DEFAULT 0,
                  stone INTEGER DEFAULT 0,
                  gold INTEGER DEFAULT 0,
                  timestamp REAL)''')
    
    c.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON logs(user_id, date)''')
    conn.commit()
    conn.close()
    print("✅ База данных SQLite готова (Ресурсы: Wood, Stone, Gold добавлены)")

# --- ОБРАБОТКА КОМАНД БОТА ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Отправляет кнопку открытия Mini App (Королевства)"""
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем кнопку отдельно
    web_button = KeyboardButton(text="🏰 Войти в Королевство", web_app=WebAppInfo(url=WEB_APP_URL))
    
    # Собираем клавиатуру (внимательно со скобками!)
    kb = ReplyKeyboardMarkup(keyboard=[[web_button]], resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Твои тренировки строят твое Королевство.\n"
        "Жми кнопку ниже, чтобы начать!",
        reply_markup=kb
    )


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Пример того, как бот может отдавать статистику прямо в чат"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT SUM(reps), SUM(wood), SUM(stone) FROM logs WHERE user_id=?", (message.from_user.id,))
    row = c.fetchone()
    conn.close()
    
    reps, wood, stone = row if row[0] is not None else (0, 0, 0)
    await message.answer(
        f"📊 Твои достижения:\n"
        f"💪 Повторений: {reps}\n"
        f"🪵 Дерево: {wood}\n"
        f"🪨 Камень: {stone}"
    )

# --- ГЛАВНАЯ ФУНКЦИЯ ЗАПУСКА ---
async def main():
    if not BOT_TOKEN:
        print("❌ ОШИБКА: Переменная окружения BOT_TOKEN не найдена!")
        return

    init_db()
    print(f"🚀 Бот запущен! Ссылка на Mini App: {WEB_APP_URL}")
    
    # Запуск опроса Telegram (Polling)
    # Бот сам будет забирать сообщения, Flask и ngrok больше не нужны
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🔴 Бот остановлен")
