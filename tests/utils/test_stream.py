import unittest
from darabonba.utils.stream import Stream

class TestStream(unittest.TestCase):

    def test_read_as_bytes_with_bytes(self):
        data = b"hello"
        bytes_data = Stream.read_as_bytes(data)
        self.assertEqual(bytes_data, b"hello")

    def test_read_as_bytes_with_string(self):
        data = "hello"
        bytes_data = Stream.read_as_bytes(data)
        self.assertEqual(bytes_data, b"hello")

    def test_read_as_bytes_with_invalid_type(self):
        data = 12345
        with self.assertRaises(TypeError):
            Stream.read_as_bytes(data)

    def test_read_as_json_with_string(self):
        data = '{"key": "value"}'
        json_data = Stream.read_as_json(data)
        self.assertEqual(json_data, {"key": "value"})

    def test_read_as_json_with_bytes(self):
        data = b'{"key": "value"}'
        json_data = Stream.read_as_json(data)
        self.assertEqual(json_data, {"key": "value"})

    def test_read_as_json_with_invalid_type(self):
        data = 12345
        with self.assertRaises(TypeError):
            Stream.read_as_json(data)

    def test_read_as_string_with_bytes(self):
        data = b"hello"
        string_data = Stream.read_as_string(data)
        self.assertEqual(string_data, "hello")

    def test_read_as_string_with_string(self):
        data = "hello"
        string_data = Stream.read_as_string(data)
        self.assertEqual(string_data, "hello")

    def test_read_as_string_with_invalid_type(self):
        data = 12345
        with self.assertRaises(TypeError):
            Stream.read_as_string(data)

    def test_read_as_sse_with_string(self):
        data = "event"
        sse_data = Stream.read_as_sse(data)
        self.assertEqual(sse_data, "data: event\n\n")

    def test_read_as_sse_with_bytes(self):
        data = b"event"
        sse_data = Stream.read_as_sse(data)
        self.assertEqual(sse_data, "data: event\n\n")

    def test_read_as_sse_with_invalid_type(self):
        data = 12345
        with self.assertRaises(TypeError):
            Stream.read_as_sse(data)

    def test_write_and_read_methods(self):
        stream = Stream()
        stream.write("hello")
        self.assertEqual(stream.read(), "hello")
        stream.write(b"world")
        self.assertEqual(stream.read(), b"world")

    def test_write_with_invalid_type(self):
        stream = Stream()
        with self.assertRaises(TypeError):
            stream.write(12345)

    def test_pipe_method(self):
        stream1 = Stream("stream1 data")
        stream2 = Stream()
        stream1.pipe(stream2)
        self.assertEqual(stream2.read(), "stream1 data")

    def test_pipe_with_invalid_stream(self):
        stream = Stream("data")
        with self.assertRaises(TypeError):
            stream.pipe("not a stream")
