from http import HTTPStatus
import logging
from logging import StreamHandler
import os
import requests
import sys
import time
from typing import Optional

from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiException

from exceptions import (
    EndpointNotWork,
    MessageNotSent,
    NoHomeworkName,
    NotExpectedAPIKeys,
    NotExpectedAPIStatus,
    UnexpectedHomeworkStatus
)

load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s'
)
logger = logging.getLogger(__name__)
handler = StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


PRACTICUM_TOKEN: Optional[str] = os.getenv('PRACTICUM_TOKEN')
"""Токен API."""

TELEGRAM_TOKEN: Optional[str] = os.getenv('TELEGRAM_TOKEN')
"""Токен от телеграм бота."""

TELEGRAM_CHAT_ID: Optional[str] = os.getenv('TELEGRAM_CHAT_ID')
"""ID чата для отправки сообщения."""

RETRY_PERIOD: int = 600
"""Кол-во секунд для запроса на сервер."""

ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
"""URL API для запроса."""

HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
"""Headers для запроса."""


HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
"""Словарь с возможными статусами домашней работы."""


def check_tokens() -> None:
    """Проверяет доступность необходимых переменных окружения."""
    if not all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]):
        logger.critical('Отсутствие обязательных переменных окружения.')
        raise SystemExit


def send_message(bot: TeleBot, message: str) -> None:
    """Отправляет сообщение."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.debug('Удачная отправка сообщения в Telegram.')
    except ApiException as error:
        raise MessageNotSent(f'ApiException возникло: {error}')
    except Exception as error:
        raise MessageNotSent(f'Cбой при отправке сообщения: {error}')


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        api_answer = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp})

        status_code = api_answer.status_code

        if status_code == HTTPStatus.OK:
            return api_answer.json()
        elif status_code == HTTPStatus.BAD_REQUEST:
            raise NotExpectedAPIStatus('Wrong from_date format.')
        elif status_code == HTTPStatus.UNAUTHORIZED:
            raise NotExpectedAPIStatus('Учетные данные не были предоставлены.')
        else:
            raise NotExpectedAPIStatus(f'Статус API {status_code}')

    except Exception as error:
        raise EndpointNotWork(f'Недоступность эндпоинта: {error}.')


def check_response(response: dict) -> None:
    """Проверяет ответ API."""
    if not isinstance(response, dict):
        raise TypeError('Ответ от API не типа словарь.')

    if ('current_date' not in response) and ('homeworks' not in response):
        raise NotExpectedAPIKeys('Отсутствие ожидаемых ключей в ответе API.')

    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        message = 'Вернулся не тип список домашней работы.'
        raise TypeError(message)


def parse_status(homework: dict) -> str:
    """Подготавливает статус домашней работы для отправки."""
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise NoHomeworkName('Нет названия домашней работы.')

    status = homework.get('status')
    if not status:
        raise UnexpectedHomeworkStatus('Нет статуса.')

    verdict = HOMEWORK_VERDICTS.get(status)
    if not verdict:
        raise UnexpectedHomeworkStatus('Недокументированный статус.')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    homework_status = ''
    check_error = ''

    while True:
        try:
            api_answer = get_api_answer(timestamp=timestamp)
            check_response(api_answer)
            homeworks = api_answer.get('homeworks')
            timestamp = api_answer.get('current_date')

            if not homeworks:
                logger.debug('Пустой список домашних работ.')
            else:
                homework = homeworks[-1]
                status = homework.get('status')

                if status != homework_status:
                    message = parse_status(homework)
                    homework_status = status
                    send_message(bot, message)
                else:
                    logger.debug('Oтсутствие в ответе новых статусов.')

        except (
            EndpointNotWork,
            TypeError,
            NotExpectedAPIStatus,
            NoHomeworkName,
            MessageNotSent
        ) as error:
            logger.error(error)

        except (NotExpectedAPIKeys, UnexpectedHomeworkStatus) as error:
            logger.error(error)
            if error != check_error:
                send_message(bot, error)
                check_error = error

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
