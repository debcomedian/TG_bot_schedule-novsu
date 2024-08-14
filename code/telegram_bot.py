import telebot
import requests

from telebot import types
from bs4 import BeautifulSoup as BS

from code.db import Database
from code.menu_handler import *
from code.config import get_telegram_token
from code.schedule import init_schedule_ptk, get_schedule_ptk, init_send_schedule

STATE_MAIN_MENU = 'main_menu'
STATE_SELECTING_LOCATION = 'selecting_location'
STATE_SELECTING_SCHEDULE = 'selecting_schedule'
STATE_SELECTING_COURSE = 'selecting_course'
STATE_SELECTING_GROUP = 'selecting_group'
STATE_SELECTING_WEEK_TYPE = 'selecting_week_type'
STATE_SELECTING_DAY = 'selecting_day'

bot = telebot.TeleBot(get_telegram_token())

days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

user_context = {}
group = []

cur = None
group_student = None
day_of_week = None
week_type = None
college = None

def init_list_group(first_group_number, college, list_group):
    course = 1
    for num_group in list_group:
        temp = int(num_group) // 1000
        if (first_group_number != temp):
            course += 1
            first_group_number = temp

        Database.execute_query(f"INSERT INTO groups_students_{college} (group_course, group_id) VALUES (%s, %s)"
                               , (course, num_group))


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
    while first_group_number > 9:
        first_group_number %= 10
    init_list_group(first_group_number, 'ptk', list_group_ptk)
    init_list_group(first_group_number, 'pedcol', list_group_pedcol)
    init_list_group(first_group_number, 'medcol', list_group_medcol)
    init_list_group(first_group_number, 'spour', list_group_spour)
    init_list_group(first_group_number, 'spoinpo', list_group_spoinpo)

def init_get_list_group(college):
    
    temp = Database.execute_query(f'SELECT group_id FROM groups_students_{college}', fetch=True)
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


@bot.message_handler(content_types=['text'])
def bot_message(message):
    global group, group_student, week_type, college
    
    # Инициализация контекста как словаря
    if message.chat.id not in user_context:
        user_context[message.chat.id] = {'state': STATE_MAIN_MENU}

    user_data = user_context[message.chat.id]
    current_state = user_data.get('state', STATE_MAIN_MENU)
    
    switch = {
        STATE_MAIN_MENU: {
            'Узнать геопозицию': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_SELECTING_LOCATION, handle_geolocation),
            'Узнать расписание': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_SELECTING_SCHEDULE, handle_schedule_request),
            'Главное меню': lambda msg: handle_main_menu(bot, msg),
        },
        STATE_SELECTING_LOCATION: {
            'Главный корпус': lambda msg: handle_location(bot, msg, 58.542306, 31.261174, '📍Местоположение Главного корпуса: Большая Санкт-Петербургская, 41'),
            'Политехнический колледж': lambda msg: handle_location(bot, msg, 58.541668, 31.264534, '📍Местоположение ПТК: Большая Санкт-Петербургская, 46'),
            'Антоново': lambda msg: handle_location(bot, msg, 58.541079, 31.288108, '📍Местоположение ИГУМ: район Антоново, 1'),
            'ИЦЭУС': lambda msg: handle_location(bot, msg, 58.522347, 31.258228, '📍Местоположение ИЦЭУС: Псковская улица, 3'),
            'ИМО': lambda msg: handle_location(bot, msg, 58.542809, 31.310567, '📍Местоположение ИМО: улица Державина, 6'),
            'ИБХИ': lambda msg: handle_location(bot, msg, 58.551745, 31.300628, '📍Местоположение ИБХИ: улица Советской Армии, 7'),
            'ПИ': lambda msg: handle_location(bot, msg, 58.523945, 31.262243, '📍Местоположение ПИ: улица Черняховского, 64/6'),
            'Главное меню': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_MAIN_MENU, handle_main_menu),
        },
        STATE_SELECTING_SCHEDULE: {
            'ПТК': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_COURSE, handle_college_selection, 'ptk', generate_course_menu),
            'СПО ИНПО': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_COURSE, handle_college_selection, 'spoinpo', generate_course_menu),
            'Мед.колледж': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_COURSE, handle_college_selection, 'medcol', generate_course_menu),
            'СПО ИЦЭУС': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_COURSE, handle_college_selection, 'pedcol', generate_course_menu),
            'СПО ИЮР': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_COURSE, handle_college_selection, 'spour', generate_course_menu),
            'Главное меню': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_MAIN_MENU, handle_main_menu),
        },
        STATE_SELECTING_COURSE: {
            '1 курс': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),
            '2 курс': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),
            '3 курс': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),
            '4 курс': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),
            '5 курс': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),
            '6 курс': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),
            'Назад': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_SELECTING_SCHEDULE, handle_schedule_request),
            'Главное меню': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_MAIN_MENU, handle_main_menu),
        },
        STATE_SELECTING_GROUP: {
            **{grp: lambda msg, group=grp: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_WEEK_TYPE, handle_group_selection, group) for grp in group},
            'Назад': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_COURSE, handle_college_selection, user_data.get('college'), generate_course_menu),
            'Главное меню': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_MAIN_MENU, handle_main_menu),
        },
        STATE_SELECTING_WEEK_TYPE: {
            'Верхняя': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_DAY, handle_week_selection, 'Верхняя'),
            'Нижняя': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_DAY, handle_week_selection, 'Нижняя'),
            'Назад': lambda msg: handle_show_groups(bot, user_context, user_data, msg, STATE_SELECTING_GROUP),  
            'Главное меню': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_MAIN_MENU, handle_main_menu),
        },
        STATE_SELECTING_DAY: {
            **{day: lambda msg, d=day: handle_display_schedule(bot, msg, user_data.get('group'), user_data.get('week_type'), d, get_schedule_ptk) for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']}, 
            'Назад': lambda msg: handle_transition_with_context(bot, user_context, msg, STATE_SELECTING_WEEK_TYPE, handle_group_selection, user_data.get('group')),
            'Главное меню': lambda msg: handle_transition_no_context(bot, user_context, msg, STATE_MAIN_MENU, handle_main_menu),
        },
    }
    handler = switch.get(current_state, {}).get(message.text, lambda msg: handle_unknown(bot, user_context, msg, STATE_MAIN_MENU))
    handler(message)

