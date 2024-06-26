import pandas as pd
import psycopg2
import requests
import telebot
from bs4 import BeautifulSoup as BS
import xml.etree.ElementTree as ET
import tempfile
import os
import types
import asyncio
import aiohttp
from io import BytesIO
import xlrd
import re
from telebot import types

TOKEN = "6848210471:AAE98dRIf47eLHGfgqKFPN78TlXbKJKZClI"
bot = telebot.TeleBot(TOKEN)

conn = psycopg2.connect(dbname='novsu_schedule', user='postgres',
                            password='debadmin', host='localhost')
cur = conn.cursor()
group_student = None
day_of_week = None
week_type = None
college = None
course = None
user_context = {}
group = []
days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']
days_full = ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА']

def init_list_group(first_group_number, table_name, list_group):
    course = 1
    for num_group in list_group:
        temp = int(num_group) // 1000;
        if (first_group_number != temp):
            course += 1
            first_group_number = temp
        cur.execute("INSERT INTO {} VALUES (%s, %s)".format(table_name),
                    (course, num_group))

def init_list_groups(soup):
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
    init_list_group(first_group_number, 'groups_students_ptk', list_group_ptk)
    init_list_group(first_group_number, 'groups_students_pedcol', list_group_pedcol)
    init_list_group(first_group_number, 'groups_students_medcol', list_group_medcol)
    init_list_group(first_group_number, 'groups_students_spour', list_group_spour)
    init_list_group(first_group_number, 'groups_students_spoinpo', list_group_spoinpo)

def init_find_distance(group_student, day_of_week, df):
    #Найти индекс столбца, содержащего дни недели
    col_index = next((col for col in df.columns if any(day in df[col].values for day in days_full)), None)
    if col_index is not None:
        # Найти индексы строк, содержащих дни недели
        days_of_week = {'ПН': 'ПОНЕДЕЛЬНИК', 'ВТ': 'ВТОРНИК', 'СР': 'СРЕДА',
                        'ЧТ': 'ЧЕТВЕРГ', 'ПТ': 'ПЯТНИЦА', 'СБ': 'СУББОТА'}
        day_indices = {day: [] for day in days_of_week.values()}
        
        for index, value in enumerate(df[col_index]):
            if value in days_of_week.values():
                day_indices[value].append(index)

        if day_of_week.upper() in days_of_week:
            current_day = days_of_week[day_of_week.upper()]
            next_day = days_of_week.get(init_get_next_weekday(day_of_week.upper()), None)

            if next_day is not None:
                if len(day_indices[current_day]) > 0 and len(day_indices[next_day]) > 0:
                    distance = day_indices[next_day][0] - day_indices[current_day][-1]
                    return distance
    return 0

def init_get_next_weekday(days):
    days_of_week = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ']
    current_day_index = days_of_week.index(days)
    return days_of_week[(current_day_index + 1) % len(days_of_week)]

def init_get_df(content):
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        tmp_file.write(content)
        tmp_file.seek(0)
        df = pd.read_excel(tmp_file)
    return df

