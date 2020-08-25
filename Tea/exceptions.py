class TeaException(Exception):
    def __init__(self, dic):
        self.code = dic.get("code")
        self.message = dic.get("message")
        self.data = dic.get("data")


class RequiredArgumentException(TeaException):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return '%s is required.' % self.arg


class RetryError(TeaException):
    def __init__(self, message):
        self.message = message
        self.data = None


class UnretryableException(TeaException):
    def __init__(self, request, ex):
        self.last_request = request
        self.inner_exception = ex
        self.message = "Retry failed: %s" % ex.message


