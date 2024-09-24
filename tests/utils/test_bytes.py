import unittest
import base64
from darabonba.utils.bytes import Bytes

class TestBytes(unittest.TestCase):

    def test_from_(self):
        input_str = 'hello'
        expected_output = b'hello'
        result = Bytes.from_(input_str)
        self.assertEqual(result, expected_output)
        
        input_str = 'hello'
        encoding = 'utf-16'
        expected_output = input_str.encode(encoding)
        result = Bytes.from_(input_str, encoding)
        self.assertEqual(result, expected_output)
        
        input_str = 'hello'
        expected_output = base64.b64encode(b'hello')
        self.assertEqual(Bytes.from_(input_str, 'base64'), expected_output)
        
        input_str = 'hello'
        expected_output = b'68656c6c6f'
        self.assertEqual(Bytes.from_(input_str, 'hex'), expected_output)
        
        input_str = 'hello'
        with self.assertRaises(LookupError):  # LookUpError is more appropriate for invalid encodings
            Bytes.from_(input_str, 'invalid-encoding')
    
    def test_from_base64_valid(self):
        self.assertEqual(Bytes.from_base64('SGVsbG8='), b'Hello')
    
    def test_from_base64_invalid(self):
        with self.assertRaises(Exception) as context:
            Bytes.from_base64('InvalidBase64')
        self.assertEqual(str(context.exception), 'Invalid base64 string')

    def test_to_hex_valid(self):
        self.assertEqual(Bytes.to_hex(b'Hello'), '48656c6c6f')
    
    def test_to_hex_invalid(self):
        with self.assertRaises(Exception) as context:
            Bytes.to_hex('NotBytes')
        self.assertEqual(str(context.exception), 'Input must be of type bytes or bytearray')

    def test_to_base64_valid(self):
        self.assertEqual(Bytes.to_base64(b'Hello'), 'SGVsbG8=')
    
    def test_to_base64_invalid(self):
        with self.assertRaises(Exception) as context:
            Bytes.to_base64('NotBytes')
        self.assertEqual(str(context.exception), 'Input must be of type bytes or bytearray')

    def test_to_json_valid(self):
        json_bytes = b'{"key": "value"}'
        self.assertEqual(Bytes.to_json(json_bytes), {"key": "value"})
    
    def test_to_json_invalid_bytes(self):
        invalid_bytes = b'\xff\xfe\xfd'
        with self.assertRaises(Exception) as context:
            Bytes.to_json(invalid_bytes)
        self.assertEqual(str(context.exception), 'Invalid bytes for JSON conversion')
    
    def test_to_json_invalid_json(self):
        non_json_bytes = b'Not a JSON string'
        with self.assertRaises(Exception) as context:
            Bytes.to_json(non_json_bytes)
        self.assertEqual(str(context.exception), 'Invalid bytes for JSON conversion')