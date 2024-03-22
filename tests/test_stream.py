import unittest
import os
import io

from alibabacloud_tea_sse.stream import BaseStream, READABLE, WRITABLE, STREAM_CLASS

root_path = os.path.dirname(__file__)


class TestTeaRequest(unittest.TestCase):
    class TestStream:
        def read(self):
            return 'content'

    def test_base_stream(self):
        stream = BaseStream()
        self.assertRaises(NotImplementedError, stream.read)
        self.assertRaises(NotImplementedError, stream.__len__)
        self.assertRaises(NotImplementedError, stream.__next__)
        self.assertIsInstance(stream, READABLE)

        with open(os.path.join(root_path, 'test.txt'), 'rb') as f:
            self.assertIsInstance(f, READABLE)
            self.assertIsInstance(f, STREAM_CLASS)

        with open(os.path.join(root_path, 'test.txt'), 'wb') as f:
            self.assertIsInstance(f, WRITABLE)
            self.assertIsInstance(f, STREAM_CLASS)

        with io.BytesIO(b'test') as bio:
            self.assertIsInstance(bio, READABLE)
            self.assertIsInstance(bio, STREAM_CLASS)

        test_stream = self.TestStream()
        self.assertFalse(isinstance(test_stream, READABLE))

        try:
            for s in stream:
                continue
        except Exception as e:
            self.assertEqual('__next__ method must be overridden', str(e))
