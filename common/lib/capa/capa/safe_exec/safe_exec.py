"""Capa's specialized use of codejail.safe_exec."""


import hashlib

from codejail.safe_exec import SafeExecException, json_safe
from codejail.safe_exec import not_safe_exec as codejail_not_safe_exec
from codejail.safe_exec import safe_exec as codejail_safe_exec
import six
from six import text_type

from . import lazymod

# Establish the Python environment for Capa.
# Capa assumes float-friendly division always.
# The name "random" is a properly-seeded stand-in for the random module.
CODE_PROLOG = """\
from __future__ import absolute_import, division

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"    # See TNL-6456

import random2 as random_module
import sys
from six.moves import xrange

random = random_module.Random(%r)
random.Random = random_module.Random
sys.modules['random'] = random
"""

ASSUMED_IMPORTS = [
    ("numpy", "numpy"),
    ("math", "math"),
    ("scipy", "scipy"),
    ("calc", "calc"),
    ("eia", "eia"),
    ("chemcalc", "chem.chemcalc"),
    ("chemtools", "chem.chemtools"),
    ("miller", "chem.miller"),
    ("draganddrop", "verifiers.draganddrop"),
]

# We'll need the code from lazymod.py for use in safe_exec, so read it now.
lazymod_py_file = lazymod.__file__
if lazymod_py_file.endswith("c"):
    lazymod_py_file = lazymod_py_file[:-1]

with open(lazymod_py_file) as f:
    lazymod_py = f.read()

LAZY_IMPORTS = [lazymod_py]
for name, modname in ASSUMED_IMPORTS:
    LAZY_IMPORTS.append("{} = LazyModule('{}')\n".format(name, modname))

LAZY_IMPORTS = "".join(LAZY_IMPORTS)


def update_hash(hasher, obj):
    """
    Update a `hashlib` hasher with a nested object.

    To properly cache nested structures, we need to compute a hash from the
    entire structure, canonicalizing at every level.

    `hasher`'s `.update()` method is called a number of times, touching all of
    `obj` in the process.  Only primitive JSON-safe types are supported.

    """
    hasher.update(six.b(str(type(obj))))
    if isinstance(obj, (tuple, list)):
        for e in obj:
            update_hash(hasher, e)
    elif isinstance(obj, dict):
        for k in sorted(obj):
            update_hash(hasher, k)
            update_hash(hasher, obj[k])
    else:
        hasher.update(six.b(repr(obj)))


def safe_exec(
    code,
    globals_dict,
    random_seed=None,
    python_path=None,
    extra_files=None,
    cache=None,
    limit_overrides_context=None,
    slug=None,
    unsafely=False,
):
    """
    Execute python code safely.

    `code` is the Python code to execute.  It has access to the globals in `globals_dict`,
    and any changes it makes to those globals are visible in `globals_dict` when this
    function returns.

    `random_seed` will be used to see the `random` module available to the code.

    `python_path` is a list of filenames or directories to add to the Python
    path before execution.  If the name is not in `extra_files`, then it will
    also be copied into the sandbox.

    `extra_files` is a list of (filename, contents) pairs.  These files are
    created in the sandbox.

    `cache` is an object with .get(key) and .set(key, value) methods.  It will be used
    to cache the execution, taking into account the code, the values of the globals,
    and the random seed.

    `limit_overrides_context` is an optional string to be used as a key on
    the `settings.CODE_JAIL['limit_overrides']` dictionary in order to apply
    context-specific overrides to the codejail execution limits.
    If `limit_overrides_context` is omitted or not present in limit_overrides,
    then use the default limits specified insettings.CODE_JAIL['limits'].

    `slug` is an arbitrary string, a description that's meaningful to the
    caller, that will be used in log messages.

    If `unsafely` is true, then the code will actually be executed without sandboxing.
    """
    # Check the cache for a previous result.
    if cache:
        safe_globals = json_safe(globals_dict)
        md5er = hashlib.md5()
        md5er.update(repr(code).encode('utf-8'))
        update_hash(md5er, safe_globals)
        key = "safe_exec.%r.%s" % (random_seed, md5er.hexdigest())
        cached = cache.get(key)
        if cached is not None:
            # We have a cached result.  The result is a pair: the exception
            # message, if any, else None; and the resulting globals dictionary.
            emsg, cleaned_results = cached
            globals_dict.update(cleaned_results)
            if emsg:
                raise SafeExecException(emsg)
            return

    # Create the complete code we'll run.
    code_prolog = CODE_PROLOG % random_seed

    # Decide which code executor to use.
    if unsafely:
        exec_fn = codejail_not_safe_exec
    else:
        exec_fn = codejail_safe_exec

    # Run the code!  Results are side effects in globals_dict.
    try:
        exec_fn(
            code_prolog + LAZY_IMPORTS + code,
            globals_dict,
            python_path=python_path,
            extra_files=extra_files,
            limit_overrides_context=limit_overrides_context,
            slug=slug,
        )
    except SafeExecException as e:
        # Saving SafeExecException e in exception to be used later.
        exception = e
        emsg = text_type(e)
    else:
        emsg = None

    # Put the result back in the cache.  This is complicated by the fact that
    # the globals dict might not be entirely serializable.
    if cache:
        cleaned_results = json_safe(globals_dict)
        cache.set(key, (emsg, cleaned_results))

    # If an exception happened, raise it now.
    if emsg:
        raise exception
