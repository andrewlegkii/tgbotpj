# Телеграм-бот "Юридический помощник"

Этот телеграм-бот представляет собой юридического помощника, который помогает пользователям в разборе юридических вопросов и документов. Бот использует модель генерации текста от Yandex, чтобы предоставлять ответы на запросы пользователей.

## Функциональность

- Бот позволяет задавать юридические вопросы и получать на них ответы.
- Пользователи могут запросить информацию о создателях бота и получить ссылку на новостной канал.
- Администратор бота может просматривать данные пользователей, отправляя запрос `/base` с паролем администратора.

## Библиотеки и технологии

- Python - основной язык программирования.
- Telebot - библиотека для работы с Telegram Bot API.
- requests - библиотека для отправки HTTP-запросов.
- sqlite3 - встроенная библиотека для работы с базами данных SQLite.
- Yandex.DJPT (DeepJointPilot) - модель генерации текста от Yandex, используемая для создания ответов бота.

## Установка и настройка

1. Установите необходимые библиотеки Python, выполнив команду `pip install -r requirements.txt`.
2. Создайте файл `.env` и добавьте в него следующие переменные среды:
   - `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота.
   - `MODEL_URI` - URI модели генерации текста от Yandex.
   - `YANDEX_API_KEY` - API-ключ для доступа к Yandex.DJPT.
   - `ADMIN_PASSWORD` - пароль администратора для просмотра данных пользователей.
3. Запустите бота, выполнив команду `python tg.py`.

## База данных

База данных создана на основе SQL. 
Она содержит:
- id запроса.
- id пользователя.
- текст пользователя.
- ответ бота.
