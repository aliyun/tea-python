from unittest import TestCase
from darabonba.exceptions import RetryError, UnretryableException, DaraException, RequiredArgumentException, ResponseException, ValidateException
from darabonba.request import DaraRequest
from darabonba.policy.retry import RetryPolicyContext


class TestDaraException(TestCase):
    def test_retry_error(self):
        try:
            raise RetryError('test_retry_error')
        except RetryError as e:
            self.assertEqual('test_retry_error', e.message)

    def test_tea_exception(self):
        dic = {
            "code": "200",
            "message": "message",
            "data": {
                "test": "test",
                "statusCode": 200
            },
            "description": "description",
            "accessDeniedDetail": {
                'AuthAction': 'ram:ListUsers',
                'AuthPrincipalType': 'SubUser',
                'PolicyType': 'ResourceGroupLevelIdentityBassdPolicy',
                'NoPermissionType': 'ImplicitDeny'
            }
        }
        try:
            raise DaraException(dic)
        except DaraException as e:
            self.assertIsNotNone(e)
            self.assertEqual("200", e.code)
            self.assertEqual("message", e.message)
            self.assertIsNotNone(e.data)
            self.assertEqual("test", e.data.get("test"))
            self.assertEqual(200, e.statusCode)
            self.assertEqual("description", e.description)
            self.assertDictEqual({
                'AuthAction': 'ram:ListUsers',
                'AuthPrincipalType': 'SubUser',
                'PolicyType': 'ResourceGroupLevelIdentityBassdPolicy',
                'NoPermissionType': 'ImplicitDeny'
            }, e.accessDeniedDetail)

    def test_dara_exception_with_no_data(self):
        dic = {
            "code": "Bad Request",
            "message": "Bad Request"
        }
        try:
            raise DaraException(dic)
        except DaraException as e:
            self.assertIsNotNone(e)
            self.assertIsNone(e.data)
            self.assertIsNotNone(e.code)

    def test_RequiredArgumentException(self):
        param_name = 'name'
        try:
            raise RequiredArgumentException(param_name)
        except RequiredArgumentException as e:
            self.assertEqual('"name" is required.', str(e))

    def test_response_exception(self):
        response_ex = ResponseException("404", "Not Found", status_code=404)
        self.assertEqual(response_ex.code, "404")
        self.assertEqual(response_ex.message, "Not Found")
        self.assertEqual(response_ex.status_code, 404)

    def test_unretryable_exception(self):
        request = DaraRequest()
        ex = RetryError("test exception")
        context = RetryPolicyContext(
            http_request=request,
            exception=ex
        )

        try:
            raise UnretryableException(context)
        except UnretryableException as e:
            self.assertIsNotNone(e)
            self.assertEqual("test exception", str(e.inner_exception))

        e = DaraException({
            'code': 'error code',
            'message': 'error message',
            'data': 'data',
        })
        context.exception = e
        with self.assertRaises(UnretryableException) as cm:
            raise UnretryableException(context)
        self.assertEqual('Error: error code error message Response: data', str(cm.exception))
        self.assertEqual('error code', cm.exception.inner_exception.code)
        self.assertEqual('error message', cm.exception.inner_exception.message)
        self.assertEqual('data', cm.exception.inner_exception.data)
    
    def test_validate_exception(self):
        with self.assertRaises(ValidateException):
            raise ValidateException("Validation error occurred")