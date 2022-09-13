
import ctypes
from ctypes import (
    CFUNCTYPE, POINTER, PYFUNCTYPE, Array, Structure, _SimpleCData, addressof, c_char, c_char_p, c_double, c_float,
    c_int, c_int8, c_int16, c_int32, c_int64, c_longlong, c_short, c_size_t, c_ssize_t, c_ubyte, c_uint, c_uint8,
    c_uint16, c_uint32, c_uint64, c_ulonglong, c_ushort, c_void_p, memmove
)
from ctypes import py_object as py_object_t
from ctypes import pythonapi, sizeof, string_at
from functools import lru_cache
from types import FunctionType, MappingProxyType
from typing import TYPE_CHECKING, Any, TypeVar, cast

from .string import String
from .types import C_T_CDB, CDataBase

if TYPE_CHECKING:
    from ctypes import _Pointer  # type: ignore
else:
    _Pointer = None


__all__ = [
    'c_void_p',

    'c_char', 'c_char_p', 'StrType',

    'c_float', 'c_double',

    'c_int',
    'c_int8', 'c_int16', 'c_int32', 'c_int64',
    'c_int8_t', 'c_int16_t', 'c_int32_t', 'c_int64_t',

    'c_uint',
    'c_uint8', 'c_uint16', 'c_uint32', 'c_uint64',
    'c_uint8_t', 'c_uint16_t', 'c_uint32_t', 'c_uint64_t',

    'c_size_t', 'c_ptrdiff_t', 'c_intptr_t',

    'py_object_t', 'py_object', 'CFUNCTYPE', 'FuncPointerType',

    'PyTypeObject', 'PyObject', 'PyVarObject', 'PyDictObject', 'StgDictObject',

    'mappingproxyobject', 'ffi_type',

    'None_ptr',

    'get_stgdict_of_type', 'make_callback_returnable',
]


c_int8_t = c_char
c_int16_t = c_short
c_int32_t = c_int
c_int64_t = c_longlong
c_uint8_t = c_ubyte
c_uint16_t = c_ushort
c_uint32_t = c_uint
c_uint64_t = c_ulonglong

if TYPE_CHECKING:
    c_ptrdiff_t: type[_SimpleCData[int]]
    c_intptr_t: type[_SimpleCData[int]]
    from ctypes import _FuncPointer as FuncPointerType
    py_object = py_object_t[Any]
else:
    FuncPointerType = FunctionType
    py_object = py_object_t


_int_types = (c_int16, c_int32, c_int64)

for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = c_intptr_t = t

StrType = str | Array[c_char] | c_char_p | String


# The PyTypeObject struct from 'Include/object.h'.
# This is a forward declaration, fields are set later once PyVarObject has been declared.


class PyTypeObject(Structure):
    ...


# The PyObject struct from 'Include/object.h'.
class PyObject(Structure):
    _fields_ = [
        ('ob_refcnt', c_ssize_t),
        ('ob_type', POINTER(PyTypeObject)),
    ]


# The PyVarObject struct from 'Include/object.h'.
class PyVarObject(Structure):
    _fields_ = [
        ('ob_base', PyObject),
        ('ob_size', c_ssize_t),
    ]


# This structure is not stable across Python versions, but the few fields that we use probably won't change.
PyTypeObject._fields_ = [
    ('ob_base', PyVarObject),
    ('tp_name', c_char_p),
    ('tp_basicsize', c_ssize_t),
    ('tp_itemsize', c_ssize_t),
    # There are many more fields, but we're only interested in the size fields, so we can leave out everything else.
]


# The PyTypeObject structure for the dict class.
# This is used to determine the size of the PyDictObject structure.
PyDict_Type = PyTypeObject.from_address(id(dict))


# The PyDictObject structure from 'Include/dictobject.h'.
# This structure is not stable across Python versions, and did indeed change in recent Python releases.
# Because we only care about the size of the structure and not its actual contents,
# we can declare it as an opaque byte array, with the length taken from PyDict_Type.
class PyDictObject(Structure):
    _fields_ = [
        ('PyDictObject_opaque', (c_ubyte * PyDict_Type.tp_basicsize)),
    ]


# The mappingproxyobject struct from 'Objects/descrobject.c'.
# This structure is not officially stable across Python versions, but its layout hasn't changed since 2001.
class mappingproxyobject(Structure):
    _fields_ = [
        ('ob_base', PyObject),
        ('mapping', py_object),
    ]


# https://github.com/python/cpython/blob/main/Modules/_ctypes/libffi_osx/include/ffi.h#L140-L145
class ffi_type(Structure):
    ...


