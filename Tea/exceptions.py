from .request import TeaRequest


class TeaException(Exception):
    def __init__(self, dic):
        self.code = dic.get("code")
        self.message = dic.get("message")
        self.data = dic.get("data")

    def __str__(self):
        return f'Error: {self.code} {self.message} Response: {self.data}'


class RequiredArgumentException(TeaException):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f'"{self.arg}" is required.'


class RetryError(TeaException):
    def __init__(self, message):
        self.message = message
        self.data = None


class UnretryableException(TeaException):
    def __init__(
            self,
            request: TeaRequest,
            ex: TeaException
    ):
        self.last_request = request
        self.inner_exception = ex
        self.message = f"Retry failed: {ex.message}"

    def __str__(self):
        return str(self.inner_exception)
