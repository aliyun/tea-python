import json
import re
import aiohttp
import codecs
from darabonba.event import Event

from io import BytesIO, StringIO
from typing import Any, BinaryIO, Generator, AsyncGenerator, Dict

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

class SyncSSEResponseWrapper:
    def __init__(self, session, response):
        self.session = session
        self.response = response
        self._closed = False
    
    def close(self):
        if not self._closed:
            self.response.close()
            self.session.close()
            self._closed = True
    
    def __iter__(self):
        return self._read_chunks()
    
    def _read_chunks(self):
        try:
            for chunk in self.response.iter_content(chunk_size=8192):
                yield chunk
        finally:
            self.close()
    
    def read(self) -> bytes:
        try:
            return self.response.content
        finally:
            self.close()

class SSEResponseWrapper:
    def __init__(self, session: aiohttp.ClientSession, response: aiohttp.ClientResponse):
        self.session = session
        self.response = response
        self._closed = False
        self._content_cache = None
    
    async def close(self):
        if not self._closed:
            self.response.close()
            await self.session.close()
            self._closed = True
    
    def __aiter__(self):
        return self._read_chunks()
    
    async def _read_chunks(self):
        try:
            async for chunk in self.response.content.iter_chunked(8192):
                yield chunk
        finally:
            await self.close()
    
    async def read(self) -> bytes:
        if self._content_cache is not None:
            return self._content_cache
        
        try:
            content = await self.response.read()
            self._content_cache = content
            return content
        finally:
            await self.close()

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
    def read_as_sse(stream) -> Generator[Event, None, None]:
        """
        Read events from SSE stream (synchronous version)
        """
        if isinstance(stream, SyncSSEResponseWrapper):
            for event in Stream._parse_sse_stream_sync(stream):
                yield Event(
                    id=event.get('id'),
                    data=event.get('data'),
                    event=event.get('event'),
                    retry=event.get('retry'))
        elif hasattr(stream, 'iter_content'):
            # Read directly from the content stream of requests response object
            for event in Stream._parse_sse_stream_from_response_sync(stream):
                yield Event(
                    id=event.get('id'),
                    data=event.get('data'),
                    event=event.get('event'),
                    retry=event.get('retry'))
        else:
            for event in Stream._parse_sse_stream_sync(stream):
                yield Event(
                    id=event.get('id'),
                    data=event.get('data'),
                    event=event.get('event'),
                    retry=event.get('retry'))

    @staticmethod
    async def read_as_sse_async(stream) -> AsyncGenerator[Event, None]:
        """
        Read events from SSE stream
        """
        if isinstance(stream, SSEResponseWrapper):
            async for event in Stream._parse_sse_stream(stream):
                yield Event(
                    id = event.get('id'),
                    data = event.get('data'),
                    event= event.get('event'),
                    retry = event.get('retry'))
        elif hasattr(stream, 'content'):
            # Read directly from the content stream of aiohttp response object
            async for event in Stream._parse_sse_stream_from_response(stream):
                yield Event(
                    id = event.get('id'),
                    data = event.get('data'),
                    event= event.get('event'),
                    retry = event.get('retry'))
        else:
            async for event in Stream._parse_sse_stream(stream):
                yield Event(
                    id = event.get('id'),
                    data = event.get('data'),
                    event= event.get('event'),
                    retry = event.get('retry'))

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
    
    @staticmethod
    async def _parse_sse_stream(wrapper: SSEResponseWrapper) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Analyze SSE stream data
        """
        buffer = ""
        current_event = Event()
        
        MAX_BUFFER_SIZE = 1024 * 1024  # 1MB
        dec = codecs.getincrementaldecoder('utf-8')()
        
        async for chunk in wrapper:
            try:
                chunk_str = dec.decode(chunk)
            except UnicodeDecodeError:
                chunk_str = chunk.decode('utf-8', errors='replace')
            
            if len(buffer) + len(chunk_str) > MAX_BUFFER_SIZE:
                import logging
                logging.warning("SSE stream data too large, skipping chunk")
                continue
                
            buffer += chunk_str

            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.rstrip('\r')  # Remove \r
                
                if not line.strip():
                    if current_event.data is not None:
                        yield {
                            'id': current_event.id,
                            'event': current_event.event or 'message',
                            'data': current_event.data,
                            'retry': current_event.retry
                        }
                        current_event = Event()
                    continue
                
                if line.startswith(':'):
                    continue
                
                if ':' in line:
                    match = sse_line_pattern.match(line)
                    if match:
                        name = match.group('name').strip()
                        value = match.group('value').strip()
                        
                        if name == 'event':
                            current_event.event = value
                        elif name == 'id':
                            current_event.id = value
                        elif name == 'data':
                            if current_event.data is None:
                                current_event.data = value
                            else:
                                current_event.data += '\n' + value
                        elif name == 'retry':
                            try:
                                current_event.retry = int(value)
                            except ValueError:
                                pass
                else:
                    if current_event.data is None:
                        current_event.data = line
                    else:
                        current_event.data += '\n' + line

        if buffer.strip() and current_event.data is not None:
            yield {
                'id': current_event.id,
                'event': current_event.event or 'message',
                'data': current_event.data,
                'retry': current_event.retry
            }

    @staticmethod
    async def _parse_sse_stream_from_response(response) -> AsyncGenerator[Dict[str, Any], None]:
        buffer = ""
        current_event = Event()

        async for chunk in response.content.iter_chunked(8192):
            try:
                chunk_str = chunk.decode('utf-8')
            except UnicodeDecodeError:
                continue
            
            buffer += chunk_str
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.rstrip('\r')
                
                if not line.strip():
                    if current_event.data is not None:
                        yield {
                            'id': current_event.id,
                            'event': current_event.event or 'message',
                            'data': current_event.data,
                            'retry': current_event.retry
                        }
                        current_event = Event()
                    continue
                
                if line.startswith(':'):
                    continue
                
                if ':' in line:
                    match = sse_line_pattern.match(line)
                    if match:
                        name = match.group('name').strip()
                        value = match.group('value').strip()
                        
                        if name == 'event':
                            current_event.event = value
                        elif name == 'id':
                            current_event.id = value
                        elif name == 'data':
                            if current_event.data is None:
                                current_event.data = value
                            else:
                                current_event.data += '\n' + value
                        elif name == 'retry':
                            try:
                                current_event.retry = int(value)
                            except ValueError:
                                pass
                else:
                    if current_event.data is None:
                        current_event.data = line
                    else:
                        current_event.data += '\n' + line

        if buffer.strip() and current_event.data is not None:
            yield {
                'id': current_event.id,
                'event': current_event.event or 'message',
                'data': current_event.data,
                'retry': current_event.retry
            }
    
    @staticmethod
    def _parse_sse_stream_sync(wrapper: SyncSSEResponseWrapper) -> Generator[Dict[str, Any], None, None]:
        """
        Analyze SSE stream data (synchronous version)
        """
        buffer = ""
        current_event = Event()

        for chunk in wrapper:
            # Decoding byte data into strings
            try:
                chunk_str = chunk.decode('utf-8')
            except UnicodeDecodeError:
                # If decoding fails, skip this chunk
                continue
            
            buffer += chunk_str
            
            # Split processing by row
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.rstrip('\r')  # Remove \r
                
                if not line.strip():
                    if current_event.data is not None:
                        yield {
                            'id': current_event.id,
                            'event': current_event.event or 'message',
                            'data': current_event.data,
                            'retry': current_event.retry
                        }
                        current_event = Event()
                    continue
                
                # Skip comment lines
                if line.startswith(':'):
                    continue
                
                if ':' in line:
                    match = sse_line_pattern.match(line)
                    if match:
                        name = match.group('name').strip()
                        value = match.group('value').strip()
                        
                        if name == 'event':
                            current_event.event = value
                        elif name == 'id':
                            current_event.id = value
                        elif name == 'data':
                            if current_event.data is None:
                                current_event.data = value
                            else:
                                current_event.data += '\n' + value
                        elif name == 'retry':
                            try:
                                current_event.retry = int(value)
                            except ValueError:
                                pass
                else:
                    if current_event.data is None:
                        current_event.data = line
                    else:
                        current_event.data += '\n' + line

        if buffer.strip() and current_event.data is not None:
            yield {
                'id': current_event.id,
                'event': current_event.event or 'message',
                'data': current_event.data,
                'retry': current_event.retry
            }

    @staticmethod
    def _parse_sse_stream_from_response_sync(response) -> Generator[Dict[str, Any], None, None]:
        """
        Parse SSE stream from requests response object (synchronous version)
        """
        buffer = ""
        current_event = Event()

        for chunk in response.iter_content(chunk_size=8192):
            try:
                chunk_str = chunk.decode('utf-8')
            except UnicodeDecodeError:
                continue
            
            buffer += chunk_str
            
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.rstrip('\r')
                
                if not line.strip():
                    if current_event.data is not None:
                        yield {
                            'id': current_event.id,
                            'event': current_event.event or 'message',
                            'data': current_event.data,
                            'retry': current_event.retry
                        }
                        current_event = Event()
                    continue
                
                if line.startswith(':'):
                    continue
                
                if ':' in line:
                    match = sse_line_pattern.match(line)
                    if match:
                        name = match.group('name').strip()
                        value = match.group('value').strip()
                        
                        if name == 'event':
                            current_event.event = value
                        elif name == 'id':
                            current_event.id = value
                        elif name == 'data':
                            if current_event.data is None:
                                current_event.data = value
                            else:
                                current_event.data += '\n' + value
                        elif name == 'retry':
                            try:
                                current_event.retry = int(value)
                            except ValueError:
                                pass
                else:
                    if current_event.data is None:
                        current_event.data = line
                    else:
                        current_event.data += '\n' + line

        if buffer.strip() and current_event.data is not None:
            yield {
                'id': current_event.id,
                'event': current_event.event or 'message',
                'data': current_event.data,
                'retry': current_event.retry
            }