ffi_type._fields_ = [
    ('size', c_size_t),
    ('alignment', c_ushort),
    ('type', c_ushort),
    ('elements', POINTER(POINTER(ffi_type)))
]


None_ptr = ctypes.cast(id(None), POINTER(PyObject))

# https://github.com/python/cpython/blob/main/Modules/_ctypes/ctypes.h#L31-L32
GETFUNC = PYFUNCTYPE(py_object, c_void_p, c_ssize_t)
SETFUNC = PYFUNCTYPE(c_void_p, c_void_p, py_object, c_ssize_t)
# PARAMFUNC = PYFUNCTYPE(POINTER(PyCArgObject), CDataObject)
PARAMFUNC = PYFUNCTYPE(POINTER(PyObject), PyObject)


class CDataBaseFix(CDataBase):
    __module__: str
    __name__: str
    _actual_size: int
    _ctypes_patch_getfunc: GETFUNC
    _ctypes_patch_setfunc: SETFUNC


C_T_CBF = TypeVar('C_T_CBF', bound=CDataBaseFix)


# https://github.com/python/cpython/blob/main/Modules/_ctypes/ctypes.h#L200-L233
class StgDictObject(Structure):
    _fields_ = [
        ('dict', PyDictObject),
        ('size', c_ssize_t),
        ('align', c_ssize_t),
        ('length', c_ssize_t),

        ('ffi_type_pointer', ffi_type),

        ('proto', py_object),

        ('setfunc', SETFUNC),
        ('getfunc', GETFUNC),
        ('paramfunc', PARAMFUNC),

        ('argtypes', POINTER(PyObject)),
        ('converters', POINTER(PyObject)),
        ('restype', POINTER(PyObject)),

        ('checker', POINTER(PyObject)),
        ('flags', c_int),

        ('format', c_char_p),
        ('ndim', c_int),
        ('shape', POINTER(c_ssize_t)),
        ('strides', POINTER(c_ssize_t)),
        ('suboffsets', POINTER(c_ssize_t))
    ]


pythonapi.Py_IncRef.restype = None
pythonapi.Py_IncRef.argtypes = [POINTER(PyObject)]


def get_stgdict_of_type(tp: C_T_CDB) -> int:
    tptp = type(tp)

    if not isinstance(tp, type):
        raise TypeError(f'Expected a type object, not {tptp.__module__}.{tptp.__qualname__}')

    stgdict = tp.__dict__  # type: ignore[unreachable]
    if isinstance(stgdict, MappingProxyType):
        stgdict = mappingproxyobject.from_address(id(stgdict)).mapping

    dict_tp = type(stgdict)

    if dict_tp.__name__ != 'StgDict':
        raise TypeError(
            f'The given type\'s dict must be a StgDict, not {dict_tp.__module__}.{dict_tp.__qualname__}'
        )

    return id(stgdict)


@lru_cache
def _check_size(func_name: str, ctype: CDataBaseFix, size: c_size_t) -> int:
    if int(size) not in {0, ctype._actual_size}:
        raise ValueError(
            f'{func_name} for ctype {ctype}: Requested size {size} does not match actual size {ctype._actual_size}'
        )

    return ctype._actual_size


def make_callback_returnable(ctype: CDataBase) -> C_T_CBF:
    ctypef = cast(C_T_CBF, ctype)

    if hasattr(ctype, '_ctypes_patch_getfunc'):
        return ctypef

    stgdict_c = StgDictObject.from_address(get_stgdict_of_type(ctypef))

    for func_type in {'getfunc', 'setfunc'}:
        if ctypes.cast(getattr(stgdict_c, func_type), c_void_p).value is not None:
            raise ValueError(
                f'The ctype {ctypef.__module__}.{ctypef.__name__} already has a {func_type}'
            )

    @GETFUNC  # type: ignore
    def getfunc(ptr: c_void_p, size: c_size_t) -> py_object:
        return ctype.from_buffer_copy(string_at(ptr, _check_size('getfunc', ctype, size)))  # type: ignore

    @SETFUNC  # type: ignore
    def setfunc(ptr: c_void_p, value: py_object, size: c_size_t) -> c_void_p:
        memmove(ptr, addressof(value), _check_size('setfunc', ctype, size))
        pythonapi.Py_IncRef(None_ptr)

        return ctypes.cast(None_ptr, c_void_p).value  # type: ignore

    ctypef._actual_size = sizeof(ctype)
    ctypef._ctypes_patch_getfunc = getfunc
    ctypef._ctypes_patch_setfunc = setfunc

    stgdict_c.getfunc = getfunc
    stgdict_c.setfunc = setfunc

    return ctypef
