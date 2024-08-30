import os
import telebot
import requests
import json
import sqlite3
from bs4 import BeautifulSoup
from telebot import types
from dotenv import load_dotenv
from time import sleep

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
MODEL_URI = os.getenv('MODEL_URI')

def init_db():
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_text TEXT,
            bot_text TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_request(user_id, user_text, bot_text):
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_requests (user_id, user_text, bot_text) VALUES (?, ?, ?)", (user_id, user_text, bot_text))
    conn.commit()
    conn.close()

def view_data():
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_requests")
    data = cursor.fetchall()
    conn.close()
    return data

def create_requests_db():
    data = view_data()
    
    if not data:
        return
    
    with open('database.txt', 'w') as f:
        for row in data:
            f.write(str(row) + '\n')

def add_to_blocklist(user_id):
    with open('blocks.txt', 'a') as f:
        f.write(str(user_id) + '\n')

def remove_from_blocklist(user_id):
    if os.path.exists('blocks.txt'):
        with open('blocks.txt', 'r') as f:
            lines = f.readlines()
        with open('blocks.txt', 'w') as f:
            for line in lines:
                if line.strip() != str(user_id):
                    f.write(line)

def is_blacklisted(user_id):
    if not os.path.exists('blocks.txt'):
        return False
    
    with open('blocks.txt', 'r') as f:
        return str(user_id) in [line.strip() for line in f]

@bot.message_handler(commands=['block'])
def block_user(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "Команда /block доступна только для администратора.")
        return

    try:
        user_id = int(message.text.split()[1])
        add_to_blocklist(user_id)
        bot.send_message(message.chat.id, f"Пользователь {user_id} заблокирован.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Использование: /block <user_id>")

@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "Команда /unblock доступна только для администратора.")
        return

    try:
        user_id = int(message.text.split()[1])
        remove_from_blocklist(user_id)
        bot.send_message(message.chat.id, f"Пользователь {user_id} разблокирован.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Использование: /unblock <user_id>")

@bot.message_handler(commands=['start'])
def start(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return

    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Задать вопрос')
    itembtn2 = types.KeyboardButton('Информация')
    itembtn3 = types.KeyboardButton('Помощь')
    itembtn4 = types.KeyboardButton('Анализировать ссылку')
    itembtn5 = types.KeyboardButton('Посетить сайт')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
    bot.send_message(message.chat.id, "Привет! Я ваш юридический помощник. Задавайте мне вопросы, и я постараюсь помочь вам.", reply_markup=markup)

@bot.message_handler(commands=['base'])
def base_handler(message):
    if message.text.strip() == f'/base {os.getenv("ADMIN_PASSWORD")}':
        data = view_data()
        
        if not data:
            bot.send_message(message.chat.id, "Нет данных для отображения.")
            return
        
        create_requests_db()
        
        file_path = 'database.txt'
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'rb') as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.send_message(message.chat.id, "Файл пустой или не был создан.")
    else:
        bot.send_message(message.chat.id, "Неверный пароль")

@bot.message_handler(func=lambda message: message.text == "Задать вопрос")
def ask_question(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return
    bot.send_message(message.chat.id, "Вы можете задать свой вопрос здесь:")

@bot.message_handler(func=lambda message: message.text == "Информация")
def show_info(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return
    bot.send_message(message.chat.id, "Мои создатели: @anzhelika_frolova7 и @dayze. Новостной канал - t.me/legalassistantranepa")

@bot.message_handler(func=lambda message: message.text == "Помощь")
def help_request(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return
    msg = bot.send_message(message.chat.id, "Пожалуйста, напишите ваше сообщение для разработчика:")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    user_id = message.chat.id
    user_message = message.text
    bot.send_message(ADMIN_CHAT_ID, f"Сообщение от пользователя {user_id}:\n{user_message}")
    bot.send_message(user_id, "Ваше сообщение отправлено разработчику. Ожидайте ответа.")

@bot.message_handler(commands=['reply'])
def reply_to_user(message):
    if message.chat.id != ADMIN_CHAT_ID:
        bot.send_message(message.chat.id, "Команда /reply доступна только для администратора.")
        return

    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.send_message(message.chat.id, "Использование: /reply <user_id> <сообщение>")
        return

    user_id = int(parts[1])
    reply_message = parts[2]

    try:
        bot.send_message(user_id, f"<b>Сообщение от администратора:</b>\n{reply_message}", parse_mode='HTML')
        bot.send_message(message.chat.id, "Сообщение отправлено пользователю.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Не удалось отправить сообщение пользователю. Ошибка: {e}")

@bot.message_handler(func=lambda message: message.text == "Анализировать ссылку")
def analyze_link_request(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return
    msg = bot.send_message(message.chat.id, "Пожалуйста, отправьте ссылку, которую вы хотите проанализировать:")
    bot.register_next_step_handler(msg, analyze_link)

def analyze_link(message):
    url = message.text
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()

        prompt = {
            "modelUri": MODEL_URI,
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000"
            },
            "messages": [
                {
                    "role": "system",
                    "text": "Ты анализируешь текст с веб-сайта и делаешь выводы."
                },
                {
                    "role": "user",
                    "text": text
                }
            ]
        }

        api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {YANDEX_API_KEY}"
        }

        response = requests.post(api_url, headers=headers, json=prompt)
        response.raise_for_status()

        result = response.json()
        analysis = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text')

        if analysis:
            bot.send_message(message.chat.id, f"Анализ текста с сайта:\n{analysis}")
        else:
            bot.send_message(message.chat.id, 'Пустой ответ от API Яндекс.ДжПТ')

    except requests.exceptions.ProxyError:
        bot.send_message(message.chat.id, 'Ошибка при анализе ссылки: Доступ к этому сайту ограничен через прокси-сервер.')
    except (requests.RequestException, json.JSONDecodeError, Exception) as e:
        bot.send_message(message.chat.id, f'Ошибка при анализе ссылки: {str(e)}')

@bot.message_handler(func=lambda message: message.text == "Посетить сайт")
def visit_site(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return
    site_url = "https://legalassistantranepa.ru/"
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="Перейти на сайт", url=site_url)
    markup.add(btn)
    bot.send_message(message.chat.id, "Нажмите кнопку ниже, чтобы посетить сайт:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def echo(message):
    if is_blacklisted(message.chat.id):
        bot.send_message(message.chat.id, "Вы заблокированы администрацией.")
        return

    user_message = message.text

    bot.send_chat_action(message.chat.id, 'typing')

    prompt = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты помогаешь подробном в разборе юридических документов, ссылаясь на нормативно-правовую базу Российской Федерации."
            },
            {
                "role": "user",
                "text": user_message
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {YANDEX_API_KEY}"
    }

    try:
        response = requests.post(url, headers=headers, json=prompt)
        response.raise_for_status()

        result = response.json()
        bot_response = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text')

        if bot_response:
            bot.send_message(message.chat.id, bot_response)
            save_request(message.chat.id, user_message, bot_response)
        else:
            bot.send_message(message.chat.id, 'Пустой ответ от API Яндекс.ДжПТ')
    except (requests.RequestException, json.JSONDecodeError) as e:
        bot.send_message(message.chat.id, f'Ошибка при запросе к API: {str(e)}')

if __name__ == '__main__':
    init_db()
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Ошибка: {e}")
            sleep(15)
