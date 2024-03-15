import os
import telebot
import requests
import json
import sqlite3

from telebot import types
from dotenv import load_dotenv

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

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

def create_text_db():
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_requests")
    data = cursor.fetchall()
    conn.close()
    
    with open('database.txt', 'w') as f:
        for row in data:
            f.write(str(row) + '\n')

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Задать вопрос')
    itembtn2 = types.KeyboardButton('Информация')
    markup.add(itembtn1, itembtn2)
    bot.send_message(message.chat.id, "Привет! Я ваш юридический помощник. Задавайте мне вопросы, и я постараюсь помочь вам.", reply_markup=markup)

# @bot.message_handler(commands=['data'])
# def data_handler(message):
#    if message.text.strip() == f'/data {os.getenv("ADMIN_PASSWORD")}':
#        data = view_data()
#        bot.send_message(message.chat.id, str(data))
#    else:
#        bot.send_message(message.chat.id, "Неверный пароль")

@bot.message_handler(commands=['base'])
def base_handler(message):
    if message.text.strip() == f'/base {os.getenv("ADMIN_PASSWORD")}':
        create_text_db()
        with open('database.txt', 'rb') as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, "Неверный пароль")

@bot.message_handler(func=lambda message: message.text == "Задать вопрос")
def ask_question(message):
    bot.send_message(message.chat.id, "Вы можете задать свой вопрос здесь:")

@bot.message_handler(func=lambda message: message.text == "Информация")
def show_info(message):
    bot.send_message(message.chat.id, "Мои создатели: @anzhelika_frolova7 и @dayze. Новостной канал - t.me/legalassistantranepa")

@bot.message_handler(func=lambda message: True)
def echo(message):
    user_message = message.text

    bot.send_chat_action(message.chat.id, 'typing')

    prompt = {
        "modelUri": os.getenv('MODEL_URI'),
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты помогаешь в разборе юридических документов."
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
        "Authorization": f"Api-Key {os.getenv('YANDEX_API_KEY')}"
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
    bot.polling()
