import unittest

from Tea.stream import BaseStream


class TestTeaRequest(unittest.TestCase):
    def test_base_stream(self):
        stream = BaseStream()
        self.assertRaises(NotImplementedError, stream.read)
        self.assertRaises(NotImplementedError, stream.__len__)
        self.assertRaises(NotImplementedError, stream.__next__)
