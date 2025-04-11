import asyncio
import threading
import time
import pytest
import unittest
import ssl
import io
from http.server import BaseHTTPRequestHandler, HTTPServer
from requests import PreparedRequest 
from unittest import mock
from darabonba.core import DaraCore, _TLSAdapter, TLSVersion, _ModelEncoder
from darabonba.exceptions import RetryError, DaraException
from darabonba.model import DaraModel
from darabonba.request import DaraRequest
from darabonba.utils.stream import BaseStream
from darabonba.policy.retry import RetryPolicyContext, RetryOptions, RetryCondition, BackoffPolicy

MAX_DELAY_TIME = 120 * 1000
MIN_DELAY_TIME = 100
@pytest.fixture(scope='session', autouse=True)
def asyncio_setup():
    loop = asyncio.get_event_loop()
    yield loop

# Mock HTTP request handler
class Request(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        body = self.rfile.read(int(self.headers['content-length']))
        self.wfile.write(b'{"result": "%s"}' % body)

def run_server():
    server = HTTPServer(('localhost', 8889), Request)
    server.serve_forever()

# Stream mock class for testing
class DaraStream(BaseStream):
    def __init__(self):
        super().__init__()
        self.content = b'Dara test'

    def read(self, size=1024):
        content = self.content
        self.content = b''
        return content

    def __len__(self):
        return len(b'Dara test')

    def __next__(self):
        content = self.read()
        if content:
            return content
        else:
            raise StopIteration

class BaseUserResponse(DaraModel):
    def __init__(self):
        super().__init__()
        self.avatar = None
        self.createdAt = None
        self.defaultDriveId = None
        self.description = None
        self.domainId = None
        self.email = None
        self.nickName = None
        self.phone = None
        self.role = None
        self.status = None
        self.updatedAt = None
        self.userId = None
        self.userName = None
        self.array = []
    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map
        
        return {
            'avatar': self.avatar,
            'createdAt': self.createdAt,
            'defaultDriveId': self.defaultDriveId,
            'description': self.description,
            'domainId': self.domainId,
            'email': self.email,
            'nickName': self.nickName,
            'phone': self.phone,
            'role': self.role,
            'status': self.status,
            'updatedAt': self.updatedAt,
            'userId': self.userId,
            'userName': self.userName,
            'array': self.array,
        }

    def from_map(self, map=None):
        dic = map or {}
        self.avatar = dic.get('avatar')
        self.createdAt = dic.get('createdAt')
        self.defaultDriveId = dic.get('defaultDriveId')
        self.description = dic.get('description')
        self.domainId = dic.get('domainId')
        self.email = dic.get('email')
        self.nickName = dic.get('nickName')
        self.phone = dic.get('phone')
        self.role = dic.get('role')
        self.status = dic.get('status')
        self.updatedAt = dic.get('updatedAt')
        self.userId = dic.get('userId')
        self.userName = dic.get('userName')
        self.array = []
        if dic.get('array') is not None:
            for i in dic.get('array'):
                self.array.append(i)
        return self
        
class TestModel(DaraModel):
    def __init__(self):
        self.test_a = 'a'
        self.test_b = 'b'

    def validate(self):
        raise ValueError('test validate')

    def to_map(self):
        return {
            'test_a': self.test_a,
            'test_b': self.test_b
        }

class TestCore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        server = threading.Thread(target=run_server)
        server.daemon = True
        server.start()
    
    def test_default_with_dara_model(self):
        mock_model = mock.Mock(spec=DaraModel)
        mock_model.to_map.return_value = {'key': 'value'}
        
        encoder = _ModelEncoder()
        result = encoder.default(mock_model)
        self.assertEqual(result, {'key': 'value'})

    def test_default_with_bytes(self):
        encoder = _ModelEncoder()
        result = encoder.default(b'binary data')
        self.assertEqual(result, 'binary data')

    def test_default_with_other_type(self):
        encoder = _ModelEncoder()
        with self.assertRaises(TypeError):
            result = encoder.default(123)

    def test_default_with_string(self):
        encoder = _ModelEncoder()
        with self.assertRaises(TypeError):
            result = encoder.default("normal string")
    def test_to_json_string(self):
        self.assertEqual('test string for to_jsonstring',
                         DaraCore.to_json_string('test string for to_jsonstring'))
        self.assertEqual('{"key":"value"}',
                         DaraCore.to_json_string({"key": "value"}))
        model = TestModel()
        any_dict = {
            'bytes': b'100',
            'str': '100',
            'int': 100,
            'model': model,
            'float': 100.1,
            'bool': True,
            'utf8': '你好'
        }
        self.assertEqual(
            '{"bytes":"100","str":"100","int":100,"model":{"test_a":"a","test_b":"b"},"float":100.1,"bool":true,"utf8":"你好"}',
            DaraCore.to_json_string(any_dict)
        )

    def test_to_json_string_with_dict(self):
        result = DaraCore.to_json_string({"key": "value"})
        self.assertEqual(result, '{"key":"value"}')

    def test_to_json_string_with_list(self):
        result = DaraCore.to_json_string(["item1", "item2", "item3"])
        self.assertEqual(result, '["item1","item2","item3"]')
    
    def test_to_json_string_with_number(self):
        result = DaraCore.to_json_string(123)
        self.assertEqual(result, '123')

        result = DaraCore.to_json_string(123.456)
        self.assertEqual(result, '123.456')

    def test_to_json_string_with_boolean(self):
        result = DaraCore.to_json_string(True)
        self.assertEqual(result, 'true')

        result = DaraCore.to_json_string(False)
        self.assertEqual(result, 'false')

    def test_to_json_string_with_none(self):
        result = DaraCore.to_json_string(None)
        self.assertEqual(result, 'null')

    def test_to_json_string_with_bytes(self):
        result = DaraCore.to_json_string(b'bytes data')
        self.assertEqual(result, '"bytes data"')
    
    def test_set_tls_minimum_version_with_tls_v1(self):
        context = mock.MagicMock()
        result = DaraCore._set_tls_minimum_version(context, 'TLSv1')
        self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1)
        self.assertEqual(result, context)

    def test_set_tls_minimum_version_with_tls_v1_1(self):
        context = mock.MagicMock()
        result = DaraCore._set_tls_minimum_version(context, 'TLSv1.1')
        self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_1)
        self.assertEqual(result, context)

    def test_set_tls_minimum_version_with_tls_v1_2(self):
        context = mock.MagicMock()
        result = DaraCore._set_tls_minimum_version(context, 'TLSv1.2')
        self.assertEqual(context.minimum_version, ssl.TLSVersion.TLSv1_2)
        self.assertEqual(result, context)
    
    def test_prepare_http_debug_EmptyHeaders_ReturnsEmptyString(self):
        request = PreparedRequest()
        request.prepare_headers({})

        result = DaraCore._prepare_http_debug(request, '*')

        self.assertEqual(result, '')

    def test_prepare_http_debug_SingleHeader_ReturnsFormattedString(self):
        request = PreparedRequest()
        request.prepare_headers({'Content-Type': 'application/json'})

        result = DaraCore._prepare_http_debug(request, '*')

        self.assertEqual(result, '\n* Content-Type : application/json')

    def test_prepare_http_debug_MultipleHeaders_ReturnsFormattedString(self):
        request = PreparedRequest()
        request.prepare_headers({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer token'
        })

        result = DaraCore._prepare_http_debug(request, '*')

        self.assertEqual(result, '\n* Content-Type : application/json\n* Authorization : Bearer token')
    
    def test_merge_with_model(self):
        model = BaseUserResponse()
        model.phone = '139xxx'
        result = DaraCore.merge(model, {'key': 'value'})
        self.assertEqual(result['phone'], '139xxx')
        self.assertEqual(result['key'], 'value')

    def test_compose_url(self):
        request = DaraRequest()
        try:
            DaraCore.compose_url(request)
        except Exception as e:
            self.assertEqual('"endpoint" is required.', str(e))

        request.headers['host'] = "fake.domain.com"
        self.assertEqual("http://fake.domain.com",
                         DaraCore.compose_url(request))

        request.headers['host'] = "http://fake.domain.com"
        self.assertEqual("http://fake.domain.com",
                         DaraCore.compose_url(request))

        request.port = 8080
        self.assertEqual("http://fake.domain.com:8080",
                         DaraCore.compose_url(request))

        request.pathname = "/index.html"
        self.assertEqual("http://fake.domain.com:8080/index.html",
                         DaraCore.compose_url(request))

        request.query["foo"] = ""
        self.assertEqual("http://fake.domain.com:8080/index.html?foo=",
                         DaraCore.compose_url(request))

        request.query["foo"] = "bar"
        self.assertEqual("http://fake.domain.com:8080/index.html?foo=bar",
                         DaraCore.compose_url(request))

        request.pathname = "/index.html?a=b"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         DaraCore.compose_url(request))

        request.pathname = "/index.html?a=b&"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         DaraCore.compose_url(request))

        request.query["fake"] = None
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         DaraCore.compose_url(request))
    def test_bytes_readable(self):
        body = "test".encode('utf-8')
        self.assertIsNotNone(DaraCore.bytes_readable(body))

    def test_do_action_with_invalid_host(self):
        request = DaraRequest()
        request.headers['host'] = "invalid.host"
        request.method = "GET"
        with self.assertRaises(RetryError):
            DaraCore.do_action(request)

    def test_get_response_body_with_empty_content(self):
        mock_resp = mock.Mock()
        mock_resp.content = b''
        self.assertEqual(DaraCore.get_response_body(mock_resp), '')

    def test_is_retryable_with_non_retryable_exception(self):
        self.assertFalse(DaraCore.is_retryable(Exception("A general exception")))
        
    def test_sleep_functionality(self):
        start_time = time.time()
        DaraCore.sleep(1000)
        elapsed_time = time.time() - start_time
        self.assertTrue(0.99 <= elapsed_time <= 1.01)

    def test_tls_adapter_initialization(self):
        adapter = DaraCore.get_adapter('https', 'TLSv1.2')
        self.assertIsInstance(adapter, _TLSAdapter)
    
    def test_allow_retry(self):
        self.assertTrue(DaraCore.allow_retry(None, 0))
        dic = {}
        self.assertTrue(DaraCore.allow_retry(dic, 0))
        dic["retryable"] = True
        dic["maxAttempts"] = 3
        self.assertTrue(DaraCore.allow_retry(dic, 0))
        self.assertFalse(DaraCore.allow_retry(dic, 4))
        dic["maxAttempts"] = None
        self.assertFalse(DaraCore.allow_retry(dic, 1))
        dic["retryable"] = False
        dic["maxAttempts"] = 3
        self.assertTrue(DaraCore.allow_retry(dic, 0))
        self.assertFalse(DaraCore.allow_retry(dic, 1))
    
    def test_should_retry(self):
        ctx = RetryPolicyContext()

        ctx.retries_attempted = 0
        options = RetryOptions({"retryable": True})
        self.assertTrue(DaraCore.should_retry(options, ctx))

        ctx.retries_attempted = 1
        options = RetryOptions({"retryable": False})
        self.assertFalse(DaraCore.should_retry(options, ctx))

        condition = RetryCondition({"exception": [Exception]})
        options = RetryOptions({
            "retryable": True,
            "no_retry_condition": [condition]
        })
        ctx.exception = Exception()
        self.assertFalse(DaraCore.should_retry(options, ctx))

        options = RetryOptions({
            "retryable": True,
            "retryCondition": [{"exception": ['DaraException'], "maxAttempts": 3}]
        })

        ctx.retries_attempted = 0
        ctx.exception = DaraException({})
        self.assertTrue(DaraCore.should_retry(options, ctx))

        ctx.retries_attempted = 1
        self.assertTrue(DaraCore.should_retry(options, ctx))
        ctx.retries_attempted = 4
        self.assertFalse(DaraCore.should_retry(options, ctx))
    def test_sleep_async_functionality(self):
        start_time = time.time()
        asyncio.run(DaraCore.sleep_async(1000))
        elapsed_time = time.time() - start_time
        self.assertTrue(0.99 <= elapsed_time <= 1.01)
    
    def test_do_action(self):
        request = DaraRequest()
        request.headers['host'] = "www.alibabacloud.com"
        request.pathname = "/s/zh"
        request.query["k"] = "ecs"
        option = None
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertIsNotNone(bytes.decode(resp.body))

        option = {
            "timeout": None,
            "readTimeout": None,
            "connectTimeout": None,
        }
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertIsNotNone(bytes.decode(resp.body))

        option = {
            "readTimeout": 20000,
            "connectTimeout": 10000,
            "httpProxy": None,
            "httpsProxy": None,
            "noProxy": None,
            "maxIdleConns": None,
            "retry": {
                "retryable": None,
                "maxAttempts": None
            },
            "backoff": {
                "policy": None,
                "period": None
            },
            'debug': 'sdk',
            "ignoreSSL": None,
            "tlsMinVersion": TLSVersion.TLSv1_2
        }
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertIsNotNone(bytes.decode(resp.body))

        option = {
            "readTimeout": 20000,
            "connectTimeout": 10000,
            "httpProxy": None,
            "httpsProxy": None,
            "noProxy": None,
            "maxIdleConns": None,
            "retry": {
                "retryable": None,
                "maxAttempts": None
            },
            "backoff": {
                "policy": None,
                "period": None
            },
            'debug': 'sdk',
            "ignoreSSL": True,
            "tlsMinVersion": TLSVersion.TLSv1_2
        }
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertIsNotNone(bytes.decode(resp.body))

        request.headers['host'] = "127.0.0.1:8889"
        request.method = "POST"
        request.protocol = "http"
        request.body = "{'test': [{'id': 'id', 'name': '中文'}]}"
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}', bytes.decode(resp.body))

        request.body = "{'test': [{'id': 'id', 'name': '\u4e2d\u6587'}]}"
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}', bytes.decode(resp.body))

        request.body = b"{'test': [{'id': 'id', 'name': '\xe4\xb8\xad\xe6\x96\x87\'}]}"
        resp = DaraCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}', bytes.decode(resp.body))

        option['httpProxy'] = '127.0.0.1'
        option['httpsProxy'] = '127.0.0.1'
        option['noProxy'] = '127.0.0.1'
        try:
            DaraCore.do_action(request, option)
            assert False
        except Exception as e:
            self.assertIsInstance(e, RetryError)
        
    def test_async_do_action(self):
        request = DaraRequest()
        request.headers['host'] = "www.alibabacloud.com"
        request.pathname = "/s/zh"
        request.query["k"] = "ecs"
        option = None
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            DaraCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertIsNotNone(bytes.decode(response.body))

        option = {
            "timeout": None,
            "readTimeout": None,
            "connectTimeout": None,
        }
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            DaraCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertIsNotNone(bytes.decode(response.body))

        option = {
            "readTimeout": 20000,
            "connectTimeout": 10000,
            "httpProxy": None,
            "httpsProxy": None,
            "noProxy": None,
            "maxIdleConns": None,
            "retry": {
                "retryable": None,
                "maxAttempts": None
            },
            "backoff": {
                "policy": None,
                "period": None
            },
            "ignoreSSL": None,
            "tlsMinVersion": TLSVersion.TLSv1_2
        }
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            DaraCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertIsNotNone(bytes.decode(response.body))

        request.headers['host'] = "127.0.0.1:8889"
        request.method = "POST"
        request.protocol = "http"
        request.body = "{'test': [{'id': 'id', 'name': '中文'}]}"
        task = asyncio.ensure_future(
            DaraCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}',
                         bytes.decode(response.body))

        request.body = "{'test': [{'id': 'id', 'name': '\u4e2d\u6587'}]}"
        task = asyncio.ensure_future(
            DaraCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}',
                         bytes.decode(response.body))

        request.body = b"{'test': [{'id': 'id', 'name': '\xe4\xb8\xad\xe6\x96\x87\'}]}"
        task = asyncio.ensure_future(
            DaraCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}',
                         bytes.decode(response.body))

        request.protocol = 'http'
        option['httpProxy'] = 'http://127.0.0.1'
        try:
            loop.run_until_complete(DaraCore.async_do_action(request, option))
            assert False
        except Exception as e:
            self.assertIsInstance(e, RetryError)
    
    def test_to_number(self):
        # Test the case with different inputs

        self.assertEqual(DaraCore.to_number(42), 42)

        self.assertEqual(DaraCore.to_number("100"), 100)

        self.assertEqual(DaraCore.to_number(3.14), 3)

        with self.assertRaises(ValueError):
            DaraCore.to_number("not_a_number")
        self.assertEqual(DaraCore.to_number(None), 0)
        self.assertEqual(DaraCore.to_number(""), 0)
        self.assertEqual(DaraCore.to_number("-15"), -15)
        self.assertEqual(DaraCore.to_number(-7.89), -7)
        self.assertEqual(DaraCore.to_number([]), 0) 
        self.assertEqual(DaraCore.to_number({}), 0) 
    
    def test_to_map(self):
        model = BaseUserResponse()
        model.phone = '139xxx'
        model.domainId = 'domainId'
        m = DaraCore.to_map(model)
        self.assertEqual('139xxx', m['phone'])
        self.assertEqual('domainId', m['domainId'])
        m = DaraCore.to_map(None)
        self.assertEqual({}, m)

        model = BaseUserResponse()
        model._map = {'phone': '139xxx'}
        m = DaraCore.to_map(model)
        self.assertEqual({'phone': '139xxx'}, m)

    def test_from_map(self):
        model = BaseUserResponse()
        model.phone = '139xxx'
        model.domainId = 'domainId'
        m = {
            'phone': '138',
            'domainId': 'test'
        }
        model1 = DaraCore.from_map(model, m)
        self.assertEqual('138', model1.phone)
        self.assertEqual('test', model1.domainId)

        m = {
            'phone': '138',
            'domainId': 'test',
            'array': [123]
        }
        model2 = DaraCore.from_map(model, m)
        not_model = DaraCore.from_map({}, m)
        self.assertEqual({}, not_model)
        self.assertEqual([123], model2.array)
    
    def test_is_null(self):
        self.assertTrue(DaraCore.is_null(None), "Expected is_null(None) to return True")
        self.assertFalse(DaraCore.is_null(0), "Expected is_null(0) to return False")
        self.assertFalse(DaraCore.is_null(""), "Expected is_null('') to return False")
        self.assertFalse(DaraCore.is_null([]), "Expected is_null([]) to return False")
        self.assertFalse(DaraCore.is_null({}), "Expected is_null({}) to return False")
        self.assertFalse(DaraCore.is_null(False), "Expected is_null(False) to return False")
    
    def test_to_readable_stream(self):
        data_str = "Hello, World!"
        stream_str = DaraCore.to_readable_stream(data_str)
        self.assertIsInstance(stream_str, io.StringIO)
        self.assertEqual(stream_str.read(), data_str)

        data_bytes = b"Hello, World!"
        stream_bytes = DaraCore.to_readable_stream(data_bytes)
        self.assertIsInstance(stream_bytes, io.BytesIO)
        self.assertEqual(stream_bytes.read(), data_bytes)

        with self.assertRaises(TypeError) as cm:
            DaraCore.to_readable_stream(123)
        self.assertEqual(str(cm.exception), "Input data must be of type str or bytes")

        with self.assertRaises(TypeError) as cm:
            DaraCore.to_readable_stream([])
        self.assertEqual(str(cm.exception), "Input data must be of type str or bytes")

        with self.assertRaises(TypeError) as cm:
            DaraCore.to_readable_stream({})
        self.assertEqual(str(cm.exception), "Input data must be of type str or bytes")
    
    def test_async_stream_upload(self):
        request = DaraRequest()
        request.method = 'POST'
        request.protocol = 'http'
        request.headers['host'] = "127.0.0.1:8889"
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(DaraCore.async_do_action(request))
        f = DaraStream()
        request.body = f
        loop.run_until_complete(task)
        self.assertEqual(b'{"result": "Dara test"}', task.result().body)
    
    def test_get_adapter(self):
        # Test TLSv1
        with mock.patch('darabonba.core.ssl.create_default_context') as mock_create_default_context:
            mock_context = mock.Mock()
            mock_create_default_context.return_value = mock_context

            adapter = DaraCore.get_adapter('https', 'TLSv1')
            self.assertEqual(mock_context.minimum_version, ssl.TLSVersion.TLSv1)

        # Test TLSv1.1
        with mock.patch('darabonba.core.ssl.create_default_context') as mock_create_default_context:
            mock_context = mock.Mock()
            mock_create_default_context.return_value = mock_context

            adapter = DaraCore.get_adapter('https', 'TLSv1.1')
            self.assertEqual(mock_context.minimum_version, ssl.TLSVersion.TLSv1_1)

        # Test TLSv1.2
        with mock.patch('darabonba.core.ssl.create_default_context') as mock_create_default_context:
            mock_context = mock.Mock()
            mock_create_default_context.return_value = mock_context

            adapter = DaraCore.get_adapter('https', 'TLSv1.2')
            self.assertEqual(mock_context.minimum_version, ssl.TLSVersion.TLSv1_2)

        # Test TLSv1.3
        with mock.patch('darabonba.core.ssl.create_default_context') as mock_create_default_context:
            mock_context = mock.Mock()
            mock_create_default_context.return_value = mock_context

            adapter = DaraCore.get_adapter('https', 'TLSv1.3')
            self.assertEqual(mock_context.minimum_version, ssl.TLSVersion.TLSv1_3)

        # Test invalid TLS version
        with mock.patch('darabonba.core.ssl.create_default_context') as mock_create_default_context:
            mock_context = mock.Mock()
            mock_create_default_context.return_value = mock_context

            adapter = DaraCore.get_adapter('https', 'TLSv1.4')
            self.assertNotIsInstance(mock_context.minimum_version, ssl.TLSVersion)

        # Test HTTP protocol
        with mock.patch('darabonba.core.ssl.create_default_context') as mock_create_default_context:
            mock_context = mock.Mock()
            mock_create_default_context.return_value = mock_context

            adapter = DaraCore.get_adapter('http', 'TLSv1.2')
            self.assertNotIsInstance(mock_context.minimum_version, ssl.TLSVersion)

    def test_get_session(self):
        request = DaraRequest()
        request.headers['host'] = "127.0.0.1:9999"
        request.protocol = "https"
        session_key = f'{request.protocol.lower()}://{request.headers["host"]}:{request.port}'

        # Test with TLSv1.2
        with mock.patch('darabonba.core.DaraCore.get_adapter') as mock_get_adapter:
            mock_adapter = mock.Mock()
            mock_get_adapter.return_value = mock_adapter

            session = DaraCore._get_session(session_key, request.protocol, 'TLSv1.2')
            mock_get_adapter.assert_called_once_with(request.protocol, 'TLSv1.2')
            self.assertIn(session_key, DaraCore._sessions)
            self.assertEqual(session, DaraCore._sessions[session_key])

        # Test with TLSv1.3
        with mock.patch('darabonba.core.DaraCore.get_adapter') as mock_get_adapter:
            mock_adapter = mock.Mock()
            mock_get_adapter.return_value = mock_adapter

            session = DaraCore._get_session(session_key, request.protocol, 'TLSv1.3')
            mock_get_adapter.assert_not_called()  # Should not call get_adapter again
            self.assertIn(session_key, DaraCore._sessions)
            self.assertEqual(session, DaraCore._sessions[session_key])

        # Test with HTTP protocol
        request.protocol = "http"
        session_key = f'{request.protocol.lower()}://{request.headers["host"]}:{request.port}'

        with mock.patch('darabonba.core.DaraCore.get_adapter') as mock_get_adapter:
            mock_adapter = mock.Mock()
            mock_get_adapter.return_value = mock_adapter

            session = DaraCore._get_session(session_key, request.protocol, 'TLSv1.2')
            mock_get_adapter.assert_called_once_with(request.protocol, 'TLSv1.2')
            self.assertIn(session_key, DaraCore._sessions)
            self.assertEqual(session, DaraCore._sessions[session_key])

        # Test session caching
        with mock.patch('darabonba.core.DaraCore.get_adapter') as mock_get_adapter:
            mock_adapter = mock.Mock()
            mock_get_adapter.return_value = mock_adapter

            session = DaraCore._get_session(session_key, request.protocol, 'TLSv1.2')
            mock_get_adapter.assert_not_called()  # Should not call get_adapter again
            self.assertIn(session_key, DaraCore._sessions)
            self.assertEqual(session, DaraCore._sessions[session_key])

