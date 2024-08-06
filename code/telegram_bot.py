import telebot
from telebot import types
from code.config import get_telegram_token
from code.db import get_db_connection, init_db
from code.schedule import init_schedule_ptk, get_schedule_ptk, init_send_schedule
from bs4 import BeautifulSoup as BS
import requests

bot = telebot.TeleBot(get_telegram_token())

days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

user_context = {}
group = []

cur = None
group_student = None
day_of_week = None
week_type = None
college = None
course = None

def init_list_group(first_group_number, table_name, list_group, cur):
    course = 1
    for num_group in list_group:
        temp = int(num_group) // 1000
        if (first_group_number != temp):
            course += 1
            first_group_number = temp
        cur.execute("INSERT INTO {} VALUES (%s, %s)".format(table_name),
                    (course, num_group))

def init_list_groups(soup, cur):
    substring_ptk = "/npe/files/_timetable/ptk/"
    substring_pedcol = "/npe/files/_timetable/pedcol/"
    substring_medcol = "/npe/files/_timetable/medcol/"
    substring_spour = "/npe/files/_timetable/spour/"
    substring_spoinpo = "/npe/files/_timetable/spoinpo/"
    
    list_group_ptk, list_group_pedcol, list_group_medcol = [], [], []
    list_group_spour, list_group_spoinpo = [], []
    
    list_groups = soup.find_all('a')
    for element in list_groups:
        if substring_ptk in str(element) and '_' not in element.get_text(): 
            list_group_ptk.append(element.get_text())
        elif substring_pedcol in str(element) and '_' not in element.get_text():
            list_group_pedcol.append(element.get_text())
        elif substring_medcol in str(element) and '_' not in element.get_text():
            list_group_medcol.append(element.get_text())
        elif substring_spour in str(element) and '_' not in element.get_text():
            list_group_spour.append(element.get_text())
        elif substring_spoinpo in str(element) and ('_' and 'o' not in element.get_text()):
            list_group_spoinpo.append(element.get_text())
            
    first_group_number = int(list_group_ptk[0]) // 1000
    init_list_group(first_group_number, 'groups_students_ptk', list_group_ptk, cur)
    #init_list_group(first_group_number, 'groups_students_pedcol', list_group_pedcol, cur)
    #init_list_group(first_group_number, 'groups_students_medcol', list_group_medcol, cur)
    #init_list_group(first_group_number, 'groups_students_spour', list_group_spour, cur)
    init_list_group(first_group_number, 'groups_students_spoinpo', list_group_spoinpo, cur)

def init_get_list_group(college, cur):
    cur.execute('SELECT group_id FROM {}'.format(college))
    temp = cur.fetchall()
    for item in temp:
        group.append(item[0])

@bot.message_handler(commands=['start'])
def main_menu(message):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_geolacation = types.KeyboardButton('Узнать геопозицию')
    item_schedule = types.KeyboardButton('Узнать расписание')
    markup_replay.add(item_schedule, item_geolacation)
    bot.send_message(message.chat.id, 'Привет! Что вы хотите узнать?',
                     reply_markup=markup_replay)


def show_groups(message, college):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    group_student = message.text
    cur.execute("SELECT group_id FROM {} WHERE group_course=%s".format(college), group_student[0])
    temp = cur.fetchall()
    temp_items = []
    for item in temp:
        temp_items.append(types.KeyboardButton(item[0]))
    markup_replay.add(*temp_items)
    item_back = types.KeyboardButton('Главное меню')
    markup_replay.add(item_back)
    bot.send_message(message.chat.id, '📝Выберите свою группу', reply_markup=markup_replay)

