"""Capa's specialized use of codejail.safe_exec."""

import codejail.safe_exec

CODE_PROLOG = """\
import random as random_module
random = random_module.Random(%r)
random.Random = random_module.Random
"""

def safe_exec(code, globals_dict, locals_dict, random_seed=None):
    code_prolog = CODE_PROLOG % random_seed
    codejail.safe_exec.safe_exec(
        code_prolog + code, globals_dict, locals_dict, future_division=True,
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
