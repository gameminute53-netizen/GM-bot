import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiohttp import web

logging.basicConfig(level=logging.INFO)

# =========================================================
# 📢 НАСТРОЙКИ И СПИСКИ
# =========================================================
# ID администраторов, которым разрешено использовать /adrek и /delrek
ADMIN_IDS = [5117783610] # 👈 ВПИШИ СВОЙ TELEGRAM ID (числом)

# 1. Список юзернеймов или ID каналов для проверки ботом
REQUIRED_CHANNELS = [
    '@GameMinute',
    # '@sponsor_channel',
]

# 2. Кнопки со ссылками для пользователей {"Текст": "Ссылка"}
SPONSOR_LINKS = {
    "👉 Подписаться на GameMinute": "https://t.me/GameMinute",
    "👉 Подписаться на Спонсора": "https://t.me/+0R6zuL2Iadg4M2My",
}
# =========================================================

API_TOKEN = '8753693282:AAEqZbBgVU6IIeP2DUEtnir5fCnGLIAy9gQ'
ARCHIVE_CHAT_ID = -1004321162872

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ФЕЙКОВЫЙ СЕРВЕР ДЛЯ RENDER ---
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

# --- ФУНКЦИЯ ПРОВЕРКИ ПОДПИСОК ---
async def check_all_subscriptions(user_id: int) -> bool:
    if not REQUIRED_CHANNELS:
        return True

    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logging.error(f"Ошибка проверки канала {channel}: {e}")
            # Если произошла ошибка (например, бот не админ или юзернейм кривой), 
            # считаем, что подписки нет, чтобы не отдавать файл бесплатно
            return False
    return True

# --- ДОБАВЛЕНИЕ РЕКЛАМЫ ЧЕРЕЗ /adrek ---
@dp.message_handler(commands=['adrek'])
async def add_ad_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS and ADMIN_IDS != [123456789]:
        return await message.answer("❌ У вас нет прав для этой команды.")

    args = message.get_args().strip()
    if not args:
        return await message.answer("⚠️ Использование: `/adrek @username` или `/adrek https://t.me/username`", parse_mode="Markdown")

    # Получаем чистое имя канала без ссылки
    channel_username = args.split('/')[-1]
    if not channel_username.startswith('@'):
        channel_username = f"@{channel_username}"

    try:
        # Бот запрашивает информацию о канале, чтобы узнать его точное название
        chat = await bot.get_chat(channel_username)
        title = chat.title or channel_username
        link = f"https://t.me/{chat.username}" if chat.username else args

        if channel_username not in REQUIRED_CHANNELS:
            REQUIRED_CHANNELS.append(channel_username)
            
        SPONSOR_LINKS[f"👉 Подписаться на {title}"] = link

        await message.answer(
            f"✅ **Рекламный канал успешно добавлен!**\n\n"
            f"📌 Название: {title}\n"
            f"🔗 Юзернейм: {channel_username}\n"
            f"🔗 Ссылка: {link}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка! Не удалось найти канал или получить информацию.\n\nПроверь, добавлен ли бот в этот канал как администратор.\n`Ошибка: {e}`", parse_mode="Markdown")

# --- УДАЛЕНИЕ РЕКЛАМЫ ЧЕРЕЗ /delrek ---
@dp.message_handler(commands=['delrek'])
async def delete_ad_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS and ADMIN_IDS != [123456789]:
        return await message.answer("❌ У вас нет прав для этой команды.")

    args = message.get_args().strip()
    if not args:
        return await message.answer("⚠️ Использование: `/delrek @username`", parse_mode="Markdown")

    channel_username = args.split('/')[-1]
    if not channel_username.startswith('@'):
        channel_username = f"@{channel_username}"

    if channel_username in REQUIRED_CHANNELS:
        REQUIRED_CHANNELS.remove(channel_username)
        # Удаляем из кнопок
        keys_to_delete = [k for k, v in SPONSOR_LINKS.items() if channel_username.lower() in v.lower()]
        for k in keys_to_delete:
            del SPONSOR_LINKS[k]
            
        await message.answer(f"✅ Канал {channel_username} удален из проверки и кнопок!")
    else:
        await message.answer(f"⚠️ Канал {channel_username} не найден в списке подписок.")

@dp.message_handler(commands=['clear_kb'])
async def clear_keyboard_command(message: types.Message):
    await message.answer("Старые кнопки удалены! 👍", reply_markup=ReplyKeyboardRemove())

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
    
    is_subscribed = await check_all_subscriptions(user_id)

    if is_subscribed:
        try:
            await bot.copy_message(
                chat_id=user_id,
                from_chat_id=ARCHIVE_CHAT_ID,
                message_id=int(msg_id),
                reply_markup=ReplyKeyboardRemove()
            )
        except Exception as e:
            await message.answer("❌ Произошла ошибка при отправке файла. Возможно, он был удален из архива.")
            logging.error(f"Ошибка отправки файла: {e}")
    else:
        keyboard = InlineKeyboardMarkup(row_width=1)
        
        for text, url in SPONSOR_LINKS.items():
            keyboard.add(InlineKeyboardButton(text=text, url=url))
            
        bot_username = (await bot.get_me()).username
        check_url = f"https://t.me/{bot_username}?start=msg{msg_id}"
        keyboard.add(InlineKeyboardButton(text="🔄 Я подписался, проверить!", url=check_url))
        
        await message.answer(
            "⚠️ **Для получения файла нужно подписаться на наши каналы:**\n\n"
            "Пожалуйста, подпишитесь и затем нажмите кнопку проверки:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_web_server())
    executor.start_polling(dp, skip_updates=True)
