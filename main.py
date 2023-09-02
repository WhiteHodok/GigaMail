from dotenv import load_dotenv
import json
import re
import os
from aiogram import Bot, types
from io import BytesIO
import logging
import asyncio
from aiogram.utils import executor , markdown
from aiogram.utils.markdown import hlink, escape_md , code
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from buttons import *
from supabase import Client, create_client
from aiogram.types.web_app_info import WebAppInfo
from datetime import date

# Подключение переменных среды
load_dotenv()

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота, диспетчера и хранилищаа состояний
bot = Bot(token=os.getenv("TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())

# Инициализация подключения к базе данных Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

#-----------------------------------------------------------------------------------------------------------------------
# Все состояния в которых может пребывать пользователь/админ бота
#-----------------------------------------------------------------------------------------------------------------------

class UserStates(StatesGroup):
    add_mail = State()
    send = State()
    cancel = State()
    menu = State()

class AdminStates(StatesGroup):
    check = State()
    check_user = State()
    menu = State()
    roles = State()
    give_roles = State()

#-----------------------------------------------------------------------------------------------------------------------
# Логика бота
#-----------------------------------------------------------------------------------------------------------------------

@dp.message_handler(commands=['start'], state ='*')
async def start(message: types.Message, state = FSMContext):
    await message.reply('Добро пожаловать в бота !', reply_markup=uskmp)
    await UserStates.menu.set()

@dp.message_handler(text='Добавить почты', state = UserStates.menu)
async def add_mail(message: types.Message, state = FSMContext):
    await message.reply('Введите почту(-ы) для добавления или отправьте .txt файл боту. \n Пример почт в файле:  \n example@mail.ru \n essa@aboba.com', reply_markup=cancel_markup)
    await UserStates.add_mail.set()

@dp.message_handler(state = UserStates.add_mail, content_types= ['text'])
async def add_one_mail(message: types.Message, state= FSMContext):
    await UserStates.send.set() # Обновляем стейт юзера
    chat_id = message.chat.id # Получаем чатид пользователя чтобы идентифицировать его
    mail = message.text # Получаем почту из текста сообщения
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b' # Паттерн почты для проверки валидности

    # Валидация на существование почты
    used_mail_data = supabase.table('Mailer').select('id').eq('mail', mail).eq('id',chat_id).execute()
    if used_mail_data.data:
        # уже присылал
        await message.reply("Вы уже присылали эту почту!", reply_markup=uskmp) # Обязательно бекаем юзера в нужный ему стейт по клаве
        await state.finish() # Сбрасываем стейт чтобы очистился aiogram`овский message.text & FSM
        await UserStates.menu.set() # Ставим нужный для работы клавы стейт
        return # Бекаем куда надо чтобы он не сидел в функции вечно

    if not re.fullmatch(email_pattern, mail):
        await message.reply("Вы ввели невалидный email", reply_markup= uskmp)
        await state.finish()
        await UserStates.menu.set()
        return

    # Делаем дату JSON-serialazable
    date_str = date.today().isoformat()
    # Сам POST запрос на занесение данных в БД
    insert_query = supabase.table('Mailer').insert({'id': chat_id, # Офаем все constraint и PK
                                                    'mail': mail,
                                                    'date': date_str}).execute()


    await message.reply("Почта успешно добавлена!", reply_markup=uskmp)
    await state.finish()
    await UserStates.add_mail.set()


@dp.message_handler(content_types=['document'], state=UserStates.add_mail)
async def add_mails_from_file(message: types.Message, state: FSMContext):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Паттерн почты для проверки валидности
    chat_id = message.chat.id
    document = message.document

    file_bytes = await bot.download_file_by_id(document.file_id)

    # Сохраняем в файл
    path = f"{document.file_unique_id}.txt"
    with open(path, 'wb') as f:
        f.write(file_bytes.getvalue())

    # Далее открываем файл для чтения
    with open(path, 'r') as f:
        emails = f.read().splitlines()


    valid_mails = []
    invalid_mails = []
    existing_mails = []

    for mail in emails:
        if not re.fullmatch(email_pattern, mail):
            invalid_mails.append(mail)
            continue

        result = supabase.table('Mailer').select('id').eq('mail', mail).eq('id', chat_id).execute()
        if result.data:
            existing_mails.append(mail)
            continue

        valid_mails.append(mail)

    # Добавляем валидные почты
    if valid_mails:
        date_str = date.today().isoformat()
        supabase.table('Mailer').insert([{'id': chat_id, 'mail': m, 'date': date_str} for m in valid_mails]).execute()

    # Формируем сообщение пользователю
    msg = f"Обработано {len(emails)} почт:\n"
    if valid_mails:
        msg += f"Добавлено {len(valid_mails)} почт\n"
    if invalid_mails:
        msg += f"Невалидные: {len(invalid_mails)} почт\n"
    if existing_mails:
        msg += f"Уже существующие: {len(existing_mails)} почт"

    await message.reply(msg)

    # Завершаем state
    await state.finish()
    await UserStates.menu.set()
    # По завершении можно удалить файл
    os.remove(path)




#-----------------------------------------------------------------------------------------------------------------------
# Колбек на отмену
#-----------------------------------------------------------------------------------------------------------------------

@dp.callback_query_handler(text='cancel', state = UserStates.add_mail)
async def cancel(call: types.CallbackQuery, state = FSMContext):
    await call.message.answer('Ваше действие было отменено', reply_markup=uskmp)
    await state.finish()
    await UserStates.menu.set()

#------------------------------------------------------------------------------------------------------------------------
#Система отлова людей без state и обработчик стикеров
#------------------------------------------------------------------------------------------------------------------------

# Ответ на отправку стикера
@dp.message_handler(content_types=types.ContentType.STICKER, state="*")
async def handle_sticker(message: types.Message):
    chat_id = message.chat.id
    await bot.send_message(chat_id, "Извините, я не принимаю стикеры.")

# ВНИМАНИЕ! Данный handler ловит людей без состояния!
@dp.message_handler(state= None)
async def handle_The_Last_Frontier(message: types.Message, state: FSMContext):
    sost = await state.get_state()
    print(sost)
    await start(message, state)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)