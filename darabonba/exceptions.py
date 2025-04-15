from Tea.exceptions import UnretryableException as TeaUnretryableException
from Tea.exceptions import RequiredArgumentException as TeaRequiredArgumentException
from Tea.exceptions import TeaException
from darabonba.policy.retry import RetryPolicyContext
from typing import Any, Optional


class DaraException(TeaException):
    def __init__(self, dic):
        super().__init__(dic)
        self.code = dic.get("code")
        self.message = dic.get("message")
        self.data = dic.get("data")
        self.description = dic.get("description")
        self.accessDeniedDetail = dic.get("accessDeniedDetail")
        if isinstance(dic.get("data"), dict) and dic.get("data").get("statusCode") is not None:
            self.statusCode = dic.get("data").get("statusCode")
        self.name = 'DaraException'

    def __str__(self):
        return f'Error: {self.code} {self.message} Response: {self.data}'

class ResponseException(DaraException):
    def __init__(self, 
                 code: Optional[str] = None,
                 message: Optional[str] = None,
                 status_code: Optional[int] = None,
                 retry_after: Optional[int] = None,
                 data: Optional[dict] = None,
                 access_denied_detail: Optional[dict] = None,
                 description: Optional[str] = None,
                 stack: Optional[str] = None):
        if data and status_code is not None:
            data['statusCode'] = status_code
        super().__init__({
            'code': code,
            'message': message,
            'data': data,
            'description': description,
            'accessDeniedDetail': access_denied_detail
        })
        
        self.name = 'ResponseException'
        self.status_code = status_code
        self.retry_after = retry_after
        self.stack = stack

class ValidateException(Exception):
    pass


class RequiredArgumentException(TeaRequiredArgumentException):
    def __init__(self, arg):
        self.arg = arg

    def __str__(self):
        return f'"{self.arg}" is required.'


class RetryError(Exception):
    def __init__(self, message):
        
        super().__init__({"message":message})
        
        self.message = message
        self.data = None
        self.name = 'RetryError'

class UnretryableException(TeaUnretryableException):
    def __init__(
            self,
            _context: RetryPolicyContext
    ):
        if isinstance(_context.exception, ResponseException):
            raise _context.exception
        
        super().__init__(
            request= _context.http_request,
            ex= _context.exception,
        )
        
        self.name = 'UnretryableException'
        

    def __str__(self):
        return str(self.inner_exception)