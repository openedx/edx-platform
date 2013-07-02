"""
Parser and evaluator for FormulaResponse and NumericalResponse

Uses pyparsing to parse. Main function as of now is evaluator().
"""

import copy
import math
import operator
import numbers
import numpy
import scipy.constants
import calcfunctions

# Have numpy ignore errors on functions outside its domain
# See http://docs.scipy.org/doc/numpy/reference/generated/numpy.seterr.html
numpy.seterr(all='ignore')  # Also: 'ignore', 'warn' (default), 'raise'

from pyparsing import (Word, nums, Literal,
                       ZeroOrMore, MatchFirst,
                       Optional, Forward,
                       CaselessLiteral, Group, ParseResults,
                       stringEnd, Suppress, Combine, alphas, alphanums)

DEFAULT_FUNCTIONS = {
    'sin': numpy.sin,
    'cos': numpy.cos,
    'tan': numpy.tan,
    'sec': calcfunctions.sec,
    'csc': calcfunctions.csc,
    'cot': calcfunctions.cot,
    'sqrt': numpy.sqrt,
    'log10': numpy.log10,
    'log2': numpy.log2,
    'ln': numpy.log,
    'exp': numpy.exp,
    'arccos': numpy.arccos,
    'arcsin': numpy.arcsin,
    'arctan': numpy.arctan,
    'arcsec': calcfunctions.arcsec,
    'arccsc': calcfunctions.arccsc,
    'arccot': calcfunctions.arccot,
    'abs': numpy.abs,
    'fact': math.factorial,
    'factorial': math.factorial,
    'sinh': numpy.sinh,
    'cosh': numpy.cosh,
    'tanh': numpy.tanh,
    'sech': calcfunctions.sech,
    'csch': calcfunctions.csch,
    'coth': calcfunctions.coth,
    'arcsinh': numpy.arcsinh,
    'arccosh': numpy.arccosh,
    'arctanh': numpy.arctanh,
    'arcsech': calcfunctions.arcsech,
    'arccsch': calcfunctions.arccsch,
    'arccoth': calcfunctions.arccoth
}
DEFAULT_VARIABLES = {
    'i': numpy.complex(0, 1),
    'j': numpy.complex(0, 1),
    'e': numpy.e,
    'pi': numpy.pi,
    'k': scipy.constants.k,
    'c': scipy.constants.c,
    'T': 298.15,
    'q': scipy.constants.e
}

# We eliminated the following extreme suffixes:
# P (1e15), E (1e18), Z (1e21), Y (1e24),
# f (1e-15), a (1e-18), z (1e-21), y (1e-24)
# since they're rarely used, and potentially
# confusing. They may also conflict with variables if we ever allow e.g.
# 5R instead of 5*R
SUFFIXES = {
    '%': 0.01, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
    'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12
}


class UndefinedVariable(Exception):
    """
    Indicate the student input of a variable which was unused by the instructor
    """
    pass


def find_vars_funcs(tree):
    """
    Aggregate a list of the variables and functions used in `tree`

    variables and functions are nodes identified by `branch.getName()`.
    As the tips of the branches are strings, avoid any possible AttributeErrors
    by looking just at the nodes which are `ParseResults`.
    """
    variables = set()
    functions = set()

    def check_branch(branch):
        """
        Add variables and functions to their respective sets, using recursion.
        """
        if isinstance(branch, ParseResults):
            if branch.getName() == "variable":
                variables.add(branch[0])
            elif branch.getName() == "function":
                functions.add(branch[0])
            for sub_branch in branch:
                check_branch(sub_branch)
    check_branch(tree)
    return (variables, functions)


def check_variables(tree, all_variables, all_functions, case_sensitive):
    """
    Confirm the only variables in the tree are defined.

    Otherwise, raise an UndefinedVariable containing all bad variables.
    """
    used_vars, used_funcs = find_vars_funcs(tree)
    if not case_sensitive:
        used_vars = set((k.lower() for k in used_vars))
        used_funcs = set((k.lower() for k in used_funcs))

    # Test that `used_vars` is a subset of `all_vars` and the same for functions
    if not (used_vars <= all_variables and
            used_funcs <= all_functions):
        bad_vars = (used_vars - all_variables) & (used_funcs - all_functions)
        raise UndefinedVariable(' '.join(bad_vars))


def lower_dict(input_dict):
    """
    Convert all keys in a dictionary to lowercase; keep their original values

    Keep in mind that it is possible (but not useful?) to define different
    variables that have the same lowercase representation. It would be hard to
    tell which is used in the final dict and which isn't.
    """
    return {k.lower(): v for k, v in input_dict.iteritems()}


# The following few functions define evaluation actions, which are run on lists
# of results from each parse component. They convert the strings and (previously
# calculated) numbers into the number that component represents.

def super_float(text):
    """
    Like float, but with si extensions. 1k goes to 1000
    """
    if text[-1] in SUFFIXES:
        return float(text[:-1]) * SUFFIXES[text[-1]]
    else:
        return float(text)


def eval_number(parse_result):
    """
    Create a float out of its string parts

    e.g. [ '7', '.', '13' ] ->  7.13
    Calls super_float above
    """
    return super_float("".join(parse_result))


def eval_atom(parse_result):
    """
    Return the value wrapped by the atom.

    In the case of parenthesis, ignore them.
    """
    float_children = [k for k in parse_result if isinstance(k, numbers.Number)]
    return float_children[0]


def eval_power(parse_result):
    """
    Take a list of numbers and exponentiate them, right to left

    e.g. [ 3, 2, 3 ] (which is 3^2^3 = 3^(2^3)) -> 6561
    """
    parse_result = reversed(
        [k for k in parse_result
         if isinstance(k, numbers.Number)]
    )
    # The result of an exponentiation is called a power
    power = reduce(lambda a, b: b ** a, parse_result)
    return power


