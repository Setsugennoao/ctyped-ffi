from __future__ import annotations

from typing import Any, Mapping, cast

from ctypesgen.libraryloader import LibraryLoader, load_library  # type: ignore

from .types import CallingConvention, MetaClassDictBase, Self
from .utils import normalize_cfunc

__all__ = [
    'LibraryMeta', 'Library',
    'CallingConvention'
]


class LibraryMetaDict(MetaClassDictBase):
    def __init__(self, lib_name: str, def_cconv: CallingConvention):
        self.lib = load_library(lib_name)
        self.def_cconv = def_cconv
        self['__pytydffi_lib__'] = self.lib

    def _setitem_(self, name: str, value: Any, /) -> None:
        if callable(value):
            norm = normalize_cfunc(value, name, self.def_cconv)

            value = self.lib.get(norm.oname or norm.name, norm.cconv.value)
            value.argtypes = norm.oargs_types or norm.args_types
            value.restype = norm.ores_type or norm.res_type

        return dict.__setitem__(self, name, value)


class LibraryMeta(type):
    @classmethod
    def _check_self(self, name: str, bases: tuple[type, ...], **kwargs: Any) -> str | None:
        if name == 'Library' and not bases:
            return None

        if Library not in bases:
            raise ValueError(
                'LibraryMeta: You should inherit from Library, not LibraryMeta directly!'
            )

        lib_name = kwargs.get('lib', None)

        if lib_name is None:
            raise ValueError(
                'Library: You have to specify the library name with `lib=\'libname\'`!'
            )

        return cast(str, lib_name)

    @property
    def lib(self) -> LibraryLoader:
        return self.__dict__.__getitem__('__pytydffi_lib__')

    @classmethod
    def __prepare__(metacls, name: str, bases: tuple[type, ...], /, **kwargs: Any) -> Mapping[str, object]:
        lib_name = LibraryMeta._check_self(name, bases, **kwargs)

        if lib_name is None:
            return dict()

        return LibraryMetaDict(lib_name, kwargs.get('cconv', CallingConvention.C))

    def __new__(
        cls: type[Self], name: str, bases: tuple[type, ...], namespace: dict[str, Any],
        /, **kwargs: Any
    ) -> Self:
        LibraryMeta._check_self(name, bases, **kwargs)

        return type.__new__(cls, name, bases, namespace)


class Library(metaclass=LibraryMeta):
    ...
