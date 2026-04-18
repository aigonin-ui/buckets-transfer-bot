from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Твой Telegram user_id (админ)
ADMIN_ID = 7611155958

# Токен твоего Telegram-бота
BOT_TOKEN = "8793281648:AAFmckNFwDz0tq0gZCREEOyxZE80imW6IeQ"

# Функция отправки уведомления админу
def send_admin_notification(sender_name, receiver_name, amount):
    text = (
        "🔔 Новый перевод!\n\n"
        f"Отправитель: {sender_name}\n"
        f"Получатель: {receiver_name}\n"
        f"Количество: {amount} ведер"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_ID,
        "text": text
    }

    try:
        requests.post(url, json=payload)
    except:
        pass


# Жители — у всех balance = 100
USERS = {
    "lubitelkotov_a": {
        "name": "Александр Игонин",
        "pin": "5831",
        "balance": 100,
        "username": "LubitelKotov_A"
    },
    "user_5526799176": {
        "name": "Максим Перминов",
        "pin": "9472",
        "balance": 100,
        "user_id": 5526799176
    },
    "bagi2013": {
        "name": "Богдан Дмитриенко",
        "pin": "1064",
        "balance": 100,
        "username": "Bagi2013"
    },
    "ivannoxw": {
        "name": "Иван Бордюжан",
        "pin": "7289",
        "balance": 100,
        "username": "ivannoxw"
    },
    "ankolbulba": {
        "name": "Антон Кульгачев",
        "pin": "3917",
        "balance": 100,
        "username": "Ankolbulba"
    },
    "go_to_spott": {
        "name": "Кристиан Ганин",
        "pin": "8640",
        "balance": 100,
        "username": "Go_to_spott"
    },
    "andreimoroz1": {
        "name": "Андрей Мороз",
        "pin": "4528",
        "balance": 100,
        "username": "Andreimoroz1"
    }
}

# Сессии пользователей
SESSIONS = {}

def get_session(user_id):
    if user_id not in SESSIONS:
        SESSIONS[user_id] = {
            "stage": "ask_pin",
            "sender": None,
            "receiver": None,
            "amount": None
        }
    return SESSIONS[user_id]


def find_user(username, user_id):
    for key, info in USERS.items():
        if info.get("username") == username:
            return key
        if info.get("user_id") == user_id:
            return key
    return None


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}

    user_id = str(data.get("user_id"))
    username = data.get("username")
    text = (data.get("text") or "").strip()

    if not user_id:
        return jsonify({"reply": "Ошибка: нет user_id"})

    session = get_session(user_id)

    # Определяем отправителя автоматически
    if session["sender"] is None:
        sender_key = find_user(username, int(user_id))
        if sender_key:
            session["sender"] = sender_key
            return jsonify({
                "reply": f"Привет, {USERS[sender_key]['name']}. Введи свой ПИН-код."
            })
        else:
            return jsonify({"reply": "Ты не зарегистрирован в системе."})

    sender_key = session["sender"]
    stage = session["stage"]

    # 1. Ввод ПИН
    if stage == "ask_pin":
        if text != USERS[sender_key]["pin"]:
            return jsonify({"reply": "❌ Неверный ПИН. Попробуй снова."})

        session["stage"] = "ask_receiver"
        names = "\n".join([u["name"] for u in USERS.values()])
        return jsonify({
            "reply": f"ПИН верный.\nКому отправить Вёдра?\n\n{names}"
        })

    # 2. Выбор получателя
    if stage == "ask_receiver":
        receiver_key = None
        for key, info in USERS.items():
            if info["name"] == text:
                receiver_key = key
                break

        if not receiver_key:
            return jsonify({"reply": "Такого получателя нет. Введи имя точно как в списке."})

        if receiver_key == sender_key:
            return jsonify({"reply": "Нельзя отправить самому себе."})

        session["receiver"] = receiver_key
        session["stage"] = "ask_amount"

        return jsonify({
            "reply": f"Сколько Вёдер отправить пользователю {USERS[receiver_key]['name']}?"
        })

    # 3. Ввод суммы
    if stage == "ask_amount":
        try:
            amount = int(text)
        except ValueError:
            return jsonify({"reply": "Введи число."})

        if amount <= 0:
            return jsonify({"reply": "Сумма должна быть больше нуля."})

        sender_balance = USERS[sender_key]["balance"]
        receiver_key = session["receiver"]

        if sender_balance < amount:
            return jsonify({
                "reply": f"❌ Недостаточно Вёдер. Твой баланс: {sender_balance}."
            })

        USERS[sender_key]["balance"] -= amount
        USERS[receiver_key]["balance"] += amount

        new_balance = USERS[sender_key]["balance"]

        # 🔔 Отправляем уведомление админу
        send_admin_notification(
            USERS[sender_key]["name"],
            USERS[receiver_key]["name"],
            amount
        )

        # Сбрасываем сессию
        SESSIONS.pop(user_id, None)

        return jsonify({
            "reply": (
                f"✔ Перевод выполнен!\n"
                f"Отправитель: {USERS[sender_key]['name']}\n"
                f"Получатель: {USERS[receiver_key]['name']}\n"
                f"Сумма: {amount}\n"
                f"Новый баланс: {new_balance}"
            )
        })

    return jsonify({"reply": "Ошибка состояния. Начни заново."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
