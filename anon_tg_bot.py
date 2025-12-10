# Файл: bot.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

# Токен бота (можно заменить на переменную окружения)
TOKEN = os.getenv('BOT_TOKEN', '8141664661:AAFkFsQ6OSDJgOhuqPQs94JxRJcJD2VCzMI')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Админы
ADMINS = {6031482327}  # первый админ

# Хранилища
user_links = {}     # user_id -> ref_code
reverse_links = {}  # ref_code -> user_id
messages = []       # список сообщений: {'author': id, 'recipient': id, 'text': str, 'message_id': id}

@dp.message(commands=['start'])
async def start_cmd(message: types.Message):
    args = message.get_args()

    if args.startswith('uid'):
        target_user_id = int(args[3:])
        await message.answer('Напиши анонимное сообщение 👇')
        dp.target = target_user_id
        dp.author = message.from_user.id
        return

    uid = message.from_user.id
    ref = f'uid{uid}'
    user_links[uid] = ref
    reverse_links[ref] = uid

    link = f'https://t.me/{(await bot.get_me()).username}?start={ref}'
    await message.answer(f'Твоя личная ссылка для анонимных сообщений:\n\n{link}')

@dp.message()
async def forward_msg(message: types.Message):
    if hasattr(dp, 'target'):
        target = dp.target
        author = dp.author

        keyboard = InlineKeyboardMarkup()
        if target in ADMINS:
            keyboard.add(InlineKeyboardButton(text='Показать отправителя', callback_data=f'who:{author}'))

        msg = await bot.send_message(target, f'📩 Новое анонимное сообщение:\n\n{message.text}', reply_markup=keyboard)

        messages.append({'author': author, 'recipient': target, 'text': message.text, 'message_id': msg.message_id})

        del dp.target
        del dp.author

        await message.answer('Отправлено!')

@dp.message(commands=['panel'])
async def show_panel(message: types.Message):
    user_id = message.from_user.id
    if user_id not in ADMINS:
        return await message.answer('У тебя нет прав!')

    keyboard = InlineKeyboardMarkup()
    for i, msg in enumerate(messages):
        if msg['recipient'] == user_id:
            text_preview = msg['text'][:20] + '...' if len(msg['text']) > 20 else msg['text']
            keyboard.add(InlineKeyboardButton(text=f'{i+1}: {text_preview}', callback_data=f'showmsg:{i}'))

    if not keyboard.inline_keyboard:
        return await message.answer('Сообщений пока нет.')

    await message.answer('Панель сообщений:', reply_markup=keyboard)

@dp.callback_query(lambda q: q.data.startswith('showmsg:'))
async def show_message_details(query: types.CallbackQuery):
    idx = int(query.data.split(':')[1])
    msg = messages[idx]

    if query.from_user.id not in ADMINS:
        return await query.answer('У тебя нет прав!', show_alert=True)

    author_id = msg['author']
    text = msg['text']

    try:
        user = await bot.get_chat(author_id)
        username = f'@{user.username}' if user.username else 'Нет username'
    except:
        username = 'Не удалось получить username'

    await query.message.answer(f'Сообщение:\n{text}\n\nАвтор:\nID: {author_id}\nUsername: {username}')

@dp.callback_query(lambda q: q.data.startswith('who:'))
async def show_author(query: types.CallbackQuery):
    author_id = int(query.data.split(':')[1])

    if query.from_user.id not in ADMINS:
        return await query.answer('У тебя нет прав!', show_alert=True)

    try:
        user = await bot.get_chat(author_id)
        username = f'@{user.username}' if user.username else 'Нет username'
    except:
        username = 'Не удалось получить username'

    await query.message.answer(f'Автор сообщения:\nID: {author_id}\nUsername: {username}')

async def main():
    await dp.start_polling(bot)

asyncio.run(main())