from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
from dotenv import load_dotenv
import os

# Загружаем переменные окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Модель для хранения бронирований
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    guests = db.Column(db.Integer, nullable=False)
    occasion = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Создаем таблицу в базе данных
with app.app_context():
    db.create_all()


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
        f"Новая заявка на бронирование!\n"
        f"Дата: {data.get('date')}\n"
        f"Время: {data.get('time')}\n"
        f"Гостей: {data.get('guests')}\n"
        f"Повод: {data.get('occasion')}\n"
        f"Телефон: {data.get('phone')}\n"
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


if __name__ == '__main__':
    app.run(debug=True)
