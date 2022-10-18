"""Телеграм-бот, проверяющий статус код-ревью."""

import json
import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import RequestExceptionError, ResponseException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600  # Период времени запроса к серверу
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
# API Яндекс Практикум.Домашка
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
# Процесс авторизации  на платформе Яндекс Практикум путем присвоения токена


HOMEWORK_STATUSES = {  # Статусы код-ревью
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(  # Глобальная настройка логов
    level=logging.DEBUG,
    filename='main.log',  # Запись логов в файл
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)


def check_tokens():
    "Функция проверяет доступность переменных окружения."
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    logger.critical('Отсутствует обязательная переменная окружения')


def send_message(bot, message):
    "Функция отправки сообщения."
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено')
    except telegram.TelegramError as telegram_error:
        logger.error(
            f'Сообщение в Telegram не отправлено: {telegram_error}')


def get_api_answer(current_timestamp):
    "Функция делает запрос к API Практикум.Домашка."
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            logger.error('Статус запроса не равен 200.')
            raise ResponseException('Ваш запрос не может быть выполнен.')
        return response.json()
    except requests.exceptions.RequestException as request_error:
        logger.error(f'Код ответа API : {request_error}')
        raise RequestExceptionError('Некорректный запрос ')
    except json.JSONDecodeError as value_error:
        logger.error(f'Код ответа API : {value_error}')
        raise json.JSONDecodeError('Некорректные данные')


def check_response(response):
    """Функция проверяет ответ от API на корректность.
    Возвращает список домашних работ при корректном ответе API.
    """
    if not isinstance(response, dict):
        raise TypeError('Неверный тип данных. Ожидается словарь.')
    homeworks = response['homeworks']
    if homeworks is None:
        logger.error('Отсутствие ожидаемых ключей в ответе API.')
        raise KeyError('Неверный ключ.')
    elif not isinstance(homeworks, list):
        raise TypeError('Неверный тип данных. Ожидается список.')
    return homeworks


def parse_status(homework):
    "Функция определяет статус работы отправленной на код-ревью."
    if 'homework_name' not in homework:
        logger.error('Отсутствие ожидаемых ключей в ответе API')
        raise KeyError("Отсутствует ключ 'homework_name' в ответе API")
    homework_name = homework['homework_name']
    if 'status' not in homework:
        logger.error('Отсутствие ожидаемых ключей в ответе API')
        raise KeyError("Отсутствует ключ 'status' в ответе API")
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        logger.error('Отсутствие ожидаемого статуса проверки работы')
        raise KeyError(f'Отсутствует ключ {homework_status} в статусах работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    "Функция запуска Телеграм-бота."
    if not check_tokens():
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 100000
    status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                send_message(bot, message)
            else:
                logger.debug('Отсутствие в ответе новых статусов')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != status:
                status = message
                send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
