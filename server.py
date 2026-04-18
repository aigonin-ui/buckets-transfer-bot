from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

ADMIN_ID = 7611155958
BOT_TOKEN = "8793281648:AAFmckNFwDz0tq0gZCREEOyxZE80imW6IeQ"

def send_admin_notification(sender_name, receiver_name, amount):
    text = (
        "🔔 Новый перевод!\n\n"
        f"Отправитель: {sender_name}\n"
        f"Получатель: {receiver_name}\n"
        f"Количество: {amount} ведер"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": ADMIN_ID, "text": text})


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

SESSIONS = {}

def get_session(uid):
    if uid not in SESSIONS:
        SESSIONS[uid] = {
            "stage": "ask_pin",
            "sender": None,
            "receiver": None,
            "amount": None,
            "admin_target": None
        }
    return SESSIONS[uid]


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

    session = get_session(user_id)

    # -------------------------
    # АДМИН МЕНЮ
    # -------------------------
    if text == "/admin" and int(user_id) == ADMIN_ID:
        return jsonify({
            "reply": "Админ меню:",
            "buttons": ["Пополнить баланс жителей"]
        })

    if text == "Пополнить баланс жителей" and int(user_id) == ADMIN_ID:
        session["stage"] = "admin_topup_select_user"
        return jsonify({
            "reply": "Выбери жителя:",
            "buttons": [u["name"] for u in USERS.values()]
        })

    # -------------------------
    # АДМИН: выбор жителя
    # -------------------------
    if session["stage"] == "admin_topup_select_user" and int(user_id) == ADMIN_ID:
        target = None
        for key, info in USERS.items():
            if info["name"] == text:
                target = key
                break

        if not target:
            return jsonify({"reply": "Такого жителя нет."})

        session["admin_target"] = target
        session["stage"] = "admin_topup_select_amount"

        return jsonify({
            "reply": f"На сколько пополнить баланс {USERS[target]['name']}?",
            "buttons": ["100", "50", "10"]
        })

    # -------------------------
    # АДМИН: выбор суммы
    # -------------------------
    if session["stage"] == "admin_topup_select_amount" and int(user_id) == ADMIN_ID:
        if text not in ["100", "50", "10"]:
            return jsonify({"reply": "Выбери сумму кнопкой."})

        amount = int(text)
        target = session["admin_target"]

        USERS[target]["balance"] += amount

        SESSIONS.pop(user_id, None)

        return jsonify({"reply": "Пополнение прошло успешно!"})

    # -------------------------
    # Обычная логика перевода
    # -------------------------

    if session["sender"] is None:
        sender_key = find_user(username, int(user_id))
        if sender_key:
            session["sender"] = sender_key
            return jsonify({
                "reply": f"Привет, {USERS[sender_key]['name']}. Введи свой ПИН-код."
            })
        else:
            return jsonify({"reply": "Ты не зарегистрирован."})

    sender_key = session["sender"]

    if session["stage"] == "ask_pin":
        if text != USERS[sender_key]["pin"]:
            return jsonify({"reply": "❌ Неверный ПИН."})

        session["stage"] = "ask_receiver"
        return jsonify({
            "reply": "Кому отправить?",
            "buttons": [u["name"] for u in USERS.values()]
        })

    if session["stage"] == "ask_receiver":
        receiver_key = None
        for key, info in USERS.items():
            if info["name"] == text:
                receiver_key = key
                break

        if not receiver_key:
            return jsonify({"reply": "Такого получателя нет."})

        if receiver_key == sender_key:
            return jsonify({"reply": "Нельзя отправить самому себе."})

        session["receiver"] = receiver_key
        session["stage"] = "ask_amount"

        return jsonify({
            "reply": f"Сколько отправить {USERS[receiver_key]['name']}?",
            "buttons": ["1", "5", "10", "20", "50"]
        })

    if session["stage"] == "ask_amount":
        try:
            amount = int(text)
        except:
            return jsonify({"reply": "Выбери сумму кнопкой."})

        receiver_key = session["receiver"]

        if USERS[sender_key]["balance"] < amount:
            return jsonify({"reply": "Недостаточно Вёдер."})

        USERS[sender_key]["balance"] -= amount
        USERS[receiver_key]["balance"] += amount

        send_admin_notification(
            USERS[sender_key]["name"],
            USERS[receiver_key]["name"],
            amount
        )

        SESSIONS.pop(user_id, None)

        return jsonify({"reply": "✔ Перевод выполнен!"})

    return jsonify({"reply": "Ошибка состояния."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
