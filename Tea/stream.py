from _io import TextIOWrapper, BufferedReader


class BaseStream:
    def __init__(self, size=1024):
        self.size = size

    def read(self, size=1024):
        raise ImportError('read method must be overridden')

    def __len__(self):
        raise ImportError('__len__ method must be overridden')

    def __next__(self):
        raise ImportError('__next__ method must be overridden')

    def __iter__(self):
        return self


STREAM_CLASS = (TextIOWrapper, BufferedReader, BaseStream)
