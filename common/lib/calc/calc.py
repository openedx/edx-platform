"""
Parser and evaluator for FormulaResponse and NumericalResponse

Uses pyparsing to parse. Main function as of now is evaluator().
"""

import copy
import logging
import math
import operator
import re

import numpy
import numbers
import scipy.constants

from pyparsing import Word, nums, Literal
from pyparsing import ZeroOrMore, MatchFirst
from pyparsing import Optional, Forward
from pyparsing import CaselessLiteral
from pyparsing import NoMatch, stringEnd, Suppress, Combine

default_functions = {'sin': numpy.sin,
                     'cos': numpy.cos,
                     'tan': numpy.tan,
                     'sqrt': numpy.sqrt,
                     'log10': numpy.log10,
                     'log2': numpy.log2,
                     'ln': numpy.log,
                     'arccos': numpy.arccos,
                     'arcsin': numpy.arcsin,
                     'arctan': numpy.arctan,
                     'abs': numpy.abs,
                     'fact': math.factorial,
                     'factorial': math.factorial
                     }
default_variables = {'j': numpy.complex(0, 1),
                     'e': numpy.e,
                     'pi': numpy.pi,
                     'k': scipy.constants.k,
                     'c': scipy.constants.c,
                     'T': 298.15,
                     'q': scipy.constants.e
                     }


ops = {"^": operator.pow,
       "*": operator.mul,
       "/": operator.truediv,
       "+": operator.add,
       "-": operator.sub,
}
# We eliminated extreme ones, since they're rarely used, and potentially
# confusing. They may also conflict with variables if we ever allow e.g.
# 5R instead of 5*R
suffixes = {'%': 0.01, 'k': 1e3, 'M': 1e6, 'G': 1e9,
            'T': 1e12,  # 'P':1e15,'E':1e18,'Z':1e21,'Y':1e24,
            'c': 1e-2, 'm': 1e-3, 'u': 1e-6,
            'n': 1e-9, 'p': 1e-12}  # ,'f':1e-15,'a':1e-18,'z':1e-21,'y':1e-24}

log = logging.getLogger("mitx.courseware.capa")


class UndefinedVariable(Exception):
    """
    Used to indicate the student input of a variable, which was unused by the
    instructor.
    """
    pass
    # unused for now
    # def raiseself(self):
    #     ''' Helper so we can use inside of a lambda '''
    #     raise self


general_whitespace = re.compile('[^\\w]+')


def check_variables(string, variables):
    """
    Confirm the only variables in string are defined.

    Pyparsing uses a left-to-right parser, which makes the more
    elegant approach pretty hopeless.

    achar = reduce(lambda a,b:a|b ,map(Literal,alphas)) # Any alphabetic character
    undefined_variable = achar + Word(alphanums)
    undefined_variable.setParseAction(lambda x:UndefinedVariable("".join(x)).raiseself())
    varnames = varnames | undefined_variable
    """
    possible_variables = re.split(general_whitespace, string)  # List of all alnums in string
    bad_variables = list()
    for v in possible_variables:
        if len(v) == 0:
            continue
        if v[0] <= '9' and '0' <= v:  # Skip things that begin with numbers
            continue
        if v not in variables:
            bad_variables.append(v)
    if len(bad_variables) > 0:
        raise UndefinedVariable(' '.join(bad_variables))

def lower_dict(d):
    """
    takes each key in the dict and makes it lowercase, still mapping to the
    same value.

    keep in mind that it is possible (but not useful?) to define different
    variables that have the same lowercase representation. It would be hard to
    tell which is used in the final dict and which isn't.
    """
    return dict([(k.lower(), d[k]) for k in d])

# The following few functions define parse actions, which are run on lists of
# results from each parse component. They convert the strings and (previously
# calculated) numbers into the number that component represents.

def super_float(text):
    """
    Like float, but with si extensions. 1k goes to 1000
    """
    if text[-1] in suffixes:
        return float(text[:-1]) * suffixes[text[-1]]
    else:
        return float(text)

def number_parse_action(x):
    """
    Create a float out of its string parts

    e.g. [ '7', '.', '13' ] ->  [ 7.13 ]
    Calls super_float above
    """
    return [super_float("".join(x))]

