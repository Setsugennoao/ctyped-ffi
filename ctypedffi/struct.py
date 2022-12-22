from __future__ import annotations

from ctypes import Structure
from inspect import get_annotations
from typing import TYPE_CHECKING, Any, Callable, Generic, Mapping, TypeVar

from .ctypes import make_callback_returnable
from .types import CDataBase, MetaClassDictBase, Self, StructMetaBase
from .utils import _protected_keys, as_cfunc, is_python_only, normalize_ctype

__all__ = [
    'StructMeta', 'Struct', 'OpaqueStruct'
]

F = TypeVar('F', bound=Callable[..., Any])

_opaqueset = False


class StructMetaDict(MetaClassDictBase):
    def _setitem_(self, name: str, value: Any, /) -> None:
        if self.to_process(value):
            value = as_cfunc(value, name)

            self['__slots__'].append(name)
            self['_fields_'].append((name, normalize_ctype(value)))

            return

        return dict.__setitem__(self, name, value)


class StructMeta(StructMetaBase):
    __bases__: tuple[type, ...]
    __slots__: list[str]
    _fields_: list[tuple[str, CDataBase]]  # type: ignore

    @classmethod
    def __prepare__(metacls, name: str, bases: tuple[type, ...], /, **kwargs: Any) -> Mapping[str, object]:
        global _opaqueset

        if name == 'OpaqueStruct':
            _opaqueset = True
        elif _opaqueset and OpaqueStruct in bases:
            return dict[str, Any]()

        return StructMetaDict(__slots__=[], _fields_=[])


class StructureBase(Generic[Self]):
    if TYPE_CHECKING:
        def __init__(self: type[Self]) -> None:  # type: ignore
            ...

    @staticmethod
    def annotate(cls: C_STB) -> C_STB:
        if Struct not in cls.mro():
            raise ValueError(
                'Struct.annotate: The annotated class must inherit from Struct!'
            )

        if OpaqueStruct not in cls.mro():
            for key, value in get_annotations(cls, eval_str=True).items():
                if key.startswith('__') or key in _protected_keys or is_python_only(value):
                    continue

                cls.__slots__.append(key)
                cls._fields_.append((key, normalize_ctype(value)))  # type: ignore

            class inner_annotated(cls):  # type: ignore
                __slots__ = cls.__slots__.copy()
                _fields_ = cls._fields_.copy()
        else:
            inner_annotated = cls  # type: ignore

        return make_callback_returnable(inner_annotated)  # type: ignore

    @staticmethod
    def python_only(func: F) -> F:
        func.__dict__['__python_only__'] = True
        return func


class Struct(StructureBase, Structure, metaclass=StructMeta):  # type: ignore
    ...


C_STB = TypeVar('C_STB', bound=StructMeta)


class OpaqueStruct(Struct):
    def __init__(self) -> None:
        raise NotImplementedError
