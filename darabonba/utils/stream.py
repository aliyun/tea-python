import json

class Stream:

    def __init__(self, data=None):
        self.data = data if data is not None else b''

    @staticmethod
    def read_as_bytes(data):
        if isinstance(data, bytes):
            return data
        elif isinstance(data, str):
            return data.encode('utf-8')
        else:
            raise TypeError("Data should be bytes or string.")

    @staticmethod
    def read_as_json(data):
        if isinstance(data, str):
            return json.loads(data)
        elif isinstance(data, bytes):
            return json.loads(data.decode('utf-8'))
        else:
            raise TypeError("Data should be bytes or string.")

    @staticmethod
    def read_as_string(data):
        if isinstance(data, bytes):
            return data.decode('utf-8')
        elif isinstance(data, str):
            return data
        else:
            raise TypeError("Data should be bytes or string.")

    @staticmethod
    def read_as_sse(data):
        if isinstance(data, str):
            return 'data: {}\n\n'.format(data)
        elif isinstance(data, bytes):
            return 'data: {}\n\n'.format(data.decode('utf-8'))
        else:
            raise TypeError("Data should be bytes or string.")

    def read(self):
        return self.data

    def write(self, data):
        if isinstance(data, (bytes, str)):
            self.data = data
        else:
            raise TypeError("Data should be bytes or string.")

    def pipe(self, output_stream):
        if isinstance(output_stream, Stream):
            output_stream.write(self.read())
        else:
            raise TypeError("Output stream should be an instance of Stream.")