def exp_parse_action(x):
    """
    Take a list of numbers and exponentiate them, right to left

    e.g. [ 3, 2, 3 ] (which is 3^2^3 = 3^(2^3)) -> 6561
    """
    x = [e for e in x if isinstance(e, numbers.Number)]  # Ignore ^
    x.reverse()
    x = reduce(lambda a, b: b ** a, x)
    return x

def parallel(x):
    """
    Compute numbers according to the parallel resistors operator

    BTW it is commutative. Its formula is given by
      out = 1 / (1/in1 + 1/in2 + ...)
    e.g. [ 1, 2 ] => 2/3

    Return NaN if there is a zero among the inputs
    """
    x = list(x)
    if len(x) == 1:
        return x[0]
    if 0 in x:
        return float('nan')
    x = [1. / e for e in x if isinstance(e, numbers.Number)]  # Ignore ||
    return 1. / sum(x)

def sum_parse_action(x):  # [ 1 + 2 - 3 ] -> 0
    """
    Add the inputs

    [ 1, '+', 2, '-', 3 ] -> 0

    Allow a leading + or -
    """
    total = 0.0
    op = ops['+']
    for e in x:
        if e in set('+-'):
            op = ops[e]
        else:
            total = op(total, e)
    return total

def prod_parse_action(x):  # [ 1 * 2 / 3 ] => 0.66
    """
    Multiply the inputs

    [ 1, '*', 2, '/', 3 ] => 0.66
    """
    prod = 1.0
    op = ops['*']
    for e in x:
        if e in set('*/'):
            op = ops[e]
        else:
            prod = op(prod, e)
    return prod

def evaluator(variables, functions, string, cs=False):
    """
    Evaluate an expression. Variables are passed as a dictionary
    from string to value. Unary functions are passed as a dictionary
    from string to function. Variables must be floats.
    cs: Case sensitive

    """
    # log.debug("variables: {0}".format(variables))
    # log.debug("functions: {0}".format(functions))
    # log.debug("string: {0}".format(string))

    all_variables = copy.copy(default_variables)
    all_functions = copy.copy(default_functions)

    def func_parse_action(x):
        return [all_functions[x[0]](x[1])]

    if not cs:
        all_variables = lower_dict(all_variables)
        all_functions = lower_dict(all_functions)

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
    number_suffix = MatchFirst([Literal(k) for k in suffixes.keys()])
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
    number = number.setParseAction(number_parse_action)  # Convert to number

    # Predefine recursive variables
    expr = Forward()
    factor = Forward()

    # Handle variables passed in. E.g. if we have {'R':0.5}, we make the substitution.
    # Special case for no variables because of how we understand PyParsing is put together
    if len(all_variables) > 0:
        # We sort the list so that var names (like "e2") match before
        # mathematical constants (like "e"). This is kind of a hack.
        all_variables_keys = sorted(all_variables.keys(), key=len, reverse=True)
        literal_all_vars = [CasedLiteral(k) for k in all_variables_keys]
        varnames = MatchFirst(literal_all_vars)
        varnames.setParseAction(lambda x: [all_variables[k] for k in x])
    else:
        # all_variables includes DEFAULT_VARIABLES, which isn't empty
        # this is unreachable. Get rid of it?
        varnames = NoMatch()

    # Same thing for functions.
    if len(all_functions) > 0:
        funcnames = MatchFirst([CasedLiteral(k) for k in all_functions.keys()])
        function = funcnames + Suppress("(") + expr + Suppress(")")
        function.setParseAction(func_parse_action)
    else:
        # see note above (this is unreachable)
        function = NoMatch()

    atom = number | function | varnames | Suppress("(") + expr + Suppress(")")

    # Do the following in the correct order to preserve order of operation
    factor << (atom + ZeroOrMore("^" + atom)).setParseAction(exp_parse_action)  # 7^6
    paritem = factor + ZeroOrMore(Literal('||') + factor)  # 5k || 4k
    paritem = paritem.setParseAction(parallel)
    term = paritem + ZeroOrMore(times_div + paritem)  # 7 * 5 / 4 - 3
    term = term.setParseAction(prod_parse_action)
    expr << Optional(plus_minus) + term + ZeroOrMore(plus_minus + term)  # -5 + 4 - 3
    expr = expr.setParseAction(sum_parse_action)
    return (expr + stringEnd).parseString(string)[0]
