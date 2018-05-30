#!/usr/bin/env python
# coding: utf8
import subprocess
import time
import MySQLdb
import sys
import webbrowser
import os
from pocketsphinx import LiveSpeech, get_model_path

command="" #текущая команда
state="Инициализация"   #текущее состояние
p_command="" #предыдущая команда
p_state="" #предыдущее состояние
grammar="терминал" #текущая грамматика
message="Скажите Терминал для начала работы"

model_path = get_model_path()

# *функция работы с базой данных*
# *на вход команда и состояние*
# *на выход массив с результатами запроса*

def request(com, st):
 print 'Com' , com
 print 'st' , st        
 con = None
 try:
    #обращение к базе данных
    con = MySQLdb.connect('localhost', 'dbuser', 'dbuserpass', 'dbname')
    cur = con.cursor()
    #выполнение запроса
    request_string="SELECT previous_command, previous_state, follow_state, grammar, link, message  FROM commands WHERE command='"+com +"' AND " + "state='"+st+"'"
    cur.execute(request_string)
    arr=[]
    while True:
        row = cur.fetchone()
        if row == None:
            break
        #Предыдущая команда - row[0], Предыдущее состояние - row[1], Следующее состояние - row[2], Грамматика - row[3], Ссылка - row[4], Переменные - row[5], Сообщение - row[6]
        arr=[row[0], row[1], row[2], row[3], row[4], row[5]]
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
# *на вход строка с конфигурацией*

def configuration():    
    speech = LiveSpeech(
    verbose=False,
    sampling_rate=16000,
    buffer_size=2048,
    no_search=False,
    full_utt=False,
    hmm=os.path.join(model_path, 'ru-ru'),
    lm=False,
    jsgf='terminal.gram',
    dic=os.path.join(model_path, 'ru.dic')
)

    return speech

# *функция записи в файл грамматики*
# *на вход строка с грамматикой*

def write_in_file(gram):
    f = open('terminal.gram', 'w')
    f.write("#JSGF V1.0;\ngrammar PI;\npublic <cmd> = ("+gram+");")
    f.close

# обновление файла грамматики
write_in_file(grammar.lower())
# переконфигурирование PocketSphinx
p=configuration()
counter=0
while True:
    subprocess.call('mpg123 -q Sound.wav', shell=True)
    mess="notify-send " + "\"" + message +"\""
    subprocess.call(mess, shell=True)
    line = ""
    for phrase in p:
        print "LINE:", phrase
        print phrase.probability()
        line = str(phrase)
        break
    if (len(line) > 1):
        command = line[0:len(line)-1]
        counter=counter+1
        #пропускаем первую команду (работает некоректно)
        if (counter==1): continue
    else:
        continue
    print command
    if (command=="Назад"):
        print "Сказано назад"
        mass_request=request(p_command, p_state)  # при команде "назад" используем в качетве первичного ключа предыдущие состояние и команду       
    else:
        print state, p_command
        mass_request=request(command, state) # иначе используем текущие состояние и команду
    # изменяем состояние  
    state=mass_request[2]
    # изменяем предыдущее состояние
    p_state=mass_request[1]
    # сохраняем предыдущую команду
    p_command=mass_request[0]
    # изменяем грамматику
    grammar=mass_request[3]
    # открываем ссылку в браузере
    if (mass_request[4]!="No"):
        webbrowser.open(mass_request[4], new=0)
    # изменяем файл грамматики
    write_in_file(grammar.lower())
    # выполняем переконфигурирование программы
    p=configuration()
    message=mass_request[5]
    counter=0
    if (retcode is not None):
        break


  

