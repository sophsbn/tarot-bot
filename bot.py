
import telebot
from telebot import types
from flask import Flask
from threading import Thread
import time


app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN = '7985871253:AAGsANqe3GvqScbUa5RlyhyB1V6EI2vbhZ8'  
GROUP_CHAT_ID = -1003260291316

bot = telebot.TeleBot(TOKEN)

# --- словарь для хранения соответствий user_id -> topic_id
user_threads = {}


# ===== Функции пересылки =====
# ===== Функция пересылки контента в группу =====
def forward_content(user_name, user_id, thread_id, message):
    if message.text:
        bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=thread_id,
            text=f"Сообщение от {user_name} (ID: {user_id}):\n{message.text}"
        )
    elif message.photo:
        photo = message.photo[-1]  # берем самый большой размер
        bot.send_photo(
            chat_id=GROUP_CHAT_ID,
            photo=photo.file_id,
            caption=f"Фото от {user_name} (ID: {user_id})",
            message_thread_id=thread_id
        )
    elif message.sticker:
        bot.send_sticker(chat_id=GROUP_CHAT_ID, sticker=message.sticker.file_id, message_thread_id=thread_id)
        bot.send_message(chat_id=GROUP_CHAT_ID, text=f"Стикер от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.document:
        bot.send_document(chat_id=GROUP_CHAT_ID, document=message.document.file_id,
                          caption=f"Документ от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.video:
        bot.send_video(chat_id=GROUP_CHAT_ID, video=message.video.file_id,
                       caption=f"Видео от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.animation:
        bot.send_animation(chat_id=GROUP_CHAT_ID, animation=message.animation.file_id,
                           caption=f"Анимация от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.voice:
        bot.send_voice(chat_id=GROUP_CHAT_ID, voice=message.voice.file_id,
                       caption=f"Голосовое сообщение от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.audio:
        bot.send_audio(chat_id=GROUP_CHAT_ID, audio=message.audio.file_id,
                       caption=f"Аудио от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.video_note:
        bot.send_video_note(chat_id=GROUP_CHAT_ID, video_note=message.video_note.file_id, message_thread_id=thread_id)
        bot.send_message(chat_id=GROUP_CHAT_ID, text=f"Видеосообщение от {user_name} (ID: {user_id})", message_thread_id=thread_id)
    elif message.contact:
        bot.send_message(chat_id=GROUP_CHAT_ID,
                         text=f"Контакт от {user_name} (ID: {user_id}):\nИмя: {message.contact.first_name}\nТелефон: {message.contact.phone_number}",
                         message_thread_id=thread_id)
    elif message.location:
        bot.send_location(chat_id=GROUP_CHAT_ID, latitude=message.location.latitude, longitude=message.location.longitude, message_thread_id=thread_id)


# ===== Функция ответа пользователю =====
def reply_to_user(user_id, message):
    if message.text:
        bot.send_message(user_id, f"💌 Ответ таролога:\n{message.text}")
    elif message.photo:
        photo = message.photo[-1]  # самый большой размер
        bot.send_photo(user_id, photo.file_id, caption="💌 Ответ таролога")
    elif message.sticker:
        bot.send_message(user_id, "💌 Ответ таролога:")
        bot.send_sticker(user_id, message.sticker.file_id)
    elif message.document:
        bot.send_document(user_id, message.document.file_id, caption="💌 Ответ таролога")
    elif message.video:
        bot.send_video(user_id, message.video.file_id, caption="💌 Ответ таролога")
    elif message.animation:
        bot.send_animation(user_id, message.animation.file_id, caption="💌 Ответ таролога")
    elif message.voice:
        bot.send_message(user_id, "💌 Ответ таролога:")
        bot.send_voice(user_id, message.voice.file_id)
    elif message.audio:
        bot.send_audio(user_id, message.audio.file_id, caption="💌 Ответ таролога")
    elif message.video_note:
        bot.send_message(user_id, "💌 Ответ таролога:")
        bot.send_video_note(user_id, message.video_note.file_id)
    elif message.contact:
        bot.send_message(user_id, f"💌 Ответ таролога\nКонтакт:\nИмя: {message.contact.first_name}\nТелефон: {message.contact.phone_number}")
    elif message.location:
        bot.send_location(user_id, message.location.latitude, message.location.longitude)


# ===== Команда /start =====
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for option in ['хочу расклад', 'price list', 'оплата']:
        markup.add(types.KeyboardButton(option))
    bot.send_message(message.chat.id, 'Привет! Выбери опцию:', reply_markup=markup)


# ===== Пересылка личных сообщений в группу (по своей теме) =====
@bot.message_handler(func=lambda message: message.chat.type == 'private',
                     content_types=['text', 'photo', 'sticker', 'document', 'video', 'audio', 'voice', 'animation', 'video_note', 'contact', 'location'])
def forward_to_group(message):
    user_id = message.from_user.id
    user_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name

    thread_id = user_threads.get(user_id)
    if thread_id is None:
        try:
            topic = bot.create_forum_topic(GROUP_CHAT_ID, name=user_name)
            thread_id = topic.message_thread_id
            user_threads[user_id] = thread_id
        except Exception as e:
            print(f"Ошибка при создании темы: {e}")
            bot.send_message(user_id, "⚠️ Ошибка при создании темы в группе.")
            return

    forward_content(user_name, user_id, thread_id, message)
    handle_user_commands(message)

# ===== Ответы из группы пользователям (по теме) =====
@bot.message_handler(func=lambda message: message.chat.id == GROUP_CHAT_ID and message.is_topic_message,
                     content_types=['text', 'photo', 'sticker', 'document', 'video', 'audio', 'voice', 'animation', 'video_note', 'contact', 'location'])
def reply_from_group(message):
    thread_id = message.message_thread_id
    user_id = next((uid for uid, tid in user_threads.items() if tid == thread_id), None)
    if not user_id:
        return
    reply_to_user(user_id, message)
    bot.reply_to(message, "✅ Сообщение отправлено пользователю.")


# ===== Обработка меню =====
def handle_user_commands(message):
    chat_id = message.chat.id
    text = message.text

    if text == 'хочу расклад':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for option in ['ответ да/нет', 'один вопрос', 'расклад на месяц', 'расклад на отношения', 'общий расклад на ситуацию', 'назад']:
            markup.add(types.KeyboardButton(option))
        bot.send_message(chat_id, 'Выберите услугу:', reply_markup=markup)

    elif text == 'price list':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for cur in ['RUB', 'UAH', 'BYN', 'EUR', 'USD', 'назад']:
            markup.add(types.KeyboardButton(cur))
        bot.send_message(chat_id, 'Выберите валюту:', reply_markup=markup)

    elif text == 'оплата':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('назад'))
        bot.send_message(chat_id, 'Оплата производится на карту 5313770066553230. Указывайте ваш никнейм.', reply_markup=markup)

    elif text in ['ответ да/нет', 'один вопрос', 'расклад на месяц', 'расклад на отношения', 'общий расклад на ситуацию']:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('назад'))

        prompt = 'Напишите ваш вопрос или опишите ситуацию'
        if text == 'расклад на месяц':
            prompt = 'Напишите, на какой месяц вы хотите расклад'
        elif text in ['ответ да/нет', 'один вопрос']:
            prompt = 'Напишите ваш вопрос'

        bot.send_message(chat_id, prompt, reply_markup=markup)

    elif text == 'назад':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for option in ['хочу расклад', 'price list', 'оплата']:
            markup.add(types.KeyboardButton(option))
        bot.send_message(chat_id, 'Вы вернулись в главное меню', reply_markup=markup)

    elif text in ['RUB', 'UAH', 'BYN', 'EUR', 'USD']:
        try:
            with open(f"{text.lower()}.jpg", "rb") as photo:
                bot.send_photo(chat_id, photo)
        except FileNotFoundError:
            bot.send_message(chat_id, "Файл с ценами для этой валюты не найден.")

keep_alive()

while True:
    try:
        bot.polling(non_stop=True, interval=1)
    except Exception as e:
        print(f"Ошибка polling: {e}")
        time.sleep(5)


