from __future__ import annotations

from ctypes import Structure
from inspect import get_annotations
from typing import TYPE_CHECKING, Any, Generic, Mapping, TypeVar

from .ctypes import make_callback_returnable
from .types import CDataBase, MetaClassDictBase, Self, StructMetaBase
from .utils import _protected_keys, as_cfunc

__all__ = [
    'StructMeta', 'Struct', 'OpaqueStruct'
]


class StructMetaDict(MetaClassDictBase):
    def _setitem_(self, name: str, value: Any, /) -> None:
        if callable(value):
            value = as_cfunc(value, name)

            self['__slots__'].append(name)
            self['_fields_'].append((name, value))

            return

        return dict.__setitem__(self, name, value)


class StructMeta(StructMetaBase):
    __bases__: tuple[type, ...]
    __slots__: list[str]
    _fields_: list[tuple[str, CDataBase]]  # type: ignore

    @classmethod
    def __prepare__(metacls, name: str, bases: tuple[type, ...], /, **kwargs: Any) -> Mapping[str, object]:
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

        for key, value in get_annotations(cls, eval_str=True).items():
            if key.startswith('__') or key in _protected_keys:
                continue

            cls.__slots__.append(key)
            cls._fields_.append((key, value))

        return make_callback_returnable(cls)  # type: ignore


class Struct(StructureBase, Structure, metaclass=StructMeta):  # type: ignore
    ...


C_STB = TypeVar('C_STB', bound=StructMeta)


class OpaqueStruct(Struct):
    def __init__(self) -> None:
        raise NotImplementedError