@bot.message_handler(content_types=['text'])
def bot_massage(message):
    global group, group_student
    if message.chat.type == 'private':
        if 'Узнать геопозицию' in message.text:
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_glav = types.KeyboardButton('Главный корпус')
            item_ptk = types.KeyboardButton('Политехнический колледж')
            item_anton = types.KeyboardButton('Антоново')
            item_itys = types.KeyboardButton('ИЦЭУС')
            item_ibhi = types.KeyboardButton('ИБХИ')
            item_med = types.KeyboardButton('ИМО')
            item_ped = types.KeyboardButton('ПИ')
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_glav, item_ptk, item_anton, item_itys,
                              item_ibhi, item_med, item_ped, item_back)
            bot.send_message(message.chat.id, 'Выберите интересующий институт',
                             reply_markup=markup_replay)

        elif message.text == 'Главный корпус':
            latitude = 58.542306
            longitude = 31.261174
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение Главного корпуса: Большая Санкт-Петербургская, 41')

        elif message.text == 'Политехнический колледж':
            latitude = 58.541668
            longitude = 31.264534
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение ПТК: Большая Санкт-Петербургская, 46')

        elif message.text == 'Антоново':
            latitude = 58.541079
            longitude = 31.288108
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение ИГУМ: район Антоново, 1')

        elif message.text == 'ИЦЭУС':
            latitude = 58.522347
            longitude = 31.258228
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение ИЦЭУС: Псковская улица, 3')

        elif message.text == 'ИМО':
            latitude = 58.542809
            longitude = 31.310567
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение ИМО: улица Державина, 6')

        elif message.text == 'ИБХИ':
            latitude = 58.551745
            longitude = 31.300628
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение ИБХИ: улица Советской Армии, 7')

        elif message.text == 'ПИ':
            latitude = 58.523945
            longitude = 31.262243
            bot.send_location(message.chat.id, latitude, longitude)
            bot.send_message(message.chat.id, '📍Местоположение ПИ: улица Черняховского, 64/6')

        elif message.text == 'Узнать расписание':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_PTK = types.KeyboardButton('ПТК')
            item_MED = types.KeyboardButton('Мед.колледж')
            item_EKO = types.KeyboardButton('СПО ИЦЭУС')
            item_IUR = types.KeyboardButton('СПО ИЮР')
            item_PED = types.KeyboardButton('СПО ИНПО')
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_PTK, item_PED, item_IUR, item_MED, item_EKO, item_back)
            bot.send_message(message.chat.id, '🏫Какой колледж вас интересует?',
                             reply_markup=markup_replay)

        elif message.text == 'ПТК':
            user_context[message.chat.id] = 'ПТК'
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')
            item_back = types.KeyboardButton('Главное меню')
            global college
            college = message.text
            global course
            course = message.text
            markup_replay.add(item_1, item_2, item_3, item_4, item_back)
            bot.send_message(message.chat.id, '❓ Какой вы курс?', reply_markup=markup_replay)

        elif message.text == 'СПО ИНПО':
            user_context[message.chat.id] = 'СПО ИНПО'
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс') 
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')
            item_back = types.KeyboardButton('Главное меню')

            college = message.text
            course = message.text
            markup_replay.add(item_1, item_2, item_3, item_4, item_back)
            bot.send_message(message.chat.id, '❓ Какой вы курс?', reply_markup=markup_replay)

        elif message.text == '1 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                show_groups(message, 'groups_students_ptk')

            elif current_context == 'СПО ИНПО':
                show_groups(message, 'groups_students_spoinpo')

        elif message.text == '2 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                show_groups(message, 'groups_students_ptk')
                
            elif current_context == 'СПО ИНПО':
                show_groups(message, 'groups_students_spoinpo')


        elif message.text == '3 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                show_groups(message, 'groups_students_ptk')

            elif current_context == 'СПО ИНПО':
                show_groups(message, 'groups_students_spoinpo')


        elif message.text == '4 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                show_groups(message, 'groups_students_ptk')

            elif current_context == 'СПО ИНПО':
                show_groups(message, 'groups_students_spoinpo')


        elif message.text == 'Мед.колледж':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            '''item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')'''
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, 'В разработке.',
                             reply_markup=markup_replay)

        elif message.text == 'СПО ИЦЭУС':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            '''item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')'''
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, 'В разработке.',
                             reply_markup=markup_replay)

        elif message.text == 'СПО ИЮР':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            '''item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')'''
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, 'В разработке.',
                             reply_markup=markup_replay)

        elif message.text == 'Главное меню':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_geolacation = types.KeyboardButton('Узнать геопозицию')
            item_schedule = types.KeyboardButton('Узнать расписание')
            markup_replay.add(item_schedule, item_geolacation)
            bot.send_message(message.chat.id, 'Главное меню',
                             reply_markup=markup_replay)

        elif message.text.isdigit():
            
            if message.text in group:
                group_student = message.text
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_pn = types.KeyboardButton('Верхняя')
                item_vt = types.KeyboardButton('Нижняя')
                item_back = types.KeyboardButton('Главное меню')
                markup_replay.add(item_pn, item_vt, item_back)
                bot.send_message(message.chat.id, '❗️ Выберите неделю',
                                 reply_markup=markup_replay)
            else:
                bot.send_message(message.chat.id, 'Такой группы несуществует!')

        elif message.text == 'Верхняя':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            global week_type
            week_type = message.text
            markup_replay.add(*days, types.KeyboardButton('Главное меню'))
            bot.send_message(message.chat.id, '📅 Выберите день недели',
                             reply_markup=markup_replay)

        elif message.text == 'Нижняя':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            week_type = message.text
            markup_replay.add(*days, types.KeyboardButton('Главное меню'))
            bot.send_message(message.chat.id, '📅 Выберите день недели',
                             reply_markup=markup_replay)

        elif message.text in days:
            day_of_week = message.text
            print(college)
            if college == 'ПТК':
                schedule = get_schedule_ptk(group_student, day_of_week, week_type)
                if schedule is None:
                    bot.send_message(message.chat.id, 'Нет занятий')
                else:
                    bot.send_message(message.chat.id, f'Расписание на {day_of_week}, неделя - {week_type}, группа -  {group_student}:\n' + '\n'.join(schedule))
            elif college == 'СПО ИНПО':
                print('ИНПО')

        else:
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, '⚠️Извините, я вас не понимаю.\nСледуйте кнопкам меню!⚠️',
                             reply_markup=markup_replay)

