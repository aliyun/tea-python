import unittest
import os

from Tea.stream import BaseStream, READABLE, WRITABLE

root_path = os.path.dirname(__file__)


class TestTeaRequest(unittest.TestCase):
    def test_base_stream(self):
        stream = BaseStream()
        self.assertRaises(NotImplementedError, stream.read)
        self.assertRaises(NotImplementedError, stream.__len__)
        self.assertRaises(NotImplementedError, stream.__next__)

        with open(os.path.join(root_path, 'test.txt'), 'rb') as f:
            self.assertIsInstance(f, READABLE)

        with open(os.path.join(root_path, 'test.txt'), 'wb') as f:
            self.assertIsInstance(f, WRITABLE)

        try:
            for s in stream:
                continue
        except Exception as e:
            self.assertEqual('__next__ method must be overridden', str(e))
