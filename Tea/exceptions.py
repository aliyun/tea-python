class RequiredArgumentException(RuntimeError):
    def __init__(self, arg):
        super().__init__()
        self.arg = arg


class RetryError(RuntimeError):
    def __init__(self, message):
        super().__init__()
        self.message = message
        self.data = None


class UnretryableException(Exception):
    def __init__(self, request, ex):
        super().__init__()
        self.last_request = request
        self.inner_exception = ex
        self.message = "Retry failed:" + ex.message


class TeaException(Exception):
    def __init__(self, dic):
        super().__init__()
        self.code = dic.get("code")
        self.message = dic.get("message")
        self.data = dic.get("data")
