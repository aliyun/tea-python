import unittest
import base64
from darabonba.utils.bytes import Bytes

class TestBytes(unittest.TestCase):

    def test_from_base64(self):
        original = b'Hello, World!'
        base64_encoded = base64.b64encode(original).decode('utf-8')
        decoded = Bytes.from_(base64_encoded, 'base64')
        self.assertEqual(decoded, b'Hello, World!')

    def test_from_hex(self):
        original = b'Hello, World!'
        hex_encoded = original.hex()
        decoded = Bytes.from_(hex_encoded, 'hex')
        self.assertEqual(decoded, b'Hello, World!')

    def test_from_utf8(self):
        original = b'Hello, World!'
        decoded = Bytes.from_(original, 'utf-8')
        self.assertEqual(decoded, original)

    def test_from_utf16(self):
        original = 'Hello, World!'.encode('utf-16')
        decoded = Bytes.from_(original, 'utf-16')
        self.assertEqual(decoded.decode('utf-16'), 'Hello, World!')  # 进行内容比较而不是字节比较

    def test_from_utf32(self):
        original = 'Hello, World!'.encode('utf-32')
        decoded = Bytes.from_(original, 'utf-32')
        self.assertEqual(decoded.decode('utf-32'), 'Hello, World!')  # 进行内容比较而不是字节比较

    def test_from_binary(self):
        binary_string = '010010000110010101101100011011000110111100100001'  # 'Hello!' 的二进制表示
        decoded = Bytes.from_(binary_string, 'binary')
        self.assertEqual(decoded, b'Hello!')

    def test_unsupported_encoding(self):
        with self.assertRaises(ValueError) as context:
            Bytes.from_("Hello", "unsupported")
        self.assertEqual(str(context.exception), "Unsupported encoding: unsupported")

if __name__ == '__main__':
    unittest.main()
