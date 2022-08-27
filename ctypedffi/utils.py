from __future__ import annotations

from dataclasses import dataclass
from inspect import get_annotations
from types import NoneType
from typing import Any, Callable, cast, overload

from .ctypes import CFUNCTYPE, FuncPointerType, StrType, c_double, c_int, c_void_p
from .string import String
from .types import CallingConvention, CDataBase, F, FuncPointer, P, Pointer, R, T

__all__ = [
    '_protected_keys',
    'ord_if_char',
    'normalize_cfunc',
    'as_cfunc'
]


_protected_keys = {
    '_fields_',
}


@overload
def ord_if_char(value: str | bytes) -> int:  # type: ignore
    ...


@overload
def ord_if_char(value: T) -> T:
    ...


def ord_if_char(value: T) -> T | int:
    if isinstance(value, (bytes, str)):
        return ord(value)

    return value


@dataclass
class NormalizedFunction:
    func: F
    name: str
    name_raw: str | None
    args_types: list[type[CDataBase]]
    args_types_raw: list[type[CDataBase]] | None
    res_type: type[CDataBase]
    res_type_raw: type[CDataBase] | None
    cconv: CallingConvention


def normalize_cfunc(
    func: F, name: str | None = None, def_cconv: CallingConvention = CallingConvention.C
) -> NormalizedFunction:
    if name is None:
        name = func.__name__

    arguments = get_annotations(func, eval_str=True)
    return_type = arguments.pop('return')
    args_types_raw = list(arguments.values())

    oname = func.__dict__.get('__ctdffi_oname__', None)
    cconv = func.__dict__.get('__ctdffi_cconv__', def_cconv)

    res_type, *args_types = [Pointer.normalize(val) for val in (return_type, *args_types_raw)]

    ores_type = func.__dict__.get('__ctdffi_ores_type__', None)
    oargs_types = func.__dict__.get('__ctdffi_oargs_types__', None)

    if ores_type is not None:
        ores_type = Pointer.normalize(ores_type)

    if oargs_types is not None:
        oargs_types = [Pointer.normalize(val) for val in oargs_types]

    return NormalizedFunction(func, name, oname, args_types, oargs_types, res_type, ores_type, cconv)


def as_cfunc(func: Callable[P, R], name: str | None = None) -> type[FuncPointer[P, R]]:
    norm = normalize_cfunc(func, name)

    return CFUNCTYPE(norm.res_type, *norm.args_types)  # type: ignore


def override(
    name: str | None = None, args_types: list[CDataBase] | None = None, res_type: CDataBase | None = None
) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        if name is not None:
            func.__setattr__('__ctdffi_oname__', name)

        if args_types is not None:
            func.__setattr__('__ctdffi_oargs_types__', args_types)

        if res_type is not None:
            func.__setattr__('__ctdffi_ores_type__', res_type)

        return func

    return wrapper


def wrap_func_pointer(
    func_ptr: FuncPointerType, name: str | None = None,
    def_cconv: CallingConvention = CallingConvention.C
) -> Callable[[Callable[P, R]], FuncPointer[P, R]]:
    def wrapper(func: Callable[P, R]) -> FuncPointer[P, R]:
        norm = normalize_cfunc(func, name, def_cconv)

        func_pointer = func_ptr
        func_pointer.argtypes = norm.args_types
        func_pointer.restype = norm.res_type

        return func_pointer  # type: ignore

    return wrapper


_normalization_map = {
    NoneType: c_void_p,
    float: c_double,
    int: c_int,
    bool: c_int,
    str: String,
    StrType: String
}


def normalize_ctype(value: Any) -> type[CDataBase]:
    return cast(type[CDataBase], _normalization_map.get(value, value))
