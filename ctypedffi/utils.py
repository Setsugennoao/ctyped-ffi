from __future__ import annotations

from ctypes import CFUNCTYPE
from inspect import get_annotations
from types import NoneType
from typing import Any, Callable, cast, overload

from .ctypes import StrType, c_double, c_int, c_void_p
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


def normalize_cfunc(
    func: F, name: str, def_cconv: CallingConvention = CallingConvention.C
) -> tuple[F, str, list[type[CDataBase]], type[CDataBase], CallingConvention]:
    cconv = CallingConvention(
        func.__dict__.get('__ctdffi_cconv__', def_cconv)
    )

    arguments = get_annotations(func, eval_str=True)

    return_type = arguments.pop('return')

    res_type = Pointer.normalize(return_type)
    args_types = [Pointer.normalize(val) for val in arguments.values()]

    return func, name, args_types, res_type, cconv


def as_cfunc(func: Callable[P, R], name: str | None = None) -> type[FuncPointer[P, R]]:
    if name is None:
        name = func.__name__

    _, _, arg_types, res_type, _ = normalize_cfunc(func, name)

    return CFUNCTYPE(res_type, *arg_types)  # type: ignore


_normalization_map = {
    NoneType: c_void_p,
    float: c_double,
    int: c_int,
    str: String,
    StrType: String
}


def normalize_ctype(value: Any) -> type[CDataBase]:
    return cast(type[CDataBase], _normalization_map.get(value, value))
