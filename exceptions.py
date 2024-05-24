class EndpointNotWork(Exception):
    """Недоступность endpoint."""


class NotExpectedAPIKeys(Exception):
    """Отсутствие ожидаемых ключей в ответе API."""


class UnexpectedHomeworkStatus(Exception):
    """Неожиданный статус домашней работы."""


class MessageNotSent(Exception):
    """Cбой при отправке сообщения в Telegram."""


class NoHomeworkName(Exception):
    """Нет названия домашней работы."""


class NotExpectedAPIStatus(Exception):
    """Ошибка статуса API ответа."""
