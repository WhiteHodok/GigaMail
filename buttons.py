from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.types.web_app_info import WebAppInfo

# user keyboard markup

uskmp = ReplyKeyboardMarkup(resize_keyboard=True)
add = KeyboardButton('Добавить почты')
score = KeyboardButton('Статистика')
uskmp.row(add)
uskmp.row(score)

# cancel markup user

cancel_markup = InlineKeyboardMarkup(resize_keyboard=True)
cancel = InlineKeyboardButton('Отмена', callback_data='cancel')
cancel_markup.row(cancel)


# cancel markup admin

cancel_markup = InlineKeyboardMarkup(resize_keyboard=True)
cancel = InlineKeyboardButton('Отмена', callback_data='cancel_admin')
cancel_markup.row(cancel)

# admin keyboard markup
adkmp = ReplyKeyboardMarkup(resize_keyboard=True)
search = KeyboardButton('Поиск почты')
load = KeyboardButton('Получить почты')
back = KeyboardButton('Назад')
adkmp.row(search)
adkmp.row(load)
adkmp.row(back)

