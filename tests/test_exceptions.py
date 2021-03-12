from unittest import TestCase
from Tea.exceptions import RetryError, UnretryableException, TeaException, RequiredArgumentException
from Tea.request import TeaRequest
import sys


class TestTeaException(TestCase):
    def test_retry_error(self):
        try:
            raise RetryError('test_retry_error')
        except RetryError as e:
            self.assertEqual('test_retry_error', e.message)

    def test_unretryable_exception(self):
        request = TeaRequest()
        ex = Exception("test exception")
        try:
            raise UnretryableException(request, ex)
        except UnretryableException as e:
            self.assertIsNotNone(e)
            self.assertIsNotNone(e.last_request)
            if sys.version_info[0:2] == (3, 6):
                self.assertEqual("Exception('test exception',)", e.message)
            else:
                self.assertEqual("Exception('test exception')", e.message)

        e = TeaException({
            'code': 'error code',
            'message': 'error message',
            'data': 'data',
        })
        try:
            raise UnretryableException(request, e)
        except UnretryableException as e:
            self.assertEqual('Error: error code error message Response: data', str(e))
            self.assertEqual('error code', e.code)
            self.assertEqual('error message', e.message)
            self.assertEqual('data', e.data)

    def test_tea_exception(self):
        dic = {"code": "200", "message": "message", "data": {"test": "test"}}
        try:
            raise TeaException(dic)
        except TeaException as e:
            self.assertIsNotNone(e)
            self.assertEqual("200", e.code)
            self.assertEqual("message", e.message)
            self.assertIsNotNone(e.data)
            self.assertEqual("test", e.data.get("test"))

    def test_RequiredArgumentException(self):
        param_name = 'name'
        try:
            raise RequiredArgumentException(param_name)
        except RequiredArgumentException as e:
            self.assertEqual('"name" is required.', str(e))
