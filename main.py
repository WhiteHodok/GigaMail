from dotenv import load_dotenv
import json
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

@dp.message_handler(commands=['start'], state = '*')
async def start(message: types.Message, state = FSMContext):
    await message.reply('Добро пожаловать в бота !', reply_markup=uskmp)
    await UserStates.menu.set()

@dp.message_handler(text='Добавить почты', state =UserStates.menu)
async def add_mail(message: types.Message, state = FSMContext):
    await message.reply('Введите почту(-ы) для добавления', reply_markup=cancel_markup)
    await UserStates.add_mail.set()



@dp.callback_query_handler(text='cancel', state = UserStates.add_mail)
async def cancel(call: types.CallbackQuery, state = FSMContext):
    await call.message.answer('Ваше действие было отменено', reply_markup=uskmp)
    await state.finish()
    await UserStates.menu.set()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)