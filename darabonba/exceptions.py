from darabonba.request import DaraRequest
from Tea.exceptions import UnretryableException as TeaUnretryableException
from darabonba.policy.retry import RetryPolicyContext
from typing import Any, Optional


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

class ResponseException(DaraException):
    def __init__(self, 
                 code: Optional[str] = None,
                 status_code: Optional[int] = None,
                 retry_after: Optional[int] = None,
                 data: Optional[dict] = None,
                 access_denied_detail: Optional[Any] = None,
                 description: Optional[str] = None):

        super().__init__(description)
        
        self.name = 'ResponseException'
        self.code = code
        self.status_code = status_code
        self.retry_after = retry_after
        self.data = data or {}
        self.access_denied_detail = access_denied_detail

        if isinstance(self.data, dict) and 'statusCode' in self.data:
            self.status_code = int(self.data['statusCode'])

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


class UnretryableException(TeaUnretryableException):
    def __init__(
            self,
            _context: RetryPolicyContext
    ):
        super().__init__(
            request= _context.http_request,
            ex= _context.exception,
        )

    def __str__(self):
        return str(self.inner_exception)
