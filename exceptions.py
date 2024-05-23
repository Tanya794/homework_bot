class EndpointNotWork(Exception):
    """Недоступность endpoint."""

    pass


class NotExpectedAPIKeys(Exception):
    """Отсутствие ожидаемых ключей в ответе API."""

    pass


class UnexpectedHomeworkStatus(Exception):
    """Неожиданный статус домашней работы."""

    pass


class MessageNotSent(Exception):
    """Cбой при отправке сообщения в Telegram."""

    pass


class NoHomeworkName(Exception):
    """Нет названия домашней работы."""

    pass


class NotExpectedAPIStatus(Exception):
    """Ошибка статуса API ответа."""

    pass
