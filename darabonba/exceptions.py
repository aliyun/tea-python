from darabonba.request import DaraRequest


class DaraException(Exception):
    def __init__(self, dic):
        self.code = dic.get("code")
        self.message = dic.get("message")
        self.data = dic.get("data")
        self.description = dic.get("description")
        self.accessDeniedDetail = dic.get("accessDeniedDetail")
        if isinstance(dic.get("data"), dict) and dic.get("data").get("statusCode") is not None:
            self.statusCode = dic.get("data").get("statusCode")

    def __str__(self):
        return f'Error: {self.code} {self.message} Response: {self.data}'


class ValidateException(Exception):
    pass


class RequiredArgumentException(ValidateException):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f'"{self.arg}" is required.'


class RetryError(Exception):
    def __init__(self, message):
        self.message = message
        self.data = None


class UnretryableException(DaraException):
    def __init__(
            self,
            request: DaraRequest,
            ex: Exception
    ):
        self.last_request = request
        self.inner_exception = ex
        if isinstance(ex, DaraException):
            super().__init__({
                'code': ex.code,
                'message': ex.message,
                'data': ex.data
            })
        else:
            super().__init__({
                'message': repr(ex),
            })

    def __str__(self):
        return str(self.inner_exception)
