import unittest
from unittest import TestCase
from darabonba.exceptions import RetryError, UnretryableException, DaraException, RequiredArgumentException, ResponseException, RetryPolicyContext
from unittest.mock import Mock


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
    def test_response_exception_initialization(self):
        code = "400"
        message = "Bad Request"
        status_code = 400
        retry_after = 30
        data = {"key": "value"}
        access_denied_detail = {"detail": "Access Denied"}
        description = "Request failed"

        response_exception = ResponseException(
            code=code,
            message=message,
            status_code=status_code,
            retry_after=retry_after,
            data=data,
            access_denied_detail=access_denied_detail,
            description=description
        )

        self.assertEqual(response_exception.code, code)
        self.assertEqual(response_exception.message, message)
        self.assertEqual(response_exception.status_code, status_code)
        self.assertEqual(response_exception.retry_after, retry_after)
        self.assertEqual(response_exception.data, data)
        self.assertEqual(response_exception.accessDeniedDetail, access_denied_detail)
        self.assertEqual(response_exception.description, description)

        expected_str = f'Error: {code} {message} Response: {data}'
        self.assertEqual(str(response_exception), expected_str)

    def test_response_exception_status_code(self):
        response_exception = ResponseException(status_code=403)

        self.assertEqual(response_exception.status_code, 403)
    def test_unretryable_exception(self):
        mock_context = Mock()
        mock_context.exception = None
        mock_context.http_request = "mock_request"

        unretryable_exception = UnretryableException(mock_context)
        self.assertEqual(unretryable_exception.last_request, mock_context.http_request)

        mock_context.exception = ResponseException(
            code="500",
            message="Internal Server Error",
            data={"error": "something went wrong"}
        )

        with self.assertRaises(ResponseException) as context:
            UnretryableException(mock_context)

        self.assertEqual(str(context.exception), str(mock_context.exception))

    def test_unretryable_exception_str(self):
        data_with_error = {"error": "something went wrong"}
        
        mock_exception = DaraException({
            "code": "500",
            "message": "Internal Server Error",
            "data": data_with_error
        })
        
        context = Mock(spec=RetryPolicyContext)
        context.exception = mock_exception
        context.http_request = "mock_request"

        unretryable_exception = UnretryableException(_context=context)

        self.assertEqual(str(unretryable_exception), str(mock_exception))