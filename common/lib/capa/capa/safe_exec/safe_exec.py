"""Capa's specialized use of codejail.safe_exec."""

from codejail.safe_exec import safe_exec as codejail_safe_exec
from codejail.safe_exec import json_safe, SafeExecException
from . import lazymod
from statsd import statsd

import hashlib

# Establish the Python environment for Capa.
# Capa assumes float-friendly division always.
# The name "random" is a properly-seeded stand-in for the random module.
CODE_PROLOG = """\
from __future__ import division

import random as random_module
import sys
random = random_module.Random(%r)
random.Random = random_module.Random
del random_module
sys.modules['random'] = random
"""

ASSUMED_IMPORTS=[
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

lazymod_py = open(lazymod_py_file).read()

LAZY_IMPORTS = [lazymod_py]
for name, modname in ASSUMED_IMPORTS:
    LAZY_IMPORTS.append("{} = LazyModule('{}')\n".format(name, modname))

LAZY_IMPORTS = "".join(LAZY_IMPORTS)


@statsd.timed('capa.safe_exec.time')
def safe_exec(code, globals_dict, random_seed=None, python_path=None, cache=None):
    """
    Exec python code safely.

    `cache` is an object with .get(key) and .set(key, value) methods.

    """
    # Check the cache for a previous result.
    if cache:
        canonical_globals = sorted(json_safe(globals_dict).iteritems())
        md5er = hashlib.md5()
        md5er.update(repr(code))
        md5er.update(repr(canonical_globals))
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

    # Run the code!  Results are side effects in globals_dict.
    try:
        codejail_safe_exec(
            code_prolog + LAZY_IMPORTS + code, globals_dict,
            python_path=python_path,
        )
    except SafeExecException as e:
        emsg = e.message
    else:
        emsg = None

    # Put the result back in the cache.  This is complicated by the fact that
    # the globals dict might not be entirely serializable.
    if cache:
        cleaned_results = json_safe(globals_dict)
        cache.set(key, (emsg, cleaned_results))

    # If an exception happened, raise it now.
    if emsg:
        raise e
