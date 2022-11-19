import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Dict, List, Tuple, Union
import requests
import telegram
from dotenv import load_dotenv
from telegram import Bot

import exception
load_dotenv()

type_dict = Dict[str, List[Tuple[Dict[str, Union[int, str]], ...]]]
type_list = List[Tuple[Dict[str, Union[int, str]], ...]]
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
DELTA_TIME = 3600 * 24 * 7 * 3
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(filename)s, %(lineno)s, %(message)s'
)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения."""
    logger.info('Начало отправки сообщения в Telegram')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Удачная отправка сообщения "{message}" в Telegram.')
    except telegram.error.TelegramError:
        message = f'Cбой при отправке сообщения "{message}" в Telegram.'
        logger.error(message)


def get_api_answer(current_timestamp: int) -> type_dict:
    """Запрос к API."""
    timestamp = current_timestamp or int(time.time())
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    response = requests.get(**request_params)
    if response.status_code != HTTPStatus.OK:
        raise exception.APINotResponding('API не отвечает')
    response = response.json()
    return response


def check_response(response: type_dict) -> type_list:
    """Проверка ответа API на корректность."""
    if response == {}:
        message = 'Ответ от API содержит пустой словарь'
        logger.error(message)
        raise exception.EmptyDictException(message)
    if not isinstance(response, dict):
        message = 'Вернулся не словарь'
        logger.error(message)
        raise TypeError(message)
    if not isinstance(response.get('homeworks'), list):
        message = 'Вернулся не список'
        logger.error(message)
        raise TypeError(message)
    if not response.get('homeworks'):
        message = 'За последние три недели сданных дз нет'
        logger.info(message)
    code = response.get('code')
    if not code:
        return response.get('homeworks')


def parse_status(homework: type_list) -> str:
    """Проверка и формирование сообщения о статусе работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_status:
        message = 'Отсутствие ключей homework_status в ответе API'
        logger.error(message)
        raise KeyError(message)
    if not homework_name:
        message = 'Отсутствие ключей homework_name в ответе API'
        logger.error(message)
        raise KeyError(message)
    if homework_status not in HOMEWORK_STATUSES:
        raise exception.APINotKeysException(
            'Отсутствие ожидаемых ключей в ответе API'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    if all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        return True
    else:
        message = 'Отсутствует обязательная переменная окружения.'
        logger.critical(message)
        return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit('Отсутствует обязательная переменная окружения')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time() - DELTA_TIME)
    save_message = ''
    global last_error
    last_error = ''
    logger.info('Начало работы')
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
                if message != save_message:
                    send_message(bot, message)
                    save_message = message
                else:
                    logger.debug('Новые статусы отсутствуют')
            current_timestamp = int(time.time())
        except Exception as error:
            if last_error != error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                send_message(bot, message)
                last_error = error
        else:
            logger.info('Программа отработала без ошибок')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
