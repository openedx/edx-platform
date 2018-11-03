# coding: utf-8
"""zmq constants"""

from ._cffi import C, c_constant_names
from zmq.utils.constant_names import all_names

g = globals()
for cname in c_constant_names:
    if cname.startswith("ZMQ_"):
        name = cname[4:]
    else:
        name = cname
    g[name] = getattr(C, cname)

DRAFT_API = C.PYZMQ_DRAFT_API
__all__ = ['DRAFT_API'] + all_names