def bot_send_location_and_message(bot, message, latitude, longitude, str):
    bot.send_location(message.chat.id, latitude, longitude)
    bot.send_message(message.chat.id, str)

def fetch_group_ids(college, group_list):
    temp = Database.execute_query(f'SELECT group_id FROM groups_students_{college}', fetch=True)
    
    for item in temp:
        group_list.append(item[0])
    
def fetch_college_courses(college):
    temp = Database.execute_query(f'SELECT DISTINCT group_course FROM groups_students_{college}', fetch=True)
    course_list = []
    
    for item in temp:
        course_list.append(item[0])
    return course_list

def generate_course_menu(college):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    course_list = sorted(fetch_college_courses(college))
    
    for course in course_list:
        markup_replay.add(types.KeyboardButton(f'{course} курс'))
    
    item_main = types.KeyboardButton('Главное меню')
    item_back = types.KeyboardButton('Назад')
    markup_replay.add(item_back).add(item_main)
    return markup_replay

def init_schedule(soup):
    for number_group in group:
        link = soup.find('a', string=number_group)  
        if (link):
            link_href = link['href']
            file_url = f"https://portal.novsu.ru/{link_href}"
            response = requests.get(file_url)
            print(number_group)
            
            Database.rebuild_group_table(number_group)
            
            for day in days:
                schedule = init_schedule_ptk(number_group, day, response.content)
                if schedule != []:
                    init_send_schedule(schedule, number_group, day, "Верхняя")
                    init_send_schedule(schedule, number_group, day, "Нижняя")
    
def main():
    global cur
    
    url = 'https://portal.novsu.ru/univer/timetable/spo/'
    Database.rebuild_db()
    
    response = requests.get(url)
    html = response.text

    soup = BS(html, 'html.parser')

    init_list_groups(soup)

    init_get_list_group('ptk')
    init_get_list_group('pedcol')
    init_get_list_group('medcol')
    init_get_list_group('spour')
    init_get_list_group('spoinpo')

    fetch_group_ids('pedcol', group)
    fetch_group_ids('medcol', group)
    fetch_group_ids('spour', group)
    fetch_group_ids('spoinpo', group)
    
    init_schedule(soup)
    
    bot.polling()

if __name__ == '__main__':
    main()