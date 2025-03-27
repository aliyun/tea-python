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

    def test_parse_json_valid(self):
        valid_json = '{"key": "value", "number": 42}'
        result = Stream._Stream__parse_json(valid_json)  # 调用私有方法
        expected_result = {"key": "value", "number": 42}
        self.assertEqual(result, expected_result)

    def test_parse_json_invalid(self):
        invalid_json = '{"key": "value", "number": }'  # 无效 JSON
        with self.assertRaises(RuntimeError) as context:
            Stream._Stream__parse_json(invalid_json)
        self.assertIn('Failed to parse the value as json format', str(context.exception))
    
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

    def test_pipe(self):
        output_stream = Stream()
        self.stream.pipe(output_stream)
        self.assertEqual(output_stream.read(), self.sample_data)

    def test_pipe_invalid_stream(self):
        with self.assertRaises(TypeError):
            self.stream.pipe('invalid stream')

    def test_base_stream_methods(self):
        base_stream = BaseStream()

        # 测试 read 方法
        with self.assertRaises(NotImplementedError):
            base_stream.read()

        # 测试 __len__ 方法
        with self.assertRaises(NotImplementedError):
            len(base_stream)

        # 测试 __next__ 方法
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
            self.stream.write(42)  # 传入非字节或字符串类型
            
    def test_pipe_with_empty_stream(self):
        output_stream = Stream()
        self.stream.pipe(output_stream)
        self.assertEqual(output_stream.read(), self.sample_data)

    def test_pipe_with_non_readable_stream(self):
        with self.assertRaises(TypeError):
            self.stream.pipe(123)  # 传入无效流
            
    def test_read_as_sse_with_empty_stream(self):
        empty_stream = [b'']
        event_gen = Stream.read_as_sse(empty_stream)
        result = next(event_gen)
        self.assertIsNone(result['event'].data)

    def test_read_as_sse_invalid_data(self):
        # 测试一个没有数字的 retry 值
        sse_data = [b'retry: notanumber\n', b'\n']
        event_gen = Stream.read_as_sse(sse_data)
        
        with self.assertRaises(ValueError):
            next(event_gen)

    def test_read_part_normal(self):
        # 创建一个模拟的可读流
        mock_stream = io.BytesIO(b'This is a simple test for read part functionality.')

        # 使用生成器读取
        chunks = list(Stream._Stream__read_part(mock_stream, size=15))  # 设置为 15 字节读取

        expected_chunks = [
            b'This is a simpl',  # 第一个分块
            b'e test for read',   # 第二个分块
            b' part functiona',    # 第三个分块
            b'lity.'              # 第四个分块
        ]
        
        # 验证结果
        self.assertEqual(chunks, expected_chunks)

    def test_read_part_empty_stream(self):
        # 创建一个模拟的空流
        mock_stream = io.BytesIO(b'')

        # 使用生成器读取
        chunks = list(Stream._Stream__read_part(mock_stream, size=10))  # 尝试读取
        self.assertEqual(chunks, [])  # 应该返回空列表

    def test_read_part_exact_size(self):
        # 创建一个模拟的可读流
        mock_stream = io.BytesIO(b'Test data')

        # 使用生成器读取
        chunks = list(Stream._Stream__read_part(mock_stream, size=9))  # 读取 9 字节
        self.assertEqual(chunks, [b'Test data'])  # 应该返回一块 9 字节的数据

