import pandas as pd
import requests
import telebot
from bs4 import BeautifulSoup as BS
import tempfile
import os
import types
import asyncio
import aiohttp
from io import BytesIO
import xlrd
import pandas as pd
import re
from telebot import types

TOKEN = "6848210471:AAE98dRIf47eLHGfgqKFPN78TlXbKJKZClI"
bot = telebot.TeleBot(TOKEN)


group_student = None
day_of_week = None
week_type = None
college = None
course = None
group = None

def get_file_schedule_PTK(group_student):
    # Отправить HTTP-запрос на сайт и получить HTML-код страницы
    url = 'https://portal.novsu.ru/univer/timetable/spo/'
    response = requests.get(url)
    html = response.text

    # Использовать BeautifulSoup для парсинга HTML-кода страницы
    soup = BS(html, 'html.parser')

#    print(group_student)
    link = soup.find('a', string=group_student)
 #   print('link done')
#    print(link)
    link_href = link['href']
 #   print('link_href done')
 #   print(link_href)
    file_url = f"https://portal.novsu.ru/{link_href}"
 #   print(file_url)

    # Отправить HTTP-запрос на сайт и получить файл
    response = requests.get(file_url)

    # Создать временный файл
    with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
        # Записать содержимое файла в временный файл
        tmp_file.write(response.content)
        tmp_file.seek(0)  # сбросить указатель файла в начало

        # Прочитать файл с помощью pandas
        df = pd.read_excel(tmp_file)
    return df



@bot.message_handler(commands=['start'])
def main_menu(message):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_geolacation = types.KeyboardButton('Узнать геопозицию')
    item_schedule = types.KeyboardButton('Узнать расписание')
    markup_replay.add(item_schedule, item_geolacation)
    bot.send_message(message.chat.id, 'Привет! Что вы хотите узнать?', reply_markup=markup_replay)


user_context = {}
group = ['3781', '3782', '3791', '3792', '3911', '3912', '3913', '3914', '3921', '3951', '3952', '3953', '3954', '3955',
         '3981', '3982', '3983', '3990', '3991', '3992', '3993', '3994', '3995', '3996', '3861', '3971', '3972', '3973',
         '2781', '2782', '2791', '2792', '2911', '2912', '2913', '2921', '2951', '2952', '2953', '2981', '2982', '2983',
         '2991', '2992', '2993', '2994', '2995', '2996', '2861', '2862', '2863', '2971', '1791', '1792', '1911', '1921',
         '1951', '1952', '1981', '1991', '1992', '1994', '1861', '1862', '1971', '0901', '0902', '0911', '0921', '0931',
         '0941', '0951', '0952', '0861']
day = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