def init_schedule_ptk(group_student, day_of_week, content):

    df = init_get_df(content)
    day_of_week_values = {'Пн': 'ПОНЕДЕЛЬНИК', 'Вт': 'ВТОРНИК', 'Ср': 'СРЕДА',
                          'Чт': 'ЧЕТВЕРГ', 'Пт': 'ПЯТНИЦА', 'Сб': 'СУББОТА'}
    row_index = None
    for row_idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if cell == day_of_week_values.get(day_of_week):
                row_index = row_idx
                break
        if row_index is not None:
            break

    column_index = None
    for column_index, column_name in enumerate(df.columns):
        if group_student in df[column_name].values:
            break

    schedule = []
    #print(f'group_student --> {group_student}\nday_os_week --> {day_of_week}\n')
    for i in range(init_find_distance(group_student, day_of_week, df)):
        time = df.iloc[row_index + i, column_index - 1]
        info = df.iloc[row_index + i, column_index]
        timeN = df.iloc[row_index + i - 1, column_index - 1]
        info = remove_lek_from_info(info)
        #print(info)
        # Обычная неделя без верха низа:

        if pd.notna(time) and pd.notna(info):
            # Предмет без групп
            if len(info.split(', ')) == 3:
                subject, teacher, audience = info.split(', ')
                schedule.append(
                    f' ⏰Время: {time} \n 📚Предмет: {subject} \n 👨‍🏫Преподаватель: {teacher} \n 📝Аудитория: {audience}\n\n')
            # Предмет по группам:
            elif len(info.split(', ')) == 5:
                subject, teacher1, audience1, teacher2, audience2 = info.split(', ')
                if pd.notna(time) and pd.notna(info):
                    schedule.append(
                        f' 📚Предмет: {subject} \n'
                        f' Группа 1: \n ⏰Время: {time} \n 👨‍🏫Преподаватель: {teacher1} \n 📝Аудитория: {audience1} \n\n' +
                        f' Группа 2: \n ⏰Время: {time} \n 👨‍🏫Преподаватель: {teacher2} \n 📝Аудитория: {audience2} \n\n')
    
        # Если появляется верхний нижний предмет:

        elif pd.isna(time) and pd.notna(info):
            # Предмет без групп нижней недели:
            if len(info.split(', ')) == 3:
                subject, teacher, audience = info.split(', ')
                schedule.append(
                    f' ⏰Время: {timeN} \n Предмет: {subject} \n Преподаватель: {teacher} \n Аудитория: {audience} - только по нижней неделе \n\n')
            # Предмет по группам нижней недели:
            elif len(info.split(', ')) == 5:
                subject1, teacher1, audience1, subject2, teacher2, audience2 = info.split(', ')
                if pd.notna(time) and pd.notna(info):
                    schedule.append(
                        f' Группа 1: \n ⏰Время: {time} \n 📚Предмет: {subject1} \n 👨‍🏫Преподаватель: {teacher1} \n 📝Аудитория: {audience1} - только по нижней неделе \n\n' +
                        f' Группа 2: \n ⏰Время: {time} \n 📚Предмет: {subject2} \n 👨‍🏫Преподаватель: {teacher2} \n 📝Аудитория: {audience2} - только по нижней неделе \n\n')
                    
    return schedule

def init_send_schedule(schedule, number_group, day, week_type):
    for i, elem in enumerate(schedule):
        if ' - только по нижней неделе' in elem:
            schedule[i - 1] = schedule[i - 1].rstrip('\n\n')
            schedule[i - 1] += ' - только по верхней неделе \n\n'

    for i, elem in enumerate(schedule):
        if week_type == 'Верхняя':
            if ' - только по нижней неделе' in elem:
                del schedule[i]
        elif week_type == 'Нижняя':
            if ' - только по верхней неделе' in elem:
                del schedule[i]
    cur.execute(f'INSERT INTO group_{number_group} VALUES (%s, %s, %s)',
                (day, week_type == "Верхняя", ''.join(schedule)))

def init_get_list_group(college):
    cur.execute('SELECT group_id FROM {}'.format(college))
    temp = cur.fetchall()
    for item in temp:
        group.append(item[0])

def init_db():
    global group
    cur.execute('DO $$ '
                'DECLARE _tableName TEXT; BEGIN '
                'FOR _tableName IN SELECT tablename FROM pg_tables WHERE tablename LIKE \'group_%\' '
                'LOOP EXECUTE \'DROP TABLE IF EXISTS \' || quote_ident(_tableName) || \' CASCADE\'; END LOOP; '
                'END; $$;'
                'CREATE TABLE groups_students_ptk'
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_pedcol' 
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_medcol' 
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_spour'
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);'
                'CREATE TABLE groups_students_spoinpo'
                '(group_course SMALLINT NOT NULL, group_id VARCHAR(6) NOT NULL);');
    
    url = 'https://portal.novsu.ru/univer/timetable/spo/'
    response = requests.get(url)
    html = response.text

    soup = BS(html, 'html.parser')
    init_list_groups(soup)
    conn.commit()

    init_get_list_group('groups_students_ptk')
    init_get_list_group('groups_students_pedcol')
    init_get_list_group('groups_students_medcol')
    init_get_list_group('groups_students_spour')
    init_get_list_group('groups_students_spoinpo')
    
    cur.execute('SELECT group_id FROM groups_students_pedcol')
    temp = cur.fetchall()
    for item in temp:
        group.append(item[0])
    # cur.execute('SELECT group_id FROM groups_students_medcol')
    # temp = cur.fetchall()
    # for item in temp:
    #    group.append(item[0])
    # cur.execute('SELECT group_id FROM groups_students_spour')
    # temp = cur.fetchall()
    # for item in temp:
    #     group.append(item[0])
    # cur.execute('SELECT group_id FROM groups_students_spoinpo')
    # temp = cur.fetchall()
    # for item in temp:
    #    group.append(item[0])
            
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
                    init_send_schedule(schedule, number_group, day, "Верхняя")
                    init_send_schedule(schedule, number_group, day, "Нижняя")
            conn.commit()
            
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


