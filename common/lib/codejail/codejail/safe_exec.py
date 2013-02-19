"""Safe execution of untrusted Python code."""

import json
import textwrap

import lazymod
import jailpy

# We'll need the code from lazymod.py for use in jailpy, so read it now.
lazymod_py_file = lazymod.__file__
if lazymod_py_file.endswith("c"):
    lazymod_py_file = lazymod_py_file[:-1]

lazymod_py = open(lazymod_py_file).read()


def safe_exec(code, globals_dict, locals_dict, future_division=False, assumed_imports=None):
    """Execute code as "exec" does, but safely.

    `code` is a string of Python code.  `globals_dict` and `locals_dict` are
    dictionaries to use as the globals and locals.  Modifications the code
    makes to `locals_dict` are reflected in the dictionary on return.

    `future_division` determines whether Python-3-style division is used.

    `assumed_imports` is a list of modules to make available as implicit
    imports for the code.  Entries are either a name, "mod", which makes
    "import mod" part of the code, or a pair, ("f", "fooey"), which makes
    "import fooey as f" part of the code.  The module name can be dotted.

    Returns None.  Changes made by `code` are visible in `locals_dict`.

    """
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
        ok_types = (type(None), int, long, float, str, unicode, list, tuple, dict)
        l_dict = {k:v for k,v in l_dict.iteritems() if isinstance(v, ok_types)}
        json.dump(l_dict, sys.stdout)
        """))

    # Turn this on to see what's being executed.
    if 0:
        print "--{:-<40}".format(" jailed ")
        print "".join(the_code)
        print "--{:-<40}".format(" exec ")
        print code

    stdin = json.dumps([code, globals_dict, locals_dict])
    res = jailpy.jailpy("".join(the_code), stdin=stdin)
    if res.status != 0:
        raise Exception("Couldn't excecute jailed code: %s" % res.stderr)
    locals_dict.update(json.loads(res.stdout))


def not_safe_exec(code, globals_dict, locals_dict, future_division=False, assumed_imports=None):
    """Another implementation of `safe_exec`, but not safe.

    This can be swapped in for debugging problems in sandboxed Python code.

    """
    def straw(d):
        """Return only the JSON-safe part of d.

        Used to emulate reading data through a serialization straw.

        """
        jd = {}
        for k,v in d.iteritems():
            try:
                json.dumps(v)
            except TypeError:
                continue
            else:
                jd[k] = v
        return json.loads(json.dumps(jd))

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

    locals_dict.update(straw(l_dict))

# Running Python code in the sandbox makes it difficult to debug.
# Turn this on to run the code directly.
if 0:
    safe_exec = not_safe_exec
