"""Телеграм-бот, проверяющий статус код-ревью."""

import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import ResponseException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
ALL_TOKEN_NAMES = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']

RETRY_TIME = 600  # Период времени запроса к серверу
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
# API Яндекс Практикум.Домашка
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
# Процесс авторизации  на платформе Яндекс Практикум путем присвоения токена

HOMEWORK_VERDICTS = {  # Статусы код-ревью
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
CHECK_TOKENS_CRITICAL_LOG = (
    'Отсутствует обязательная переменная окружения: {}'
)
SEND_MESSAGE_INFO_LOG = ('Сообщение отправлено: {}')
SEND_MESSAGE_EXCEPTION_LOG = ('Сообщение {} в Telegram не отправлено: {}')
GET_API_ANSWER_REQUEST_ERROR = (
    'Некорректный запрос: {}. '
    'Передаваемые параметры:{}, {}, {}'
)
GET_API_ANSWER_RESPONSE_ERROR = (
    'Ответ сервера = {}. '
    'Входящие параметры: {}, {}, {}. '
    '{}'
)
TYPE_ERROR_LIST = 'Неверный тип данных: {}. Ожидается список.'
TYPE_ERROR_DICT = 'Неверный тип данных: {}. Ожидается словарь.'
KEY_ERROR = 'Невозможно получить значение по ключу: homeworks.'
PARSE_STATUS_RETURN_PHRASE = (
    'Изменился статус проверки работы "{}". '
    '{}'
)
MAIN_EXCEPTION_MESSAGE = 'Сбой в работе программы: {}'
NO_NEW_STATUS_IN_API = 'Отсутствие в ответе новых статусов'


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    for name in ALL_TOKEN_NAMES:
        if not globals()[name]:
            logging.critical(CHECK_TOKENS_CRITICAL_LOG.format(name))
            return False
    return True


def send_message(bot, message):
    """Функция отправки сообщения."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.info(SEND_MESSAGE_INFO_LOG.format(message))
    except telegram.TelegramError as telegram_error:
        logging.exception(SEND_MESSAGE_EXCEPTION_LOG(message, telegram_error))


def get_api_answer(current_timestamp):
    """Функция делает запрос к API Практикум.Домашка."""
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except requests.exceptions.RequestException as request_error:
        raise ConnectionError(
            GET_API_ANSWER_REQUEST_ERROR.format(
                f'{request_error}, {ENDPOINT},{HEADERS}, {params}')
        )
    if response.status_code != 200:
        description = ''
        try:
            response = response.json()
            if 'code' in response:
                description += f"code: {response['code']}. "
            if 'error' in response:
                description += f"error: {response['error']}"
        finally:
            raise ResponseException(
                GET_API_ANSWER_RESPONSE_ERROR.format(
                    f'{response.status_code} ',
                    f'{ENDPOINT} ',
                    f'{HEADERS} ',
                    f'{params}',
                    f'{description}'
                )
            )
    return response.json()


def check_response(response):
    """Функция проверяет ответ от API на корректность.
    Возвращает список домашних работ при корректном ответе API.
    """
    if not isinstance(response, dict):
        raise TypeError(TYPE_ERROR_DICT.format(type(response)))
    if 'homeworks' not in response:
        raise KeyError(KEY_ERROR)
    data = response['homeworks']
    if not isinstance(data, list):
        raise TypeError(TYPE_ERROR_LIST.format(type(data)))
    return data


def parse_status(homework):
    """Функция определяет статус работы отправленной на код-ревью."""
    name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(KEY_ERROR.format(status))
    return PARSE_STATUS_RETURN_PHRASE.format(name, HOMEWORK_VERDICTS[status])


def main():
    """Функция запуска Телеграм-бота."""
    if not check_tokens():
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 100000
    while True:
        try:
            response = get_api_answer(current_timestamp)
            response.get('current_date', current_timestamp)
            data = check_response(response)
            if data:
                message = parse_status(data[0])
                send_message(bot, message)
            else:
                logging.debug(NO_NEW_STATUS_IN_API)
        except Exception as error:
            message = MAIN_EXCEPTION_MESSAGE.format(error)
            logging.error(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    LOG_ATTRIBUTES = ('%(asctime)s, '
                      '%(levelname)s, '
                      '%(name)s, '
                      '%(message)s, '
                      '%(funcName)s, '
                      '%(lineno)d')
    logging.basicConfig(  # Глобальная настройка логов
        level=logging.DEBUG,
        filename=__file__ + '.log',  # Запись логов в файл
        filemode='w',
        format=LOG_ATTRIBUTES
    )
    logging.StreamHandler()
    main()
