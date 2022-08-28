from __future__ import annotations

from dataclasses import dataclass
from inspect import get_annotations
from types import NoneType
from typing import Any, Callable, Generic, cast, overload

from .ctypes import CFUNCTYPE, FuncPointerType, StrType, c_double, c_int, c_void_p
from .string import String
from .types import CallingConvention, CDataBase, F, FuncPointer, P, Pointer, R, T

__all__ = [
    '_protected_keys',

    'ord_if_char',

    'normalize_cfunc', 'normalize_ctype',

    'as_cfunc', 'wrap_func_pointer',

    'with_signature',
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
class NormalizedFunction(Generic[P, R]):
    func: Callable[P, R]
    name: str
    oname: str | None
    args_types: list[type[CDataBase]]
    oargs_types: list[type[CDataBase]] | None
    res_type: type[CDataBase]
    ores_type: type[CDataBase] | None
    cconv: CallingConvention


def normalize_cfunc(
    func: Callable[P, R], name: str | None = None, def_cconv: CallingConvention = CallingConvention.C
) -> NormalizedFunction[P, R]:
    if '__wrapped__' in func.__dir__():
        old_dict = func.__dict__.copy()
        func = func.__wrapped__  # type: ignore
        func.__dict__ |= old_dict | func.__dict__

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


@overload
def as_cfunc(func: Callable[P, R], name: str | None = None) -> type[FuncPointer[P, R]]:
    ...


@overload
def as_cfunc(func: NormalizedFunction[P, R], name: str | None = None) -> type[FuncPointer[P, R]]:
    ...


def as_cfunc(func: Callable[P, R] | NormalizedFunction[P, R], name: str | None = None) -> type[FuncPointer[P, R]]:
    if not isinstance(func, NormalizedFunction):
        func = normalize_cfunc(func, name)

    return CFUNCTYPE(  # type: ignore
        func.ores_type or func.res_type, *(func.oargs_types or func.args_types)
    )


def with_signature(
    args_types: list[type[CDataBase]] | None = None,
    res_type: type[CDataBase] | None = None,
    name: str | None = None, **kwargs: type[CDataBase]
) -> Callable[[F], F]:
    def wrapper(func: F) -> F:
        nonlocal args_types, res_type, name, kwargs

        if name is not None:
            func.__dict__.__setitem__('__ctdffi_oname__', name)

        annotations = get_annotations(func, eval_str=True)

        if kwargs:
            if (empty_args := not args_types):
                args_types = []
            for i, (param_name, otype) in enumerate(annotations.items()):
                if param_name == 'return':
                    continue

                arg_type = kwargs.get(param_name, otype)

                if empty_args:
                    args_types.append(arg_type)
                else:
                    try:
                        args_types[i] = arg_type
                    except KeyError:
                        raise ValueError(
                            'override: Not enough arguments specified for args_types!'
                        )
        elif args_types:
            if len(args_types) != len(annotations) - ('return' in annotations):
                raise ValueError(
                    'override: Arguments number mismatch for args_types!'
                )

        if args_types is not None:
            func.__dict__.__setitem__('__ctdffi_oargs_types__', args_types)

        if res_type is not None:
            func.__dict__.__setitem__('__ctdffi_ores_type__', res_type)

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
