from __future__ import annotations

from abc import abstractmethod
from ctypes import POINTER, Structure, c_void_p
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Generic, ParamSpec, Sequence, TypeVar

if TYPE_CHECKING:
    from ctypes import _CData as CDataBase
    from ctypes import _Pointer  # type: ignore
    from ctypes import _StructUnionMeta as StructMetaBase
else:
    _Pointer = Generic
    PointerBase = object
    StructMetaBase = type(Structure)
    CDataBase = Structure.__bases__[0]


__all__ = [
    'MetaClassDictBase',
    'StructMetaBase',
    'CDataBase',
    'Pointer', 'FuncPointer',
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
    class PointerBase(Generic[C_T], _Pointer[C_T]):
        ...
else:
    class PointerBase(Generic[C_T], CDataBase):
        ...


class Pointer(Generic[C_T], PointerBase[C_T]):
    _type_: type[C_T]
    contents: C_T

    def __class_getitem__(cls, _type: C_T) -> type[PointerBound]:
        class PointerInnerClass(PointerBound):
            __bound_value__ = _type

        return PointerInnerClass

    @staticmethod
    def _norm_ptr(cls_type: C_T) -> Pointer[C_T]:
        ptr_type = POINTER(cls_type)  # type: ignore

        if hasattr(cls_type, '_ctypes_patch_getfunc'):
            from .ctypes import make_callback_returnable

            return make_callback_returnable(ptr_type)  # type: ignore

        return ptr_type  # type: ignore

    def __new__(cls: type[Self], cls_type: C_T | None = None) -> type[Pointer[C_T]]:
        from .struct import Struct

        if cls_type.__class__.__base__ is Struct:
            return cls_type  # type: ignore

        if cls_type is None:
            if not hasattr(cls, '_type_'):
                return c_void_p(None)  # type: ignore

            cls_type = cls._type_  # type: ignore

        return Pointer._norm_ptr(cls_type)

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


class PointerBound(Pointer):  # type: ignore
    __bound_value__: C_TB  # type: ignore

    def __new__(cls: type[Self], size: int | None = None) -> Pointer[C_TB]:
        from .utils import normalize_ctype

        nvalue = normalize_ctype(cls.__bound_value__)  # type: ignore
        bvalue = nvalue if size is None else nvalue * size

        return Pointer._norm_ptr(bvalue)()  # type: ignore


class FuncPointer(Generic[P, R]):
    restype: type[CDataBase]
    argtypes: Sequence[type[CDataBase]]
    errcheck: Callable[[type[CDataBase] | None, FuncPointer[P, R], tuple[CDataBase, ...]], CDataBase]

    def __new__(cls: type[Self], func: c_void_p | Callable[P, R]) -> Self:
        ...

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
    @abstractmethod
    def _setitem_(self, name: str, value: object, /) -> None:
        ...

    def __setitem__(self, name: str, value: object, /) -> None:
        if name.startswith('__'):
            return dict.__setitem__(self, name, value)

        return self._setitem_(name, value)
