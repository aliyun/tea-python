import json
import re
from darabonba.event import Event
from io import BytesIO, StringIO
from typing import Any, BinaryIO

# define WRITEABLE
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
    def __read_part(f, size=1024):
        while True:
            part = f.read(size)
            if part:
                yield part
            else:
                return

    @staticmethod
    def __to_string(
        val: bytes,
    ) -> str:
        """
        Convert a bytes to string(utf8)
        @return: the return string
        """
        if isinstance(val, str):
            return val
        elif isinstance(val, bytes):
            return val.decode('utf-8')
        else:
            return str(val)

    @staticmethod
    def __parse_json(
        val: str,
    ) -> Any:
        """
        Parse it by JSON format
        @return: the parsed result
        """
        try:
            return json.loads(val)
        except ValueError:
            raise RuntimeError(f'Failed to parse the value as json format, Value: "{val}".')

    @staticmethod
    def read_as_bytes(stream) -> bytes:
        """
        Read data from a readable stream, and compose it to a bytes
        @param stream: the readable stream
        @return: the bytes result
        """
        if isinstance(stream, READABLE):
            b = b''
            for part in Stream.__read_part(stream, 1024):
                b += part
            return b
        elif isinstance(stream, bytes):
            return stream
        else:
            return bytes(stream, encoding='utf-8')
    
    @staticmethod
    async def read_as_bytes_async(stream) -> bytes:
        """
        Read data from a readable stream, and compose it to a bytes
        @param stream: the readable stream
        @return: the bytes result
        """
        if isinstance(stream, bytes):
            return stream
        elif isinstance(stream, str):
            return bytes(stream, encoding='utf-8')
        else:
            return await stream.read()
    
    @staticmethod
    def read_as_json(stream) -> Any:
        """
        Read data from a readable stream, and parse it by JSON format
        @param stream: the readable stream
        @return: the parsed result
        """
        return Stream.__parse_json(Stream.read_as_string(stream))

    @staticmethod
    async def read_as_json_async(stream) -> Any:
        """
        Read data from a readable stream, and parse it by JSON format
        @param stream: the readable stream
        @return: the parsed result
        """
        return Stream.__parse_json(
            await Stream.read_as_string_async(stream)
        )


    @staticmethod
    def read_as_string(stream) -> str:
        """
        Read data from a readable stream, and compose it to a string
        @param stream: the readable stream
        @return: the string result
        """
        buff = Stream.read_as_bytes(stream)
        return Stream.__to_string(buff)
    
    @staticmethod
    async def read_as_string_async(stream) -> str:
        """
        Read data from a readable stream, and compose it to a string
        @param stream: the readable stream
        @return: the string result
        """
        buff = await Stream.read_as_bytes_async(stream)
        return Stream.__to_string(buff)
    
    @staticmethod
    def read_as_sse(stream):
        bytes_content = Stream.read_as_bytes(stream)
        lines = bytes_content.splitlines()

        sse_line_pattern = re.compile(r'^(?P<name>[^:]+): (?P<value>.+)$')
        current_event = Event()  # Initialize current event
    
        for line_item in lines:
            line = line_item.decode('utf-8')

            if not line.strip() or line.startswith(':'):
                continue
            
            match = sse_line_pattern.match(line)
            if match:
                name = match.group('name')
                value = match.group('value')
                
                if name == 'event':
                    current_event.event = value
                elif name == 'id':
                    current_event.id = value
                elif name == 'data':
                    current_event.data = value
                elif name == 'retry':
                    try:
                        current_event.retry = int(value)
                    except ValueError:
                        pass

                # If data is present, yield the event since data line indicates completion of an event typically
            if current_event.data is not None:
                yield {
                    'id': current_event.id,
                    'event': current_event.event,
                    'data': current_event.data
                }
                current_event = Event() 

    @staticmethod
    async def read_as_sse_async(stream):
        bytes_content = await Stream.read_as_bytes_async(stream)
        lines = bytes_content.splitlines()

        sse_line_pattern = re.compile(r'^(?P<name>[^:]+): (?P<value>.+)$')
        event = Event()

        async for line_item in lines:
            line = line_item.decode('utf-8')

            if not line.strip() or line.startswith(':'):
                continue
            
            match = sse_line_pattern.match(line)
            if match:
                name = match.group('name')
                value = match.group('value')
                
                if name == 'event':
                    current_event.event = value
                elif name == 'id':
                    current_event.id = value
                elif name == 'data':
                    current_event.data = value
                elif name == 'retry':
                    try:
                        current_event.retry = int(value)
                    except ValueError:
                        pass

                # If data is present, yield the event since data line indicates completion of an event typically
            if current_event.data is not None:
                yield {
                    'id': current_event.id,
                    'event': current_event.event,
                    'data': current_event.data
                }
                current_event = Event() 

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
    
    @staticmethod
    def to_readable(
        value: Any,
    ) -> BinaryIO:
        """
        Assert a value, if it is a readable, return it, otherwise throws
        @return: the readable value
        """
        if isinstance(value, str):
            value = value.encode('utf-8')

        if isinstance(value, bytes):
            value = BytesIO(value)
        elif not isinstance(value, READABLE):
            raise ValueError(f'The value is not a readable')
        return value

    @staticmethod
    def to_writeable(
        value: Any,
    ) -> WRITABLE:
        """
        Assert a value, if it is a writeable, return it, otherwise throws
        @return: the writeable value
        """
        if isinstance(value, str):
            value = StringIO(value)

        elif isinstance(value, bytes):
            value = BytesIO(value)
        elif not isinstance(value, WRITABLE):
            raise ValueError(f'The value is not a writeable')
        return value