def remove_lek_from_info(info):
    if isinstance(info, str) and ',' in info:
        parts = info.split(', ')
        if len(parts) > 3:
            return ', '.join(parts[:3])
    return info


def get_schedule_ptk(group_student, day_of_week, week_type):
    conn = psycopg2.connect(dbname='novsu_schedule', user='postgres',
                            password='debadmin', host='localhost')
    cur = conn.cursor()
    cur.execute(f'SELECT group_data FROM group_{group_student} WHERE week_day=\'{day_of_week}\' AND group_week_type={week_type=="Верхняя"}')
    shedule = cur.fetchone()
    
    conn.commit()
    return shedule
    
def get_schedule_inpo(group_number_ptk, day_of_week_ptk, week_type):
    print('Get_schedule start')
    df = get_file_schedule_PTK(group_number_ptk)
    print('valid groups getting')
    # Список допустимых групп

    valid_groups = [df.iloc[0, 3], df.iloc[0, 9], df.iloc[0, 15]]
    print('Группы: ' + str(valid_groups))
    print('day of week getting')
    print(day_of_week_ptk)
    # Выбрать алгоритм в зависимости от дня недели


    if group_number_ptk in valid_groups[0]:
        column_index = 2
    elif group_number_ptk in valid_groups[1]:
        column_index = 6
    elif group_number_ptk in valid_groups[2]:
        column_index = 9
    elif group_number_ptk in valid_groups[3]:
        column_index = 12
    print('Get_schedule done')

    time = df.iloc[1:11, column_index].tolist()
    new_time = []
    for item in time:
        if not pd.isna(item):
            new_time.append(item)
    time = new_time

    time1 = time[0]
    time2 = time[1]
    time3 = time[2]
    time4 = time[3]
    time5 = time[4]
    print(time1, time2, time3, time4, time5)

    if day_of_week_ptk == 'Пн':
        row_index = 11

        subjects = df.iloc[1:row_index, column_index + 1].tolist()

        new_subjects = []
        prev_subject = None
        for i, subject in enumerate(subjects):
            if not pd.isna(subject):
                prev_subject = subject
            elif i == len(subjects) - 1 or (pd.isna(prev_subject) and new_subjects and new_subjects[
                -1] is not None):  # проверяем, что текущий элемент является последним или предыдущий элемент является nan и предыдущий не-nan элемент уже добавлен в список
                new_subjects.append(None)
            elif pd.isna(
                    prev_subject) and i > 0:  # проверяем, что предыдущий элемент является nan и текущий элемент не является первым
                continue
            else:
                new_subjects.append(prev_subject)

        subjects = new_subjects
        print(subjects)

        teachers = df.iloc[1:row_index, column_index+4].tolist()
        print(teachers)

        auditors = df.iloc[1:row_index, column_index+6].tolist()
        print(auditors)

    elif day_of_week_ptk == 'Вт':
        row_index = 21

        subjects = df.iloc[11:row_index, column_index + 1].tolist()
        print(subjects)

        new_subjects = []
        prev_subject = None
        for i, subject in enumerate(subjects):
            if not pd.isna(subject):
                prev_subject = subject
            elif i == len(subjects) - 1 or (pd.isna(prev_subject) and new_subjects and new_subjects[
                -1] is not None):  # проверяем, что текущий элемент является последним или предыдущий элемент является nan и предыдущий не-nan элемент уже добавлен в список
                new_subjects.append(None)
            elif pd.isna(
                    prev_subject) and i > 0:  # проверяем, что предыдущий элемент является nan и текущий элемент не является первым
                continue
            else:
                new_subjects.append(prev_subject)

        subjects = new_subjects
        print(subjects)

        teachers = df.iloc[11:row_index, column_index+4].tolist()
        print(teachers)

        auditors = df.iloc[11:row_index, column_index+6].tolist()
        print(auditors)
    elif day_of_week_ptk == 'Ср':
        row_index = 31

        subjects = df.iloc[21:row_index, column_index + 1].tolist()
        print(subjects)

        new_subjects = []
        prev_subject = None
        for i, subject in enumerate(subjects):
            if not pd.isna(subject):
                prev_subject = subject
            elif i == len(subjects) - 1 or (pd.isna(prev_subject) and new_subjects and new_subjects[
                -1] is not None):  # проверяем, что текущий элемент является последним или предыдущий элемент является nan и предыдущий не-nan элемент уже добавлен в список
                new_subjects.append(None)
            elif pd.isna(
                    prev_subject) and i > 0:  # проверяем, что предыдущий элемент является nan и текущий элемент не является первым
                continue
            else:
                new_subjects.append(prev_subject)

        subjects = new_subjects
        print(subjects)

        teachers = df.iloc[21:row_index, column_index+4].tolist()
        print(teachers)

        auditors = df.iloc[21:row_index, column_index+6].tolist()
        print(auditors)
    elif day_of_week_ptk == 'Чт':
        row_index = 41

        subjects = df.iloc[31:row_index, column_index + 1].tolist()
        print(subjects)

        new_subjects = []
        prev_subject = None
        for i, subject in enumerate(subjects):
            if not pd.isna(subject):
                prev_subject = subject
            elif i == len(subjects) - 1 or (pd.isna(prev_subject) and new_subjects and new_subjects[
                -1] is not None):  # проверяем, что текущий элемент является последним или предыдущий элемент является nan и предыдущий не-nan элемент уже добавлен в список
                new_subjects.append(None)
            elif pd.isna(
                    prev_subject) and i > 0:  # проверяем, что предыдущий элемент является nan и текущий элемент не является первым
                continue
            else:
                new_subjects.append(prev_subject)

        subjects = new_subjects
        print(subjects)

        teachers = df.iloc[31:row_index, column_index+4].tolist()
        print(teachers)

        auditors = df.iloc[31:row_index, column_index+6].tolist()
        print(auditors)
    elif day_of_week_ptk == 'Пт':
        row_index = 51

        subjects = df.iloc[41:row_index, column_index + 1].tolist()
        print(subjects)

        new_subjects = []
        prev_subject = None
        for i, subject in enumerate(subjects):
            if not pd.isna(subject):
                prev_subject = subject
            elif i == len(subjects) - 1 or (pd.isna(prev_subject) and new_subjects and new_subjects[
                -1] is not None):  # проверяем, что текущий элемент является последним или предыдущий элемент является nan и предыдущий не-nan элемент уже добавлен в список
                new_subjects.append(None)
            elif pd.isna(
                    prev_subject) and i > 0:  # проверяем, что предыдущий элемент является nan и текущий элемент не является первым
                continue
            else:
                new_subjects.append(prev_subject)

        subjects = new_subjects
        print(subjects)

        teachers = df.iloc[41:row_index, column_index+4].tolist()
        print(teachers)

        auditors = df.iloc[41:row_index, column_index+6].tolist()
        print(auditors)
    elif day_of_week_ptk == 'Сб':
        row_index = 65

        subjects = df.iloc[51:row_index, column_index + 1].tolist()
        print(subjects)

        new_subjects = []
        prev_subject = None
        for i, subject in enumerate(subjects):
            if not pd.isna(subject):
                prev_subject = subject
            elif i == len(subjects) - 1 or (pd.isna(prev_subject) and new_subjects and new_subjects[
                -1] is not None):  # проверяем, что текущий элемент является последним или предыдущий элемент является nan и предыдущий не-nan элемент уже добавлен в список
                new_subjects.append(None)
            elif pd.isna(prev_subject) and i > 0 and subjects[i - 1] == subjects[
                i - 2]:  # проверяем, что предыдущий элемент является nan и текущий элемент не является первым и предыдущий не-nan элемент повторяется
                continue
            else:
                new_subjects.append(prev_subject)

        subjects = new_subjects
        print(subjects)


        teachers = df.iloc[51:row_index, column_index+4].tolist()
        print(teachers)

        auditors = df.iloc[51:row_index, column_index+6].tolist()
        print(auditors)

if __name__ == '__main__':
    init_db()
    bot.polling()
