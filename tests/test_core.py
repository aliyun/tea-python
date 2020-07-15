import unittest
import time

from unittest import mock

from Tea.model import TeaModel
from Tea.core import TeaCore
from Tea.request import TeaRequest
from Tea.exceptions import TeaException


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

    def to_map(self):
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

    @classmethod
    def names(cls):
        return {
            "avatar": "avatar",
            "createdAt": "created_at",
            "defaultDriveId": "default_driveId",
            "description": "description",
            "domainId": "domain_id",
            "email": "email",
            "nickName": "nick_name",
            "phone": "phone",
            "role": "role",
            "status": "status",
            "updatedAt": "updated_at",
            "userName": "user_name",
        }

    @classmethod
    def requireds(cls):
        return {
            "avatar": False,
            "createdAt": False,
            "defaultDriveId": False,
            "description": False,
            "domainId": False,
            "email": False,
            "nickName": False,
            "phone": False,
            "role": False,
            "status": False,
            "updatedAt": False,
            "userName": False,
        }


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


class Testcore(unittest.TestCase):
    def test_compose_url(self):
        request = TeaRequest()
        self.assertEqual("http://", TeaCore.compose_url(request))

        request.headers['host'] = "fake.domain.com"
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
        request.headers['host'] = "www.aliyun.com"
        request.pathname = "/s/zh"
        request.query["k"] = "ecs"
        option = {
            "readTimeout": 0,
            "connectTimeout": 0,
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
        resp = TeaCore.do_action(request, option)
        self.assertIsNotNone(bytes.decode(resp.body))

    def test_get_response_body(self):
        moc_resp = mock.Mock()
        moc_resp.content = "test".encode("utf-8")
        self.assertAlmostEqual("test", TeaCore.get_response_body(moc_resp))

    def test_allow_retry(self):
        self.assertFalse(TeaCore.allow_retry(None, 0))
        dic = {}
        self.assertFalse(TeaCore.allow_retry(dic, 0))
        dic["maxAttempts"] = 3
        self.assertTrue(TeaCore.allow_retry(dic, 0))
        self.assertFalse(TeaCore.allow_retry(dic, 4))
        dic["maxAttempts"] = None
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

    def test_is_retryable(self):
        self.assertFalse(TeaCore.is_retryable("test"))
        ex = TeaException({})
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
