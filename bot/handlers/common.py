import random

from functools import wraps
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot
from bot.texts import START_TEXT, TARGET_CHAT_ID, SUBSCRIBE_TEXT, SUPPORT_TEXT, HOW_TO_TEXT
from bot.keyboards import START_KEYBOARD, CHECK_SUBSCRIPTION, BACK_BUTTON, back_menu
from bot.models import Category, Place


def start(message: Message):
    """Функция, вызываемая при /start"""
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    bot.send_message(chat_id = message.chat.id, text = START_TEXT)
    
    # Проверяем подписку человека на группу
    if bot.get_chat_member(chat_id = TARGET_CHAT_ID, user_id = message.chat.id).status in ["member", "administrator", "creator"]:
        bot.send_message(chat_id = message.chat.id, text = "Главное меню", reply_markup = START_KEYBOARD)
    else:
        bot.send_message(chat_id = message.chat.id, text = SUBSCRIBE_TEXT, reply_markup = CHECK_SUBSCRIPTION)


# Обработчики кнопок из меню
def where_to_go_handler(call: CallbackQuery):
    """Обработчик кнопки Куда пойти?"""

    # Получаем категории
    markup = InlineKeyboardMarkup()
    for category in Category.objects.filter(parent_category__isnull=True):
        markup.add(InlineKeyboardButton(text=category.name, callback_data=f"category_{category.pk}"))
    markup.add(back_menu)
    try:
        bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = "Выбери категорию", reply_markup = markup)
    except:
        bot.send_message(chat_id = call.message.chat.id, text = "Выбери категорию", reply_markup = markup)


def support_handler(call: CallbackQuery):
    """Обработчик кнопки Обратная связь"""

    bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = SUPPORT_TEXT, reply_markup = BACK_BUTTON)


def how_to_handler(call: CallbackQuery):
    """Обработчик кнопки Предложить заведение"""

    bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = HOW_TO_TEXT, reply_markup = BACK_BUTTON)

# Обработчик кнопок Категорий и Подкатегорий
def categories_handler(call: CallbackQuery):
    """Обработчик кнопок Категорий и Подкатегорий"""
    try:
        _, pk_, status, place_pk = call.data.split("_")
        status = int(status)
        place_pk = int(place_pk)
    except:
        _, pk_ = call.data.split("_")
        status = 0
        place_pk = -1
    category = Category.objects.get(pk=pk_)
    
    if Category.objects.filter(parent_category = category).exists():
        # Получаем подкатегории
        markup = InlineKeyboardMarkup()
        for category_ in Category.objects.filter(parent_category = category).order_by('order'):
            markup.add(InlineKeyboardButton(text=category_.name, callback_data=f"category_{category_.pk}"))

        if category.parent_category:
            markup.add(InlineKeyboardButton(text="Назад", callback_data=f"category_{category.parent_category.pk}"))
        else:
            markup.add(InlineKeyboardButton(text="Назад", callback_data="start_where"))
        markup.add(back_menu)

        try:
            bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = "Выбери категорию", reply_markup = markup)
        except:
            bot.send_message(chat_id = call.message.chat.id, text = "Выбери категорию", reply_markup = markup)
    else:
        # Получаем случайное место
        places = Place.objects.filter(category = category)
        try:
            if place_pk != -1 and places.count() > 1:
                places = places.remove(Place.objects.get(pk=place_pk))
        except:
            pass
        place = random.choice(places)

        if status == 0:
            if category.description:
                bot.edit_message_text(chat_id = call.message.chat.id, message_id = call.message.message_id, text = category.description)
       
        # Создаем кнопки с ссылками на соц.сети
        markup = InlineKeyboardMarkup()
        try:
            if place.web_link:
                markup.add(InlineKeyboardButton(text="Перейти на сайт", url=place.web_link))
            if place.vk_link:
                markup.add(InlineKeyboardButton(text="Посмотреть в ВК", url=place.vk_link))
            if place.instagram_link:
                markup.add(InlineKeyboardButton(text="Посмотреть в Instagram", url=place.instagram_link))
            if place.telegram_link:
                markup.add(InlineKeyboardButton(text="Посмотреть в Telegram", url=place.telegram_link))

            # Создаем кнопку с ссылкой на Яндекс.Карты
            if place.map_link:
                markup.add(InlineKeyboardButton(text="Проложить маршрут", url=f"{place.map_link}"))

            markup.add(InlineKeyboardButton(text="Следующее место", callback_data=f"category_{category.pk}_1_{place.pk}"))
        
        except Exception as e:
            bot.send_message(chat_id=call.message.chat.id, text=e)

        try:
            if category.parent_category:
                markup.add(InlineKeyboardButton(text="Назад", callback_data=f"category_{category.parent_category.pk}"))
            else:
                markup.add(InlineKeyboardButton(text="Назад", callback_data="start_where"))
        except Exception as e:
            bot.send_message(chat_id=call.message.chat.id, text=e)

        markup.add(back_menu)

        try:
            if place.photo:
                with open(place.photo.path, 'rb') as photo:
                    bot.send_photo(chat_id = call.message.chat.id, photo = photo, caption = place.get_text(), reply_markup = markup)
            else:
                bot.send_message(chat_id = call.message.chat.id, text = place.get_text(), reply_markup = markup)
        except Exception as e:
            bot.send_message(chat_id=call.message.chat.id, text=e)

# Обработчики служебных кнопок
def back_handler(call: CallbackQuery):
    """Обработчик кнопки назад"""
    bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
    if bot.get_chat_member(chat_id = TARGET_CHAT_ID, user_id = call.message.chat.id).status in ["member", "administrator", "creator"]:
        bot.send_message(chat_id = call.message.chat.id, text = "Главное меню", reply_markup = START_KEYBOARD)
    else:
        bot.send_message(chat_id = call.message.chat.id, text = SUBSCRIBE_TEXT, reply_markup = CHECK_SUBSCRIPTION)


def check_handler(call: CallbackQuery):
    """Обработчик кнопки Проверить подписку"""
    if bot.get_chat_member(chat_id = TARGET_CHAT_ID, user_id = call.message.chat.id).status in ["member", "administrator", "creator"]:
        bot.send_message(chat_id = call.message.chat.id, text = "Главное меню", reply_markup = START_KEYBOARD)
    else:
        bot.send_message(chat_id = call.message.chat.id, text = SUBSCRIBE_TEXT, reply_markup = CHECK_SUBSCRIPTION)

