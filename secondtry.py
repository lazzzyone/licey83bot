from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import vk_api
import numpy as np
import random
import requests
from bs4 import BeautifulSoup
import datetime
import ast

from config import TIMETABLE_URL, BELLS_URL, LOGIN, PASSWORD, DIARYPAGE, ELSCHOOL, TOKEN


def get_timetable_elschool(day):
    global m_index
    try:
        r_session = requests.Session()

        r_session.post(url=ELSCHOOL, data={'login': LOGIN, 'password': PASSWORD})
        response = r_session.get(DIARYPAGE)

        f = open('resp.html', 'wb')
        f.write(response.content)

        soup = BeautifulSoup(response.content, 'html.parser')
        table_mon_wed = list(soup.find_all(class_="col-6"))[1]
        table_thu_sat = list(soup.find_all(class_="col-6"))[2]

        days = list(table_mon_wed.find_all('tbody'))
        for item in list(table_thu_sat.find_all('tbody')):
            days.append(item)
        result = process_days_html(days)
        with open('last_homework.txt', 'w+') as fi:
            fi.write(str(result))

    except Exception:
        with open('last_homework.txt', 'w+') as fi:
            result = ast.literal_eval(fi.read())

    days = ['понедельник Понедельник', 'вторник Вторник', 'среда среду Среда Среду', 'четверг', 'пятница пятницу',
            'суббота', 'воскресенье', 'неделю', 'сегодня', 'завтра']
    days_in_dict = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
    for item in days:
        if day in item:
            m_index = days.index(item)
    if m_index is not None and 0 <= m_index <= 5:
        return result[days_in_dict[m_index]]
    elif m_index is 9:
        return result.get(days_in_dict[(datetime.datetime.today().weekday() + 1) % 6])
    else:
        return result.get(days_in_dict[(datetime.datetime.today().weekday()) % 6])


def dict_prettify(d):
    res = ''
    for key in d:
        res += key
        res += ' : ' + d[key]
        res += '\n'

    return res


def process_subj(day):
    subjects = day.find_all(class_='diary__lesson')
    if subjects.__sizeof__() > 0:
        d = {}
        for subject in subjects:
            try:
                d[subject.find(class_='flex-grow-1').contents[0]] = \
                    subject.find(class_='diary__homework-text').contents[0]
            except IndexError:
                d[subject.find(class_='flex-grow-1').contents[0]] = 'Домашнее задание отсутствует'
            except AttributeError:
                return 'Уроков нет'

        return d
    else:
        return 'Занятий нет'


def process_days_html(days_html):
    if days_html is not None:
        d = {'Понедельник': process_subj(days_html[0]), 'Вторник': process_subj(days_html[1]),
             'Среда': process_subj(days_html[2]), 'Четверг': process_subj(days_html[3]),
             'Пятница': process_subj(days_html[4]), 'Суббота': process_subj(days_html[5])}

        return d
    else:
        return None


def send_photo(u_id, p_id, urls):
    try:
        attachments = []
        from vk_api import VkUpload
        upload = VkUpload(vk_session)
        print(type(urls))
        if isinstance(urls, list):
            for url in urls:
                image_url = url
                image = session.get(url=image_url, stream=True)
                photo = upload.photo_messages(photos=image.raw, peer_id=peer_id)[0]
                print(photo)
                attachments.append(
                    'photo{}_{}'.format(photo['owner_id'], photo['id'])
                )
        else:
            image_url = urls
            image = session.get(url=image_url, stream=True)
            photo = upload.photo_messages(photos=image.raw, peer_id=peer_id)[0]
            print(photo)
            attachments.append(
                'photo{}_{}'.format(photo['owner_id'], photo['id'])
            )
        vk.messages.send(
            peer_id=p_id,
            user_id=u_id,
            attachment=','.join(attachments),
            message='Актуалочка',
            random_id=np.int64(random.randint(10000, 1000000000000))
        )
    except vk_api.ApiError:
        send_photo(u_id, p_id, urls)
    pass


def send_message(u_id, p_id, text):
    vk.messages.send(
        peer_id=p_id,
        user_id=u_id,
        message=text,
        random_id=np.int64(random.randint(10000, 1000000000000))
    )


vk_session = vk_api.VkApi(token=TOKEN)
print(vk_session.api_version)
session = requests.Session()
longpoll = VkBotLongPoll(vk_session, group_id=194333368)
vk = vk_session.get_api()

for event in longpoll.listen():
    # print(event)
    if event.type == VkBotEventType.MESSAGE_NEW:
        peer_id = event.object.get('peer_id')
        user_id = event.object.get('user_id')
        user_message_lower = event.object.get('text').lower()
        # Слушаем longpoll, если пришло сообщение то:
        if 'бот,' in user_message_lower:
            user_message_lower = str(user_message_lower[4:])
            if 'расписание' in user_message_lower:  # Если написали заданную фразу
                send_photo(user_id, peer_id, TIMETABLE_URL)
            elif 'звонки' in user_message_lower:
                send_photo(user_id, peer_id, BELLS_URL)
            elif 'тест' in user_message_lower:
                send_message(user_id, peer_id, 'Бот работает в бета режиме \n Версия API ' + vk_session.api_version)
            elif 'дз на' in user_message_lower:
                print('ЙОУ ' + user_message_lower.split(' ')[-1])
                print(get_timetable_elschool(user_message_lower.split(' ')[-1]))
                send_message(user_id, peer_id, dict_prettify(get_timetable_elschool(user_message_lower.split(' ')[-1])))
