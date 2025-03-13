import unittest
import asyncio
from darabonba.utils.stream import Stream, BaseStream, READABLE, WRITABLE, STREAM_CLASS
import os
import io

root_path = os.path.dirname(__file__)

class TestStream(unittest.TestCase):
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

    def setUp(self):
        self.stream = Stream()
        self.sample_data = b'data: Hello World\n\n'
        self.stream.write(self.sample_data)

    def test_write_and_read(self):
        self.stream.write(b'Hello, world!')
        self.assertEqual(self.stream.read(), b'Hello, world!')

    def test_write_with_string(self):
        self.stream.write('Hello, string world!')
        self.assertEqual(self.stream.read(), 'Hello, string world!')

    def test_write_invalid_type(self):
        with self.assertRaises(TypeError):
            self.stream.write(123)

    def test_read_as_bytes(self):
        self.assertEqual(Stream.read_as_bytes(b'byte data'), b'byte data')
        self.assertEqual(Stream.read_as_bytes('string data'), b'string data')

    def test_read_as_json(self):
        json_str = '{"key": "value"}'
        json_bytes = json_str.encode('utf-8')
        self.assertEqual(Stream.read_as_json(json_str), {"key": "value"})
        self.assertEqual(Stream.read_as_json(json_bytes), {"key": "value"})

    def test_read_as_string(self):
        self.assertEqual(Stream.read_as_string(b'byte data'), 'byte data')
        self.assertEqual(Stream.read_as_string('string data'), 'string data')

    def test_read_as_sse(self):
        sse_data = [b'data: Hello World\n', b'id: 1\n', b'event: message\n', b'retry: 1000\n', b'\n']
        event_gen = Stream.read_as_sse(sse_data)
        result = next(event_gen)
        event = result['event']
        self.assertEqual(event.data, 'Hello World')
        self.assertEqual(event.id, '1')
        self.assertEqual(event.event, 'message')
        self.assertEqual(event.retry, 1000)

    async def async_test_read_as_sse_async(self):
        sse_data = [b'data: Hello World\n', b'id: 2\n', b'event: message\n', b'retry: 2000\n', b'\n']
        event_gen = Stream.read_as_sse_async(sse_data)
        result = await event_gen.__anext__() 
        event = result['event']
        self.assertEqual(event.data, 'Hello World')
        self.assertEqual(event.id, '2')
        self.assertEqual(event.event, 'message')
        self.assertEqual(event.retry, 2000)

    def test_pipe(self):
        output_stream = Stream()
        self.stream.pipe(output_stream)
        self.assertEqual(output_stream.read(), self.sample_data)

    def test_pipe_invalid_stream(self):
        with self.assertRaises(TypeError):
            self.stream.pipe('invalid stream')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(TestStream.async_test_read_as_sse_async())
    unittest.main()
