from calc import evaluator, UndefinedVariable

#-----------------------------------------------------------------------------
#
# Utility functions used in CAPA responsetypes


def compare_with_tolerance(v1, v2, tol):
    ''' Compare v1 to v2 with maximum tolerance tol
    tol is relative if it ends in %; otherwise, it is absolute

     - v1    :  student result (number)
     - v2    :  instructor result (number)
     - tol   :  tolerance (string or number)

    '''
    relative = tol.endswith('%')
    if relative:
        tolerance_rel = evaluator(dict(), dict(), tol[:-1]) * 0.01
        tolerance = tolerance_rel * max(abs(v1), abs(v2))
    else:
        tolerance = evaluator(dict(), dict(), tol)
    return abs(v1 - v2) <= tolerance


def contextualize_text(text, context):  # private
    ''' Takes a string with variables. E.g. $a+$b.
    Does a substitution of those variables from the context '''
    if not text: return text
    for key in sorted(context, lambda x, y: cmp(len(y), len(x))):
        text = text.replace('$' + key, str(context[key]))
    return text
