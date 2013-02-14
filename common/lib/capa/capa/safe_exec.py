"""Capa's specialized use of codejail.safe_exec."""

import codejail.safe_exec

def safe_exec(code, globals_dict, locals_dict):
    codejail.safe_exec.safe_exec(
        code, globals_dict, locals_dict, future_division=True,
        assumed_imports=[
            "random",
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
