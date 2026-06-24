import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ТВОИ ТОЧНЫЕ ДАННЫЕ
API_TOKEN = '8753693282:AAFf6fqHtdFdmkNvtjsvlN7LIfeonVbCjA4'
MAIN_CHANNEL_URL = 'https://t.me/GameMinute'
MAIN_CHANNEL_ID = '@GameMinute'
ARCHIVE_CHAT_ID = -1004321162872

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ ОБМАНА RENDER ---
async def handle(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Читаем порт, который требует Render (по умолчанию 10000)
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Фейковый веб-сервер запущен на порту {port}")

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    args = message.get_args()
    if not args or not args.startswith('msg'):
        await message.answer(
            "Привет! 👋 Этот бот выдает файлы игр для подписчиков канала GameMinute.\n\n"
            "Перейди в наш основной канал, выбери нужную игру и нажми на ссылку для скачивания!"
        )
        return

    msg_id = args.replace('msg', '')
    user_id = message.from_user.id
    
    is_subscribed = False
    try:
        user_status = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=user_id)
        if user_status.status in ['member', 'administrator', 'creator']:
            is_subscribed = True
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки: {e}")
        is_subscribed = True 

    if is_subscribed:
        try:
            # Чистое копирование БЕЗ надписи "Переслано из"
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=ARCHIVE_CHAT_ID,
                message_id=int(msg_id)
            )
        except Exception as e:
            await message.answer("❌ Произошла ошибка при отправке файла. Возможно, этот файл был удален из архива.")
            logging.error(f"Ошибка отправки файла: {e}")
    else:
        keyboard = InlineKeyboardMarkup()
        btn_sub = InlineKeyboardButton(text="👉 Подписаться на GameMinute", url=MAIN_CHANNEL_URL)
        keyboard.add(btn_sub)
        
        await message.answer(
            "Вы не подписаны.\n"
            "Чтобы получить файл, подпишитесь на наш канал:",
            reply_markup=keyboard
        )

if __name__ == '__main__':
    # Запускаем фейковый сервер перед запуском бота
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    
    # Запуск самого бота
    executor.start_polling(dp, skip_updates=True)
