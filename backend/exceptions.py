"""Доменні помилки. Сервіси кидають їх, а HTTP-код визначає лише обробник у main.py."""


class DomainError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404


class ForbiddenError(DomainError):
    status_code = 403
