import copy
import logging
import math
import operator
import re

import numpy
import numbers
import scipy.constants

from pyparsing import Word, alphas, nums, oneOf, Literal
from pyparsing import ZeroOrMore, OneOrMore, StringStart
from pyparsing import StringEnd, Optional, Forward
from pyparsing import CaselessLiteral, Group, StringEnd
from pyparsing import NoMatch, stringEnd, alphanums

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
                     'abs': numpy.abs
                     }
default_variables = {'j': numpy.complex(0, 1),
                     'e': numpy.e,
                     'pi': numpy.pi,
                     'k': scipy.constants.k,
                     'c': scipy.constants.c,
                     'T': 298.15,
                     'q': scipy.constants.e
                     }

log = logging.getLogger("mitx.courseware.capa")


class UndefinedVariable(Exception):
    def raiseself(self):
        ''' Helper so we can use inside of a lambda '''
        raise self


general_whitespace = re.compile('[^\w]+')


def check_variables(string, variables):
    '''Confirm the only variables in string are defined.

    Pyparsing uses a left-to-right parser, which makes the more
    elegant approach pretty hopeless.

    achar = reduce(lambda a,b:a|b ,map(Literal,alphas)) # Any alphabetic character
    undefined_variable = achar + Word(alphanums)
    undefined_variable.setParseAction(lambda x:UndefinedVariable("".join(x)).raiseself())
    varnames = varnames | undefined_variable
    '''
    possible_variables = re.split(general_whitespace, string)  # List of all alnums in string
    bad_variables = list()
    for v in possible_variables:
        if len(v) == 0:
            continue
        if v[0] <= '9' and '0' <= 'v':  # Skip things that begin with numbers
            continue
        if v not in variables:
            bad_variables.append(v)
    if len(bad_variables) > 0:
        raise UndefinedVariable(' '.join(bad_variables))


