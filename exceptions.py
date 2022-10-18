"""Исключения"""


class ResponseException(Exception):
    "Ответ сервера не равен 200"


class RequestExceptionError(Exception):
    """Ошибка запроса."""
