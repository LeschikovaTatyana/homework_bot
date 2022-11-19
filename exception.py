import logging
import os
import sys

from telegram import Bot

import homework


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(filename)s, %(lineno)s, %(message)s'
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)

class MyException(Exception):
    """Класс собственых ошибок."""

    def __init__(self, message):
        """Определяем объект с текстом сообщения."""
        self.message = message

    def __str__(self):
        """Переопределенный вывод отправляет сообщение об ошибке.
        И пишет ошибку в логи.
        """
        global save_error
        if save_error != self.message:
            message = f'Сбой в работе программы: {self.message}'
            logger.error(message)
            homework.send_message(Bot(token=TELEGRAM_TOKEN), message)
            save_error = self.message


class APIRequestingException(MyException):
    """Ошибка при запросе к основному API."""

    pass


class APINotResponding(MyException):
    """API не отвечает."""

    pass


class APINotKeysException(MyException):
    """Отсутствие ожидаемых ключей в ответе API."""

    pass


class EmptyDictException(MyException):
    """Ответ от API содержит пустой словарь"""

    pass
