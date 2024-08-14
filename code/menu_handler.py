from telebot import types

from code.db import Database

def handle_geolocation(bot, message):
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

def handle_location(bot, message, latitude, longitude, location_message):
    bot.send_location(message.chat.id, latitude, longitude)
    bot.send_message(message.chat.id, location_message)

def handle_schedule_request(bot, message):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_PTK = types.KeyboardButton('ПТК')
    item_MED = types.KeyboardButton('Мед.колледж')
    item_EKO = types.KeyboardButton('СПО ИЦЭУС')
    item_IUR = types.KeyboardButton('СПО ИЮР')
    item_PED = types.KeyboardButton('СПО ИНПО')
    item_main = types.KeyboardButton('Главное меню')
    markup_replay.add(item_PTK, item_PED, item_IUR, item_MED, item_EKO).add(item_main)
    bot.send_message(message.chat.id, '🏫Какой колледж вас интересует?', reply_markup=markup_replay)

def handle_college_selection(bot, user_context, message, college_code, generate_course_menu):
    user_context[message.chat.id]['college'] = college_code
    markup_replay = generate_course_menu(college_code)
    bot.send_message(message.chat.id, '❓ Какой вы курс?', reply_markup=markup_replay)

def handle_course_selection(bot, user_context, message, course, show_groups):
    current_context = user_context.get(message.chat.id, {})
    current_context['course'] = course
    selected_college = current_context.get('college')
    if selected_college == 'ptk':
        show_groups(message, 'groups_students_ptk')
    elif selected_college == 'spoinpo':
        show_groups(message, 'groups_students_spoinpo')

def handle_show_groups(bot, user_context, user_data, message, next_state):
    user_context[message.chat.id]['state'] = next_state
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if message.text[0].isdigit():
        user_data['course'] = message.text[0]  
        user_context[message.chat.id] = user_data
    
    course = user_data.get('course')
    college = user_data.get('college')
    
    conn = Database.get_connection()
    try:
        temp = Database.execute_query("SELECT group_id FROM groups_students_{} WHERE group_course=%s".format(college), (course,), fetch=True)
        
        temp_items = []
        for item in temp:
            temp_items.append(types.KeyboardButton(item[0]))
        
        markup_replay.add(*temp_items)
    finally:
        conn.close()
        
    markup_replay.add(types.KeyboardButton('Назад')).add(types.KeyboardButton('Главное меню'))
    bot.send_message(message.chat.id, '📝Выберите свою группу', reply_markup=markup_replay)


def handle_group_selection(bot, user_context, message, group):
    user_context[message.chat.id]['group'] = group
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_replay.add(types.KeyboardButton('Верхняя'), types.KeyboardButton('Нижняя'))
    markup_replay.add(types.KeyboardButton('Назад')).add(types.KeyboardButton('Главное меню'))
    bot.send_message(message.chat.id, '❓ Выберите тип недели', reply_markup=markup_replay)

def handle_week_selection(bot, user_context, message, week_type):
    user_context[message.chat.id]['week_type'] = week_type
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_replay.add(*[types.KeyboardButton(day) for day in ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']])
    markup_replay.add(types.KeyboardButton('Назад')).add(types.KeyboardButton('Главное меню'))
    bot.send_message(message.chat.id, '📅 Выберите день недели', reply_markup=markup_replay)

def handle_display_schedule(bot, message, group, week_type, day, get_schedule_ptk):
    schedule = get_schedule_ptk(group, day, week_type)
    if schedule:
        bot.send_message(message.chat.id, f'Расписание на {day}, неделя - {week_type}, группа - {group}:\n' + '\n'.join(schedule))
    else:
        bot.send_message(message.chat.id, 'Нет занятий')

def handle_main_menu(bot, message):
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_geolacation = types.KeyboardButton('Узнать геопозицию')
    item_schedule = types.KeyboardButton('Узнать расписание')
    markup_replay.add(item_schedule, item_geolacation)
    bot.send_message(message.chat.id, 'Главное меню', reply_markup=markup_replay)

def handle_unknown(bot, user_state, message, STATE_MAIN_MENU):
    current_state = user_state.get(message.chat.id, {}).get('state', STATE_MAIN_MENU)
    markup_replay = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if current_state != STATE_MAIN_MENU:
        item_back = types.KeyboardButton('Назад')
        markup_replay.add(item_back)
    item_main_menu = types.KeyboardButton('Главное меню')
    markup_replay.add(item_main_menu)
    
    bot.send_message(message.chat.id, '⚠️Извините, я вас не понимаю.\nCлeдyйтe кнопкам меню!⚠️',
                     reply_markup=markup_replay)

def handle_transition_with_context(bot, user_context, message, next_state, handler, *args):
    user_context[message.chat.id]['state'] = next_state
    handler(bot, user_context, message, *args)

def handle_transition_no_context(bot, user_context, message, next_state, handler, *args):
    user_context[message.chat.id]['state'] = next_state
    handler(bot, message, *args)
