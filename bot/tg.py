import os
from dotenv import load_dotenv
import telebot
import requests
import json

# Загрузка переменных окружения из файла .env
load_dotenv()

# Создание экземпляра бота с использованием токена из переменных окружения
bot = telebot.TeleBot(os.getenv('TELEGRAM_BOT_TOKEN'))

# Функция для обработки команды /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот.")

# Функция для обработки сообщений от пользователя
@bot.message_handler(func=lambda message: True)
def echo(message):
    user_message = message.text

    prompt = {
        "modelUri": "gpt://b1gevpns458a0bh39eo3/yandexgpt-lite",
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
        response.raise_for_status()  # Проверяем статус код ответа

        result = response.json()
        bot_response = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text')

        if bot_response:
            bot.send_message(message.chat.id, bot_response)
        else:
            bot.send_message(message.chat.id, 'Пустой ответ от API Яндекс.ДжПТ')
    except (requests.RequestException, json.JSONDecodeError) as e:
        bot.send_message(message.chat.id, f'Ошибка при запросе к API: {str(e)}')

# Запуск бота
if __name__ == '__main__':
    bot.polling()
