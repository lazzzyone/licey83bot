from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import requests
import vk_api
import numpy as np
import random
import requests
import config

TIMETABLE_URL = 'http://licey83.ru/images/raspisanie/ras%D1%80.JPG'
BELLS_URL = 'http://licey83.ru/images/rasp_urukov2020.JPG'

vk_session = vk_api.VkApi(token=config.token)
print(vk_session.api_version)
session = requests.Session()
longpoll = VkBotLongPoll(vk_session, group_id=194333368)
vk = vk_session.get_api()


def send_photo(user_id, peer_id, url):
    attachments = []
    from vk_api import VkUpload
    upload = VkUpload(vk_session)
    image_url = url
    image = session.get(url=image_url, stream=True)
    photo = upload.photo_messages(photos=image.raw)[0]
    attachments.append(
        'photo{}_{}'.format(photo['owner_id'], photo['id'])
    )
    vk.messages.send(
        peer_id=peer_id,
        user_id=user_id,
        attachment=','.join(attachments),
        message='Актуалочка',
        random_id=np.int64(random.randint(10000, 1000000000000))
    )

    pass


for event in longpoll.listen():
    print(event)
    if event.type == VkBotEventType.MESSAGE_NEW :
        # Слушаем longpoll, если пришло сообщение то:
        if 'расписание' in event.object.get('text'):  # Если написали заданную фразу
            if event.from_user:  # Если написали в ЛС
                send_photo(event.object.get('user_id'), event.object.get('peer_id'), TIMETABLE_URL)
            elif event.from_chat:  # Если написали в Беседе
                send_photo(event.object.get('user_id'), event.object.get('peer_id'), TIMETABLE_URL)
        elif 'звонки' in event.object.get('text'):
            if event.from_user:  # Если написали в ЛС
                send_photo(event.object.get('user_id'), event.object.get('peer_id'), BELLS_URL)
            elif event.from_chat:  # Если написали в Беседе
                send_photo(event.object.get('user_id'), event.object.get('peer_id'), BELLS_URL)
        elif 'тест' in event.object.get('text'):
            vk.messages.send(
                peer_id=event.object.get('peer_id'),
                user_id=event.object.get('user_id'),
                message='Бот работаетв бета режиме \n Версия API ' + vk_session.api_version,
                random_id=np.int64(random.randint(10000, 1000000000000))
            )
