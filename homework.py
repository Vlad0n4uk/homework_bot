"""Телеграм-бот, проверяющий статус код-ревью."""

import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import ResponseException, ServiceDenial

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
    'Передаваемые параметры:{url}, {headers}, {params}'
)
GET_API_ANSWER_RESPONSE_ERROR = (
    'Ответ сервера = {}. '
    'Входящие параметры: {url}, {headers}, {params}. '
)
SERVICE_DENIAL_ERROR = (
    'Отказ в обслуживании:{}: {}. '
    'Входящие параметры: {url}, {headers}, {params}.'
)
TYPE_ERROR_LIST = 'Неверный тип данных: {}. Ожидается список.'
TYPE_ERROR_DICT = 'Неверный тип данных: {}. Ожидается словарь.'
KEY_ERROR = 'Невозможно получить значение по ключу: homeworks.'
PARSE_STATUS_RETURN = (
    'Изменился статус проверки работы "{}". '
    '{}'
)
MAIN_EXCEPTION_MESSAGE = 'Сбой в работе программы: {}'
NO_NEW_STATUS_IN_API = 'Отсутствие в ответе новых статусов'
MAIN_EXCEPTION_ERROR = 'Ошибка: {}'


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    are_tokens_valid = True
    for name in ALL_TOKEN_NAMES:
        if not globals()[name]:
            are_tokens_valid = False
            logging.critical(CHECK_TOKENS_CRITICAL_LOG.format(name))
    return are_tokens_valid


def send_message(bot, message):
    """Функция отправки сообщения."""
    success = True
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.info(SEND_MESSAGE_INFO_LOG.format(message))
    except telegram.TelegramError as telegram_error:
        logging.exception(SEND_MESSAGE_EXCEPTION_LOG(message, telegram_error))
        success = False
    return success


def get_api_answer(current_timestamp):
    """Функция делает запрос к API Практикум.Домашка."""
    params = {'from_date': current_timestamp}
    data = dict(url=ENDPOINT, headers=HEADERS, params=params)
    try:
        response = requests.get(**data)
    except requests.exceptions.RequestException as request_error:
        raise ConnectionError(
            GET_API_ANSWER_REQUEST_ERROR.format(request_error, **data)
        )
    response_json = response.json()
    for error in ['code', 'error']:
        if error in response_json:
            raise ServiceDenial(
                SERVICE_DENIAL_ERROR.format(
                    error, response_json[error], **data)
            )
    if response.status_code != 200:
        raise ResponseException(
            GET_API_ANSWER_RESPONSE_ERROR.format(response.status_code, **data)
        )
    return response_json


def check_response(response):
    """Функция проверяет ответ от API на корректность.
    Возвращает список домашних работ при корректном ответе API.
    """
    if not isinstance(response, dict):
        raise TypeError(TYPE_ERROR_DICT.format(type(response)))
    if 'homeworks' not in response:
        raise KeyError(KEY_ERROR)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError(TYPE_ERROR_LIST.format(type(homeworks)))
    return homeworks


def parse_status(homework):
    """Функция определяет статус работы отправленной на код-ревью."""
    name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise ValueError(KEY_ERROR.format(status))
    return PARSE_STATUS_RETURN.format(name, HOMEWORK_VERDICTS[status])


def main():
    """Функция запуска Телеграм-бота."""
    if not check_tokens():
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    last_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if send_message(bot, message):
                    timestamp = response.get(
                        'current_date', timestamp)
            else:
                logging.debug(NO_NEW_STATUS_IN_API)
        except Exception as error:
            message = MAIN_EXCEPTION_MESSAGE.format(error)
            logging.error(message)
            if message != last_message:
                if send_message(bot, message):
                    last_message = message
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
        handlers=[
            logging.FileHandler(__file__ + '.log', mode='w'),
            logging.StreamHandler(sys.stdout)
        ],
        format=LOG_ATTRIBUTES
    )
    main()
