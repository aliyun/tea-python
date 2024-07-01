import unittest
import time
import asyncio

from aiohttp.client_exceptions import ClientProxyConnectionError
from unittest import mock
from requests.exceptions import ProxyError

from Tea.model import TeaModel
from Tea.core import TeaCore
from Tea.request import TeaRequest
from Tea.exceptions import TeaException, RetryError
from Tea.stream import BaseStream

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class Request(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        body = self.rfile.read(int(self.headers['content-length']))
        self.wfile.write(b'{"result": "%s"}' % body)


def run_server():
    server = HTTPServer(('localhost', 8888), Request)
    server.serve_forever()


class TeaStream(BaseStream):
    def __init__(self):
        super().__init__()
        self.content = b'tea test'

    def read(self, size=1024):
        content = self.content
        self.content = b''
        return content

    def __len__(self):
        return len(b'tea test')

    def __next__(self):
        content = self.read()
        if content:
            return content
        else:
            raise StopIteration


class BaseUserResponse(TeaModel):
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


class ListUserResponse(TeaModel):
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
    @classmethod
    def setUpClass(cls):
        server = threading.Thread(target=run_server)
        server.setDaemon(True)
        server.start()

    def test_compose_url(self):
        request = TeaRequest()
        try:
            TeaCore.compose_url(request)
        except Exception as e:
            self.assertEqual('"endpoint" is required.', str(e))

        request.headers['host'] = "fake.domain.com"
        self.assertEqual("http://fake.domain.com",
                         TeaCore.compose_url(request))

        request.headers['host'] = "http://fake.domain.com"
        self.assertEqual("http://fake.domain.com",
                         TeaCore.compose_url(request))

        request.port = 8080
        self.assertEqual("http://fake.domain.com:8080",
                         TeaCore.compose_url(request))

        request.pathname = "/index.html"
        self.assertEqual("http://fake.domain.com:8080/index.html",
                         TeaCore.compose_url(request))

        request.query["foo"] = ""
        self.assertEqual("http://fake.domain.com:8080/index.html?foo=",
                         TeaCore.compose_url(request))

        request.query["foo"] = "bar"
        self.assertEqual("http://fake.domain.com:8080/index.html?foo=bar",
                         TeaCore.compose_url(request))

        request.pathname = "/index.html?a=b"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         TeaCore.compose_url(request))

        request.pathname = "/index.html?a=b&"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         TeaCore.compose_url(request))

        request.query["fake"] = None
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         TeaCore.compose_url(request))

    def test_do_action(self):
        request = TeaRequest()
        request.headers['host'] = "www.alibabacloud.com"
        request.pathname = "/s/zh"
        request.query["k"] = "ecs"
        option = None
        resp = TeaCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertIsNotNone(bytes.decode(resp.body))

        option = {
            "timeout": None,
            "readTimeout": None,
            "connectTimeout": None,
        }
        resp = TeaCore.do_action(request, option)
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
            "ignoreSSL": None
        }
        resp = TeaCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertIsNotNone(bytes.decode(resp.body))

        request.headers['host'] = "127.0.0.1:8888"
        request.method = "POST"
        request.protocol = "http"
        request.body = "{'test': [{'id': 'id', 'name': '中文'}]}"
        resp = TeaCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}', bytes.decode(resp.body))

        request.body = "{'test': [{'id': 'id', 'name': '\u4e2d\u6587'}]}"
        resp = TeaCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}', bytes.decode(resp.body))

        request.body = b"{'test': [{'id': 'id', 'name': '\xe4\xb8\xad\xe6\x96\x87\'}]}"
        resp = TeaCore.do_action(request, option)
        self.assertTrue(resp.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}', bytes.decode(resp.body))

        option['httpProxy'] = '127.0.0.1'
        option['httpsProxy'] = '127.0.0.1'
        option['noProxy'] = '127.0.0.1'
        try:
            TeaCore.do_action(request, option)
            assert False
        except Exception as e:
            self.assertIsInstance(e, RetryError)

    def test_async_do_action(self):
        request = TeaRequest()
        request.headers['host'] = "www.alibabacloud.com"
        request.pathname = "/s/zh"
        request.query["k"] = "ecs"
        option = None
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            TeaCore.async_do_action(request, option)
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
            TeaCore.async_do_action(request, option)
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
            "ignoreSSL": None
        }
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            TeaCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertIsNotNone(bytes.decode(response.body))

        request.headers['host'] = "127.0.0.1:8888"
        request.method = "POST"
        request.protocol = "http"
        request.body = "{'test': [{'id': 'id', 'name': '中文'}]}"
        task = asyncio.ensure_future(
            TeaCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}',
                         bytes.decode(response.body))

        request.body = "{'test': [{'id': 'id', 'name': '\u4e2d\u6587'}]}"
        task = asyncio.ensure_future(
            TeaCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}',
                         bytes.decode(response.body))

        request.body = b"{'test': [{'id': 'id', 'name': '\xe4\xb8\xad\xe6\x96\x87\'}]}"
        task = asyncio.ensure_future(
            TeaCore.async_do_action(request, option)
        )
        loop.run_until_complete(task)
        response = task.result()
        self.assertTrue(response.headers.get('server'))
        self.assertEqual('{"result": "{\'test\': [{\'id\': \'id\', \'name\': \'中文\'}]}"}',
                         bytes.decode(response.body))

        request.protocol = 'http'
        option['httpProxy'] = 'http://127.0.0.1'
        try:
            loop.run_until_complete(TeaCore.async_do_action(request, option))
            assert False
        except Exception as e:
            self.assertIsInstance(e, RetryError)

    def test_get_response_body(self):
        moc_resp = mock.Mock()
        moc_resp.content = "test".encode("utf-8")
        self.assertAlmostEqual("test", TeaCore.get_response_body(moc_resp))

    def test_allow_retry(self):
        self.assertTrue(TeaCore.allow_retry(None, 0))
        dic = {}
        self.assertTrue(TeaCore.allow_retry(dic, 0))
        dic["retryable"] = True
        dic["maxAttempts"] = 3
        self.assertTrue(TeaCore.allow_retry(dic, 0))
        self.assertFalse(TeaCore.allow_retry(dic, 4))
        dic["maxAttempts"] = None
        self.assertFalse(TeaCore.allow_retry(dic, 1))
        dic["retryable"] = False
        dic["maxAttempts"] = 3
        self.assertTrue(TeaCore.allow_retry(dic, 0))
        self.assertFalse(TeaCore.allow_retry(dic, 1))

    def test_get_backoff_time(self):
        dic = {}
        self.assertEqual(0, TeaCore.get_backoff_time(dic, 1))
        dic["policy"] = None
        self.assertEqual(0, TeaCore.get_backoff_time(dic, 1))
        dic["policy"] = ""
        self.assertEqual(0, TeaCore.get_backoff_time(dic, 1))
        dic["policy"] = "no"
        self.assertEqual(0, TeaCore.get_backoff_time(dic, 1))
        dic["policy"] = "yes"
        self.assertEqual(0, TeaCore.get_backoff_time(dic, 1))
        dic["period"] = None
        self.assertEqual(0, TeaCore.get_backoff_time(dic, 1))
        dic["period"] = -1
        self.assertEqual(1, TeaCore.get_backoff_time(dic, 1))
        dic["period"] = 1000
        self.assertEqual(1000, TeaCore.get_backoff_time(dic, 1))

    def test_sleep(self):
        ts_before = int(round(time.time() * 1000))
        TeaCore.sleep(1)
        ts_after = int(round(time.time() * 1000))
        ts_subtract = ts_after - ts_before
        self.assertTrue(1000 <= ts_subtract < 1100)

    def test_sleep_async(self):
        ts_before = int(round(time.time() * 1000))
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(
            TeaCore.sleep_async(1)
        )
        loop.run_until_complete(task)
        ts_after = int(round(time.time() * 1000))
        ts_subtract = ts_after - ts_before
        self.assertTrue(1000 <= ts_subtract < 1100)

    def test_is_retryable(self):
        self.assertFalse(TeaCore.is_retryable("test"))
        ex = TeaException({})
        self.assertFalse(TeaCore.is_retryable(ex))
        ex = RetryError('error')
        self.assertTrue(TeaCore.is_retryable(ex))

    def test_bytes_readable(self):
        body = "test".encode('utf-8')
        self.assertIsNotNone(TeaCore.bytes_readable(body))

    def test_merge(self):
        model = BaseUserResponse()
        dic = TeaCore.merge(model, {'k1': 'test'})
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
        m = TeaCore.to_map(model)
        self.assertEqual('139xxx', m['phone'])
        self.assertEqual('domainId', m['domainId'])
        m = TeaCore.to_map(None)
        self.assertEqual({}, m)

        model = BaseUserResponse()
        model._map = {'phone': '139xxx'}
        m = TeaCore.to_map(model)
        self.assertEqual({'phone': '139xxx'}, m)

    def test_from_map(self):
        model = BaseUserResponse()
        model.phone = '139xxx'
        model.domainId = 'domainId'
        m = {
            'phone': '138',
            'domainId': 'test'
        }
        model1 = TeaCore.from_map(model, m)
        self.assertEqual('138', model1.phone)
        self.assertEqual('test', model1.domainId)

        m = {
            'phone': '138',
            'domainId': 'test',
            'array': 123
        }
        model2 = TeaCore.from_map(model, m)
        self.assertEqual([], model2.array)
        self.assertEqual(123, model2._map['array'])

    def test_async_stream_upload(self):
        request = TeaRequest()
        request.method = 'POST'
        request.protocol = 'http'
        request.headers['host'] = "127.0.0.1:8888"
        loop = asyncio.get_event_loop()
        task = asyncio.ensure_future(TeaCore.async_do_action(request))
        f = TeaStream()
        request.body = f
        loop.run_until_complete(task)
        self.assertEqual(b'{"result": "tea test"}', task.result().body)
