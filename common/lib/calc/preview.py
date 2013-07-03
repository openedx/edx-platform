"""
Previewing capability for FormulaResponse and NumericalResponse
"""

def latex_preview(string, variables=None, functions=None, case_sensitive=False):
    """
    Render the math string into latex for previewing.

    -`variables` is an interable of valid user-defined variables
    -`functions` is one of functions
    -`case_sensitive` tells how to match variables in the string to these user-
     defined sets.

    TODO actually have a preview here
    """
    return u"{len}\\text{{ chars in: \"{str}\"}}".format(
        str=string,
        len=len(string)
    )
