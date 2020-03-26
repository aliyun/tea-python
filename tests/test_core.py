import unittest
import time

from unittest import mock
from requests import Request, Session

from Tea.model import TeaModel
from Tea.core import TeaCore
from Tea.request import TeaRequest
from Tea.exceptions import TeaException


class BaseUserResponse(TeaModel):
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


class TestTeaCore(unittest.TestCase):
    def test_compose_url(self):
        core = TeaCore()
        request = TeaRequest()
        self.assertEqual("http://", core.compose_url(request))

        request.set_host("fake.domain.com")
        self.assertEqual("http://fake.domain.com",
                         core.compose_url(request))
        request.port = 8080
        self.assertEqual("http://fake.domain.com:8080",
                         core.compose_url(request))

        request.pathname = "/index.html"
        self.assertEqual("http://fake.domain.com:8080/index.html",
                         core.compose_url(request))

        request.query["foo"] = ""
        self.assertEqual("http://fake.domain.com:8080/index.html",
                         core.compose_url(request))

        request.query["foo"] = "bar"
        self.assertEqual("http://fake.domain.com:8080/index.html?foo=bar",
                         core.compose_url(request))

        request.pathname = "/index.html?a=b"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         core.compose_url(request))

        request.pathname = "/index.html?a=b&"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         core.compose_url(request))

        request.query["fake"] = None
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar",
                         core.compose_url(request))

        request.query["fake"] = "val*"
        self.assertEqual("http://fake.domain.com:8080/index.html?a=b&foo=bar&fake=val%2A",
                         core.compose_url(request))

    def test_do_action(self):
        core = TeaCore()
        request = TeaRequest()
        request.set_host("www.alibabacloud.com")
        request.pathname = "/s/zh"
        request.query["k"] = "ecs"
        resp = core.do_action(request)
        self.assertIsNotNone(bytes.decode(resp.content))

    def test_get_response_body(self):
        moc_resp = mock.Mock()
        moc_resp.content = "test".encode("utf-8")
        self.assertAlmostEqual("test", TeaCore.get_response_body(moc_resp))

    def test_allow_retry(self):
        self.assertFalse(TeaCore.allow_retry(None, 0, 0))
        dic = {}
        self.assertFalse(TeaCore.allow_retry(dic, 0, 0))
        dic["maxAttempts"] = 3
        self.assertTrue(TeaCore.allow_retry(dic, 0, 0))
        self.assertFalse(TeaCore.allow_retry(dic, 4, 0))
        dic["maxAttempts"] = None
        self.assertFalse(TeaCore.allow_retry(dic, 1, 0))

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
        self.assertTrue(ts_subtract < 1100 and ts_subtract >= 1000)

    def test_is_retryable(self):
        self.assertFalse(TeaCore.is_retryable("test"))
        ex = TeaException({})
        self.assertTrue(TeaCore.is_retryable(ex))

    def test_bytes_readable(self):
        body = "test".encode('utf-8')
        self.assertIsNotNone(TeaCore.bytes_readable(body))
