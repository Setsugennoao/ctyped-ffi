
from types import ModuleType
from typing import Any, Mapping

from .libs import PyCapsule
from .struct import Struct, StructMeta
from .types import MetaClassDictBase, Self
from .utils import as_cfunc

__all__ = [
    'CythonModuleMeta', 'CythonModule'
]


class CythonModuleMetaDict(MetaClassDictBase):
    def __init__(self, module: ModuleType) -> None:
        self.module = module
        self.capsules = module.__pyx_capi__

        super().__init__(module=self.module, capsules=self.capsules, __slots__=[], _fields_=[])

    def _setitem_(self, name: str, value: Any, /) -> None:
        if callable(value):
            try:
                capsule = self.capsules[name]
            except KeyError as e:
                raise AttributeError(name) from e

            func_type = as_cfunc(value, name)

            mangled_name = PyCapsule.GetName(capsule)
            capsule_ptr = PyCapsule.GetPointer(capsule, mangled_name)

            value = func_type(capsule_ptr)

        return dict.__setitem__(self, name, value)


class CythonModuleMeta(StructMeta):
    @classmethod
    def __prepare__(metacls, name: str, bases: tuple[type, ...], /, **kwargs: Any) -> Mapping[str, object]:
        if 'module' in kwargs:
            module = kwargs.pop('module')

            if module is not None:
                if not hasattr(module, '__pyx_capi__'):
                    raise ValueError("Not a cython module.")

                return CythonModuleMetaDict(module)

        return dict[str, Any]()

    def __new__(
        cls: type[Self], name: str, bases: tuple[type, ...], namespace: dict[str, Any], /, **kwargs: Any
    ) -> Self:
        return super().__new__(cls, name, bases, namespace)  # type: ignore


class CythonModule(Struct, metaclass=CythonModuleMeta, module=None):
    ...
