# coding: utf-8
"""The main CFFI wrapping of libzmq"""

# Copyright (C) PyZMQ Developers
# Distributed under the terms of the Modified BSD License.


import json
import os
from os.path import dirname, join
from cffi import FFI

from zmq.utils.constant_names import all_names, no_prefix


base_zmq_version = (3,2,2)

def load_compiler_config():
    """load pyzmq compiler arguments"""
    import zmq
    zmq_dir = dirname(zmq.__file__)
    zmq_parent = dirname(zmq_dir)
    
    fname = join(zmq_dir, 'utils', 'compiler.json')
    if os.path.exists(fname):
        with open(fname) as f:
            cfg = json.load(f)
    else:
        cfg = {}
    
    cfg.setdefault("include_dirs", [])
    cfg.setdefault("library_dirs", [])
    cfg.setdefault("runtime_library_dirs", [])
    cfg.setdefault("libraries", ["zmq"])
    
    # cast to str, because cffi can't handle unicode paths (?!)
    cfg['libraries'] = [str(lib) for lib in cfg['libraries']]
    for key in ("include_dirs", "library_dirs", "runtime_library_dirs"):
        # interpret paths relative to parent of zmq (like source tree)
        abs_paths = []
        for p in cfg[key]:
            if p.startswith('zmq'):
                p = join(zmq_parent, p)
            abs_paths.append(str(p))
        cfg[key] = abs_paths
    return cfg


def zmq_version_info():
    """Get libzmq version as tuple of ints"""
    major = ffi.new('int*')
    minor = ffi.new('int*')
    patch = ffi.new('int*')

    C.zmq_version(major, minor, patch)

    return (int(major[0]), int(minor[0]), int(patch[0]))


cfg = load_compiler_config()
ffi = FFI()

def _make_defines(names):
    _names = []
    for name in names:
        define_line = "#define %s ..." % (name)
        _names.append(define_line)

    return "\n".join(_names)

c_constant_names = ['PYZMQ_DRAFT_API']
for name in all_names:
    if no_prefix(name):
        c_constant_names.append(name)
    else:
        c_constant_names.append("ZMQ_" + name)

# load ffi definitions
here = os.path.dirname(__file__)
with open(os.path.join(here, '_cdefs.h')) as f:
    _cdefs = f.read()

with open(os.path.join(here, '_verify.c')) as f:
    _verify = f.read()

ffi.cdef(_cdefs)
ffi.cdef(_make_defines(c_constant_names))

try:
    C = ffi.verify(_verify,
        modulename='_cffi_ext',
        libraries=cfg['libraries'],
        include_dirs=cfg['include_dirs'],
        library_dirs=cfg['library_dirs'],
        runtime_library_dirs=cfg['runtime_library_dirs'],
    )
    _version_info = zmq_version_info()
except Exception as e:
    raise ImportError("PyZMQ CFFI backend couldn't find zeromq: %s\n"
    "Please check that you have zeromq headers and libraries." % e)

if _version_info < (3,2,2):
    raise ImportError("PyZMQ CFFI backend requires zeromq >= 3.2.2,"
        " but found %i.%i.%i" % _version_info
    )

nsp = new_sizet_pointer = lambda length: ffi.new('size_t*', length)

new_uint64_pointer = lambda: (ffi.new('uint64_t*'),
                              nsp(ffi.sizeof('uint64_t')))
new_int64_pointer = lambda: (ffi.new('int64_t*'),
                             nsp(ffi.sizeof('int64_t')))
new_int_pointer = lambda: (ffi.new('int*'),
                           nsp(ffi.sizeof('int')))
new_binary_data = lambda length: (ffi.new('char[%d]' % (length)),
                                  nsp(ffi.sizeof('char') * length))

value_uint64_pointer = lambda val : (ffi.new('uint64_t*', val),
                                     ffi.sizeof('uint64_t'))
value_int64_pointer = lambda val: (ffi.new('int64_t*', val),
                                   ffi.sizeof('int64_t'))
value_int_pointer = lambda val: (ffi.new('int*', val),
                                 ffi.sizeof('int'))
value_binary_data = lambda val, length: (ffi.new('char[%d]' % (length + 1), val),
                                         ffi.sizeof('char') * length)

IPC_PATH_MAX_LEN = C.get_ipc_path_max_len()
