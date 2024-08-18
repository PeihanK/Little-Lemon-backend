from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import requests
from dotenv import load_dotenv
import os
from datetime import datetime
from flask_cors import CORS

# Загружаем переменные окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Настройка базы данных
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "booking.db")}'


# Инициализация расширений
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Настройка CORS
CORS(app, resources={r"/api/*": {"origins": "https://littlelemonproject.netlify.app"}})


# Определение модели
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    occasion = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Определение маршрута
@app.route('/api/reserve', methods=['POST'])
def reserve_table():
    data = request.get_json()

    # Валидация входных данных
    if not all(key in data for key in ['date', 'time', 'guests', 'occasion', 'phone', 'email']):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400

    try:
        # Сохранение данных в базе
        new_booking = Booking(
            date=data.get('date'),
            time=data.get('time'),
            guests=data.get('guests'),
            occasion=data.get('occasion'),
            phone=data.get('phone'),
            email=data.get('email')
        )
        db.session.add(new_booking)
        db.session.commit()

        # Отправка уведомления в Telegram
        send_telegram_notification(data)

        return jsonify({'status': 'success', 'message': 'Reservation received'}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500


# Функция отправки уведомлений в Telegram
def send_telegram_notification(data):
    # Получаем токен и ID чата из переменных окружения
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Проверка на наличие токена и ID чата
    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID is not set.")
        return

    # Сообщение для отправки
    message = (
        f"New reservation!\n"
        f"Date: {data.get('date')}\n"
        f"Time: {data.get('time')}\n"
        f"Guests: {data.get('guests')}\n"
        f"Occasion: {data.get('occasion')}\n"
        f"Phone: {data.get('phone')}\n"
        f"Email: {data.get('email')}"
    )

    # Отправка запроса в Telegram API
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Проверка на успешность запроса
    except requests.exceptions.RequestException as e:
        print(f"Telegram notification error: {e}")


# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
