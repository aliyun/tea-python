import unittest

from Tea.stream import BaseStream


class TestTeaRequest(unittest.TestCase):
    def test_base_stream(self):
        stream = BaseStream()
        self.assertRaises(ImportError, stream.read)
        self.assertRaises(ImportError, stream.__len__)
        self.assertRaises(ImportError, stream.__next__)
