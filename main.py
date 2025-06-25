import json
import os
import logging
import traceback
from functools import wraps
from dotenv import load_dotenv

from vk_maria.dispatcher import Dispatcher
from vk_maria import Vk, types
from vk_maria.dispatcher.fsm import StatesGroup, State, PickleStorage, FSMContext
from vk_maria.types import KeyboardMarkup, Button, Color

load_dotenv()

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
else:
    logging.error("Данный файл нельзя импортировать как библиотеку")
    os.exit(100)

try:
    access_token = os.getenv("VK_API_KEY")
    delay_in_seconds = os.getenv("DELAY")
    talk_id = int(os.getenv("VK_TALK_ID"))
    debug_mode = bool(os.getenv("DEBUG"))
    if access_token is None or delay_in_seconds is None:
        raise Exception()
except Exception:
    logger.error("Не все нужные для работы данные были указаны(VK_API_KEY, VK_TALK_ID, DELAY)")
    os.exit(1)

try:
    vk = Vk(access_token=access_token)
    dp = Dispatcher(vk, PickleStorage("state/state.pck"))
except Exception as e:
    logger.error("Инициализация не удалась!")
    logger.exception(e)
    os.exit(2)


class Form(StatesGroup):
    waiting_for_name: State
    waiting_for_phone: State
    waiting_for_text: State
    waiting_for_photos: State


default_markup = KeyboardMarkup(one_time=False)

default_markup.add_button(Button.Text(Color.PRIMARY, "Создать обращение"))


def log_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error("".join(traceback.format_exception(type(e), e, e.__traceback__.tb_next, limit=3)))
            logger.error(f"Переменные при ошибки, позиционные: {args}; именованные: {kwargs}")

    return wrapper


@dp.message_handler(state=Form.waiting_for_name)
@log_exception
def process_name(event: types.Message, state: FSMContext):
    details = event.message.text.split()
    name = " ".join(details)

    if len(event.message.text) < 4 or len(details) < 2:
        event.answer("Должно быть введено корректное имя и фамилия!")
        return
    if len(name) > 36:
        event.answer(
            "Ваши данные слишком длинные, укажите только имя и фамилию, если ошибка остаётся, сократите фамилию или/и имя"
        )
        return

    state.update_data(name=name)
    event.reply("Ваш телефон:")
    Form.next()


@dp.message_handler(state=Form.waiting_for_phone)
@log_exception
def process_phone(event: types.Message, state: FSMContext):
    phone = event.message.text.replace(" ", "")
    if not 10 < len(phone) < 20 or not all([x in "0123456789()+-" for x in phone]):
        if len(phone) <= 10:
            event.answer("Телефон слишком короткий")
        elif len(phone) >= 20:
            event.answer("Телефон слишком длинный")
        else:
            event.answer("Телефон не может содержать букв")

        return

    state.update_data(phone=phone)

    event.reply("Отправьте ваше обращение к администрации:")
    Form.next()


@dp.message_handler(state=Form.waiting_for_text)
@log_exception
def process_text(event: types.Message, state: FSMContext):
    if len(event.message.text) > 3500:
        event.answer("Текст слишком большой(Максимум: 3500 символов)!")
        return

    state.update_data(text=event.message.text)

    markup = KeyboardMarkup(one_time=False)
    markup.add_button(Button.Text(Color.SECONDARY, "Фото нет"))

    event.reply(
        "Отправьте фотографии, которые вы хотите прикрепить к обращению, если фотографий несколько, отправьте их одним сообщением(До 10 штук)",
        keyboard=markup,
    )
    Form.next()


@dp.message_handler(state=Form.waiting_for_photos)
@log_exception
def process_callback(event: types.Message, state: FSMContext):
    if event.message.text != "Фото нет":
        event.answer("Если фото нет, необходимо нажать на кнопку")
        return

    photos = []

    for x in event.message.attachments:
        if x.type != "photo":
            event.answer(
                "Обнаружены недопустимые вложения, пожалуйста используйте только фотографии, отправленные при помощи быстрой отправки"
            )
            return
        photos.append(f"photo{x.photo.owner_id}_{x.photo.id}_{x.photo.access_key}")

    user_data = state.get_data()

    vk.messages_send(
        peer_id=2000000000 + talk_id,
        message=f"Обращение от: {user_data['name']}\nС телефоном: {user_data['phone']}\nhttps://vk.com/id{event.message.from_id}\n{'-' * 15}\n{user_data['text']}",
        attachment=",".join(photos),
        content_source=json.dumps(
            {
                "type": "message",
                # от чьего имени указан peer_id. т.е. вы можете использовать контент из сообщения другой группы.
                "owner_id": event.message.from_id,
                # id диалога
                "peer_id": event.message.peer_id,
                # id сообщения в беседе. Не путать с message.id профиля
                "conversation_message_id": event.message.conversation_message_id,
            }
        ),
    )

    event.answer(
        "Принято! Ваше обращение было сформировано и отправлено администрации техникума. Если хотите отправить новое обращение, нажмите на кнопку ниже",
        keyboard=default_markup,
    )

    state.finish(with_data=True)
    Form.finish()
    logger.info(f"Обращение успешно отправлено от {user_data['name']} в беседу предложки!")


@dp.message_handler(text="Начать")
@log_exception
def welcome(event):
    event.answer(
        """Добро пожаловать в чат-бот для обращений.
Сюда вы можете написать свои вопросы, жалобы, или предложения администрации ОГБПОУ «ТТИТ»""",
        keyboard=default_markup,
    )


@dp.message_handler(text="Создать обращение")
@log_exception
def start_send_process(event):
    event.reply("Введите своё фамилию и имя для обращения:", keyboard=KeyboardMarkup())
    Form.waiting_for_name.set()


@dp.message_handler()
@log_exception
def echo(event: types.Message):
    event.reply(
        "Для отправки обращения нажмите на кнопку и заполните анкету",
        keyboard=default_markup,
    )


logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%m/%d/%Y %H:%M:%S", level=logging.INFO)
logger.info("Начинаю работу")


@log_exception
def poll():
    dp.start_polling(debug=debug_mode)


try:
    poll()
except KeyboardInterrupt:
    logger.info("Сохранение состояния на диск")

logger.info("Процесс завершился")
