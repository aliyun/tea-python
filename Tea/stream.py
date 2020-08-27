from _io import (
    TextIOWrapper,
    BufferedReader, BytesIO,
    BufferedWriter
)


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


STREAM_CLASS = (TextIOWrapper, BufferedReader, BaseStream, BytesIO)
READABLE = (BaseStream, BufferedReader, BytesIO)
WRITABLE = (BufferedWriter,)
