import unittest

from Tea.request import TeaRequest


class TestTeaRequest(unittest.TestCase):
    def test_init(self):
        request = TeaRequest()
        self.assertEqual({}, request.query)
        self.assertEqual({}, request.headers)
        self.assertEqual('http', request.protocol)
        self.assertEqual(80, request.port)
        self.assertEqual('GET', request.method)
        self.assertEqual("", request.host)
        self.assertEqual("", request.pathname)
        self.assertEqual(None, request.body)

    def test_set_host(self):
        request = TeaRequest()
        request.set_host("test.host")
        self.assertEqual("test.host", request.host)
        self.assertEqual("test.host", request.headers["host"])

    def test_set_method(self):
        request = TeaRequest()
        request.set_method("post")
        self.assertEqual("POST", request.method)
