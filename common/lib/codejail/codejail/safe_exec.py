"""Safe execution of untrusted Python code."""

import json
import textwrap

import lazymod
import jailpy

# If we aren't running safe, then we need to artificially pass the values
# through a JSON straw to ensure we aren't passing something that won't
# be executable in the safe context.
def straw(d):
    jd = {}
    for k,v in d.iteritems():
        try:
            json.dumps(v)
        except TypeError:
            continue
        else:
            jd[k] = v
    return json.loads(json.dumps(jd))

def safe_exec(code, globals_dict, locals_dict, future_division=False, assumed_imports=None):
    """Execute code safely.

    Returns None.  The code can modify globals in `global_dict`.

    """
    if future_division:
        code = "from __future__ import division\n" + code

    g_dict = straw(globals_dict)
    l_dict = straw(locals_dict)

    for modname in assumed_imports or ():
        if isinstance(modname, tuple):
            name, modname = modname
        else:
            name = modname
        g_dict[name] = lazymod.LazyModule(modname)

    exec code in g_dict, l_dict

    globals_dict.update(straw(g_dict))
    locals_dict.update(straw(l_dict))

# We'll need the code from lazymod.py for use in jailpy, so read it now.
lazymod_py_file = lazymod.__file__
if lazymod_py_file.endswith("c"):
    lazymod_py_file = lazymod_py_file[:-1]

lazymod_py = open(lazymod_py_file).read()


def safe_exec(code, globals_dict, locals_dict, future_division=False, assumed_imports=None):
    the_code = []

    if future_division:
        the_code.append("from __future__ import division\n")

    the_code.append(textwrap.dedent("""\
        import json
        import sys
        code, g_dict, l_dict = json.load(sys.stdin)
        """))

    if assumed_imports:
        the_code.append(lazymod_py)
        for modname in assumed_imports:
            if isinstance(modname, tuple):
                name, modname = modname
            else:
                name = modname
            the_code.append("g_dict['{}'] = LazyModule('{}')\n".format(name, modname))

    the_code.append(textwrap.dedent("""\
        exec code in g_dict, l_dict
        print >>sys.stderr, l_dict.keys()
        ok_types = (type(None), int, long, float, str, unicode, list, tuple, dict)
        l_dict = {k:v for k,v in l_dict.iteritems() if isinstance(v, ok_types)}
        json.dump(l_dict, sys.stdout)
        """))

    if 0:
        print "-- {:-<40}".format("jailed ")
        print "".join(the_code)
        print "-- {:-<40}".format("exec ")
        print code

    stdin = json.dumps([code, globals_dict, locals_dict])
    res = jailpy.jailpy("".join(the_code), stdin=stdin)
    if res.status != 0:
        raise Exception("Couldn't excecute jailed code: %s" % res.stderr)
    locals_dict.update(json.loads(res.stdout))
