import json
import os
import secrets
from dotenv import load_dotenv

from vk_maria.dispatcher import Dispatcher
from vk_maria import Vk, types
from vk_maria.dispatcher.fsm import StatesGroup, State, MemoryStorage, FSMContext
from vk_maria.types import KeyboardMarkup, Button, Color

load_dotenv()

access_token = os.getenv("VK_API_KEY")
delay_in_seconds = os.getenv("DELAY")
beseda_id = int(os.getenv("VK_TALK_ID"))

vk = Vk(access_token=access_token)
dp = Dispatcher(vk, MemoryStorage())


class Form(StatesGroup):
    waiting_for_name: State
    waiting_for_phone: State
    waiting_for_text: State
    waiting_for_photos: State


users = dict()
users_info = dict()

default_markup = KeyboardMarkup(one_time=False)

default_markup.add_button(Button.Text(Color.PRIMARY, "Отправить предложение!"))


@dp.message_handler(text="Начать")
def welcome(event):
    event.answer("Привет, на связи бот для получения обратной связи!", keyboard=default_markup)


@dp.message_handler(text="Отправить предложение!")
def start_send_process(event):
    event.reply("Введите своё фамилию и имя для обращения:")
    Form.waiting_for_name.set()


@dp.message_handler(state=Form.waiting_for_name)
def process_name(event: types.Message, state: FSMContext):
    if len(event.message.text) < 6 or len(event.message.text.split()) < 2:
        event.answer("Должно быть введено корректное имя и фамилия!")
        return

    state.update_data(name=event.message.text)
    event.reply("Ваш телефон:")
    Form.next()


@dp.message_handler(state=Form.waiting_for_phone)
def process_phone(event: types.Message, state: FSMContext):
    if not 11 < len(event.message.text) < 20 or not all([x in "0123456789()+" for x in event.message.text]):
        event.answer("Должно быть введен корректный номер телефона")
        return

    state.update_data(phone=event.message.text)

    event.reply('Введите ваше обращение к администрации:')
    Form.next()


@dp.message_handler(state=Form.waiting_for_text)
def process_text(event: types.Message, state: FSMContext):
    if len(event.message.text) < 20:
        event.answer("Текст слишком маленький")
        return
    elif len(event.message.text) > 7000:
        event.answer("Текст слишком большой!")
        return

    state.update_data(text=event.message.text)

    markup = KeyboardMarkup(one_time=True)
    markup.add_button(Button.Text(Color.SECONDARY, "Фото нет"))

    event.reply("Прикрепите все фотографии сейчас(если они нужны и имеются)!", keyboard=markup)
    Form.next()


@dp.message_handler(state=Form.waiting_for_photos)
def process_callback(event: types.Message, state: FSMContext):
    if event.message.text not in ("Фото нет", ""):
        event.answer("Если фото нет, необходимо нажать на кнопку!")
        return

    state.update_data(photos=event.message.text)
    user_data = state.get_data()
    event.answer("Принято!", keyboard=default_markup)

    photos = []

    for x in event.message.attachments:
        if x.type != 'photo':
            continue
        photos.append(f"photo{x.photo.owner_id}_{x.photo.id}_{x.photo.access_key}")

    vk.messages_send(peer_id=2000000000 + beseda_id,
                     message=f"Обращение от: {user_data["name"]}\nС телефоном: {user_data["phone"]}\n\n{user_data["text"]}",
                     attachment=",".join(photos),
                     content_source=json.dumps({"type": "message",
                                                # от чьего имени указан peer_id. т.е. вы можете использовать контент из сообщения другой группы.
                                                "owner_id": event.message.from_id,
                                                # id диалога
                                                "peer_id": event.message.peer_id,
                                                # id сообщения в беседе. Не путать с message.id профиля
                                                "conversation_message_id": event.message.conversation_message_id,
                                                }))

    Form.finish()


@dp.message_handler()
def echo(event: types.Message):
    event.reply("Для отправки сообщения нажмите на кнопку и заполните анкету", keyboard=default_markup)


dp.start_polling(debug=True)
