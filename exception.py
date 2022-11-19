class APINotResponding(Exception):
    """API не отвечает."""

    pass


class APINotKeysException(Exception):
    """Отсутствие ожидаемых ключей в ответе API."""

    pass


class EmptyDictException(Exception):
    """Ответ от API содержит пустой словарь"""

    pass