class TestGetBackoffTime(unittest.TestCase):
    def setUp(self):
        self.retry_error = RetryError("Test error")
        self.retry_condition = {"exception": ["RetryError"], "errorCode": [500], "maxDelay": 1000, "maxAttempts": 3}
        self.retry_options = RetryOptions({"retryCondition": [self.retry_condition]})

    def test_get_backoff_time_ExceptionNameMatch_ReturnsCorrectBackoffTime(self):
        self.retry_error.name = "RetryError"
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertGreater(result, 0)

    def test_get_backoff_time_ErrorCodeMatch_ReturnsCorrectBackoffTime(self):
        self.retry_error.code = 500
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertGreater(result, 0)

    def test_get_backoff_time_BothMatch_ReturnsCorrectBackoffTime(self):
        self.retry_error.name = "RetryError"
        self.retry_error.code = 500
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertGreater(result, 0)

    def test_get_backoff_time_NoMatch_ReturnsMinDelayTime(self):
        self.retry_error.name = "UnknownError"
        self.retry_error.code = 400
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertEqual(result, MIN_DELAY_TIME)

    def test_get_backoff_time_WithRetryAfter_ReturnsMinOfRetryAfterAndMaxDelay(self):
        self.retry_error.retry_after = 500
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertEqual(result, 500)

    def test_get_backoff_time_WithRetryAfterGreaterThanMaxDelay_ReturnsMaxDelay(self):
        self.retry_error.retry_after = 1500
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertEqual(result, 1000)

    def test_get_backoff_time_WithBackoff_ReturnsBackoffDelay(self):
        self.retry_condition["maxDelay"] = 750 
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertEqual(result, MIN_DELAY_TIME)

    def test_get_backoff_time_WithoutBackoff_ReturnsMinDelayTime(self):
        ctx = RetryPolicyContext(exception=self.retry_error)
        result = DaraCore.get_backoff_time(self.retry_options, ctx)
        self.assertEqual(result, MIN_DELAY_TIME)