@bot.message_handler(content_types=['text'])
def bot_massage(message):
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
            markup_replay.add(item_glav, item_ptk, item_anton, item_itys, item_ibhi, item_med, item_ped, item_back)
            bot.send_message(message.chat.id, 'Выберите интересующий институт', reply_markup=markup_replay)

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
            bot.send_message(message.chat.id, '🏫Какой колледж вас интересует?', reply_markup=markup_replay)

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
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_3781 = types.KeyboardButton('3781')
                item_3782 = types.KeyboardButton('3782')
                item_3791 = types.KeyboardButton('3791')
                item_3792 = types.KeyboardButton('3792')
                item_3911 = types.KeyboardButton('3911')
                item_3912 = types.KeyboardButton('3912')
                item_3913 = types.KeyboardButton('3913')
                item_3914 = types.KeyboardButton('3914')
                item_3921 = types.KeyboardButton('3921')
                item_3951 = types.KeyboardButton('3951')
                item_3952 = types.KeyboardButton('3952')
                item_3953 = types.KeyboardButton('3953')
                item_3954 = types.KeyboardButton('3954')
                item_3955 = types.KeyboardButton('3955')
                item_3981 = types.KeyboardButton('3981')
                item_3982 = types.KeyboardButton('3982')
                item_3983 = types.KeyboardButton('3983')
                item_3990 = types.KeyboardButton('3990')
                item_3991 = types.KeyboardButton('3991')
                item_3992 = types.KeyboardButton('3992')
                item_3993 = types.KeyboardButton('3993')
                item_3994 = types.KeyboardButton('3994')
                item_3995 = types.KeyboardButton('3995')
                item_3996 = types.KeyboardButton('3996')
                item_back = types.KeyboardButton('Главное меню')
                global group_student
                group_student = message.text
                markup_replay.add(item_3781, item_3782, item_3791, item_3792, item_3911, item_3912, item_3913,
                                  item_3914, item_3921, item_3951, item_3952, item_3953, item_3954, item_3955,
                                  item_3981, item_3982, item_3983, item_3990, item_3991, item_3992, item_3993,
                                  item_3994, item_3995, item_3996, item_back)
                bot.send_message(message.chat.id, '📝Выберите свою группу', reply_markup=markup_replay)



            elif current_context == 'СПО ИНПО':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_3861 = types.KeyboardButton('3861')
                item_3971 = types.KeyboardButton('3971')
                item_3972 = types.KeyboardButton('3972')
                item_3973 = types.KeyboardButton('3973')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_3861, item_3971, item_3972, item_3973, item_back)
                bot.send_message(message.chat.id, '📝Выберите свою группу', reply_markup=markup_replay)


        elif message.text == '2 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_2781 = types.KeyboardButton('2781')
                item_2782 = types.KeyboardButton('2782')
                item_2791 = types.KeyboardButton('2791')
                item_2792 = types.KeyboardButton('2792')
                item_2911 = types.KeyboardButton('2911')
                item_2912 = types.KeyboardButton('2912')
                item_2913 = types.KeyboardButton('2913')
                item_2921 = types.KeyboardButton('2921')
                item_2951 = types.KeyboardButton('2951')
                item_2952 = types.KeyboardButton('2952')
                item_2953 = types.KeyboardButton('2953')
                item_2981 = types.KeyboardButton('2981')
                item_2982 = types.KeyboardButton('2982')
                item_2983 = types.KeyboardButton('2983')
                item_2991 = types.KeyboardButton('2991')
                item_2992 = types.KeyboardButton('2992')
                item_2993 = types.KeyboardButton('2993')
                item_2994 = types.KeyboardButton('2994')
                item_2995 = types.KeyboardButton('2995')
                item_2996 = types.KeyboardButton('2996')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_2781, item_2782, item_2791, item_2792, item_2911, item_2912, item_2913,
                                  item_2921, item_2951, item_2952, item_2953, item_2981, item_2982, item_2983,
                                  item_2991, item_2992, item_2993, item_2994, item_2995, item_2996, item_back)
                bot.send_message(message.chat.id, '📝Выберете свою группу.', reply_markup=markup_replay)

            elif current_context == 'СПО ИНПО':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_2861 = types.KeyboardButton('2861')
                item_2862 = types.KeyboardButton('2862')
                item_2863 = types.KeyboardButton('2863')
                item_2971 = types.KeyboardButton('2971')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_2861, item_2862, item_2863, item_2971, item_back)
                bot.send_message(message.chat.id, 'Выберете свою группу.', reply_markup=markup_replay)


        elif message.text == '3 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_1791 = types.KeyboardButton('1791')
                item_1792 = types.KeyboardButton('1792')
                item_1911 = types.KeyboardButton('1911')
                item_1921 = types.KeyboardButton('1921')
                item_1951 = types.KeyboardButton('1951')
                item_1952 = types.KeyboardButton('1952')
                item_1981 = types.KeyboardButton('1981')
                item_1991 = types.KeyboardButton('1991')
                item_1992 = types.KeyboardButton('1992')
                item_1994 = types.KeyboardButton('1994')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_1791, item_1792, item_1911, item_1921, item_1951, item_1952, item_1981,
                                  item_1991, item_1992, item_1994, item_back)
                bot.send_message(message.chat.id, '📝Выберете свою группу.', reply_markup=markup_replay)

            elif current_context == 'СПО ИНПО':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_1861 = types.KeyboardButton('2861')
                item_1862 = types.KeyboardButton('2862')
                item_1971 = types.KeyboardButton('2971')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_1861, item_1862, item_1971, item_back)
                bot.send_message(message.chat.id, '📝Выберете свою группу.', reply_markup=markup_replay)


        elif message.text == '4 курс':
            current_context = user_context.get(message.chat.id)
            if current_context == 'ПТК':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_0901 = types.KeyboardButton('0901')
                item_0902 = types.KeyboardButton('0902')
                item_0911 = types.KeyboardButton('0911')
                item_0921 = types.KeyboardButton('0921')
                item_0931 = types.KeyboardButton('0931')
                item_0941 = types.KeyboardButton('0941')
                item_0951 = types.KeyboardButton('0951')
                item_0952 = types.KeyboardButton('0952')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_0901, item_0902, item_0911, item_0921, item_0931, item_0941, item_0951,
                                  item_0952, item_back)
                bot.send_message(message.chat.id, 'Выберете свою группу.', reply_markup=markup_replay)

            elif current_context == 'СПО ИНПО':
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_0861 = types.KeyboardButton('0861')
                item_back = types.KeyboardButton('Главное меню')
                group_student = message.text
                markup_replay.add(item_0861, item_back)
                bot.send_message(message.chat.id, 'Выберете свою группу.', reply_markup=markup_replay)


        elif message.text == 'Мед.колледж':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            '''item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')'''
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, 'В разработке.', reply_markup=markup_replay)

        elif message.text == 'СПО ИЦЭУС':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            '''item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')'''
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, 'В разработке.', reply_markup=markup_replay)

        elif message.text == 'СПО ИЮР':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            '''item_1 = types.KeyboardButton('1 курс')
            item_2 = types.KeyboardButton('2 курс')
            item_3 = types.KeyboardButton('3 курс')
            item_4 = types.KeyboardButton('4 курс')'''
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, 'В разработке.', reply_markup=markup_replay)

        elif message.text == 'Главное меню':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_geolacation = types.KeyboardButton('Узнать геопозицию')
            item_schedule = types.KeyboardButton('Узнать расписание')
            markup_replay.add(item_schedule, item_geolacation)
            bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup_replay)


        elif message.text.isdigit():
            if message.text in group:
                group_student = message.text
                markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item_pn = types.KeyboardButton('Верхняя')
                item_vt = types.KeyboardButton('Нижняя')
                item_back = types.KeyboardButton('Главное меню')
                markup_replay.add(item_pn, item_vt, item_back)
                bot.send_message(message.chat.id, '❗️ Выберите неделю', reply_markup=markup_replay)
            else:
                bot.send_message(message.chat.id, 'Такой группы несуществует!')

        elif message.text == 'Верхняя':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_pn = types.KeyboardButton('Пн')
            item_vt = types.KeyboardButton('Вт')
            item_sr = types.KeyboardButton('Ср')
            item_ch = types.KeyboardButton('Чт')
            item_pt = types.KeyboardButton('Пт')
            item_sb = types.KeyboardButton('Сб')
            item_back = types.KeyboardButton('Главное меню')
            global week_type
            week_type = message.text
            markup_replay.add(item_pn, item_vt, item_sr, item_ch, item_pt, item_sb, item_back)
            bot.send_message(message.chat.id, '📅 Выберите день недели', reply_markup=markup_replay)

        elif message.text == 'Нижняя':
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_pn = types.KeyboardButton('Пн')
            item_vt = types.KeyboardButton('Вт')
            item_sr = types.KeyboardButton('Ср')
            item_ch = types.KeyboardButton('Чт')
            item_pt = types.KeyboardButton('Пт')
            item_sb = types.KeyboardButton('Сб')
            week_type = message.text
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_pn, item_vt, item_sr, item_ch, item_pt, item_sb, item_back)
            bot.send_message(message.chat.id, '📅 Выберите день недели', reply_markup=markup_replay)

        elif message.text in day:
            day_of_week = message.text
            print(college)
            if college == 'ПТК':
                schedule = get_schedule_ptk(group_student, day_of_week, week_type)
                bot.send_message(message.chat.id, f'Расписание на {day_of_week}, неделя - {week_type}, группа -  {group_student}:\n' + '\n'.join(schedule))
            elif college == 'СПО ИНПО':
                print('ИНПО')

        else:
            markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item_back = types.KeyboardButton('Главное меню')
            markup_replay.add(item_back)
            bot.send_message(message.chat.id, '⚠️Извините, я вас не понимаю.\nСледуйте кнопкам меню!⚠️',
                             reply_markup=markup_replay)


