#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import time
import MySQLdb
import sys
import webbrowser
import os
from pocketsphinx import LiveSpeech, get_model_path

command = ''  # текущая команда
state = "Инициализация"  # текущее состояние
p_command = ''  # предыдущая команда
p_state = ''  # предыдущее состояние
grammar = "терминал"  # текущая грамматика
message = "Скажите Терминал для начала работы"  # сообщение пользователю
variable = ""  # переменная для формирования ссылки

# путь к русской акустической модели

model_path = get_model_path()


# *функция работы с базой данных*
# *на вход команда и состояние*
# *на выход массив с результатами запроса*

def request(com, st):
    #print "Команда: ", com
    #print "Состояние: ", st
    con = None
    try:

    # подключение к базе данных

        con = MySQLdb.connect('localhost', 'user', '11111111', 'diplom')
        cur = con.cursor()
        cur.execute('SET NAMES `utf8`')

    # выполнение запроса

        request_string = \
            "SELECT previous_command, previous_state, follow_state, grammar, link, message, variables  FROM commands WHERE command='" \
            + com + "' AND " + "state='" + st + "'"
        cur.execute(request_string)
        arr = []
        while True:
            row = cur.fetchone()
        # print "массив ", row
            if row == None:
                break

        # Предыдущая команда - row[0], 
        # Предыдущее состояние - row[1], 
        # Следующее состояние - row[2], 
        # Грамматика - row[3], 
        # Ссылка - row[4], 
        # Сообщение - row[5], 
        # Переменные - row[6]

            arr = [
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6]
                ]
    except MySQLdb.DatabaseError, e:
        if con:
            con.rollback()

        print 'Error %s' % e
        sys.exit(1)
    finally:

        if con:
            con.close()
    return arr


# *функция переконфигурирования PocketSphinx*

def configuration():
    try:
        speech = LiveSpeech(
            verbose=False,
            sampling_rate=16000,
            buffer_size=2048,
            no_search=False,
            full_utt=False,
            hmm=os.path.join(model_path, 'ru-ru'),
            lm=False,
            jsgf='terminal.gram',
            dic=os.path.join(model_path, 'ru.dic'),
            )
        return speech
    except:
        print "Ошибка! Несоответствие грамматики и словаря"
        exit(0)


# *функция записи в файл грамматики*
# *на вход строка с грамматикой*

def write_in_file(gram):
    f = open('terminal.gram', 'w')
    f.write('''#JSGF V1.0;
grammar PI;
public <cmd> = (''' + gram + ' | выход);'
            )
    f.close

# *функция определения номера факультета или курса*
# *на вход команда*
# *на выход значение переменной*

def faculty(com):
    if com ==    "первый":
        return 1
    elif com  == "второй":
        return 2
    elif com  == "третий":
        return 3
    elif com  == "четвёртый":
        return 4
    elif com  == "пятый":
        return 5
    elif com  == "шестой":
        return 6   

# *функция определения номера группы*
# *на вход команда*
# *на выход значение переменной*

def group(com):
    f = open('groups')
    for line in f:
        if (line.find(com)==0):
            return (line[len(com)+1:len(line)])  

# обновление файла грамматики

write_in_file(grammar.lower())

# переконфигурирование PocketSphinx

p = configuration()
temp_state = state

while True:

    # вывод сообщения пользователю

    mess = 'notify-send ' + '"' + message + '"'
    subprocess.call(mess, shell=True)

    # подача звукового сигнала

    subprocess.call('mpg123 -q Sound.wav', shell=True)

    # идентификация команды

    for phrase in p:
        #print 'LINE:', phrase
        #print 'prob: ', phrase.probability()
        command = str(phrase)
        break
    # обработка команды
    # при команде "назад" используем в качестве первичного ключа предыдущие состояние и команду
    if (command == 'назад'):
        if (state == "Расписание-факультет"):
            # очищаем variable
            variable='' 
        elif (state == "Расписание-курс"):
            variable=''  
        elif state == "Сон":
            # удаляем информацию о курсе
            variable = variable[0:variable.find('&')]
        elif state == "Инициализация":
            # удаляем информацию о группе
            variable = variable[0:variable.rfind('&')]
        mass_request = request(p_command, p_state) 
        print "variable: ", variable
        
    elif (command == 'выход'):
        # при команде "выход" выходим из программы
        print "Команда \"Выход\". Закрытие программы."
        exit()
    else:
        if (state == "Инициализация"):
            variable = "" 
        if (state == "Расписание-факультет"):
            variable = "?" + variable + "=" + str(faculty(command)) 
            print "variable: ", variable
            mass_request = request("выбор курса", state)  

        elif (state == "Расписание-курс"):
            variable = variable + "=" + str(faculty(command)) 
            print "variable: ", variable
            mass_request = request("выбор группы", state)

        elif (state == "Сон"):
            variable = variable + "=" + str(group(command))
            print "variable: ", variable
            mass_request = request("сон", state)

        else:
            # иначе используем текущие состояние и команду
            mass_request = request(str(command), state)  
    print "Команда: ", command
    print "Состояние: ", state
    try:

        # заполнение переменных
        # изменяем состояние
        state = mass_request[2]

        # изменяем предыдущее состояние
        p_state = mass_request[1]

        # сохраняем предыдущую команду
        p_command = mass_request[0]

        # изменяем грамматику
        grammar = mass_request[3]

        # открываем ссылку в браузере
        if mass_request[4] != 'No':
            webbrowser.open(mass_request[4] + variable, new=0)
        message = mass_request[5]

        # изменяем переменную 
        if (mass_request[6]!=None):
            if (variable == ""):
                variable = variable + mass_request[6]
            else:
                variable = variable + "&" + mass_request[6]
    except:
        print "Таблица не заполнена или заполнена некорректно"

    # изменяем файл грамматики

    write_in_file(grammar.lower())

    # выполняем переконфигурирование программы

    p = configuration()
