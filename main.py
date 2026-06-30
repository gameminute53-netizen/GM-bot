import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiohttp import web

# Настройка логирования, чтобы видеть работу бота в панели Render
logging.basicConfig(level=logging.INFO)

# =========================================================
# 📢 БЛОК НАСТРОЕК РЕКЛАМЫ (Сейчас тут только твой канал!)
# =========================================================
# 1. Список каналов для проверки. Тестовые спонсоры временно скрыты решетками #
REQUIRED_CHANNELS = [
    '@GameMinute',        # Твой основной канал
    # '@sponsor_channel1',  # СКРЫТО: когда купят рекламу, просто убери # и впиши юзернейм
    # '@sponsor_channel2',  # СКРЫТО
]

# 2. Кнопки со ссылками для пользователей. Рекламные кнопки тоже пока скрыты.
SPONSOR_LINKS = {
    "👉 Подписаться на GameMinute": "https://t.me/GameMinute",
    # "👉 Подписаться на Спонсора 1": "https://t.me/sponsor_channel1",
    # "👉 Подписаться на Спонсора 2": "https://t.me/sponsor_channel2",
}
# =========================================================

# ТВОИ ТОЧНЫЕ ДАННЫЕ
API_TOKEN = '8753693282:AAEqZbBgVU6IIeP2DUEtnir5fCnGLIAy9gQ'
ARCHIVE_CHAT_ID = -1004321162872

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ ОБМАНА RENDER (чтобы работал UptimeRobot) ---
async def handle(request):
    return web.Response(text="Bot is running smoothly!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Фейковый веб-сервер запущен на порту {port}")

# Функция автоматической проверки подписки на все открытые каналы
async def check_all_subscriptions(user_id: int) -> bool:
    for chat_id in REQUIRED_CHANNELS:
        try:
            user_status = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if user_status.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logging.error(f"Ошибка при проверке подписки на {chat_id}: {e}")
            # Если бот не админ в канале спонсора, пропускаем, чтобы бот не зависал
            continue 
    return True

@dp.message_handler(commands=['clear_kb'])
async def clear_keyboard_command(message: types.Message):
    await message.answer(
        "Старые кнопки удалены! Теперь всё чисто. 👍", 
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    args = message.get_args()
    if not args or not args.startswith('msg'):
        await message.answer(
            "Привет! 👋 Этот бот выдает файлы игр для подписчиков канала GameMinute.\n\n"
            "Перейди в наш основной канал, выбери нужную игру и нажми на ссылку для скачивания!",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    msg_id = args.replace('msg', '')
    user_id = message.from_user.id
    
    # Запускаем проверку подписок
    is_subscribed = await check_all_subscriptions(user_id)

    if is_subscribed:
        try:
            # Чистое копирование файла из архива БЕЗ надписи "Переслано из"
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=ARCHIVE_CHAT_ID,
                message_id=int(msg_id),
                reply_markup=ReplyKeyboardRemove() # Сносит клавиатуру, если она была
            )
        except Exception as e:
            await message.answer("❌ Произошла ошибка при отправке файла. Возможно, этот файл был удален из архива.")
            logging.error(f"Ошибка отправки файла: {e}")
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        # Выводим только активные каналы из настроек (без знака #)
        for text, url in SPONSOR_LINKS.items():
            keyboard.add(InlineKeyboardButton(text=text, url=url))
            
        # Кнопка авто-проверки (перезапускает ту же ссылку на скачивание)
        bot_username = (await bot.get_me()).username
        check_url = f"https://t.me/{bot_username}?start=msg{msg_id}"
        keyboard.add(InlineKeyboardButton(text="🔄 Я подписался, проверить!", url=check_url))
        
        await message.answer(
            "⚠️ **Для получения файла нужно подписаться на наш канал!**\n\n"
            "Пожалуйста, подпишитесь и затем нажмите кнопку проверки:",
            reply_markup=keyboard
        )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    executor.start_polling(dp, skip_updates=True)
