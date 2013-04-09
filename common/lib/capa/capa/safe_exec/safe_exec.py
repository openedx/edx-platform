"""Capa's specialized use of codejail.safe_exec."""

from codejail.safe_exec import safe_exec as codejail_safe_exec
from codejail.safe_exec import json_safe
from . import lazymod

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


def safe_exec(code, globals_dict, random_seed=None, python_path=None, cache=None):
    """Exec python code safely.

    `cache` is an object with .get(key) and .set(key, value) methods.

    """
    # Check the cache for a previous result.
    if cache:
        canonical_globals = sorted(json_safe(globals_dict).iteritems())
        key = "safe_exec %r %s %r" % (random_seed, code, canonical_globals)
        cached = cache.get(key)
        if cached is not None:
            globals_dict.update(cached)
            return

    # Create the complete code we'll run.
    code_prolog = CODE_PROLOG % random_seed

    # Run the code!  Results are side effects in globals_dict.
    codejail_safe_exec(
        code_prolog + LAZY_IMPORTS + code, globals_dict,
        python_path=python_path,
    )

    # Put the result back in the cache.  This is complicated by the fact that
    # the globals dict might not be entirely serializable.
    if cache:
        cleaned_results = json_safe(globals_dict)
        cache.set(key, cleaned_results)
