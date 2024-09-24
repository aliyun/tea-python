import unittest
import os
from io import StringIO
from unittest.mock import patch
from darabonba.utils.file import File

class TestFile(unittest.TestCase):

    def setUp(self):
        # Create a temporary file for testing
        self.test_file = 'test_file.txt'
        with open(self.test_file, 'w') as f:
            f.write('Hello, world!')

    def tearDown(self):
        # Remove temporary file after tests
        try:
            os.remove(self.test_file)
        except OSError:
            pass

    def test_create_read_stream_file_exists(self):
        # Test reading a stream from an existing file
        read_stream = File.create_read_stream(self.test_file)
        content = read_stream.read()
        read_stream.close()
        self.assertEqual(content, 'Hello, world!')

    def test_create_read_stream_file_not_exists(self):
        # Test reading a stream from a non-existing file raises an exception
        with self.assertRaises(Exception) as context:
            File.create_read_stream('non_existing_file.txt')
        self.assertEqual(str(context.exception), 'File not found: non_existing_file.txt')

    def test_create_write_stream(self):
        # Test writing a stream to a new file
        new_file = 'new_file.txt'
        write_stream = None
        try:
            write_stream = File.create_write_stream(new_file)
            write_stream.write('Testing write stream.')
            write_stream.close()
            with open(new_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, 'Testing write stream.')
        finally:
            try:
                os.remove(new_file)
            except OSError:
                pass

    def test_exists_true(self):
        # Test checking existence of an existing file
        self.assertTrue(File.exists(self.test_file))

    def test_exists_false(self):
        # Test checking existence of a non-existing file
        self.assertFalse(File.exists('non_existing_file.txt'))


if __name__ == '__main__':
    unittest.main()
