from typing import Awaitable, Callable, Generic, TypeVar

_T = TypeVar("_T")


class StreamIterator:
    def __init__(self, read_func) -> None:
        self.read_func = read_func

    def __iter__(self) -> "StreamIterator[_T]":
        return self

    def __next__(self) -> _T:
        try:
            rv = self.read_func()
        except EofStream:
            raise StopIteration
        if rv == b"":
            raise StopIteration
        return rv


class EofStream(Exception):
    """eof stream indication."""


class AsyncStreamIterator(Generic[_T]):
    def __init__(self, read_func: Callable[[], Awaitable[_T]]) -> None:
        self.read_func = read_func

    def __aiter__(self) -> "AsyncStreamIterator[_T]":
        return self

    async def __anext__(self) -> _T:
        try:
            rv = await self.read_func()
        except EofStream:
            raise StopAsyncIteration
        if rv == b"":
            raise StopAsyncIteration
        return rv
