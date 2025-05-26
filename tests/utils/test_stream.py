import unittest
import asyncio
from darabonba.utils.stream import Stream, BaseStream, READABLE, WRITABLE, STREAM_CLASS, AsyncBytesIO
import os
from io import BytesIO, StringIO

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

            with BytesIO(b'test') as bio:
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
        self.stream.write('stream data')
        self.assertEqual(Stream.read_as_bytes(self.stream.read()), b'stream data')
    
    def test_read_as_bytes_async(self):
        task1 = asyncio.run(Stream.read_as_bytes_async(b'test'))

        task2 = asyncio.run(Stream.read_as_bytes_async('testStr'))
        self.assertEqual(b'test', task1)
        self.assertEqual(b'testStr', task2)

    def test_read_as_json(self):
        json_str = '{"key": "value"}'
        json_bytes = json_str.encode('utf-8')
        self.assertEqual(Stream.read_as_json(json_str), {"key": "value"})
        self.assertEqual(Stream.read_as_json(json_bytes), {"key": "value"})
    
    
    def test_read_as_json_async(self):
        task1 = asyncio.run(Stream.read_as_json_async(b'{"key": "value"}'))
        self.assertEqual({"key": "value"}, task1)
        try:
            task2 = asyncio.run(Stream.read_as_json_async("{1:'2'}"))
            assert False
        except Exception as e:
            self.assertEqual('''Failed to parse the value as json format, Value: "{1:'2'}".''', str(e))

    def test_parse_json_valid(self):
        valid_json = '{"key": "value", "number": 42}'
        result = Stream._Stream__parse_json(valid_json)
        expected_result = {"key": "value", "number": 42}
        self.assertEqual(result, expected_result)

    def test_parse_json_invalid(self):
        invalid_json = '{"key": "value", "number": }'
        with self.assertRaises(RuntimeError) as context:
            Stream._Stream__parse_json(invalid_json)
        self.assertIn('Failed to parse the value as json format', str(context.exception))
    
    def test_read_as_string(self):
        self.assertEqual(Stream.read_as_string(b'byte data'), 'byte data')
        self.assertEqual(Stream.read_as_string('string data'), 'string data')

    def test_pipe(self):
        output_stream = Stream()
        self.stream.pipe(output_stream)
        self.assertEqual(output_stream.read(), self.sample_data)

    def test_pipe_invalid_stream(self):
        with self.assertRaises(TypeError):
            self.stream.pipe('invalid stream')

    def test_base_stream_methods(self):
        base_stream = BaseStream()

        with self.assertRaises(NotImplementedError):
            base_stream.read()

        with self.assertRaises(NotImplementedError):
            len(base_stream)

        with self.assertRaises(NotImplementedError):
            next(base_stream)

    def test_iter(self):
        base_stream = BaseStream()
        self.assertEqual(iter(base_stream), base_stream)
        
    def test_write_with_bytes(self):
        self.stream.write(b'This is a valid byte string.')
        self.assertEqual(self.stream.read(), b'This is a valid byte string.')

    def test_write_with_invalid_data_type(self):
        with self.assertRaises(TypeError):
            self.stream.write(42) 
            
    def test_pipe_with_empty_stream(self):
        output_stream = Stream()
        self.stream.pipe(output_stream)
        self.assertEqual(output_stream.read(), self.sample_data)

    def test_pipe_with_non_readable_stream(self):
        with self.assertRaises(TypeError):
            self.stream.pipe(123)

    def test_read_part_normal(self):
        mock_stream = BytesIO(b'This is a simple test for read part functionality.')

        chunks = list(Stream._Stream__read_part(mock_stream, size=15))

        expected_chunks = [
            b'This is a simpl',
            b'e test for read',
            b' part functiona',
            b'lity.'
        ]
        
        self.assertEqual(chunks, expected_chunks)

    def test_read_part_empty_stream(self):
        mock_stream = BytesIO(b'')

        chunks = list(Stream._Stream__read_part(mock_stream, size=10))
        self.assertEqual(chunks, [])

    def test_read_part_exact_size(self):
        mock_stream = BytesIO(b'Test data')

        chunks = list(Stream._Stream__read_part(mock_stream, size=9))
        self.assertEqual(chunks, [b'Test data'])
        
        
    async def test_read_as_string_async(self):
        async def async_generator():
            for byte in self.data:
                yield byte.to_bytes(1, 'big')
        
        result =  asyncio.run(Stream.read_as_string_async(async_generator()))
        self.assertEqual(result, "data line 1\ndata line 2\n\n:data line 3")
    
    def test_to_string_str(self):
        result = Stream._Stream__to_string('test string')
        self.assertEqual(result, "test string")
        result = Stream._Stream__to_string(123)
        self.assertEqual(result, "123")

    def test_read_as_sse(self):
        sse_data_array = [
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 0}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 1}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 2}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 3}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 4}\n\n'
        ]

        sse_bytes = b''.join([item.encode('utf-8') for item in sse_data_array])
        stream = BytesIO(sse_bytes)

        result = list(Stream.read_as_sse(stream))

        expected = [
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 0}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 1}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 2}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 3}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 4}'},
        ]

        for exp, res in zip(expected, result):
            self.assertEqual(exp['id'], res['id'])
            self.assertEqual(exp['event'], res['event'])
            self.assertEqual(exp['data'], res['data'])

    async def test_read_as_sse_async(self):
        sse_data_array = [
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 0}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 1}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 2}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 3}\n\n',
            'id: sse-test\n',
            'event: flow\n',
            'data: {"count": 4}\n\n'
        ]

        sse_bytes = b''.join([item.encode('utf-8') for item in sse_data_array])
        stream = BytesIO(sse_bytes)

        result = asyncio.run(Stream.read_as_sse_async(stream))

        expected = [
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 0}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 1}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 2}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 3}'},
            {'id': 'sse-test', 'event': 'flow', 'data': '{"count": 4}'},
        ]

        for exp, res in zip(expected, result):
            self.assertEqual(exp['id'], res['id'])
            self.assertEqual(exp['event'], res['event'])
            self.assertEqual(exp['data'], res['data'])
    
    
    def test_to_readable(self):
        # Test with string input
        readable = Stream.to_readable("This is a string")
        self.assertIsInstance(readable, BytesIO)
        self.assertEqual(readable.getvalue(), b"This is a string")

        # Test with bytes input
        readable = Stream.to_readable(b"This is bytes")
        self.assertIsInstance(readable, BytesIO)
        self.assertEqual(readable.getvalue(), b"This is bytes")

        # Test with valid readable stream (BytesIO)
        readable = Stream.to_readable(BytesIO(b"Stream"))
        self.assertIsInstance(readable, BytesIO)
        self.assertEqual(readable.getvalue(), b"Stream")

        # Test with invalid input (should raise ValueError)
        with self.assertRaises(ValueError):
            Stream.to_readable(123)

    def test_to_writeable(self):
        # Test with string input
        writeable = Stream.to_writeable("This is a string")
        self.assertIsInstance(writeable, StringIO)
        self.assertEqual(writeable.getvalue(), "This is a string")

        # Test with bytes input
        writeable = Stream.to_writeable(b"This is bytes")
        self.assertIsInstance(writeable, BytesIO)
        self.assertEqual(writeable.getvalue(), b"This is bytes")

        # Test with valid writeable stream (StringIO)
        writeable = Stream.to_writeable(StringIO("Stream"))
        self.assertIsInstance(writeable, StringIO)
        self.assertEqual(writeable.getvalue(), "Stream")

        # Test with invalid input (should raise ValueError)
        with self.assertRaises(ValueError):
            Stream.to_writeable(123)
    
        
    async def test_to_readable_async_with_string(self):
        test_input = "Hello, world!"
        readable = await Stream.to_readable_async(test_input)
        self.assertIsInstance(readable, AsyncBytesIO)
        content = await readable.read()
        self.assertEqual(content, test_input.encode('utf-8'))

    async def test_to_readable_async_with_bytes(self):
        test_input = b"Hello, world!"
        readable = await Stream.to_readable_async(test_input)
        self.assertIsInstance(readable, AsyncBytesIO)
        content = await readable.read()
        self.assertEqual(content, test_input)

    async def test_to_readable_async_with_readable_object(self):
        class SimpleReadable:
            def __init__(self, data):
                self.data = data.encode('utf-8')
            
            async def read(self):
                return self.data

            def __iter__(self):
                return iter(self.data)

        test_input = SimpleReadable("Hello, world!")
        readable = await Stream.to_readable_async(test_input)
        content = await readable.read()
        self.assertEqual(content.decode('utf-8'), "Hello, world!")

    async def test_to_readable_async_invalid_type(self):
        test_input = 12345
        with self.assertRaises(ValueError):
            await Stream.to_readable_async(test_input)