from __future__ import annotations

import array
import mmap
import pickle
import sys
from abc import abstractmethod
from ctypes import POINTER, Array, Union, c_char, c_char_p, cast
from typing import (
    TYPE_CHECKING, Any, Iterable, NoReturn, Protocol, SupportsIndex, TypeAlias, TypeVar, runtime_checkable
)

from .types import CDataBase

# From ctypesgen.printer_python.preamble.3_2, which isn't importable. Added typing and did small fixes.


__all__ = [
    'StrType',
    'UserString',
    'MutableString',
    'String'
]


@runtime_checkable
class SupportsString(Protocol):
    @abstractmethod
    def __str__(self) -> str:
        pass


ReadOnlyBuffer: TypeAlias = bytes
if TYPE_CHECKING:
    WriteableBuffer: TypeAlias = bytearray | memoryview | array.array[Any] | mmap.mmap | CDataBase | pickle.PickleBuffer
else:
    WriteableBuffer: TypeAlias = bytearray | memoryview | array.array | mmap.mmap | CDataBase | pickle.PickleBuffer

ReadableBuffer: TypeAlias = ReadOnlyBuffer | WriteableBuffer


def _args_nn(val: Any) -> tuple[Any, ...]:
    return () if val is None else (val, )


class UserString:
    data: bytes

    def __init__(self, seq: bytes | UserString | SupportsString) -> None:
        if isinstance(seq, bytes):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq).encode()

    def __bytes__(self) -> bytes:
        return self.data

    def __str__(self) -> str:
        return self.data.decode()

    def __repr__(self) -> str:
        return repr(self.data)

    def __int__(self) -> int:
        return int(self.data.decode())

    def __long__(self) -> int:
        return int(self.data.decode())

    def __float__(self) -> float:
        return float(self.data.decode())

    def __complex__(self) -> complex:
        return complex(self.data.decode())

    def __hash__(self) -> int:
        return hash(self.data)

    def __le__(self, string: bytes | UserString | SupportsString) -> bool:
        if isinstance(string, bytes):
            return self.data <= string
        elif isinstance(string, UserString):
            return self.data <= string.data
        else:
            return self.data <= str(string).encode()

    def __lt__(self, string: bytes | UserString | SupportsString) -> bool:
        if isinstance(string, bytes):
            return self.data < string
        elif isinstance(string, UserString):
            return self.data < string.data
        else:
            return self.data < str(string).encode()

    def __ge__(self, string: bytes | UserString | SupportsString) -> bool:
        if isinstance(string, bytes):
            return self.data >= string
        elif isinstance(string, UserString):
            return self.data >= string.data
        else:
            return self.data >= str(string).encode()

    def __gt__(self, string: bytes | UserString | SupportsString) -> bool:
        if isinstance(string, bytes):
            return self.data > string
        elif isinstance(string, UserString):
            return self.data > string.data
        else:
            return self.data > str(string).encode()

    def __eq__(self, string: bytes | UserString | SupportsString) -> bool:
        if isinstance(string, bytes):
            return self.data == string
        elif isinstance(string, UserString):
            return self.data == string.data
        else:
            return self.data == str(string).encode()

    def __ne__(self, string: bytes | UserString | SupportsString) -> bool:
        if isinstance(string, bytes):
            return self.data != string
        elif isinstance(string, UserString):
            return self.data != string.data
        else:
            return self.data != str(string).encode()

    def __contains__(self, char: SupportsIndex | bytes) -> bool:
        return char in self.data

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self: C_USB, index: int) -> C_USB:
        return self.__class__(self.data[index])

    def __getslice__(self: C_USB, start: int, end: int) -> C_USB:
        start = max(start, 0)
        end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self: C_USB, other: bytes | UserString | SupportsString) -> C_USB:
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, bytes):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other).encode())

    def __radd__(self: C_USB, other: bytes | UserString | SupportsString) -> C_USB:
        if isinstance(other, UserString):
            return self.__class__(other.data + self.data)
        elif isinstance(other, bytes):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other).encode() + self.data)

    def __mul__(self: C_USB, n: SupportsIndex) -> C_USB:
        return self.__class__(self.data * n)

    __rmul__ = __mul__

    def __mod__(self: C_USB, args: Any) -> C_USB:
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self: C_USB) -> C_USB:
        return self.__class__(self.data.capitalize())

    def center(self: C_USB, width: SupportsIndex, fillchar: bytes | None = None) -> C_USB:
        return self.__class__(self.data.center(width, *_args_nn(fillchar)))

    def count(
        self: C_USB, sub: ReadableBuffer | SupportsIndex,
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> int:
        return self.data.count(sub, start, end)

    def decode(self: C_USB, encoding: str | None = None, errors: str | None = None) -> C_USB:
        args = (encoding, errors) if (encoding and errors) else (encoding, ) if encoding else ()
        return self.__class__(self.data.decode(*args))

    def encode(self: C_USB, encoding: str | None = None, errors: str | None = None) -> C_USB:
        args = (encoding, errors) if (encoding and errors) else (encoding, ) if encoding else ()
        return self.__class__(self.data.decode(*args))

    def endswith(
        self: C_USB, suffix: ReadableBuffer | tuple[ReadableBuffer, ...],
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> bool:
        return self.data.endswith(suffix, start, end)

    def expandtabs(self: C_USB, tabsize: SupportsIndex = 8) -> C_USB:
        return self.__class__(self.data.expandtabs(tabsize))

    def find(
        self: C_USB, sub: ReadableBuffer | SupportsIndex,
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> int:
        return self.data.find(sub, start, end)

    def index(
        self: C_USB, sub: ReadableBuffer | SupportsIndex,
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> int:
        return self.data.index(sub, start, end)

    def isalpha(self: C_USB) -> bool:
        return self.data.isalpha()

    def isalnum(self: C_USB) -> bool:
        return self.data.isalnum()

    def isdecimal(self: C_USB) -> bool:
        return str(self.data).isdecimal()

    def isdigit(self: C_USB) -> bool:
        return self.data.isdigit()

    def islower(self: C_USB) -> bool:
        return self.data.islower()

    def isnumeric(self: C_USB) -> bool:
        return str(self.data).isnumeric()

    def isspace(self: C_USB) -> bool:
        return self.data.isspace()

    def istitle(self: C_USB) -> bool:
        return self.data.istitle()

    def isupper(self: C_USB) -> bool:
        return self.data.isupper()

    def join(self: C_USB, seq: Iterable[ReadableBuffer]) -> C_USB:
        return self.__class__(self.data.join(seq))

    def ljust(self: C_USB, width: SupportsIndex, fillchar: bytes | bytearray | None = None) -> C_USB:
        return self.__class__(self.data.ljust(width, *_args_nn(fillchar)))

    def lower(self: C_USB) -> C_USB:
        return self.__class__(self.data.lower())

    def lstrip(self: C_USB, chars: ReadableBuffer | None = None) -> C_USB:
        return self.__class__(self.data.lstrip(chars))

    def partition(self: C_USB, sep: ReadableBuffer) -> tuple[bytes, bytes, bytes]:
        return self.data.partition(sep)

    def replace(self: C_USB, old: ReadableBuffer, new: ReadableBuffer, maxsplit: SupportsIndex = -1) -> C_USB:
        return self.__class__(self.data.replace(old, new, maxsplit))

    def rfind(
        self: C_USB, sub: ReadableBuffer | SupportsIndex,
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> int:
        return self.data.rfind(sub, start, end)

    def rindex(
        self: C_USB, sub: ReadableBuffer | SupportsIndex,
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> int:
        return self.data.rindex(sub, start, end)

    def rjust(self: C_USB, width: SupportsIndex, fillchar: bytes | bytearray | None = None) -> C_USB:
        return self.__class__(self.data.rjust(width, *_args_nn(fillchar)))

    def rpartition(self: C_USB, sep: ReadableBuffer) -> tuple[bytes, bytes, bytes]:
        return self.data.rpartition(sep)

    def rstrip(self: C_USB, chars: ReadableBuffer | None = None) -> C_USB:
        return self.__class__(self.data.rstrip(chars))

    def split(self, sep: ReadableBuffer | None, maxsplit: SupportsIndex = -1) -> list[bytes]:
        return self.data.split(sep, maxsplit)

    def rsplit(self, sep: ReadableBuffer | None, maxsplit: SupportsIndex = -1) -> list[bytes]:
        return self.data.rsplit(sep, maxsplit)

    def splitlines(self: C_USB, keepends: bool = False) -> list[bytes]:
        return self.data.splitlines(keepends)

    def startswith(
        self, prefix: ReadableBuffer | tuple[ReadableBuffer, ...],
        start: SupportsIndex | None = 0, end: SupportsIndex | None = sys.maxsize
    ) -> bool:
        return self.data.startswith(prefix, start, end)

    def strip(self: C_USB, chars: ReadableBuffer | None = None) -> C_USB:
        return self.__class__(self.data.strip(chars))

    def swapcase(self: C_USB) -> C_USB:
        return self.__class__(self.data.swapcase())

    def title(self: C_USB) -> C_USB:
        return self.__class__(self.data.title())

    def translate(self: C_USB, table: ReadableBuffer | None, /, delete: bytes | None = None) -> C_USB:
        return self.__class__(self.data.translate(table, *_args_nn(delete)))

    def upper(self: C_USB) -> C_USB:
        return self.__class__(self.data.upper())

    def zfill(self: C_USB, width: SupportsIndex) -> C_USB:
        return self.__class__(self.data.zfill(width))


C_USB = TypeVar('C_USB', bound=UserString)


class MutableString(UserString):
    def __init__(self: C_MPB, string_data: str = '') -> None:
        self.data = str(string_data).encode()

    def __hash__(self) -> NoReturn:
        raise TypeError("unhashable mutable type")

    def __setitem__(self, index: int, sub: UserString | bytes | SupportsString) -> None:
        if index < 0:
            index += len(self.data)

        if index < 0 or index >= len(self.data):
            raise IndexError

        self.data = self.data[:index] + sub + self.data[index + 1:]  # type: ignore

    def __delitem__(self, index: int) -> None:
        if index < 0:
            index += len(self.data)

        if index < 0 or index >= len(self.data):
            raise IndexError

        self.data = self.data[:index] + self.data[index + 1:]

    def __setslice__(self, start: int, end: int, sub: UserString | bytes | SupportsString) -> None:
        start = max(start, 0)
        end = max(end, 0)

        if isinstance(sub, UserString):
            self.data = self.data[:start] + sub.data + self.data[end:]
        elif isinstance(sub, bytes):
            self.data = self.data[:start] + sub + self.data[end:]
        else:
            self.data = self.data[:start] + str(sub).encode() + self.data[end:]

    def __delslice__(self, start: int, end: int) -> None:
        start = max(start, 0)
        end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]

    def __iadd__(self: C_MPB, other: UserString | bytes | SupportsString) -> C_MPB:
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, bytes):
            self.data += other
        else:
            self.data += str(other).encode()
        return self

    def __imul__(self: C_MPB, n: SupportsIndex) -> C_MPB:
        self.data *= n
        return self

    def immutable(self) -> UserString:
        return UserString(self.data)


C_MPB = TypeVar('C_MPB', bound=MutableString)


class String(MutableString, Union):
    _fields_ = [("raw", POINTER(c_char)), ("data", c_char_p)]

    def __init__(self, obj: Any = "") -> None:
        if isinstance(obj, (bytes, UserString)):
            self.data = bytes(obj)
        else:
            self.raw = obj

    def __len__(self) -> int:
        return self.data and len(self.data) or 0

    @classmethod
    def from_param(cls, obj: StrType | int | None) -> StrType:
        if obj is None or obj == 0:  # Convert None or 0
            return cls(POINTER(c_char)())  # type: ignore
        elif isinstance(obj, bytes):  # Convert from bytes
            return cls(obj)
        elif isinstance(obj, str):  # Convert from str
            return cls(obj.encode())
        elif isinstance(obj, int):  # Convert from raw pointer
            return cls(cast(obj, POINTER(c_char)))
        elif isinstance(obj, String):  # Convert from String
            return obj
        elif isinstance(obj, c_char_p):  # Convert from c_char_p
            return obj
        elif isinstance(obj, POINTER(c_char)):  # Convert from POINTER(c_char)
            return obj
        elif isinstance(obj, c_char * len(obj)):  # Convert from c_char array
            return obj

        # Convert from object
        return String.from_param(obj._as_parameter_)


StrType = str | String | c_char_p | Array[c_char] | POINTER(c_char)
