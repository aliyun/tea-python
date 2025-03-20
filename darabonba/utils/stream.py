import json
import re
from darabonba.event import Event

sse_line_pattern = re.compile('(?P<name>[^:]*):?( ?(?P<value>.*))?')

class BaseStream:
    def __init__(self, size=1024):
        self.size = size

    def read(self, size=1024):
        raise NotImplementedError('read method must be overridden')

    def __len__(self):
        raise NotImplementedError('__len__ method must be overridden')

    def __next__(self):
        raise NotImplementedError('__next__ method must be overridden')

    def __iter__(self):
        return self


class _ReadableMc(type):
    def __instancecheck__(self, instance):
        if hasattr(instance, 'read') and hasattr(instance, '__iter__'):
            return True


class READABLE(metaclass=_ReadableMc):
    pass


class _WriteableMc(type):
    def __instancecheck__(self, instance):
        if hasattr(instance, 'write'):
            return True


class WRITABLE(metaclass=_WriteableMc):
    pass


STREAM_CLASS = (READABLE, WRITABLE)

class Stream:

    def __init__(self, data=None):
        self.data = data if data is not None else b''
        self.position = 0

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

    def read_as_sse(stream):
        event = Event()
        for line_bytes in stream:
            line = line_bytes.decode('utf-8')
            if not line.strip() or line.startswith(':'):
                continue
            match = sse_line_pattern.match(line)
            if match:
                name = match.group('name')
                value = match.group('value')
                if name == 'data':
                    if event.data:
                        event.data = f'{event.data}\n{value}'
                    else:
                        event.data = value
                elif name == 'event':
                    event.event = value
                elif name == 'id':
                    event.id = value
                elif name == 'retry':
                    event.retry = int(value)
        yield {'event': event}

    async def read_as_sse_async(stream):
        event = Event()
        async for line_bytes in stream:
            line = line_bytes.decode('utf-8')
            if not line.strip() or line.startswith(':'):
                continue
            match = sse_line_pattern.match(line)
            if match:
                name = match.group('name')
                value = match.group('value')
                if name == 'data':
                    if event.data:
                        event.data = f'{event.data}\n{value}'
                    else:
                        event.data = value
                elif name == 'event':
                    event.event = value
                elif name == 'id':
                    event.id = value
                elif name == 'retry':
                    event.retry = int(value)
        yield {'event': event}

    def read(self, size=None):
        if size is None:
            return self.data[self.position:]
        
        start = self.position
        end = min(start + size, len(self.data))
        self.position = end
        return self.data[start:end]

    def write(self, data):
        if isinstance(data, (bytes, str)):
            self.data = data
        else:
            raise TypeError("Data should be bytes or string.")

    def pipe(self, output_stream, buffer_size=1024):
        if not isinstance(output_stream, Stream):
            raise TypeError("Output stream should be an instance of Stream.")
        
        while True:
            chunk = self.read(buffer_size)
            if not chunk:
                break
            output_stream.write(chunk) 