def find_distance(group_student, day_of_week):
    df = get_file_schedule_PTK(group_student)

    # Найти индекс столбца, содержащего дни недели
    col_index = next((col for col in df.columns if any(day in df[col].values for day in ['ПОНЕДЕЛЬНИК', 'ВТОРНИК', 'СРЕДА', 'ЧЕТВЕРГ', 'ПЯТНИЦА', 'СУББОТА'])), None)
    print("col_index --> " + col_index)
    # Найти индексы строк, содержащих дни недели
    days_of_week = {'ПН': 'ПОНЕДЕЛЬНИК', 'ВТ': 'ВТОРНИК', 'СР': 'СРЕДА', 'ЧТ': 'ЧЕТВЕРГ', 'ПТ': 'ПЯТНИЦА', 'СБ': 'СУББОТА'}
    day_indices = {day: [] for day in days_of_week.values()}

    for index, value in enumerate(df[col_index]):
        if value in days_of_week.values():
            day_indices[value].append(index)

    if day_of_week.upper() in days_of_week:
        current_day = days_of_week[day_of_week.upper()]
        next_day = days_of_week.get(get_next_weekday(day_of_week.upper()), None)

        if next_day is not None:
            if len(day_indices[current_day]) > 0 and len(day_indices[next_day]) > 0:
                distance = day_indices[next_day][0] - day_indices[current_day][-1]
                return distance

