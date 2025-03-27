import os
import unittest
import tempfile
from datetime import datetime
from darabonba.file import File 

class TestFile(unittest.TestCase):
    
    def setUp(self):
        # 在测试前创建一个临时文件
        self.test_file = tempfile.NamedTemporaryFile(delete=False)
        self.file_path = self.test_file.name
        # 写入一些初始数据
        self.test_file.write(b'Test data')
        self.test_file.close() 

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

        # 正常读取的情况
        data = file.read(9)  # 读取 'Test data'
        self.assertEqual(data, b'Test data')

        # 读取超出文件大小
        data = file.read(20)  # 这个应该返回空字节
        self.assertEqual(data, b'')  # 现在应该返回空字节

        # 在测试完成后，关闭文件以避免资源泄露
        if file._file is not None:
            file._file.close()

    def test_write(self):
        file = File(self.file_path)
        additional_data = b' appended'
        file.write(additional_data)

        # Re-open the file to check the content
        with open(self.file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'Test data appended')

        # 测试连续写入
        additional_data_2 = b' More data'
        file.write(additional_data_2)

        with open(self.file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'Test data appended More data')

    def test_create_read_stream(self):
        stream = File.create_read_stream(self.file_path)
        self.assertIsNotNone(stream)
        self.assertEqual(stream.read(), b'Test data')
        stream.close()

        # 测试打开不存在的文件
        with self.assertRaises(FileNotFoundError):
            File.create_read_stream('/invalid/path')

    def test_create_write_stream(self):
        stream = File.create_write_stream(self.file_path)
        self.assertIsNotNone(stream)
        
        stream.write(b' additional data')
        stream.close()

        # Re-open the file to check the new content
        with open(self.file_path, 'rb') as f:
            content = f.read()
            self.assertEqual(content, b'Test data additional data')

    def test_length_of_nonexistent_file(self):
        nonexistent_file = File('/invalid/path')
        with self.assertRaises(FileNotFoundError):
            nonexistent_file.length()

    def test_read_nonexistent_file(self):
        nonexistent_file = File('/invalid/path')
        with self.assertRaises(FileNotFoundError):
            nonexistent_file.read(10)

    def test_create_time_of_nonexistent_file(self):
        nonexistent_file = File('/invalid/path')
        with self.assertRaises(FileNotFoundError):
            nonexistent_file.create_time()

    def test_modify_time_of_nonexistent_file(self):
        nonexistent_file = File('/invalid/path')
        with self.assertRaises(FileNotFoundError):
            nonexistent_file.modify_time()