def eval_parallel(parse_result):
    """
    Compute numbers according to the parallel resistors operator

    BTW it is commutative. Its formula is given by
      out = 1 / (1/in1 + 1/in2 + ...)
    e.g. [ 1, 2 ] -> 2/3

    Return NaN if there is a zero among the inputs
    """
    if len(parse_result) == 1:
        return parse_result[0]
    if 0 in parse_result:
        return float('nan')
    reciprocals = [1. / e for e in parse_result
                   if isinstance(e, numbers.Number)]
    return 1. / sum(reciprocals)


def eval_sum(parse_result):
    """
    Add the inputs

    [ 1, '+', 2, '-', 3 ] -> 0

    Allow a leading + or -
    """
    total = 0.0
    current_op = operator.add
    for token in parse_result:
        if token is '+':
            current_op = operator.add
        elif token is '-':
            current_op = operator.sub
        else:
            total = current_op(total, token)
    return total


def eval_product(parse_result):
    """
    Multiply the inputs

    [ 1, '*', 2, '/', 3 ] -> 0.66
    """
    prod = 1.0
    current_op = operator.mul
    for token in parse_result:
        if token is '*':
            current_op = operator.mul
        elif token is '/':
            current_op = operator.truediv
        else:
            prod = current_op(prod, token)
    return prod


def parse_algebra(string):
    """
    Parse an algebraic expression into a tree.

    Return a `pyparsing.ParseResult` with proper groupings to reflect
    parenthesis and order of operations. Leave all operators in the tree and do
    not parse any strings of numbers into their float versions.

    Adding the groups and result names makes the string representation of the
    result really gross. For debugging, use something like
      print parse_algebra("1+1/2").asXML()
    """
    # 0.33 or 7 or .34 or 16.
    number_part = Word(nums)
    inner_number = (number_part + Optional("." + Optional(number_part))) | ("." + number_part)
    # By default pyparsing allows spaces between tokens--`Combine` prevents that
    inner_number = Combine(inner_number)

    # SI suffixes and percent
    number_suffix = MatchFirst((Literal(k) for k in SUFFIXES.keys()))

    # 0.33k or 17
    plus_minus = Literal('+') | Literal('-')
    number = Group(
        inner_number +
        Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part) +
        Optional(number_suffix)
    )
    number = number("number")

    # Predefine recursive variables
    expr = Forward()

    # Handle variables passed in. They must start with letters/underscores and
    # may contain numbers afterward
    inner_varname = Word(alphas + "_", alphanums + "_")
    varname = Group(inner_varname)("variable")

    # Same thing for functions.
    function = Group(inner_varname + Suppress("(") + expr + Suppress(")"))("function")

    atom = number | function | varname | "(" + expr + ")"
    atom = Group(atom)("atom")

    # Do the following in the correct order to preserve order of operation
    pow_term = atom + ZeroOrMore("^" + atom)
    pow_term = Group(pow_term)("power")

    par_term = pow_term + ZeroOrMore('||' + pow_term)  # 5k || 4k
    par_term = Group(par_term)("parallel")

    prod_term = par_term + ZeroOrMore((Literal('*') | Literal('/')) + par_term)  # 7 * 5 / 4
    prod_term = Group(prod_term)("product")

    sum_term = Optional(plus_minus) + prod_term + ZeroOrMore(plus_minus + prod_term)  # -5 + 4 - 3
    sum_term = Group(sum_term)("sum")

    # Finish the recursion
    expr << sum_term  # pylint: disable=W0104
    return (expr + stringEnd).parseString(string)[0]


def add_defaults(variables, functions, case_sensitive):
    """
    Create dictionaries with both the default and user-defined variables.
    """
    all_variables = copy.copy(DEFAULT_VARIABLES)
    all_functions = copy.copy(DEFAULT_FUNCTIONS)
    all_variables.update(variables)
    all_functions.update(functions)

    if not case_sensitive:
        all_variables = lower_dict(all_variables)
        all_functions = lower_dict(all_functions)

    return (all_variables, all_functions)


def evaluator(variables, functions, string, cs=False):
    """
    Evaluate an expression; that is, take a string of math and return a float

    -Variables are passed as a dictionary from string to value. They must be
     python numbers
    -Unary functions are passed as a dictionary from string to function.
    -cs: Case sensitive
    """
    # No need to go further
    if string.strip() == "":
        return float('nan')

    # Parse tree
    tree = parse_algebra(string)

    # Get our variables together
    all_variables, all_functions = add_defaults(variables, functions, cs)

    # ...and check them
    check_variables(tree, set(all_variables), set(all_functions), cs)

    # Create a recursion to evaluate the tree
    casify = lambda x: x if cs else x.lower()  # Lowercase for case insens.
    evaluate_action = {
        'number': eval_number,
        'variable': lambda x: all_variables[casify(x[0])],
        'function': lambda x: all_functions[casify(x[0])](x[1]),
        'atom': eval_atom,
        'power': eval_power,
        'parallel': eval_parallel,
        'product': eval_product,
        'sum': eval_sum
    }

    def evaluate_branch(branch):
        """
        Return the float representing the branch, using recursion.

        Call the appropriate `evaluate_action` for this branch. As its inputs,
        feed it the output of `evaluate_branch` for each child branch.
        """
        if not isinstance(branch, ParseResults):
            return branch

        action = evaluate_action[branch.getName()]
        evaluated_kids = [evaluate_branch(k) for k in branch]
        return action(evaluated_kids)

    # Find the value of the entire tree
    return evaluate_branch(tree)
