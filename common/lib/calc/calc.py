"""
Parser and evaluator for FormulaResponse and NumericalResponse

Uses pyparsing to parse. Main function as of now is evaluator().
"""

import copy
import math
import operator
import re

import numpy
import scipy.constants
import calcfunctions

# have numpy raise errors on functions outside its domain
# See http://docs.scipy.org/doc/numpy/reference/generated/numpy.seterr.html
numpy.seterr(all='ignore')  # Also: 'ignore', 'warn' (default), 'raise'

from pyparsing import (Word, nums, Literal,
                       ZeroOrMore, MatchFirst,
                       Optional, Forward,
                       CaselessLiteral,
                       stringEnd, Suppress, Combine)

DEFAULT_FUNCTIONS = {'sin': numpy.sin,
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
DEFAULT_VARIABLES = {'i': numpy.complex(0, 1),
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
SUFFIXES = {'%': 0.01, 'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
            'c': 1e-2, 'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12}


class UndefinedVariable(Exception):
    """
    Used to indicate the student input of a variable, which was unused by the
    instructor.
    """
    pass


def check_variables(string, variables):
    """
    Confirm the only variables in string are defined.

    Otherwise, raise an UndefinedVariable containing all bad variables.

    Pyparsing uses a left-to-right parser, which makes a more
    elegant approach pretty hopeless.
    """
    general_whitespace = re.compile('[^\\w]+')
    # List of all alnums in string
    possible_variables = re.split(general_whitespace, string)
    bad_variables = []
    for var in possible_variables:
        if len(var) == 0:
            continue
        if var[0].isdigit():  # Skip things that begin with numbers
            continue
        if var not in variables:
            bad_variables.append(var)
    if len(bad_variables) > 0:
        raise UndefinedVariable(' '.join(bad_variables))


def lower_dict(input_dict):
    """
    takes each key in the dict and makes it lowercase, still mapping to the
    same value.

    keep in mind that it is possible (but not useful?) to define different
    variables that have the same lowercase representation. It would be hard to
    tell which is used in the final dict and which isn't.
    """
    return {k.lower(): v for k, v in input_dict.iteritems()}


# The following few functions define parse actions, which are run on lists of
# results from each parse component. They convert the strings and (previously
# calculated) numbers into the number that component represents.

def super_float(text):
    """
    Like float, but with si extensions. 1k goes to 1000
    """
    if text[-1] in SUFFIXES:
        return float(text[:-1]) * SUFFIXES[text[-1]]
    else:
        return float(text)


def number_parse_action(parse_result):
    """
    Create a float out of its string parts

    e.g. [ '7', '.', '13' ] ->  [ 7.13 ]
    Calls super_float above
    """
    return super_float("".join(parse_result))


def exp_parse_action(parse_result):
    """
    Take a list of numbers and exponentiate them, right to left

    e.g. [ 3, 2, 3 ] (which is 3^2^3 = 3^(2^3)) -> 6561
    """
    # pyparsing.ParseResults doesn't play well with reverse()
    parse_result = reversed(parse_result)
    # the result of an exponentiation is called a power
    power = reduce(lambda a, b: b ** a, parse_result)
    return power


def parallel(parse_result):
    """
    Compute numbers according to the parallel resistors operator

    BTW it is commutative. Its formula is given by
      out = 1 / (1/in1 + 1/in2 + ...)
    e.g. [ 1, 2 ] => 2/3

    Return NaN if there is a zero among the inputs
    """
    # convert from pyparsing.ParseResults, which doesn't support '0 in parse_result'
    parse_result = parse_result.asList()
    if len(parse_result) == 1:
        return parse_result[0]
    if 0 in parse_result:
        return float('nan')
    reciprocals = [1. / e for e in parse_result]
    return 1. / sum(reciprocals)


def sum_parse_action(parse_result):
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


def prod_parse_action(parse_result):
    """
    Multiply the inputs

    [ 1, '*', 2, '/', 3 ] => 0.66
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


def evaluator(variables, functions, string, cs=False):
    """
    Evaluate an expression. Variables are passed as a dictionary
    from string to value. Unary functions are passed as a dictionary
    from string to function. Variables must be floats.
    cs: Case sensitive

    """

    all_variables = copy.copy(DEFAULT_VARIABLES)
    all_functions = copy.copy(DEFAULT_FUNCTIONS)
    all_variables.update(variables)
    all_functions.update(functions)

    if not cs:
        string_cs = string.lower()
        all_functions = lower_dict(all_functions)
        all_variables = lower_dict(all_variables)
        CasedLiteral = CaselessLiteral
    else:
        string_cs = string
        CasedLiteral = Literal

    check_variables(string_cs, set(all_variables.keys() + all_functions.keys()))

    if string.strip() == "":
        return float('nan')

    # SI suffixes and percent
    number_suffix = MatchFirst([Literal(k) for k in SUFFIXES.keys()])
    plus_minus = Literal('+') | Literal('-')
    times_div = Literal('*') | Literal('/')

    number_part = Word(nums)

    # 0.33 or 7 or .34 or 16.
    inner_number = (number_part + Optional("." + Optional(number_part))) | ("." + number_part)
    # by default pyparsing allows spaces between tokens--Combine prevents that
    inner_number = Combine(inner_number)

    # 0.33k or -17
    number = (inner_number
              + Optional(CaselessLiteral("E") + Optional(plus_minus) + number_part)
              + Optional(number_suffix))
    number.setParseAction(number_parse_action)  # Convert to number

    # Predefine recursive variables
    expr = Forward()

    # Handle variables passed in.
    #  E.g. if we have {'R':0.5}, we make the substitution.
    # We sort the list so that var names (like "e2") match before
    # mathematical constants (like "e"). This is kind of a hack.
    all_variables_keys = sorted(all_variables.keys(), key=len, reverse=True)
    varnames = MatchFirst([CasedLiteral(k) for k in all_variables_keys])
    varnames.setParseAction(
        lambda x: [all_variables[k] for k in x]
    )

    # if all_variables were empty, then pyparsing wants
    # varnames = NoMatch()
    # this is not the case, as all_variables contains the defaults

    # Same thing for functions.
    all_functions_keys = sorted(all_functions.keys(), key=len, reverse=True)
    funcnames = MatchFirst([CasedLiteral(k) for k in all_functions_keys])
    function = funcnames + Suppress("(") + expr + Suppress(")")
    function.setParseAction(
        lambda x: [all_functions[x[0]](x[1])]
    )

    atom = number | function | varnames | Suppress("(") + expr + Suppress(")")

    # Do the following in the correct order to preserve order of operation
    pow_term = atom + ZeroOrMore(Suppress("^") + atom)
    pow_term.setParseAction(exp_parse_action)  # 7^6
    par_term = pow_term + ZeroOrMore(Suppress('||') + pow_term)  # 5k || 4k
    par_term.setParseAction(parallel)
    prod_term = par_term + ZeroOrMore(times_div + par_term)  # 7 * 5 / 4 - 3
    prod_term.setParseAction(prod_parse_action)
    sum_term = Optional(plus_minus) + prod_term + ZeroOrMore(plus_minus + prod_term)  # -5 + 4 - 3
    sum_term.setParseAction(sum_parse_action)
    expr << sum_term  # finish the recursion
    return (expr + stringEnd).parseString(string)[0]
