from __future__ import annotations

from types import ModuleType
from typing import Any, Mapping, NoReturn

from .libs import PyCapsule
from .struct import Struct, StructMeta
from .types import MetaClassDictBase, Self
from .utils import as_cfunc, normalize_cfunc

__all__ = [
    'CythonModuleMeta', 'CythonModule'
]

_DUMMYMODULE = object()


class CythonModuleMetaDict(MetaClassDictBase):
    def __init__(self, cls_name: str, module: ModuleType | None) -> None:
        self.cls_name = cls_name
        self.module = module

        if module:
            self.capsules = module.__pyx_capi__
        else:
            self.capsules = dict[str, Any]()

        super().__init__(module=self.module, capsules=self.capsules)

    def _setitem_(self, name: str, value: Any, /) -> None:
        if callable(value):
            if self.module is None:
                value = self._raise_module_unavailable
            else:
                norm = normalize_cfunc(value, name)
                capsule_name = norm.oname or norm.name

                try:
                    capsule = self.capsules[capsule_name]
                except KeyError as e:
                    raise AttributeError(capsule_name) from e

                func_type = as_cfunc(norm)

                mangled_name = PyCapsule.GetName(capsule)
                capsule_ptr = PyCapsule.GetPointer(capsule, mangled_name)

                value = func_type(capsule_ptr)

        return dict.__setitem__(self, name, value)

    def _raise_module_unavailable(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise ModuleNotFoundError(
            f'{self.cls_name}: The cython module is unavailable!'
        )


class CythonModuleMeta(StructMeta):
    @classmethod
    def __prepare__(metacls, name: str, bases: tuple[type, ...], /, **kwargs: Any) -> Mapping[str, object]:
        if 'module' not in kwargs:
            raise ValueError(
                'CythonModule: You must specify a module with subclass kwargs!'
            )

        module = kwargs.pop('module')

        if module is _DUMMYMODULE:
            return dict[str, Any]()

        if module is not None and not hasattr(module, '__pyx_capi__'):
            raise ValueError(
                'CythonModule: Passed module isn\'t a cython module!'
            )

        return CythonModuleMetaDict(name, module)

    def __new__(
        cls: type[Self], name: str, bases: tuple[type, ...], namespace: dict[str, Any], /, **kwargs: Any
    ) -> Self:
        return super().__new__(cls, name, bases, namespace)  # type: ignore


class CythonModule(Struct, metaclass=CythonModuleMeta, module=_DUMMYMODULE):
    ...
