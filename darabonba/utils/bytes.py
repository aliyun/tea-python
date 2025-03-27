import base64
from typing import Union

class Bytes:
    
    @staticmethod
    def from_(data: Union[str, bytes], encoding: str) -> bytes:
        if encoding == 'base64':
            if isinstance(data, str):
                data = data.encode('utf-8')
            return base64.b64decode(data)
        elif encoding == 'hex':
            if isinstance(data, str):
                return bytes.fromhex(data)
        elif encoding == 'utf-8':
            if isinstance(data, bytes):
                return data
            if isinstance(data, str):
                return data.encode('utf-8')
        elif encoding == 'utf-16':
            if isinstance(data, bytes):
                return data.decode('utf-16').encode('utf-16')
        elif encoding == 'utf-32':
            if isinstance(data, bytes):
                return data.decode('utf-32').encode('utf-32')
        elif encoding == 'binary':
            if isinstance(data, str):
                return bytes(int(data[i:i+8], 2) for i in range(0, len(data), 8))

        raise ValueError(f"Unsupported encoding: {encoding}")
