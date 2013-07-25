"""
Parser and evaluator for FormulaResponse and NumericalResponse

Uses pyparsing to parse. Main function as of now is evaluator().
"""

import math
import operator
import numbers
import numpy
import scipy.constants
import calcfunctions

# Have numpy ignore errors on functions outside its domain.
# See http://docs.scipy.org/doc/numpy/reference/generated/numpy.seterr.html
# TODO worry about thread safety/changing a global setting
numpy.seterr(all='ignore')  # Also: 'ignore', 'warn' (default), 'raise'

from pyparsing import (
    Word, Literal, CaselessLiteral, ZeroOrMore, MatchFirst, Optional, Forward,
    Group, ParseResults, stringEnd, Suppress, Combine, alphas, nums, alphanums
)

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
#   P (1e15), E (1e18), Z (1e21), Y (1e24),
#   f (1e-15), a (1e-18), z (1e-21), y (1e-24)
# since they're rarely used, and potentially confusing.
# They may also conflict with variables if we ever allow e.g.
#   5R instead of 5*R
SUFFIXES = {
    '%': 0.01, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
    'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12
}


class UndefinedVariable(Exception):
    """
    Indicate when a student inputs a variable which was not expected.
    """
    pass


def lower_dict(input_dict):
    """
    Convert all keys in a dictionary to lowercase; keep their original values.

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
    Like float, but with SI extensions. 1k goes to 1000.
    """
    if text[-1] in SUFFIXES:
        return float(text[:-1]) * SUFFIXES[text[-1]]
    else:
        return float(text)


def eval_number(parse_result):
    """
    Create a float out of its string parts.

    e.g. [ '7.13', 'e', '3' ] ->  7130
    Calls super_float above.
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
    Take a list of numbers and exponentiate them, right to left.

    e.g. [ 2, 3, 2 ] -> 2^3^2 = 2^(3^2) -> 512
    (not to be interpreted (2^3)^2 = 64)
    """
    # `reduce` will go from left to right; reverse the list.
    parse_result = reversed(
        [k for k in parse_result
         if isinstance(k, numbers.Number)]  # Ignore the '^' marks.
    )
    # Having reversed it, raise `b` to the power of `a`.
    power = reduce(lambda a, b: b ** a, parse_result)
    return power


