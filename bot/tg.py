import os
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
import json

load_dotenv()

bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('Задать вопрос')
    itembtn2 = types.KeyboardButton('Информация')
    markup.add(itembtn1, itembtn2)
    bot.send_message(message.chat.id, "Привет! Я ваш юридический помощник. Задавайте мне вопросы, и я постараюсь помочь вам.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Задать вопрос")
def ask_question(message):
    bot.send_message(message.chat.id, "Вы можете задать свой вопрос здесь:")

@bot.message_handler(func=lambda message: message.text == "Информация")
def show_info(message):
    bot.send_message(message.chat.id, "Мои создатели: @anzhelika_frolova7 и @dayze. Новостной канал - t.me/legalassistantranepa")

@bot.message_handler(func=lambda message: True)
def echo(message):
    user_message = message.text

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
        else:
            bot.send_message(message.chat.id, 'Пустой ответ от API Яндекс.ДжПТ')
    except (requests.RequestException, json.JSONDecodeError) as e:
        bot.send_message(message.chat.id, f'Ошибка при запросе к API: {str(e)}')

if __name__ == '__main__':
    bot.polling()