def get_next_weekday(day):
    days_of_week = ['ПН', 'ВТ', 'СР', 'ЧТ', 'ПТ', 'СБ']
    current_day_index = days_of_week.index(day)
    return days_of_week[(current_day_index + 1) % len(days_of_week)]


def remove_lek_from_info(info):
    if isinstance(info, str) and ',' in info:
        parts = info.split(', ')
        if len(parts) > 3:
            return ', '.join(parts[:3])
    return info


def get_schedule_ptk(group_student, day_of_week, week_type):
    df = get_file_schedule_PTK(group_student)

    day_of_week_values = {'Пн': 'ПОНЕДЕЛЬНИК', 'Вт': 'ВТОРНИК', 'Ср': 'СРЕДА', 'Чт': 'ЧЕТВЕРГ', 'Пт': 'ПЯТНИЦА',
                          'Сб': 'СУББОТА'}
    row_index = None
    for row_idx, row in df.iterrows():
        for col_idx, cell in enumerate(row):
            if cell == day_of_week_values.get(day_of_week):
                row_index = row_idx
                break
        if row_index is not None:
            break



#    print(day_of_week)
#    print(group_student)
    # Искать номер группы в файле
    column_index = None
    for column_index, column_name in enumerate(df.columns):
        if group_student in df[column_name].values:
            break


#    print(column_index,row_index)

    schedule = []

    for i in range(find_distance(group_student,day_of_week)):
        time = df.iloc[row_index + i, column_index - 1]
        info = df.iloc[row_index + i, column_index]
        timeN = df.iloc[row_index + i - 1, column_index - 1]
        info = remove_lek_from_info(info)
        print(info)
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
                        f' Группа 1: \n ⏰Время: {time} \n 👨‍🏫Преподаватель: {teacher1} \n 📝Аудитория: {audience1}\n\n' +
                        f' Группа 2: \n ⏰Время: {time} \n 👨‍🏫Преподаватель: {teacher2} \n 📝Аудитория: {audience2}\n\n')


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



    for i, elem in enumerate(schedule):
        if ' - только по нижней неделе' in elem:
            schedule[i - 1] = schedule[i - 1].rstrip('\n\n')
            schedule[i - 1] += ' - только по верхней неделе \n'


    for i, elem in enumerate(schedule):
        if week_type == 'Верхняя':
            if ' - только по нижней неделе' in elem:
                del schedule[i]
        elif week_type == 'Нижняя':
            if ' - только по верхней неделе' in elem:
                del schedule[i]

    return schedule

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
    bot.polling()