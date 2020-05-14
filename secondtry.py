import ast
import datetime
import io
import random
import html
import os


import numpy as np
import requests
import vk_api
from bs4 import BeautifulSoup
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from config import TIMETABLE_URL, BELLS_URL, LOGIN, PASSWORD, DIARYPAGE, ELSCHOOL, BACKUP_TIMETABLE_URL


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


def list_prettify(l):
    if l.__len__() > 0:
        res = ''
        for index, value in enumerate(l):
            res += str(index+1)
            res += ' : ' + value
            res += '\n'
        return res
    else:
        return 'Заметок нет'


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
    except vk_api.ApiError as error:
        send_photo(u_id, p_id, urls)
        send_message(u_id, p_id, 'Произошла ошибка загрузки фото, ебучий сайт упал')
        print(error.raw)
    pass


def send_message(u_id, p_id, text):
    vk.messages.send(
        peer_id=p_id,
        user_id=u_id,
        message=text,
        random_id=np.int64(random.randint(10000, 1000000000000))
    )


def add_note_to_file(note):
    with io.open('notes.txt', 'r+', encoding='utf-8') as notes_file:
        data = ast.literal_eval(notes_file.read())
        data.append(note)
        notes_file.seek(0)
        notes_file.write(str(data))
        notes_file.truncate()
    pass


def get_fresh_anec():
    anekurl = 'https://www.anekdot.ru/rss/random.html'
    response = requests.get(url=anekurl)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.decode()[soup.decode().find('['):soup.decode().find(']') + 1]
    text = html.unescape(text.replace('\\', '\'').replace('\"', '').replace('\'\'\'', '*'))
    mylist = ast.literal_eval(text)
    for item in mylist:
        item.replace('<br/>', ' ')
    return random.choice(mylist)


def get_all_notes():
    with io.open('notes.txt', 'r+', encoding='utf-8') as notes_file:
        data = ast.literal_eval(notes_file.read())
        return list_prettify(data)
    pass


def remove_note_from_file(number_of_note_to_remove):
    try:
        with io.open('notes.txt', 'r+', encoding='utf-8') as notes_file:
            data = ast.literal_eval(notes_file.read())
            print(data.pop(int(number_of_note_to_remove)-1))
            notes_file.seek(0)
            notes_file.write(str(data))
            notes_file.truncate()
    except Exception as e:
        print(e)
        pass


token = os.environ.get('token', None)
if token is None:
    import private
    token = private.token
vk_session = vk_api.VkApi(token=token)
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
            user_message_lower = str(user_message_lower[4:]).strip(' ')
            if 'расписание' in user_message_lower:  # Если написали заданную фразу
                send_photo(user_id, peer_id, TIMETABLE_URL)
            elif 'другое' in user_message_lower:
                send_photo(user_id, peer_id, BACKUP_TIMETABLE_URL)
            elif 'звонки' in user_message_lower:
                send_photo(user_id, peer_id, BELLS_URL)
            elif 'тест' in user_message_lower:
                send_message(user_id, peer_id, 'Бот работает в бета режиме \n Версия API ' + vk_session.api_version)
            elif 'дз на' in user_message_lower:
                print('ЙОУ ' + user_message_lower.split(' ')[-1])
                print(get_timetable_elschool(user_message_lower.split(' ')[-1]))
                send_message(user_id, peer_id, dict_prettify(get_timetable_elschool(user_message_lower.split(' ')[-1])))
            elif 'заметка' in user_message_lower:
                add_note_to_file(user_message_lower[7:].strip(' '))
            elif 'удалить' in user_message_lower:
                print(user_message_lower[7:].strip(' '))
                remove_note_from_file(user_message_lower[7:].strip(' '))
            elif 'заметки' in user_message_lower:
                send_message(user_id, peer_id, get_all_notes())
            elif 'анекдот' in user_message_lower:
                send_message(user_id, peer_id, get_fresh_anec())
