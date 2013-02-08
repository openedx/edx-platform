"""Safe execution of untrusted Python code."""

import json

from .lazymod import LazyModule

def straw(v):
    return json.loads(json.dumps(jsonable_dict(v)))

def jsonable_dict(d):
    jd = {}
    for k,v in d.iteritems():
        try:
            json.dumps(v)
        except TypeError:
            continue
        else:
            jd[k] = v
    return jd

def safe_exec(code, globals_dict, locals_dict=None, future_division=False, assumed_imports=None):
    if future_division:
        code = "from __future__ import division\n" + code

    g_dict = straw(globals_dict)

    if locals_dict is None:
        l_dict = g_dict
    else:
        l_dict = straw(locals_dict)

    for modname in assumed_imports or ():
        if isinstance(modname, tuple):
            name, modname = modname
        else:
            name = modname
        g_dict[name] = LazyModule(modname)

    exec code in g_dict, l_dict

    globals_dict.update(straw(g_dict))
    if locals_dict is not None:
        locals_dict.update(straw(l_dict))
