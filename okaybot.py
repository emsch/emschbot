import telebot
from telebot import types
from datetime import datetime
import random
import sqlite3

TOKEN = open('.private/TOKEN').read()
admin_id = 104663766
support_chat = -1001098463982
bot = telebot.TeleBot(TOKEN)


def report_error(e, other_info = ""):
    try:
        bot.send_message(admin_id, "Error:\n" + str(e))
    except Exception as e:
        print(e)

def make_query(*params):
    try:
        conn = sqlite3.connect('okay_db.db')
        c = conn.cursor()
        c.execute(*params)
        retur = c.fetchall()
        conn.commit()
        conn.close()
        return retur
    except Exception as e:
        report_error(e)

def prepare_db():
    make_query('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
    blocked BOOL default 0, telegram_id integer, telegram_nick string, surname string,
    name string, type STRING default 'student')''')

    make_query('''CREATE TABLE IF NOT EXISTS issues (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, person_id INTEGER,
    person_nick STRING, message STRING, time_created timestamp, solved BOOL default 0, whosolved_tel_id INTEGER, time_solved timestamp,
    solved_text string)''')



def check_user(message):
    try:
        tel_id = message.chat.id
        tel_nick = message.from_user.username
        surname = message.from_user.last_name
        name = message.from_user.first_name

        if(len(make_query('''select * from users where telegram_id = ? ''', (tel_id,))) == 0):
            make_query('''insert into users (telegram_id, telegram_nick, surname, name) 
            values (?, ?, ?, ?)''', (tel_id,tel_nick, surname, name, ))
            return True
        else:
            return  1 - make_query('''select blocked from users where telegram_id = ? ''', (tel_id,))[0][0]

    except Exception as e:
        report_error(e)
        
def send_to_staff(message):
    try:
        keyboard = types.InlineKeyboardMarkup()
        callback_bt1 = types.InlineKeyboardButton(text="Решено", callback_data="solved")
        callback_bt2 = types.InlineKeyboardButton(text="Блокировать", callback_data="block")
        keyboard.add(callback_bt1, callback_bt2)
        te = make_query('''select issues.id, users.telegram_nick message, users.surname, users.name, 
    issues.message from issues left join users on users.telegram_id = issues.person_id order by issues.id desc limit 1''' )[0]
        text = "<b>Ticket {}</b>\n{} {}\n@{}\n\n<i>{}</i>".format(te[0], te[2], te[3], te[1], te[4])
        bot.send_message(support_chat, text, parse_mode='HTML', reply_markup = keyboard)
    except Exception as e:
        report_error(e)


def reply_issue(i, text):
    try:
        issue = make_query('''select * from issues where id = ?''', (i, ))[0]
        chat_id = issue[1]
        issue_text = issue[3]
        text = "Ваше обращение:\n<i>{}</i>\nбыло рассмотрено. Ответ:\n<i>{}</i>".format(issue_text, text)
        bot.send_message(chat_id, text, parse_mode='HTML')
    except Exception as e:
        report_error(e)
    
@bot.message_handler(commands=['help'])
def help(message):
    try:
        help_text = '''
            Это бот, который может вам помочь... Дописать текст help...
    '''
        bot.send_message(message.chat.id, help_text, parse_mode = 'Markdown')
    except Exception as e:
        report_error(e)


@bot.message_handler(commands=['start'])
def start(message):
    try:
        start_text = '''
            Это бот, который может вам помочь... Дописать текст start...
    '''
        bot.send_message(message.chat.id, start_text, parse_mode = 'Markdown')    
    
    except Exception as e:
        report_error(e)
        
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    #print(call)
    if(call.data == 'solved'):
        ticket_id = int(call.message.text.split('\n')[0].split()[1])
        make_query("update issues set solved = 1, time_solved = ?, whosolved_tel_id = ?, solved_text = 'by_button' where id = ?", 
          (datetime.now(), call.from_user.id, ticket_id))
    
    if(call.data == 'block'):
        print('block')
        ticket_id = int(call.message.text.split('\n')[0].split()[1])
        person_tel_id = make_query("select person_id from issues where id = ?", (ticket_id, ))[0][0]
        print(person_tel_id)
        make_query("update users set blocked = 1 where telegram_id = ?", (person_tel_id, )) 
    
@bot.message_handler(func = lambda message: True)
def echo(message):
    if(message.chat.type == 'private' and check_user(message)):
        reply_text = 'Спасибо за обращение!\nМы постараемся решить Вашу проблему как можно скорее'
        bot.send_message(message.chat.id, reply_text, parse_mode = 'Markdown')
        make_query('''insert into issues (person_id, person_nick, message, time_created) values (?, ?, ?, ?)''', 
                   (message.chat.id, message.from_user.username, message.text, datetime.now()), )
        send_to_staff(message)
    
    elif(message.chat.id == support_chat):
        i = int(message.reply_to_message.text.split('\n')[0].split()[1])
        t = make_query('''select  * from issues where id = ?''', (i, ))[0]
        reply_issue (i, message.text)
        make_query('''update issues set solved = 1, whosolved_tel_id = ?, time_solved = ?, solved_text = ? where id = ?''', 
                   (a.from_user.id, datetime.now(),  message.text, i, ))
        # print(message)

    
def main():
    prepare_db()
    bot.polling(none_stop = True, interval = 1)
    
if __name__ == '__main__':
    main()