class BaseError(Exception):

    def __init__(self, map: dict):
        self.name = map.get('name', None)
        self.code = map.get('code', None)
        self.message = map.get('message', None)

class AErr(BaseError):

    def __init__(self, map: dict):
        super().__init__(map)
        self.name = 'AErr'

class BErr(BaseError):

    def __init__(self, map: dict):
        super().__init__(map)
        self.name = 'BErr'

class CErr(BaseError):

    def __init__(self, map: dict):
        super().__init__(map)
        self.name = 'BErr'
        self.retry_after = map.get('retryAfter', None)

class TestRetry(unittest.TestCase):

    def test_init_base_backoff_policy_should_not_okay(self):
        with self.assertRaises(NotImplementedError) as context:
            err = BackoffPolicy({})
            ctx = RetryPolicyContext(
                retries_attempted=3,
                exception=AErr({
                    'code': 'A1Err',
                    'message': 'a1 error',
                })
            )
            err.get_delay_time(ctx)
        self.assertEqual(str(context.exception), 'un-implemented')

    def test_should_retry(self):
        ctx = RetryPolicyContext(
            retries_attempted=3,
        )
        self.assertFalse(DaraCore.should_retry(None, ctx))
        self.assertFalse(DaraCore.should_retry({}, ctx))

        ctx = RetryPolicyContext(
            retries_attempted=0,
        )
        self.assertTrue(DaraCore.should_retry(None, ctx))

        condition1 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err']
        })
        options = RetryOptions({
            'retryable': True,
            'retryCondition': [condition1]
        })

        ctx = RetryPolicyContext(
            retries_attempted=3,
            exception=AErr({
                'code': 'A1Err',
                'message': 'a1 error',
            })
        )
        self.assertFalse(DaraCore.should_retry(options, ctx))

        options = RetryOptions({
            'retryable': True,
        })
        self.assertFalse(DaraCore.should_retry(options, ctx))

        options = RetryOptions({
            'retryable': True,
            'retryCondition': [condition1]
        })
        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=AErr({
                'code': 'A1Err',
                'message': 'a1 error',
            })
        )
        self.assertTrue(DaraCore.should_retry(options, ctx))

        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=AErr({
                'code': 'B1Err',
                'message': 'b1 error',
            })
        )
        self.assertTrue(DaraCore.should_retry(options, ctx))

        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=BErr({
                'code': 'B1Err',
                'message': 'b1 error',
            })
        )
        self.assertFalse(DaraCore.should_retry(options, ctx))

        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=BErr({
                'code': 'A1Err',
                'message': 'b1 error',
            })
        )
        self.assertTrue(DaraCore.should_retry(options, ctx))

        condition2 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['BErr'],
            'errorCode': ['B1Err']
        })

        options = RetryOptions({
            'retryable': True,
            'retryCondition': [condition2],
            'noRetryCondition': [condition2]
        })

        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=AErr({
                'code': 'B1Err',
                'message': 'b1 error',
            })
        )
        self.assertFalse(DaraCore.should_retry(options, ctx))

        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=BErr({
                'code': 'A1Err',
                'message': 'a1 error',
            })
        )
        self.assertFalse(DaraCore.should_retry(options, ctx))

        ctx = RetryPolicyContext(
            retries_attempted=1,
            exception=BErr({
                'code': 'A1Err',
                'message': 'b1 error',
            })
        )
        self.assertFalse(DaraCore.should_retry(options, ctx))
    def test_get_backoff_time(self):
        condition = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err']
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition]
        })
        
        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=AErr({
                'code': 'A1Err',
                'message': 'a1 error',
            })
        )
        self.assertEqual(DaraCore.get_backoff_time(option, ctx), 100)
        
        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=BErr({
                'code': 'B1Err',
                'message': 'a1 error',
            })
        )
        self.assertEqual(DaraCore.get_backoff_time(option, ctx), 100)
        
        fixedPolicy = BackoffPolicy.new_backoff_policy({"policy": "Fixed", "period": 1000})
        condition1 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": fixedPolicy
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition1]
        })
        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=AErr({
                'code': 'AErr',
                'message': 'a error',
            })
        )
        self.assertEqual(DaraCore.get_backoff_time(option, ctx), 1000)
        
        randomPolicy = BackoffPolicy.new_backoff_policy({"policy": "Random", "period": 1000, "cap": 10000})
        condition2 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": randomPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition2]
        })
        self.assertTrue(DaraCore.get_backoff_time(option, ctx) < 10000)
        
        randomPolicy2 = BackoffPolicy.new_backoff_policy({"policy": "Random", "period": 10000, "cap": 10})
        condition2Other = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": randomPolicy2,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition2Other]
        })
        self.assertEqual(DaraCore.get_backoff_time(option, ctx), 10)
        
        exponentialPolicy = BackoffPolicy.new_backoff_policy({"policy": "Exponential", "period": 5, "cap": 10000})
        condition3 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": exponentialPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition3]
        })
        self.assertEqual(DaraCore.get_backoff_time(option, ctx), 1024)
        
        exponentialPolicy = BackoffPolicy.new_backoff_policy({"policy": "Exponential", "period": 10, "cap": 10000})
        condition4 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": exponentialPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition4]
        })
        self.assertEqual(DaraCore.get_backoff_time(option, ctx), 10000)
        
        equalJitterPolicy = BackoffPolicy.new_backoff_policy({"policy": "EqualJitter", "period": 5, "cap": 10000})
        condition5 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": equalJitterPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition5]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertTrue(backoffTime > 512 and backoffTime < 1024)
        
        equalJitterPolicy = BackoffPolicy.new_backoff_policy({"policy": "EqualJitter", "period": 10, "cap": 10000})
        condition6 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": equalJitterPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition6]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertTrue(backoffTime > 5000 and backoffTime < 10000)
        
        fullJitterPolicy = BackoffPolicy.new_backoff_policy({"policy": "FullJitter", "period": 5, "cap": 10000})
        condition7 = RetryCondition({
            'maxAttempts': 2,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": fullJitterPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition7]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertTrue(backoffTime > 0 and backoffTime < 1024)
        
        fullJitterPolicy = BackoffPolicy.new_backoff_policy({"policy": "ExponentialWithFullJitter", "period": 10, "cap": 10000})
        condition8 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": fullJitterPolicy,
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition8]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertTrue(backoffTime >= 0 and backoffTime < 10000)
        
        condition9 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": fullJitterPolicy,
            "maxDelay": 1000
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition9]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertTrue(backoffTime >= 0 and backoffTime <= 1000)
        
        fullJitterPolicy = BackoffPolicy.new_backoff_policy({"policy": "ExponentialWithFullJitter", "period": 100, "cap": 10000 * 10000})
        condition12 = RetryCondition({
            'maxAttempts': 2,
            'exception': ['AErr'],
            'errorCode': ['A1Err'],
            "backoff": fullJitterPolicy
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition12]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertTrue(backoffTime >= 0 and backoffTime <= 120 * 1000)

        
        ctx = RetryPolicyContext(
            retries_attempted=2,
            exception=CErr({
                'code': 'CErr',
                'message': 'c error',
                'retryAfter': 3000
            })
        )
        fullJitterPolicy = BackoffPolicy.new_backoff_policy({"policy": "ExponentialWithFullJitter", "period": 100, "cap": 10000 * 10000})
        condition10 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['CErr'],
            'errorCode': ['CErr'],
            "backoff": fullJitterPolicy,
            "maxDelay": 5000
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition10]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertEqual(backoffTime, 3000)
        
        condition11 = RetryCondition({
            'maxAttempts': 3,
            'exception': ['CErr'],
            'errorCode': ['CErr'],
            "backoff": fullJitterPolicy,
            "maxDelay": 1000
        })
        option = RetryOptions({
            'retryable': True,
            'retryCondition': [condition11]
        })
        backoffTime = DaraCore.get_backoff_time(option, ctx)
        self.assertEqual(backoffTime, 1000)