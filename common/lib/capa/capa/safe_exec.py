"""Capa's specialized use of codejail.safe_exec."""

import codejail.safe_exec

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

def safe_exec(code, globals_dict, random_seed=None, python_path=None):
    """Exec python code safely.

    """
    code_prolog = CODE_PROLOG % random_seed
    codejail.safe_exec.safe_exec(
        code_prolog + code, globals_dict,
        python_path=python_path,
        assumed_imports=[
            "numpy",
            "math",
            "scipy",
            "calc",
            "eia",
            ("chemcalc", "chem.chemcalc"),
            ("chemtools", "chem.chemtools"),
            ("miller", "chem.miller"),
            ("draganddrop", "verifiers.draganddrop"),
        ],
    )
