import asyncio


import threading
import time
import ssl
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from darabonba.core import DaraCore, _TLSAdapter, TLSVersion
from darabonba.exceptions import RetryError, DaraException
from darabonba.model import DaraModel
from darabonba.request import DaraRequest
from darabonba.utils.stream import BaseStream
from darabonba.policy.retry import RetryOptions, RetryPolicyContext, RetryCondition


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
        self.array = None

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

class ListUserResponse(DaraModel):
    def __init__(self):
        super().__init__()
        self.items = None
        self.nextMarker = None

    @classmethod
    def names(cls):
        return {
            "items": "items",
            "nextMarker": "next_marker",
        }

    @classmethod
    def requireds(cls):
        return {
            "items": False,
            "nextMarker": False,
        }


class TestCore(unittest.TestCase):
    
    def test_get_adapter(self):
        adapter = DaraCore.get_adapter('HTTPS', tls_min_version='TLSv1.2')
        self.assertIsNotNone(adapter)
        self.assertIsInstance(adapter, _TLSAdapter)

    def test_should_retry(self):
        options = RetryOptions({"retryable":True, "retry_condition":[], "no_retry_condition":[]})
        ctx = RetryPolicyContext(retries_attempted=0)
        
        # 测试应重试的情况
        self.assertTrue(DaraCore.should_retry(options, ctx))

        # 测试不应重试的情况
        ctx.retries_attempted = 1
        options.retryable = False
        self.assertFalse(DaraCore.should_retry(options, ctx))
        
        ctx.retries_attempted = 1
        options.no_retry_condition = [RetryCondition({})] 
        self.assertFalse(DaraCore.should_retry(options, ctx))
    def test_do_action_error_handling(self):
        request = DaraRequest()
        request.headers['host'] = "mock.invalid"
        request.method = "GET"
        
        with self.assertRaises(RetryError):
            DaraCore.do_action(request)

    def test_merge_empty_dict(self):
        merged_result = DaraCore.merge({}, {'key': 'value'})
        self.assertEqual(merged_result, {'key': 'value'})

    def test_is_null(self):
        self.assertTrue(DaraCore.is_null(None))
        self.assertFalse(DaraCore.is_null(0))
        self.assertFalse(DaraCore.is_null(''))

    @classmethod
    def setUpClass(cls):
        server = threading.Thread(target=run_server)
        server.daemon = True
        server.start()

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

    def test_get_response_body(self):
        moc_resp = mock.Mock()
        moc_resp.content = "test".encode("utf-8")
        self.assertAlmostEqual("test", DaraCore.get_response_body(moc_resp))

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

    def test_get_backoff_time(self):
        dic = {}
        self.assertEqual(0, DaraCore.get_backoff_time(dic, 1))
        dic["policy"] = None
        self.assertEqual(0, DaraCore.get_backoff_time(dic, 1))
        dic["policy"] = ""
        self.assertEqual(0, DaraCore.get_backoff_time(dic, 1))
        dic["policy"] = "no"
        self.assertEqual(0, DaraCore.get_backoff_time(dic, 1))
        dic["policy"] = "yes"
        self.assertEqual(0, DaraCore.get_backoff_time(dic, 1))
        dic["period"] = None
        self.assertEqual(0, DaraCore.get_backoff_time(dic, 1))
        dic["period"] = -1
        self.assertEqual(1, DaraCore.get_backoff_time(dic, 1))
        dic["period"] = 1000
        self.assertEqual(1000, DaraCore.get_backoff_time(dic, 1))

    def test_sleep(self):
        ts_before = int(round(time.time() * 1000))
        DaraCore.sleep(1000)
        ts_after = int(round(time.time() * 1000))
        ts_subtract = ts_after - ts_before
        self.assertTrue(1000 <= ts_subtract < 1100)

    def test_sleep_async(self):
        ts_before = int(round(time.time() * 1000))
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            DaraCore.sleep_async(1000)
        )
        loop.run_until_complete(task)
        ts_after = int(round(time.time() * 1000))
        ts_subtract = ts_after - ts_before
        self.assertTrue(1000 <= ts_subtract < 1100)

    def test_is_retryable(self):
        self.assertFalse(DaraCore.is_retryable("test"))
        ex = DaraException({})
        self.assertFalse(DaraCore.is_retryable(ex))
        ex = RetryError('error')
        self.assertTrue(DaraCore.is_retryable(ex))

    def test_bytes_readable(self):
        body = "test".encode('utf-8')
        self.assertIsNotNone(DaraCore.bytes_readable(body))

    def test_merge(self):
        model = BaseUserResponse()
        dic = DaraCore.merge(model, {'k1': 'test'})
        self.assertEqual(
            {
                'avatar': None,
                'createdAt': None,
                'defaultDriveId': None,
                'description': None,
                'domainId': None,
                'email': None,
                'nickName': None,
                'phone': None,
                'role': None,
                'status': None,
                'updatedAt': None,
                'userId': None,
                'userName': None,
                'k1': 'test'
            }, dic
        )

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
            'array': 123
        }
        model2 = DaraCore.from_map(model, m)
        self.assertEqual([], model2.array)
        self.assertEqual(123, model2._map['array'])

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
