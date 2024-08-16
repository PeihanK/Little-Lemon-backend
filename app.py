from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests

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

    return jsonify({'status': 'success', 'message': 'Reservation received'})


def send_telegram_notification(data):
    # Ваш Telegram токен и ID чата
    bot_token = "7529848581:AAHS2Ka13rO32rLB12FJk8ClkZ-0zmC3GHw"
    chat_id = "873817956"

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
    requests.post(url, json=payload)


if __name__ == '__main__':
    app.run(debug=True)
