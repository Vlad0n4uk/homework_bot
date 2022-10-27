"""Исключения"""


class ResponseException(Exception):
    "Ответ сервера не равен 200"


class ServiceDenial(Exception):
    "Отказ в обслуживании"
