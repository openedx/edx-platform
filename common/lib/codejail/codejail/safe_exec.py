"""Safe execution of untrusted Python code."""

import json
import os.path
import shutil
import sys
import textwrap

import lazymod
import jailpy

from util import temp_directory, change_directory, TempDirectory

# We'll need the code from lazymod.py for use in jailpy, so read it now.
lazymod_py_file = lazymod.__file__
if lazymod_py_file.endswith("c"):
    lazymod_py_file = lazymod_py_file[:-1]

lazymod_py = open(lazymod_py_file).read()


def names_and_modules(assumed_imports):
    """Get uniform names and modules from assumed_imports."""
    for modname in assumed_imports:
        if isinstance(modname, tuple):
            yield modname
        else:
            yield modname, modname


def safe_exec(code, globals_dict, locals_dict, assumed_imports=None, files=None, python_path=None):
    """Execute code as "exec" does, but safely.

    `code` is a string of Python code.  `globals_dict` and `locals_dict` are
    dictionaries to use as the globals and locals.  Modifications the code
    makes to `locals_dict` are reflected in the dictionary on return.

    `assumed_imports` is a list of modules to make available as implicit
    imports for the code.  Entries are either a name, "mod", which makes
    "import mod" part of the code, or a pair, ("f", "fooey"), which makes
    "import fooey as f" part of the code.  The module name can be dotted.

    Returns None.  Changes made by `code` are visible in `locals_dict`.

    """
    the_code = []
    files = list(files or ())

    the_code.append(textwrap.dedent("""\
        import json
        import sys
        code, g_dict, l_dict = json.load(sys.stdin)
        """))

    for pydir in python_path or ():
        pybase = os.path.basename(pydir)
        the_code.append("sys.path.append(%r)\n" % pybase)
        files.append(pydir)

    if assumed_imports:
        the_code.append(lazymod_py)
        for name, modname in names_and_modules(assumed_imports):
            the_code.append("g_dict['{}'] = LazyModule('{}')\n".format(name, modname))

    the_code.append(textwrap.dedent("""\
        exec code in g_dict, l_dict
        ok_types = (type(None), int, long, float, str, unicode, list, tuple, dict)
        l_dict = {k:v for k,v in l_dict.iteritems() if isinstance(v, ok_types)}
        json.dump(l_dict, sys.stdout)
        """))

    stdin = json.dumps([code, globals_dict, locals_dict])
    jailed_code = "".join(the_code)

    # Turn this on to see what's being executed.
    if 0:
        print "--{:-<40}".format(" jailed ")
        print jailed_code
        print "--{:-<40}".format(" exec ")
        print code

    res = jailpy.jailpy(jailed_code, stdin=stdin, files=files)
    if res.status != 0:
        raise Exception("Couldn't excecute jailed code: %s" % res.stderr)
    locals_dict.update(json.loads(res.stdout))


def not_safe_exec(code, globals_dict, locals_dict, assumed_imports=None, files=None, python_path=None):
    """Another implementation of `safe_exec`, but not safe.

    This can be swapped in for debugging problems in sandboxed Python code.

    This is not thread-safe, due to temporarily changing the current directory
    and modifying sys.path.

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

    g_dict = straw(globals_dict)
    l_dict = straw(locals_dict)

    for name, modname in names_and_modules(assumed_imports or ()):
        g_dict[name] = lazymod.LazyModule(modname)

    with temp_directory(delete_when_done=True) as tmpdir:
        with change_directory(tmpdir):
            # Copy the files here.
            for filename in files or ():
                dest = os.path.join(tmpdir, os.path.basename(filename))
                shutil.copyfile(filename, dest)

            original_path = sys.path
            if python_path:
                sys.path.extend(python_path)
            try:
                exec code in g_dict, l_dict
            finally:
                sys.path = original_path

    locals_dict.update(straw(l_dict))

# Running Python code in the sandbox makes it difficult to debug.
# Change 0 to 1 to run the code directly.
if 0 or not jailpy.is_configured():
    safe_exec = not_safe_exec
