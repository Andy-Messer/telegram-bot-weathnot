#!/usr/bin/python
# -*- coding: utf8 -*-
import telebot
import config
from bs4 import BeautifulSoup
import requests as req
import schedule
import time
from threading import Thread

try:

    from googlesearch import search

except ImportError:

    print("No module named 'google' found")



class ThreadingSchedule(object):
    flag = True

    def __init__(self, interval=1):
        self.interval = interval
        thread = Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        while ThreadingSchedule.flag:
            schedule.run_pending()
            time.sleep(1)

    def join(self):
        ThreadingSchedule.flag = False


thread1 = ThreadingSchedule()

bot = telebot.TeleBot(config.TOKEN)

city_name = "Moscow (RU)"
default_time = "10:00"

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36 OPR/40.0.2308.81',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'DNT': '1',
    'Accept-Encoding': 'gzip, deflate, lzma, sdch',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.6,en;q=0.4'
}


def parse_for_week(url):
    resp = req.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'lxml')
    dep = soup.find('span', class_="js_value tab-weather__value_l")
    tp_now = list()
    for i in dep:
        tp_now.append(i)
    tp_now = tp_now[0].strip()
    dep2 = soup.find_all('span', class_="unit unit_temperature_c")[6:]
    tp_week = list()
    for i in dep2:
        for j in i:
            tp_week.append(j)
    dep3 = soup.find_all('span', class_="tooltip")
    tp_week_traits = list()
    for i in dep3:
        tp_week_traits.append(i['data-text'])
    # print(soup)
    dep4 = soup.find_all('a', class_="tab tablink tooltip")
    tp_now_traits = dep4[0]['data-text']
    ans = "Погода на сегодня:\n" \
          "сейчас: " + tp_now + ' ' + tp_now_traits + '\n'
    for i in range(0, len(tp_week)):
        tp_week[i] += '°C ' + tp_week_traits[i] + '\n';
    ans += " 00:00 " + tp_week[0]
    ans += " 03:00 " + tp_week[1]
    ans += " 06:00 " + tp_week[2]
    ans += " 09:00 " + tp_week[3]
    ans += " 12:00 " + tp_week[4]
    ans += " 15:00 " + tp_week[5]
    ans += " 18:00 " + tp_week[6]
    ans += " 21:00 " + tp_week[7]
    return ans


def get_weather_now(local_id):
    query = str("погода в " + city_name + " site:gismeteo.ru")
    links = search(query)
    weather_for_week = parse_for_week(links[0])
    bot.send_message(local_id, weather_for_week)


# ok
@bot.message_handler(commands=['start'])
def send_welcome(message):
    m = "Привет, я начал  отслеживание погоды, чтобы остановить меня напиши /stop, для большей информации обо мне напиши /help"
    bot.send_message(message.chat.id, m)
    schedule.every().day.at(default_time).do(get_weather_now, message.chat.id).tag('alarms')
    global thread1
    thread1.run()


# ok
@bot.message_handler(commands=['help'])
def send_help(message):
    m = "Я могу говорить погоду с помощью команды /weather.\n Вы в любой момент можете сменить время в которое присылается погода, по умолчанию это " + default_time + ".\n Еще Вы можете сменить город, для которого будет показываться погода, командой /setcity, сейчас это " + city_name + "\nдля остановки бота введите /stop"
    bot.send_message(message.chat.id, m)


# ok
@bot.message_handler(commands=['settime'])
def set_time(message):
    schedule.clear('alarms')
    m = bot.send_message(message.chat.id, "Введите желаемое время в формате АА:АА")
    bot.register_next_step_handler(m, set_time)


# ok
def set_time(message):
    try:
        time.strptime(message.text, '%H:%M')
        global default_time
        default_time = str(message.text)
        schedule.every().day.at(default_time).do(get_weather_now, message.chat.id).tag('alarms')
    except ValueError:
        bot.send_message(message.chat.id, "Wrong format, try again")


# ok
@bot.message_handler(commands=['time'])
def send_time(message):
    bot.send_message(message.chat.id, time.strftime('%d/%m/%Y %H:%M:%S'))


# ok
@bot.message_handler(commands=['setcity'])
def send_city(message):
    m = bot.send_message(message.chat.id, "Введите желаемый город на Английском")
    bot.register_next_step_handler(m, set_city)


# ok
def set_city(message):
    global city_name
    city_name = message.text + " (RU)"


@bot.message_handler(commands=['weather'])
def get_weather(message):
    get_weather_now(message.chat.id)


# ok
@bot.message_handler(commands=['stop'])
def stop(message):
    schedule.clear('alarms')
    global thread1
    thread1.join()
    bot.send_message(message.chat.id, "stopped")


# RUN
bot.polling(none_stop=True)
