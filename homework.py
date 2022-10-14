"""Создаем Телеграм-бота, способного оповещать пользователя
при получении результатов проверки код-ревью"""


import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater

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

ALL_TOKENS = [
    PRACTICUM_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
]

logging.basicConfig(  # Глобальная настройка логов
    level=logging.DEBUG,
    filename='main.log',  # Запись логов в файл
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)


class NotOkResponseException(Exception):
    pass


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    if all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        return True
    logging.critical('Отсутствует обязательная переменная окружения')


def send_message(bot, message):
    """"Функция отправки сообщения с уведомолением
    об изменении статуса код-ревью."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
        logging.info('Сообщение отправлено')
    except Exception:
        logging.exception('Не удалось отправить сообщение')


def get_api_answer(current_timestamp):
    """Функция делает запрос к API Практикум.Домашка"""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            NotOkResponseException('Ваш запрос не может быть отработан')
            logging.error('Ошибка при запросе к API')
    except Exception:
        NotOkResponseException('Ваш запрос не может быть отработан')
        logging.error('Неизвестная ошибка')
    return response.json()


def check_response(response):
    """Функция проверяет ответ от API на корректность.
    Возвращает список домашних работ при корректном ответе API."""
    ...


def parse_status(homework):
    """Функция определяет статус работы отправленной на код-ревью."""
    homework_name = ...
    homework_status = ...

    ...

    verdict = ...

    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    ...

    while True:
        try:
            response = ...

            ...

            current_timestamp = ...
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()