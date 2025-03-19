import os
import unittest
import tempfile
import time
from datetime import datetime
from darabonba.file import File 

class TestFile(unittest.TestCase):
    
    def setUp(self):
        # 在测试前创建一个临时文件
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.file_path = self.test_file.name
        # 写入一些初始数据
        self.test_file.write(b'Test data')
        self.test_file.close()  # 关闭文件，以便后续读取

    def tearDown(self):
        # 在测试后删除临时文件
        os.remove(self.file_path)

    def test_exists(self):
        self.assertTrue(File.exists(self.file_path))
        self.assertFalse(File.exists('/invalid/path/to/file'))

    def test_path(self):
        file = File(self.file_path)
        self.assertEqual(file.path(), self.file_path)

    def test_length(self):
        file = File(self.file_path)
        self.assertEqual(file.length(), 9)  # 'Test data' 的字节长度是 9

    def test_create_time(self):
        file = File(self.file_path)
        create_time = file.create_time()
        self.assertTrue(isinstance(create_time.date, datetime))

    def test_modify_time(self):
        file = File(self.file_path)
        modify_time = file.modify_time()
        self.assertTrue(isinstance(modify_time.date, datetime))

    def test_read(self):
        file = File(self.file_path)
        data = file.read(9)
        self.assertEqual(data, b'Test data')

    def test_write(self):
        file = File(self.file_path)
        additional_data = b' appended'
        file.write(additional_data)

        # Re-open the file to check the content
        with open(self.file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'Test data appended')

    def test_create_read_stream(self):
        stream = File.create_read_stream(self.file_path)
        self.assertIsNotNone(stream)
        self.assertEqual(stream.read(), b'Test data')
        stream.close()

    def test_create_write_stream(self):
        stream = File.create_write_stream(self.file_path)
        self.assertIsNotNone(stream)
        stream.write(b' additional data')
        stream.close()

        # Re-open the file to check the new content
        with open(self.file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'Test data additional data')
