"""Capa's specialized use of codejail.safe_exec."""

import codejail.safe_exec
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

# We'll need the code from lazymod.py for use in jailpy, so read it now.
lazymod_py_file = lazymod.__file__
if lazymod_py_file.endswith("c"):
    lazymod_py_file = lazymod_py_file[:-1]

lazymod_py = open(lazymod_py_file).read()

LAZY_IMPORTS = [lazymod_py]
for name, modname in ASSUMED_IMPORTS:
    LAZY_IMPORTS.append("{} = LazyModule('{}')\n".format(name, modname))

LAZY_IMPORTS = "".join(LAZY_IMPORTS)


def safe_exec(code, globals_dict, random_seed=None, python_path=None):
    """Exec python code safely.

    """
    code_prolog = CODE_PROLOG % random_seed

    codejail.safe_exec.safe_exec(
        code_prolog + LAZY_IMPORTS + code, globals_dict,
        python_path=python_path,
    )