def evaluator(variables, functions, string, cs=False):
    '''
    Evaluate an expression. Variables are passed as a dictionary
    from string to value. Unary functions are passed as a dictionary
    from string to function. Variables must be floats.
    cs: Case sensitive

    TODO: Fix it so we can pass integers and complex numbers in variables dict
    '''
    # log.debug("variables: {0}".format(variables))
    # log.debug("functions: {0}".format(functions))
    # log.debug("string: {0}".format(string))

    def lower_dict(d):
        return dict([(k.lower(), d[k]) for k in d])

    all_variables = copy.copy(default_variables)
    all_functions = copy.copy(default_functions)

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
              'T': 1e12,#  'P':1e15,'E':1e18,'Z':1e21,'Y':1e24,
              'c': 1e-2, 'm': 1e-3, 'u': 1e-6,
              'n': 1e-9, 'p': 1e-12}#  ,'f':1e-15,'a':1e-18,'z':1e-21,'y':1e-24}

    def super_float(text):
        ''' Like float, but with si extensions. 1k goes to 1000'''
        if text[-1] in suffixes:
            return float(text[:-1]) * suffixes[text[-1]]
        else:
            return float(text)

    def number_parse_action(x):  # [ '7' ] ->  [ 7 ]
        return [super_float("".join(x))]

    def exp_parse_action(x):  # [ 2 ^ 3 ^ 2 ] -> 512
        x = [e for e in x if isinstance(e, numbers.Number)]  # Ignore ^
        x.reverse()
        x = reduce(lambda a, b: b ** a, x)
        return x

    def parallel(x):  # Parallel resistors [ 1 2 ] => 2/3
        if len(x) == 1:
            return x[0]
        if 0 in x:
            return float('nan')
        x = [1. / e for e in x if isinstance(e, numbers.Number)]  # Ignore ||
        return 1. / sum(x)

    def sum_parse_action(x):  # [ 1 + 2 - 3 ] -> 0
        total = 0.0
        op = ops['+']
        for e in x:
            if e in set('+-'):
                op = ops[e]
            else:
                total = op(total, e)
        return total

    def prod_parse_action(x):  # [ 1 * 2 / 3 ] => 0.66
        prod = 1.0
        op = ops['*']
        for e in x:
            if e in set('*/'):
                op = ops[e]
            else:
                prod = op(prod, e)
        return prod

    def func_parse_action(x):
        return [all_functions[x[0]](x[1])]

    # SI suffixes and percent
    number_suffix = reduce(lambda a, b: a | b, map(Literal, suffixes.keys()), NoMatch())
    (dot, minus, plus, times, div, lpar, rpar, exp) = map(Literal, ".-+*/()^")

    number_part = Word(nums)

    # 0.33 or 7 or .34
    inner_number = (number_part + Optional("." + number_part)) | ("." + number_part)

    # 0.33k or -17
    number = (Optional(minus | plus) + inner_number
              + Optional(CaselessLiteral("E") + Optional("-") + number_part)
              + Optional(number_suffix))
    number = number.setParseAction(number_parse_action)  # Convert to number

    # Predefine recursive variables
    expr = Forward()
    factor = Forward()

    def sreduce(f, l):
        ''' Same as reduce, but handle len 1 and len 0 lists sensibly '''
        if len(l) == 0:
            return NoMatch()
        if len(l) == 1:
            return l[0]
        return reduce(f, l)

    # Handle variables passed in. E.g. if we have {'R':0.5}, we make the substitution.
    # Special case for no variables because of how we understand PyParsing is put together
    if len(all_variables) > 0:
        # We sort the list so that var names (like "e2") match before
        # mathematical constants (like "e"). This is kind of a hack.
        all_variables_keys = sorted(all_variables.keys(), key=len, reverse=True)
        varnames = sreduce(lambda x, y: x | y, map(lambda x: CasedLiteral(x), all_variables_keys))
        varnames.setParseAction(lambda x: map(lambda y: all_variables[y], x))
    else:
        varnames = NoMatch()

    # Same thing for functions.
    if len(all_functions) > 0:
        funcnames = sreduce(lambda x, y: x | y,
                            map(lambda x: CasedLiteral(x), all_functions.keys()))
        function = funcnames + lpar.suppress() + expr + rpar.suppress()
        function.setParseAction(func_parse_action)
    else:
        function = NoMatch()

    atom = number | function | varnames | lpar + expr + rpar
    factor << (atom + ZeroOrMore(exp + atom)).setParseAction(exp_parse_action)  # 7^6
    paritem = factor + ZeroOrMore(Literal('||') + factor)  # 5k || 4k
    paritem = paritem.setParseAction(parallel)
    term = paritem + ZeroOrMore((times | div) + paritem)  # 7 * 5 / 4 - 3
    term = term.setParseAction(prod_parse_action)
    expr << Optional((plus | minus)) + term + ZeroOrMore((plus | minus) + term)  # -5 + 4 - 3
    expr = expr.setParseAction(sum_parse_action)
    return (expr + stringEnd).parseString(string)[0]

if __name__ == '__main__':
    variables = {'R1': 2.0, 'R3': 4.0}
    functions = {'sin': numpy.sin, 'cos': numpy.cos}
    print "X", evaluator(variables, functions, "10000||sin(7+5)-6k")
    print "X", evaluator(variables, functions, "13")
    print evaluator({'R1': 2.0, 'R3': 4.0}, {}, "13")

    print evaluator({'e1': 1, 'e2': 1.0, 'R3': 7, 'V0': 5, 'R5': 15, 'I1': 1, 'R4': 6}, {}, "e2")

    print evaluator({'a': 2.2997471478310274, 'k': 9, 'm': 8, 'x': 0.66009498411213041}, {}, "5")
    print evaluator({}, {}, "-1")
    print evaluator({}, {}, "-(7+5)")
    print evaluator({}, {}, "-0.33")
    print evaluator({}, {}, "-.33")
    print evaluator({}, {}, "5+1*j")
    print evaluator({}, {}, "j||1")
    print evaluator({}, {}, "e^(j*pi)")
    print evaluator({}, {}, "5+7 QWSEKO")
