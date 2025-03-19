import unittest

from darabonba.request import DaraRequest

class TestDaraRequest(unittest.TestCase):
    def test_init(self):
        request = DaraRequest()
        self.assertEqual({}, request.query)
        self.assertEqual({}, request.headers)
        self.assertEqual('http', request.protocol)
        self.assertEqual(80, request.port)
        self.assertEqual('GET', request.method)
        self.assertEqual("", request.pathname)
        self.assertEqual(None, request.body)

        request.query = None
        self.assertEqual({}, request.query)
