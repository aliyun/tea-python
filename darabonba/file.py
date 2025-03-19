import os
from datetime import datetime
from darabonba.date import Date

class File:
    def __init__(self, path: str):
        self._path = path

    @staticmethod
    def exists(path: str) -> bool:
        return os.path.exists(path)

    def path(self) -> str:
        return self._path

    def length(self) -> int:
        return os.path.getsize(self._path)

    def create_time(self) -> Date:
        ctime = os.path.getctime(self._path)
        return Date(datetime.fromtimestamp(ctime).isoformat())

    def modify_time(self) -> Date:
        mtime = os.path.getmtime(self._path)
        return Date(datetime.fromtimestamp(mtime).isoformat())

    def read(self, size: int) -> bytes:
        with open(self._path, 'rb') as f:
            return f.read(size)

    def write(self, data: bytes) -> None:
        with open(self._path, 'ab') as f:
            f.write(data)

    @staticmethod
    def create_read_stream(path: str):
        return open(path, 'rb')

    @staticmethod
    def create_write_stream(path: str):
        return open(path, 'ab')