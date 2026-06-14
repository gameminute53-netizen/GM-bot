import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Настройка логирования, чтобы видеть процессы в консоли Render
logging.basicConfig(level=logging.INFO)

# ТВОИ ТОЧНЫЕ ДАННЫЕ
API_TOKEN = '8753693282:AAFYMdqTa9kybi9Tcn6JkLzPmtMpE1JqqVM'
MAIN_CHANNEL_URL = 'https://t.me/GameMinute'  # Ссылка для кнопки «Подписаться»
MAIN_CHANNEL_ID = '@GameMinute'               # Юзернейм канала для проверки подписки ботом
ARCHIVE_CHAT_ID = -1004321162872              # ID твоего закрытого архива, где лежат файлы

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    # Вытаскиваем хвостик из ссылки (например: из ссылки ?start=msg6 вытащит "msg6")
    args = message.get_args()
    
    # Если пользователь зашел в бота просто так (без синей ссылки на игру)
    if not args or not args.startswith('msg'):
        await message.answer(
            "Привет! 👋 Этот бот выдает файлы игр для подписчиков канала GameMinute.\n\n"
            "Перейди в наш основной канал, выбери нужную игру и нажми на ссылку для скачивания!"
        )
        return

    # Убираем буквы 'msg', оставляя только чистый номер сообщения (например, "6")
    msg_id = args.replace('msg', '')
    user_id = message.from_user.id
    
    # 1. ПРОВЕРКА ПОДПИСКИ ПОЛЬЗОВАТЕЛЯ
    is_subscribed = False
    try:
        # Бот запрашивает у Telegram статус человека в канале @GameMinute
        user_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=user_id)
        
        # Если статус совпадает с участником, админом или создателем — значит он подписан
        if user_status.status in ['member', 'administrator', 'creator']:
            is_subscribed = True
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        # Защитная заглушка: если бота забыли добавить в админы GameMinute,
        # он временно пропустит человека, чтобы у людей не ло
