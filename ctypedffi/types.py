from __future__ import annotations

import array
import builtins
import mmap
from abc import abstractmethod
from ctypes import CDLL, POINTER, Structure, c_void_p, pointer
from enum import Enum
from pickle import PickleBuffer
from types import FunctionType, UnionType
from typing import TYPE_CHECKING, Any, Callable, Generic, ParamSpec, Sequence, TypeAlias, TypeVar

if TYPE_CHECKING:
    from ctypes import _CData as CDataBase
    from ctypes import _FuncPointer as FuncPointerType
    from ctypes import _Pointer
    from ctypes import _StructUnionMeta as StructMetaBase
else:
    _Pointer = Generic
    PointerBase = object
    FuncPointerType = FunctionType
    StructMetaBase = type(Structure)
    CDataBase = Structure.__bases__[0]


ReadOnlyBuffer: TypeAlias = bytes
if TYPE_CHECKING:
    WriteableBuffer: TypeAlias = (
        bytearray | memoryview | array.array[Any] | mmap.mmap | CDataBase | PickleBuffer
    )
else:
    WriteableBuffer: TypeAlias = (
        bytearray | memoryview | array.array | mmap.mmap | CDataBase | PickleBuffer
    )
ReadableBuffer: TypeAlias = ReadOnlyBuffer | WriteableBuffer


__all__ = [
    'MetaClassDictBase',
    'StructMetaBase',
    'CDataBase',
    'Pointer', 'FuncPointer', 'FuncPointerType',
    'T', 'F', 'P', 'R', 'C_T', 'Self',
    'CallingConvention'
]


T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
C_T = TypeVar('C_T')
C_TB = TypeVar('C_TB')
C_T_CDB = TypeVar('C_T_CDB', bound=CDataBase)
Self = TypeVar('Self')
P = ParamSpec('P')
R = TypeVar('R')


if TYPE_CHECKING:
    class PointerBase(Generic[C_T], _Pointer[C_T]):  # type: ignore
        ...
else:
    class PointerBase(Generic[C_T], CDataBase):
        ...


class Pointer(Generic[C_T], PointerBase[C_T]):
    _type_: type[C_T]
    contents: C_T

    def __class_getitem__(cls, _type: C_T) -> type[PointerBound]:
        try:
            return _cache_pbound_getitem[_type]
        except KeyError:
            from .utils import normalize_ctype

            _typev = normalize_ctype(_type)

            class PointerInnerClass(PointerBound):
                __bound_value__ = _typev
                __norm_bvalue__ = Pointer._norm_ptr(_typev)

            _cache_pbound_getitem[_type] = PointerInnerClass

        return _cache_pbound_getitem[_type]

    @staticmethod
    def _norm_ptr(cls_type: C_T) -> Pointer[C_T]:
        ptr_type = POINTER(cls_type)  # type: ignore

        if hasattr(cls_type, '_ctypes_patch_getfunc'):
            from .ctypes import make_callback_returnable

            return make_callback_returnable(ptr_type)  # type: ignore

        return ptr_type  # type: ignore

    def __new__(cls: type[Self], cls_type: C_T | None = None) -> type[Pointer[C_T]]:  # type: ignore
        if not isinstance(cls_type, type):
            return pointer(cls_type)  # type: ignore

        from .struct import Struct

        if cls_type.__class__.__base__ is Struct:  # type: ignore
            return cls_type

        if cls_type is None:
            if not hasattr(cls, '_type_'):  # type: ignore
                return c_void_p(None)

            cls_type = cls._type_

        return Pointer._norm_ptr(cls_type)  # type: ignore

    @staticmethod
    def _to_normalize(value: Any) -> bool:
        return hasattr(value, 'mro') and (Pointer in value.mro())

    @staticmethod
    def normalize(value: Any) -> type[CDataBase]:
        from .utils import normalize_ctype

        value = normalize_ctype(value)

        if Pointer._to_normalize(value):
            if hasattr(value, '__args__'):
                basecls = value.__args__[0]
            else:
                basecls = value.__bound_value__

            basecls = normalize_ctype(basecls)
            if Pointer._to_normalize(basecls):
                basecls = Pointer.normalize(basecls)

            value = Pointer._norm_ptr(basecls)

        return normalize_ctype(value)

    @classmethod
    def from_buffer(cls: type[Self], source: WriteableBuffer, offset: int = 0) -> Self:
        return Pointer.normalize(cls).from_buffer(source, offset)  # type: ignore

    @classmethod
    def from_buffer_copy(cls: type[Self], source: ReadableBuffer, offset: int = 0) -> Self:
        return Pointer.normalize(cls).from_buffer_copy(source, offset)  # type: ignore

    @classmethod
    def from_address(cls: type[Self], address: int) -> Self:
        return Pointer.normalize(cls).from_address(address)  # type: ignore

    @classmethod
    def from_param(cls: type[Self], obj: Any) -> Self:
        return Pointer.normalize(cls).from_param(obj)  # type: ignore

    @classmethod
    def in_dll(cls: type[Self], library: CDLL, name: str) -> Self:
        return Pointer.normalize(cls).in_dll(library, name)  # type: ignore


