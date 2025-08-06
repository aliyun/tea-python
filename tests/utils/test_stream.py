import unittest
from unittest import mock
import asyncio
from darabonba.exceptions import DaraException
from darabonba.utils.stream import Stream, BaseStream, READABLE, WRITABLE, STREAM_CLASS
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

    def test_read_as_sse_success(self):
        mock_session = mock.MagicMock()
        mock_response = mock.MagicMock()
        sse_data = [
            b'id: 1\nevent: create\ndata: {"message": "test1"}\n\n',
            b'event: update\ndata: {"message": "test2"}\n\n',
            b'id: 123\ndata: {"message": "test3"}\n\n'
        ]
        mock_response.iter_content.return_value = sse_data
        
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/event-stream'}
        from darabonba.utils.stream import SyncSSEResponseWrapper
        stream_wrapper = SyncSSEResponseWrapper(mock_session, mock_response)

        results = list(Stream.read_as_sse(stream_wrapper))
        # Check the number of events and their content
        self.assertEqual(results[0].id, '1')
        self.assertEqual(results[0].event, 'create')
        self.assertEqual(results[0].data, '{"message": "test1"}')

        self.assertEqual(results[1].event, 'update')
        self.assertEqual(results[2].id, '123')


    def test_read_as_sse_error(self):
        mock_session = mock.MagicMock()
        mock_response = mock.MagicMock()
        mock_response.iter_content.return_value = [
            b'data: error occurred\n\n'
        ]
        mock_response.status_code = 400
        
        mock_response.headers = {'Content-Type': 'text/event-stream'}
        from darabonba.utils.stream import SyncSSEResponseWrapper
        stream_wrapper = SyncSSEResponseWrapper(mock_session, mock_response)

        results = list(Stream.read_as_sse(stream_wrapper))

        # Check the number of events and their content
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].data, 'error occurred')

    async def test_read_as_sse_async_error(self):
        async def mock_stream():
            yield {
                'status_code': 400,
                'headers': {},
                'body': b'{"Code": "400", "Message": "Bad Request", "RequestId": "12345"}\n'
            }

        with self.assertRaises(DaraException) as context:
            async for _ in Stream.read_as_sse_async(mock_stream()):
                pass
        self.assertEqual(context.exception.message, "code: 400, code: 400, request id: 12345")
        
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