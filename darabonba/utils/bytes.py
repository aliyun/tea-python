import base64
import json
import codecs
class Bytes:

    @staticmethod
    def from_(input_str, encoding='utf-8'):
        """Convert a string to bytes."""
        try:
            if encoding == 'base64':
                return base64.b64encode(input_str.encode('utf-8'))
            elif encoding == 'hex':
                return codecs.encode(input_str.encode('utf-8'), 'hex')
            else:
                return input_str.encode(encoding)
        except ValueError:
            raise Exception('Invalid string')

    @staticmethod
    def from_base64(base64_string):
        """Convert a base64 string to bytes."""
        try:
            return base64.b64decode(base64_string)
        except (ValueError, TypeError):
            raise Exception('Invalid base64 string')

    @staticmethod
    def to_hex(byte_data):
        """Convert bytes to a hex string."""
        if not isinstance(byte_data, (bytes, bytearray)):
            raise Exception('Input must be of type bytes or bytearray')
        return byte_data.hex()

    @staticmethod
    def to_base64(byte_data):
        """Convert bytes to a base64 string."""
        if not isinstance(byte_data, (bytes, bytearray)):
            raise Exception('Input must be of type bytes or bytearray')
        return base64.b64encode(byte_data).decode('utf-8')

    @staticmethod
    def to_json(byte_data, encoding='utf-8'):
        """Convert bytes to a JSON object assuming a string format."""
        if not isinstance(byte_data, (bytes, bytearray)):
            raise Exception('Input must be of type bytes or bytearray')
        try:
            return json.loads(byte_data.decode(encoding))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise Exception('Invalid bytes for JSON conversion')