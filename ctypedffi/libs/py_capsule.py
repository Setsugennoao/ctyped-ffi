from ctypes import pythonapi

from ..ctypes import c_char_p, c_void_p, py_object
from ..utils import wrap_func_pointer


@wrap_func_pointer(pythonapi.PyCapsule_GetName)
def GetName(obj: py_object) -> c_char_p:
    ...


@wrap_func_pointer(pythonapi.PyCapsule_GetPointer)
def GetPointer(obj: py_object, name: c_char_p) -> c_void_p:
    ...
