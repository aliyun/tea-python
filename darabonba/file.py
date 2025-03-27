import os
from datetime import datetime
from darabonba.date import Date

class File:
    def __init__(self, path: str):
        self._path = path
        self._file = None

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
        if self._file is None:
            self._file = open(self._path, 'rb')

        data = self._file.read(size)
        if not data:
            self._file.close()
            self._file = None
        return data

    def write(self, data: bytes) -> None:
        with open(self._path, 'ab') as f:
            f.write(data)

    @staticmethod
    def create_read_stream(path: str):
        return open(path, 'rb')

    @staticmethod
    def create_write_stream(path: str):
        return open(path, 'ab')