def eval_parallel(parse_result):
    """
    Compute numbers according to the parallel resistors operator.

    BTW it is commutative. Its formula is given by
      out = 1 / (1/in1 + 1/in2 + ...)
    e.g. [ 1, 2 ] -> 2/3

    Return NaN if there is a zero among the inputs.
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
    Add the inputs, keeping in mind their sign.

    [ 1, '+', 2, '-', 3 ] -> 0

    Allow a leading + or -.
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
    Multiply the inputs.

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


def add_defaults(variables, functions, case_sensitive):
    """
    Create dictionaries with both the default and user-defined variables.
    """
    all_variables = dict(DEFAULT_VARIABLES)
    all_functions = dict(DEFAULT_FUNCTIONS)
    all_variables.update(variables)
    all_functions.update(functions)

    if not case_sensitive:
        all_variables = lower_dict(all_variables)
        all_functions = lower_dict(all_functions)

    return (all_variables, all_functions)


def evaluator(variables, functions, math_expr, case_sensitive=False):
    """
    Evaluate an expression; that is, take a string of math and return a float.

    -Variables are passed as a dictionary from string to value. They must be
     python numbers.
    -Unary functions are passed as a dictionary from string to function.
    """
    # No need to go further.
    if math_expr.strip() == "":
        return float('nan')

    # Parse the tree.
    thing = ParseAugmenter(math_expr, case_sensitive)
    thing.parse_algebra()

    # Get our variables together.
    all_variables, all_functions = add_defaults(variables, functions, case_sensitive)

    # ...and check them
    thing.check_variables(all_variables, all_functions)

    # Create a recursion to evaluate the tree.
    if case_sensitive:
        casify = lambda x: x
    else:
        casify = lambda x: x.lower()  # Lowercase for case insens.

    evaluate_actions = {
        'number': eval_number,
        'variable': lambda x: all_variables[casify(x[0])],
        'function': lambda x: all_functions[casify(x[0])](x[1]),
        'atom': eval_atom,
        'power': eval_power,
        'parallel': eval_parallel,
        'product': eval_product,
        'sum': eval_sum
    }

    return thing.handle_tree(evaluate_actions)


class ParseAugmenter(object):
    """
    Holds the data for a particular parse.

    Retains the `math_expr` and `case_sensitive` so they needn't be passed
    around method to method.
    Eventually holds the parse tree and sets of variables as well.
    """
    def __init__(self, math_expr, case_sensitive=False):
        """
        Create the ParseAugmenter for a given math expression string.

        Do the parsing later, when called like `OBJ.parse_algebra()`.
        """
        self.case_sensitive = case_sensitive
        self.math_expr = math_expr
        self.tree = None
        self.variables_used = set()
        self.functions_used = set()

    def make_variable_parse_action(self):
        """
        Create a wrapper to store variables as they are parsed.
        """
        def vpa(tokens):
            """
            When a variable is recognized, store its correct form in `variables_used`.
            """
            if self.case_sensitive:
                varname = tokens[0][0]
            else:
                varname = tokens[0][0].lower()
            self.variables_used.add(varname)
        return vpa

    def make_function_parse_action(self):
        """
        Create a wrapper to store functions as they are parsed.
        """
        def fpa(tokens):
            """
            When a function is recognized, store its correct form in `variables_used`.
            """
            if self.case_sensitive:
                varname = tokens[0][0]
            else:
                varname = tokens[0][0].lower()
            self.functions_used.add(varname)
        return fpa

    def parse_algebra(self):
        """
        Parse an algebraic expression into a tree.

        Store a `pyparsing.ParseResult` in `self.tree` with proper groupings to
        reflect parenthesis and order of operations. Leave all operators in the
        tree and do not parse any strings of numbers into their float versions.

        Adding the groups and result names makes the `repr()` of the result
        really gross. For debugging, use something like
          print OBJ.tree.asXML()
        """
        # 0.33 or 7 or .34 or 16.
        number_part = Word(nums)
        inner_number = (number_part + Optional("." + Optional(number_part))) | ("." + number_part)
        # pyparsing allows spaces between tokens--`Combine` prevents that.
        inner_number = Combine(inner_number)

        # SI suffixes and percent.
        number_suffix = MatchFirst(Literal(k) for k in SUFFIXES.keys())

        # 0.33k or 17
        plus_minus = Literal('+') | Literal('-')
        number = Group(
            inner_number +
            Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part) +
            Optional(number_suffix)
        )
        number = number("number")

        # Predefine recursive variables.
        expr = Forward()

        # Handle variables passed in. They must start with letters/underscores
        # and may contain numbers afterward.
        inner_varname = Word(alphas + "_", alphanums + "_")
        varname = Group(inner_varname)("variable")
        varname.setParseAction(self.make_variable_parse_action())

        # Same thing for functions.
        function = Group(inner_varname + Suppress("(") + expr + Suppress(")"))("function")
        function.setParseAction(self.make_function_parse_action())

        atom = number | function | varname | "(" + expr + ")"
        atom = Group(atom)("atom")

        # Do the following in the correct order to preserve order of operation.
        pow_term = atom + ZeroOrMore("^" + atom)
        pow_term = Group(pow_term)("power")

        par_term = pow_term + ZeroOrMore('||' + pow_term)  # 5k || 4k
        par_term = Group(par_term)("parallel")

        prod_term = par_term + ZeroOrMore((Literal('*') | Literal('/')) + par_term)  # 7 * 5 / 4
        prod_term = Group(prod_term)("product")

        sum_term = Optional(plus_minus) + prod_term + ZeroOrMore(plus_minus + prod_term)  # -5 + 4 - 3
        sum_term = Group(sum_term)("sum")

        # Finish the recursion.
        expr << sum_term  # pylint: disable=W0104
        self.tree = (expr + stringEnd).parseString(self.math_expr)[0]

    def handle_tree(self, handle_actions, handle_terminal=None):
        """
        Call `handle_actions` recursively on `self.tree` and return result.

        `handle_actions` is a dictionary of node names (e.g. 'product', 'sum',
        etc&) to functions. These functions are of the following form:
         -input: a list of processed child nodes. If it includes any terminal
          nodes in the list, they will be given as their processed forms also.
         -output: whatever to be passed to the level higher, and what to
          return for the final node.
        `handle_terminal` is a function that takes in a token and returns a
        processed form. Leaving it as `None` just leaves them as strings.
        """
        def handle_node(node):
            """
            Return the result representing the node, using recursion.

            Call the appropriate `handle_action` for this node. As its inputs,
            feed it the output of `handle_node` for each child node.
            """
            if not isinstance(node, ParseResults):
                # Then it is a terminal node.
                if handle_terminal is None:
                    return node
                else:
                    return handle_terminal(node)

            node_name = node.getName()
            if node_name not in handle_actions:  # pragma: no cover
                raise Exception(u"Unknown branch name '{}'".format(node_name))

            action = handle_actions[node_name]
            handled_kids = [handle_node(k) for k in node]
            return action(handled_kids)

        # Find the value of the entire tree.
        return handle_node(self.tree)

    def check_variables(self, valid_variables, valid_functions):
        """
        Confirm that all the variables used in the tree are valid/defined.

        Otherwise, raise an UndefinedVariable containing all bad variables.
        """
        # Test that `used_vars` is a subset of `all_vars`; also do functions.
        if not (self.variables_used.issubset(valid_variables) and
                self.functions_used.issubset(valid_functions)):
            bad_vars = self.variables_used.difference(valid_variables)
            bad_vars &= self.functions_used.difference(valid_functions)
            raise UndefinedVariable(' '.join(bad_vars))
