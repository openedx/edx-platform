"""
Parser and evaluator for FormulaResponse and NumericalResponse

Uses pyparsing to parse. Main function as of now is evaluator().
"""

import math
import numbers
import operator

import numpy
from pyparsing import (
    CaselessLiteral,
    Combine,
    Forward,
    Group,
    Literal,
    MatchFirst,
    Optional,
    ParseResults,
    Suppress,
    Word,
    ZeroOrMore,
    alphanums,
    alphas,
    nums,
    stringEnd
)

import functions

# Functions available by default
# We use scimath variants which give complex results when needed. For example:
#   np.sqrt(-4+0j) = 2j
#   np.sqrt(-4) = nan, but
#   np.lib.scimath.sqrt(-4) = 2j
DEFAULT_FUNCTIONS = {
    'sin': numpy.sin,
    'cos': numpy.cos,
    'tan': numpy.tan,
    'sec': functions.sec,
    'csc': functions.csc,
    'cot': functions.cot,
    'sqrt': numpy.lib.scimath.sqrt,
    'log10': numpy.lib.scimath.log10,
    'log2': numpy.lib.scimath.log2,
    'ln': numpy.lib.scimath.log,
    'exp': numpy.exp,
    'arccos': numpy.lib.scimath.arccos,
    'arcsin': numpy.lib.scimath.arcsin,
    'arctan': numpy.arctan,
    'arcsec': functions.arcsec,
    'arccsc': functions.arccsc,
    'arccot': functions.arccot,
    'abs': numpy.abs,
    'fact': math.factorial,
    'factorial': math.factorial,
    'sinh': numpy.sinh,
    'cosh': numpy.cosh,
    'tanh': numpy.tanh,
    'sech': functions.sech,
    'csch': functions.csch,
    'coth': functions.coth,
    'arcsinh': numpy.arcsinh,
    'arccosh': numpy.arccosh,
    'arctanh': numpy.lib.scimath.arctanh,
    'arcsech': functions.arcsech,
    'arccsch': functions.arccsch,
    'arccoth': functions.arccoth
}

DEFAULT_VARIABLES = {
    'i': numpy.complex(0, 1),
    'j': numpy.complex(0, 1),
    'e': numpy.e,
    'pi': numpy.pi,
}

SUFFIXES = {
    '%': 0.01,
}


class UndefinedVariable(Exception):
    """
    Indicate when a student inputs a variable which was not expected.
    """
    pass