class PointerBound(Pointer):  # type: ignore
    __bound_value__: C_TB  # type: ignore
    __norm_bvalue__: Pointer[C_TB]

    def __new__(cls: type[Self], value: Self | Any | None = None) -> Pointer[C_TB]:  # type: ignore
        if value is None:
            try:
                return _cache_pbound_voidptr[cls]  # type: ignore
            except KeyError:
                ...

        ptr = cls.__norm_bvalue__()  # type: ignore

        if value is None:
            _cache_pbound_voidptr[cls] = ptr  # type: ignore

        return ptr  # type: ignore


if TYPE_CHECKING:
    class CFuncPointerBase(FuncPointerType):
        _flags_: int
else:
    from _ctypes import FUNCFLAG_CDECL, FUNCFLAG_USE_ERRNO, FUNCFLAG_USE_LASTERROR, CFuncPtr

    class CFuncPointerBase(CFuncPtr):
        _flags_ = FUNCFLAG_CDECL | FUNCFLAG_USE_ERRNO | FUNCFLAG_USE_LASTERROR


class FuncPointer(Generic[P, R], CFuncPointerBase):
    _flags_ = CFuncPointerBase._flags_

    if TYPE_CHECKING:
        restype: type[CDataBase]
        argtypes: Sequence[type[CDataBase]]
        errcheck: Callable[  # type: ignore
            [type[CDataBase] | None, FuncPointer[P, R], tuple[CDataBase, ...]], CDataBase
        ]

    def __new__(cls: type[Self], func: c_void_p | Callable[P, R] | None = None) -> Self:
        if func is None:
            def _func(*args):  # type: ignore
                ...
            func = _func  # type: ignore
        return super().__new__(cls, func)  # type: ignore

    if TYPE_CHECKING:
        def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
            ...


class CallingConvention(str, Enum):
    C = 'cdecl'
    Win32 = 'stdcall'

    def __call__(self, func: F) -> F:
        if not callable(func):
            raise ValueError(
                'CallingConvention: Call must be used as a decorator on a funtion!'
            )

        func.__dict__.__setitem__('__ctdffi_cconv__', self)

        return func


class MetaClassDictBase(dict[str, Any]):
    @classmethod
    def to_process(cls, value: object, ) -> bool:
        from .utils import is_python_only
        return callable(value) and not is_python_only(value)

    @abstractmethod
    def _setitem_(self, name: str, value: object, /) -> None:
        ...

    def __setitem__(self, name: str, value: object, /) -> None:
        if name.startswith('__'):
            return dict.__setitem__(self, name, value)

        return self._setitem_(name, value)


if TYPE_CHECKING:
    _cache_pbound_getitem = dict[C_T, type[PointerBound]]()
    _cache_pbound_voidptr = dict[type[PointerBound], Pointer[C_T]]()
else:
    _cache_pbound_getitem = {}
    _cache_pbound_voidptr = {}


builtins_isinstance = builtins.isinstance


def ctypedffi_isinstance(
    __obj: object, __class_or_tuple: type | UnionType | tuple[type | UnionType | tuple[Any, ...], ...]
) -> bool:
    if builtins_isinstance(__class_or_tuple, type) and issubclass(__class_or_tuple, PointerBound):  # type: ignore
        __class_or_tuple = __class_or_tuple.__norm_bvalue__  # type: ignore

    return builtins_isinstance(__obj, __class_or_tuple)


builtins.isinstance = ctypedffi_isinstance
