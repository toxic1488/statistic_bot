import os
import psycopg2
import random
import sqlite3
import telebot
import time

types_dict = {
    0: 'Отжимания',
    10: 'Бег',
    20: 'Пресс'
}
push_ups = {
    1: 'Узким хватом',
    2: 'Средним хватом',
    3: 'Широким хватом',
    4: 'Задние',
}


def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key
    return None


keyboard_basic = telebot.types.ReplyKeyboardMarkup(True)
keyboard_activity = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard_push_ups = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard_basic.row('Внести данные', 'График')
for key in types_dict:
    keyboard_activity.add(types_dict[key])
for key in push_ups:
    keyboard_push_ups.add(push_ups[key])

DATABASE_URL = os.environ['DATABASE_URL']
token = os.environ.get('token', None)
bot = telebot.TeleBot(token)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Бот для статистики упражнений', reply_markup=keyboard_basic)


@bot.message_handler(content_types=['text'])
def send_text(message):
    chat_id = message.chat.id
    if message.text.lower() == 'привет':
        bot.send_message(chat_id, 'Приветствую тебя, мой ,белый хозяин!')
    elif message.text.lower() == 'внести данные':
        bot.send_message(chat_id, 'Выберите упражнение', reply_markup=keyboard_activity)
        bot.register_next_step_handler(message, choose_type)
    elif message.text.lower() == 'график':
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        sql = "SELECT type, result, date FROM measurements WHERE chat_id = ? ORDER BY date;"
        try:
            cursor.execute(sql, (chat_id,))
        except:
            pass
        data = cursor.fetchall()
        for measurement in data:
            res = 'type: ' + str(measurement[0]) + ', result: ' + measurement[1] + ', date: ' + measurement[2]
            bot.send_message(chat_id, res, reply_markup=keyboard_basic)
        cursor.close()


def choose_type(message):
    if message.text == types_dict[0]:
        bot.send_message(message.chat.id, 'Выберите тип отжимания', reply_markup=keyboard_push_ups)
        bot.register_next_step_handler(message, choose_type)
    else:
        bot.send_message(message.chat.id, 'Введите результаты тренировки')
        global activity_type
        activity_type = get_key(types_dict, message.text)
        if activity_type is None:
            activity_type = get_key(push_ups, message.text)
        # print(message, activity_type)
        bot.register_next_step_handler(message, enter_data)


def enter_data(message):
    # sql = "INSERT INTO measurements (chat_id, type, result, date) VALUES (?, ?, ?, ?)"
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    global activity_type
    try:
        cursor.execute(
            "INSERT INTO measurements (chat_id, type, result, date) VALUES (%s, %i, %s, %s)"
            % (message.chat.id, activity_type, message.text, time.strftime("%Y-%m-%d", time.gmtime()))
        )
        conn.commit()
    except Exception as exc:
        print(exc)
        bot.send_message(message.chat.id, 'Произошла какая-то ошибка', reply_markup=keyboard_basic)
    else:
        bot.send_message(message.chat.id, 'Данные успешно записаны!', reply_markup=keyboard_basic)
    cursor.close()


# Executing
while True:
    try:
        bot.polling(none_stop=True)

    except Exception as e:
        print(e)
        time.sleep(15)