class UnmatchedParenthesis(Exception):
    """
    Indicate when a student inputs a formula with mismatched parentheses.
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
    # Find first number in the list
    result = next(k for k in parse_result if isinstance(k, numbers.Number))
    return result


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
        if token == '+':
            current_op = operator.add
        elif token == '-':
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
        if token == '*':
            current_op = operator.mul
        elif token == '/':
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
    check_parens(math_expr)
    math_interpreter = ParseAugmenter(math_expr, case_sensitive)
    math_interpreter.parse_algebra()

    # Get our variables together.
    all_variables, all_functions = add_defaults(variables, functions, case_sensitive)

    # ...and check them
    math_interpreter.check_variables(all_variables, all_functions)

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

    return math_interpreter.reduce_tree(evaluate_actions)


def check_parens(formula):
    """
    Check that any open parentheses are closed

    Otherwise, raise an UnmatchedParenthesis exception
    """
    count = 0
    delta = {
        '(': +1,
        ')': -1
    }
    for index, char in enumerate(formula):
        if char in delta:
            count += delta[char]
            if count < 0:
                msg = "Invalid Input: A closing parenthesis was found after segment " + \
                      "{}, but there is no matching opening parenthesis before it."
                raise UnmatchedParenthesis(msg.format(formula[0:index]))
    if count > 0:
        msg = "Invalid Input: Parentheses are unmatched. " + \
              "{} parentheses were opened but never closed."
        raise UnmatchedParenthesis(msg.format(count))


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

        def vpa(tokens):
            """
            When a variable is recognized, store it in `variables_used`.
            """
            varname = tokens[0][0]
            self.variables_used.add(varname)

        def fpa(tokens):
            """
            When a function is recognized, store it in `functions_used`.
            """
            varname = tokens[0][0]
            self.functions_used.add(varname)

        self.variable_parse_action = vpa
        self.function_parse_action = fpa

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
            Optional(plus_minus) +
            inner_number +
            Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part) +
            Optional(number_suffix)
        )
        number = number("number")

        # Predefine recursive variables.
        expr = Forward()

        # Handle variables passed in. They must start with a letter
        # and may contain numbers and underscores afterward.
        inner_varname = Combine(Word(alphas, alphanums + "_") + ZeroOrMore("'"))
        # Alternative variable name in tensor format
        # Tensor name must start with a letter, continue with alphanums
        # Indices may be alphanumeric
        # e.g., U_{ijk}^{123}
        upper_indices = Literal("^{") + Word(alphanums) + Literal("}")
        lower_indices = Literal("_{") + Word(alphanums) + Literal("}")
        tensor_lower = Combine(Word(alphas, alphanums) + lower_indices + ZeroOrMore("'"))
        tensor_mixed = Combine(Word(alphas, alphanums) + Optional(lower_indices) + upper_indices + ZeroOrMore("'"))
        # Test for mixed tensor first, then lower tensor alone, then generic variable name
        varname = Group(tensor_mixed | tensor_lower | inner_varname)("variable")
        varname.setParseAction(self.variable_parse_action)

        # Same thing for functions.
        function = Group(inner_varname + Suppress("(") + expr + Suppress(")"))("function")
        function.setParseAction(self.function_parse_action)

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
        expr << sum_term  # pylint: disable=pointless-statement
        self.tree = (expr + stringEnd).parseString(self.math_expr)[0]

    def reduce_tree(self, handle_actions, terminal_converter=None):
        """
        Call `handle_actions` recursively on `self.tree` and return result.

        `handle_actions` is a dictionary of node names (e.g. 'product', 'sum',
        etc&) to functions. These functions are of the following form:
         -input: a list of processed child nodes. If it includes any terminal
          nodes in the list, they will be given as their processed forms also.
         -output: whatever to be passed to the level higher, and what to
          return for the final node.
        `terminal_converter` is a function that takes in a token and returns a
        processed form. The default of `None` just leaves them as strings.
        """
        def handle_node(node):
            """
            Return the result representing the node, using recursion.

            Call the appropriate `handle_action` for this node. As its inputs,
            feed it the output of `handle_node` for each child node.
            """
            if not isinstance(node, ParseResults):
                # Then treat it as a terminal node.
                if terminal_converter is None:
                    return node
                else:
                    return terminal_converter(node)

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
        if self.case_sensitive:
            casify = lambda x: x
        else:
            casify = lambda x: x.lower()  # Lowercase for case insens.

        bad_vars = set(var for var in self.variables_used
                       if casify(var) not in valid_variables)

        if bad_vars:
            varnames = ", ".join(sorted(bad_vars))
            message = "Invalid Input: {} not permitted in answer as a variable".format(varnames)

            # Check to see if there is a different case version of the variables
            caselist = set()
            if self.case_sensitive:
                for var2 in bad_vars:
                    for var1 in valid_variables:
                        if var2.lower() == var1.lower():
                            caselist.add(var1)
                if len(caselist) > 0:
                    betternames = ', '.join(sorted(caselist))
                    message += " (did you mean " + betternames + "?)"

            raise UndefinedVariable(message)

        bad_funcs = set(func for func in self.functions_used
                        if casify(func) not in valid_functions)
        if bad_funcs:
            funcnames = ', '.join(sorted(bad_funcs))
            message = "Invalid Input: {} not permitted in answer as a function".format(funcnames)

            # Check to see if there is a corresponding variable name
            if any(casify(func) in valid_variables for func in bad_funcs):
                message += " (did you forget to use * for multiplication?)"

            # Check to see if there is a different case version of the function
            caselist = set()
            if self.case_sensitive:
                for func2 in bad_funcs:
                    for func1 in valid_functions:
                        if func2.lower() == func1.lower():
                            caselist.add(func1)
                if len(caselist) > 0:
                    betternames = ', '.join(sorted(caselist))
                    message += " (did you mean " + betternames + "?)"

            raise UndefinedVariable(message)