def fetch_group_ids(cur, table_name, group_list):
    cur.execute(f'SELECT group_id FROM {table_name}')
    
    temp = cur.fetchall()
    for item in temp:
        group_list.append(item[0])

def main():
    global cur
    
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    
    url = 'https://portal.novsu.ru/univer/timetable/spo/'
    response = requests.get(url)
    html = response.text

    soup = BS(html, 'html.parser')
    init_list_groups(soup, cur)
    conn.commit()

    init_get_list_group('groups_students_ptk', cur)
    init_get_list_group('groups_students_pedcol', cur)
    init_get_list_group('groups_students_medcol', cur)
    init_get_list_group('groups_students_spour', cur)
    init_get_list_group('groups_students_spoinpo', cur)
    
    # fetch_group_ids(cur, 'groups_students_pedcol', group)
    # fetch_group_ids(cur, 'groups_students_medcol', group)
    # fetch_group_ids(cur, 'groups_students_spour', group)
    # fetch_group_ids(cur, 'groups_students_spoinpo', group)
       
            
    for number_group in group:
        link = soup.find('a', string=number_group)  
        if (link):
            link_href = link['href']
            file_url = f"https://portal.novsu.ru/{link_href}"
            response = requests.get(file_url)
            print(number_group)
            cur.execute(f'DROP TABLE IF EXISTS group_{number_group}');
            cur.execute(f'CREATE TABLE group_{number_group}(week_day VARCHAR(2) NOT NULL,'
                         'group_week_type BOOLEAN NOT NULL, group_data VARCHAR(1024) NOT NULL)')
            for day in days:
                schedule = init_schedule_ptk(number_group, day, response.content)
                if schedule != []:
                    init_send_schedule(schedule, number_group, day, "Верхняя", cur)
                    init_send_schedule(schedule, number_group, day, "Нижняя", cur)
            conn.commit()
    
    bot.polling()
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()