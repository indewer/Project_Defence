import asyncio
import threading
import os
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton

# КОНФИГУРАЦИЯ
BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://indewer.github.io")
DB_PATH = "press.db"

app = Flask(__name__)
app.config['SERVER_NAME'] = None

def get_db():
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn

def init_db():
	conn = get_db()
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS logs 
				 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
				  user_id INTEGER, name TEXT, date TEXT, reps INTEGER, timestamp REAL)''')
	c.execute('''CREATE UNIQUE INDEX IF NOT EXISTS idx_user_date ON logs(user_id, date)''')
	conn.commit()
	conn.close()
	print("✅ База данных готова.")

@app.route('/')
def index():
	return send_from_directory(BASE_DIR, 'index.html')

@app.route('/api/save', methods=['POST'])
def save_reps():
	data = request.json
	if not data:
		return jsonify({"status": "error", "message": "Нет данных"}), 400
	
	user_id = data.get('user_id')
	name = data.get('name', 'Unknown')
	
	try:
		reps = int(data.get('reps', 0))
	except ValueError:
		return jsonify({"status": "error", "message": "Неверное число"}), 400

	today = datetime.now().strftime('%Y-%m-%d')
	timestamp = datetime.now().timestamp()

	conn = get_db()
	c = conn.cursor()
	try:
		c.execute('''INSERT OR REPLACE INTO logs (user_id, name, date, reps, timestamp) 
					 VALUES (?, ?, ?, ?, ?)''', 
				  (user_id, name, today, reps, timestamp))
		conn.commit()
		return jsonify({"status": "success"})
	except Exception as e:
		return jsonify({"status": "error", "message": str(e)}), 500
	finally:
		conn.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
	conn = get_db()
	c = conn.cursor()
	c.execute('''SELECT name, SUM(reps) as total, MAX(date) as last FROM logs GROUP BY user_id ORDER BY total DESC''')
	leaderboard = [{"name": r["name"], "total": r["total"]} for r in c.fetchall()]
	
	today = datetime.now().strftime('%Y-%m-%d')
	c.execute('''SELECT name, reps, timestamp FROM logs WHERE date = ?''', (today,))
	today_list = []
	now = datetime.now().timestamp()
	
	for r in c.fetchall():
		can_edit = False
		minutes_left = 0
		if r['timestamp']:
			hours_passed = (now - r['timestamp']) / 3600
			if hours_passed < 1:
				can_edit = True
				minutes_left = int((1 - hours_passed) * 60)
		
		today_list.append({
			"name": r["name"],
			"reps": r["reps"],
			"can_edit": can_edit,
			"minutes_left": minutes_left
		})
	conn.close()
	
	return jsonify({"leaderboard": leaderboard, "today": today_list})

@app.route('/api/can_edit', methods=['GET'])
def can_edit():
	user_id = request.args.get('user_id')
	today = datetime.now().strftime('%Y-%m-%d')
	
	conn = get_db()
	c = conn.cursor()
	c.execute('''SELECT timestamp FROM logs WHERE user_id = ? AND date = ?''', 
			  (user_id, today))
	row = c.fetchone()
	conn.close()
	
	if not row:
		return jsonify({"can_edit": False, "reason": "no_data"})
	
	timestamp = row['timestamp']
	now = datetime.now().timestamp()
	hours_passed = (now - timestamp) / 3600
	
	if hours_passed < 1:
		minutes_left = int((1 - hours_passed) * 60)
		return jsonify({"can_edit": True, "minutes_left": minutes_left})
	else:
		return jsonify({"can_edit": False, "reason": "time_expired"})

async def run_bot():
	if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
		print("⚠️ Токен бота не установлен!")
		return
		
	bot = Bot(token=BOT_TOKEN)
	dp = Dispatcher()

	@dp.message(Command("start"))
	async def cmd_start(message: types.Message):
		kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="💪 Открыть трекер", web_app=WebAppInfo(url=WEB_APP_URL))]], resize_keyboard=True)
		await message.answer("Жми кнопку, чтобы отметить подход!", reply_markup=kb)

	await dp.start_polling(bot)

def start_flask():
	init_db()
	app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)

if __name__ == '__main__':
	import sys
	if len(sys.argv) > 1:
		WEB_APP_URL = sys.argv[1]
		print(f"🌍 Веб-апп доступен по адресу: {WEB_APP_URL}")
	
	t = threading.Thread(target=start_flask)
	t.daemon = True
	t.start()
	
	print("🚀 Запуск бота...")
	asyncio.run(run_bot())