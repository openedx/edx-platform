#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Flexible python representation of a symbolic mathematical formula.
Acceptes Presentation MathML, Content MathML (and could also do OpenMath).
Provides sympy representation.
"""
#
# File:   formula.py
# Date:   04-May-12 (creation)
# Author: I. Chuang <ichuang@mit.edu>
#


import logging
import operator
import os
import re
import string
import unicodedata
#import subprocess
from copy import deepcopy
from functools import reduce
from xml.sax.saxutils import unescape

import six
import sympy
from lxml import etree
from sympy import latex, sympify
from sympy.physics.quantum.qubit import Qubit
from sympy.physics.quantum.state import Ket
from sympy.printing.latex import LatexPrinter
from sympy.printing.str import StrPrinter

from openedx.core.djangolib.markup import HTML

log = logging.getLogger(__name__)

log.warning("Dark code. Needs review before enabling in prod.")

os.environ['PYTHONIOENCODING'] = 'utf-8'

#-----------------------------------------------------------------------------


class dot(sympy.operations.LatticeOp):	 # pylint: disable=invalid-name, no-member
    """my dot product"""
    zero = sympy.Symbol('dotzero')
    identity = sympy.Symbol('dotidentity')


def _print_dot(_self, expr):
    """Print statement used for LatexPrinter"""
    return r'{((%s) \cdot (%s))}' % (expr.args[0], expr.args[1])

LatexPrinter._print_dot = _print_dot  # pylint: disable=protected-access

#-----------------------------------------------------------------------------
# unit vectors (for 8.02)


def _print_hat(_self, expr):
    """Print statement used for LatexPrinter"""
    return '\\hat{%s}' % str(expr.args[0]).lower()

LatexPrinter._print_hat = _print_hat  # pylint: disable=protected-access
StrPrinter._print_hat = _print_hat  # pylint: disable=protected-access

#-----------------------------------------------------------------------------
# helper routines


def to_latex(expr):
    """
    Convert expression to latex mathjax format
    """
    if expr is None:
        return ''
    expr_s = latex(expr)
    expr_s = expr_s.replace(r'\XI', 'XI')	 # workaround for strange greek

    # substitute back into latex form for scripts
    # literally something of the form
    # 'scriptN' becomes '\\mathcal{N}'
    # note: can't use something akin to the _print_hat method above because we
    # sometimes get 'script(N)__B' or more complicated terms
    expr_s = re.sub(
        r'script([a-zA-Z0-9]+)',
        r'\\mathcal{\\1}',
        expr_s
    )

    #return '<math>%s{}{}</math>' % (xs[1:-1])
    if expr_s[0] == '$':
        return HTML('[mathjax]{expression}[/mathjax]<br>').format(expression=expr_s[1:-1])	 # for sympy v6
    return HTML('[mathjax]{expression}[/mathjax]<br>').format(expression=expr_s)		# for sympy v7


def my_evalf(expr, chop=False):
    """
    Enhanced sympy evalf to handle lists of expressions
    and catch eval failures without dropping out.
    """
    if isinstance(expr, list):
        try:
            return [x.evalf(chop=chop) for x in expr]
        except Exception:  # pylint: disable=broad-except
            return expr
    try:
        return expr.evalf(chop=chop)
    except Exception:  # pylint: disable=broad-except
        return expr


def my_sympify(expr, normphase=False, matrix=False, abcsym=False, do_qubit=False, symtab=None):
    """
    Version of sympify to import expression into sympy
    """
    # make all lowercase real?
    if symtab:
        varset = symtab
    else:
        varset = {
            'p': sympy.Symbol('p'),
            'g': sympy.Symbol('g'),
            'e': sympy.E,			# for exp
            'i': sympy.I,			# lowercase i is also sqrt(-1)
            'Q': sympy.Symbol('Q'),	 # otherwise it is a sympy "ask key"
            'I': sympy.Symbol('I'),	 # otherwise it is sqrt(-1)
            'N': sympy.Symbol('N'),	 # or it is some kind of sympy function
            'ZZ': sympy.Symbol('ZZ'),	 # otherwise it is the PythonIntegerRing
            'XI': sympy.Symbol('XI'),	 # otherwise it is the capital \XI
            'hat': sympy.Function('hat'),	 # for unit vectors (8.02)
        }
    if do_qubit:		# turn qubit(...) into Qubit instance
        varset.update({
            'qubit': Qubit,
            'Ket': Ket,
            'dot': dot,
            'bit': sympy.Function('bit'),
        })
    if abcsym:			# consider all lowercase letters as real symbols, in the parsing
        for letter in string.ascii_lowercase:
            if letter in varset:	 # exclude those already done
                continue
            varset.update({letter: sympy.Symbol(letter, real=True)})

    sexpr = sympify(expr, locals=varset)
    if normphase:	 # remove overall phase if sexpr is a list
        if isinstance(sexpr, list):
            if sexpr[0].is_number:
                ophase = sympy.sympify('exp(-I*arg(%s))' % sexpr[0])
                sexpr = [sympy.Mul(x, ophase) for x in sexpr]

    def to_matrix(expr):
        """
        Convert a list, or list of lists to a matrix.
        """
        # if expr is a list of lists, and is rectangular, then return Matrix(expr)
        if not isinstance(expr, list):
            return expr
        for row in expr:
            if not isinstance(row, list):
                return expr
        rdim = len(expr[0])
        for row in expr:
            if not len(row) == rdim:
                return expr
        return sympy.Matrix(expr)

    if matrix:
        sexpr = to_matrix(sexpr)
    return sexpr

#-----------------------------------------------------------------------------
# class for symbolic mathematical formulas


class formula(object):
    """
    Representation of a mathematical formula object.  Accepts mathml math expression
    for constructing, and can produce sympy translation.  The formula may or may not
    include an assignment (=).
    """
    def __init__(self, expr, asciimath='', options=None):
        self.expr = expr.strip()
        self.asciimath = asciimath
        self.the_cmathml = None
        self.the_sympy = None
        self.options = options

    def is_presentation_mathml(self):
        """
        Check if formula is in mathml presentation format.
        """
        return '<mstyle' in self.expr

    def is_mathml(self):
        """
        Check if formula is in mathml format.
        """
        return '<math ' in self.expr

    def fix_greek_in_mathml(self, xml):
        """
        Recursively fix greek letters in passed in xml.
        """
        def gettag(expr):
            return re.sub('{http://[^}]+}', '', expr.tag)

        for k in xml:
            tag = gettag(k)
            if tag == 'mi' or tag == 'ci':
                usym = six.text_type(k.text)
                try:
                    udata = unicodedata.name(usym)
                except Exception:  # pylint: disable=broad-except
                    udata = None
                # print "usym = %s, udata=%s" % (usym,udata)
                if udata:			# eg "GREEK SMALL LETTER BETA"
                    if 'GREEK' in udata:
                        usym = udata.split(' ')[-1]
                        if 'SMALL' in udata:
                            usym = usym.lower()
                        #print "greek: ",usym
                k.text = usym
            self.fix_greek_in_mathml(k)
        return xml

    def preprocess_pmathml(self, xml):
        r"""
        Pre-process presentation MathML from ASCIIMathML to make it more
        acceptable for SnuggleTeX, and also to accomodate some sympy
        conventions (eg hat(i) for \hat{i}).

        This method would be a good spot to look for an integral and convert
        it, if possible...
        """

        if isinstance(xml, (str, six.text_type)):
            xml = etree.fromstring(xml)		# TODO: wrap in try

        xml = self.fix_greek_in_mathml(xml)	 # convert greek utf letters to greek spelled out in ascii

        def gettag(expr):
            return re.sub('{http://[^}]+}', '', expr.tag)

        def fix_pmathml(xml):
            """
            f and g are processed as functions by asciimathml, eg "f-2" turns
            into "<mrow><mi>f</mi><mo>-</mo></mrow><mn>2</mn>" this is
            really terrible for turning into cmathml.  undo this here.
            """
            for k in xml:
                tag = gettag(k)
                if tag == 'mrow':
                    if len(k) == 2:
                        if gettag(k[0]) == 'mi' and k[0].text in ['f', 'g'] and gettag(k[1]) == 'mo':
                            idx = xml.index(k)
                            xml.insert(idx, deepcopy(k[0]))	 # drop the <mrow> container
                            xml.insert(idx + 1, deepcopy(k[1]))
                            xml.remove(k)
                fix_pmathml(k)

        fix_pmathml(xml)

        def fix_hat(xml):
            """
            hat i is turned into <mover><mi>i</mi><mo>^</mo></mover> ; mangle
            this into <mi>hat(f)</mi> hat i also somtimes turned into
            <mover><mrow> <mi>j</mi> </mrow><mo>^</mo></mover>
            """
            for k in xml:
                tag = gettag(k)
                if tag == 'mover':
                    if len(k) == 2:
                        if gettag(k[0]) == 'mi' and gettag(k[1]) == 'mo' and str(k[1].text) == '^':
                            newk = etree.Element('mi')
                            newk.text = 'hat(%s)' % k[0].text
                            xml.replace(k, newk)
                        if gettag(k[0]) == 'mrow' and gettag(k[0][0]) == 'mi' and \
                           gettag(k[1]) == 'mo' and str(k[1].text) == '^':
                            newk = etree.Element('mi')
                            newk.text = 'hat(%s)' % k[0][0].text
                            xml.replace(k, newk)
                fix_hat(k)
        fix_hat(xml)

        def flatten_pmathml(xml):
            """
            Give the text version of certain PMathML elements

            Sometimes MathML will be given with each letter separated (it
            doesn't know if its implicit multiplication or what). From an xml
            node, find the (text only) variable name it represents. So it takes
            <mrow>
              <mi>m</mi>
              <mi>a</mi>
              <mi>x</mi>
            </mrow>
            and returns 'max', for easier use later on.
            """
            tag = gettag(xml)
            if tag == 'mn':
                return xml.text
            elif tag == 'mi':
                return xml.text
            elif tag == 'mrow':
                return ''.join([flatten_pmathml(y) for y in xml])
            raise Exception('[flatten_pmathml] unknown tag %s' % tag)

        def fix_mathvariant(parent):
            """
            Fix certain kinds of math variants

            Literally replace <mstyle mathvariant="script"><mi>N</mi></mstyle>
            with 'scriptN'. There have been problems using script_N or script(N)
            """
            for child in parent:
                if gettag(child) == 'mstyle' and child.get('mathvariant') == 'script':
                    newchild = etree.Element('mi')
                    newchild.text = 'script%s' % flatten_pmathml(child[0])
                    parent.replace(child, newchild)
                fix_mathvariant(child)
        fix_mathvariant(xml)

        # find "tagged" superscripts
        # they have the character \u200b in the superscript
        # replace them with a__b so snuggle doesn't get confused
        def fix_superscripts(xml):
            """ Look for and replace sup elements with 'X__Y' or 'X_Y__Z'

            In the javascript, variables with '__X' in them had an invisible
            character inserted into the sup (to distinguish from powers)
            E.g. normal:
            <msubsup>
              <mi>a</mi>
              <mi>b</mi>
              <mi>c</mi>
            </msubsup>
            to be interpreted '(a_b)^c' (nothing done by this method)

            And modified:
            <msubsup>
              <mi>b</mi>
              <mi>x</mi>
              <mrow>
                <mo>&#x200B;</mo>
                <mi>d</mi>
              </mrow>
            </msubsup>
            to be interpreted 'a_b__c'

            also:
            <msup>
              <mi>x</mi>
              <mrow>
                <mo>&#x200B;</mo>
                <mi>B</mi>
              </mrow>
            </msup>
            to be 'x__B'
            """
            for k in xml:
                tag = gettag(k)

                # match things like the last example--
                # the second item in msub is an mrow with the first
                # character equal to \u200b
                if (
                        tag == 'msup' and
                        len(k) == 2 and gettag(k[1]) == 'mrow' and
                        gettag(k[1][0]) == 'mo' and k[1][0].text == u'\u200b'  # whew
                ):

                    # replace the msup with 'X__Y'
                    k[1].remove(k[1][0])
                    newk = etree.Element('mi')
                    newk.text = '%s__%s' % (flatten_pmathml(k[0]), flatten_pmathml(k[1]))
                    xml.replace(k, newk)

                # match things like the middle example-
                # the third item in msubsup is an mrow with the first
                # character equal to \u200b
                if (
                        tag == 'msubsup' and
                        len(k) == 3 and gettag(k[2]) == 'mrow' and
                        gettag(k[2][0]) == 'mo' and k[2][0].text == u'\u200b'    # whew
                ):

                    # replace the msubsup with 'X_Y__Z'
                    k[2].remove(k[2][0])
                    newk = etree.Element('mi')
                    newk.text = '%s_%s__%s' % (flatten_pmathml(k[0]), flatten_pmathml(k[1]), flatten_pmathml(k[2]))
                    xml.replace(k, newk)

                fix_superscripts(k)
        fix_superscripts(xml)

        def fix_msubsup(parent):
            """
            Snuggle returns an error when it sees an <msubsup> replace such
            elements with an <msup>, except the first element is of
            the form a_b. I.e. map a_b^c => (a_b)^c
            """
            for child in parent:
                # fix msubsup
                if gettag(child) == 'msubsup' and len(child) == 3:
                    newchild = etree.Element('msup')
                    newbase = etree.Element('mi')
                    newbase.text = '%s_%s' % (flatten_pmathml(child[0]), flatten_pmathml(child[1]))
                    newexp = child[2]
                    newchild.append(newbase)
                    newchild.append(newexp)
                    parent.replace(child, newchild)

                fix_msubsup(child)
        fix_msubsup(xml)

        self.xml = xml  # pylint: disable=attribute-defined-outside-init
        return self.xml

    def get_content_mathml(self):
        if self.the_cmathml:
            return self.the_cmathml

        # pre-process the presentation mathml before sending it to snuggletex to convert to content mathml
        try:
            xml = self.preprocess_pmathml(self.expr).decode('utf-8')
        except Exception as err:  # pylint: disable=broad-except
            log.warning('Err %s while preprocessing; expr=%s', err, self.expr)
            return "<html>Error! Cannot process pmathml</html>"
        pmathml = etree.tostring(xml, pretty_print=True)
        self.the_pmathml = pmathml  # pylint: disable=attribute-defined-outside-init
        return self.the_pmathml

    cmathml = property(get_content_mathml, None, None, 'content MathML representation')

    def make_sympy(self, xml=None):
        """
        Return sympy expression for the math formula.
        The math formula is converted to Content MathML then that is parsed.

        This is a recursive function, called on every CMML node. Support for
        more functions can be added by modifying opdict, abould halfway down
        """

        if self.the_sympy:
            return self.the_sympy

        if xml is None:	 # root
            if not self.is_mathml():
                return my_sympify(self.expr)
            if self.is_presentation_mathml():
                cmml = None
                try:
                    cmml = self.cmathml
                    xml = etree.fromstring(str(cmml))
                except Exception as err:
                    if 'conversion from Presentation MathML to Content MathML was not successful' in cmml:
                        msg = "Illegal math expression"
                    else:
                        msg = 'Err %s while converting cmathml to xml; cmml=%s' % (err, cmml)
                    raise Exception(msg)
                xml = self.fix_greek_in_mathml(xml)
                self.the_sympy = self.make_sympy(xml[0])
            else:
                xml = etree.fromstring(self.expr)
                xml = self.fix_greek_in_mathml(xml)
                self.the_sympy = self.make_sympy(xml[0])
            return self.the_sympy

        def gettag(expr):
            return re.sub('{http://[^}]+}', '', expr.tag)

        def op_plus(*args):
            return args[0] if len(args) == 1 else op_plus(*args[:-1]) + args[-1]

        def op_times(*args):
            return reduce(operator.mul, args)

        def op_minus(*args):
            if len(args) == 1:
                return -args[0]
            if not len(args) == 2:
                raise Exception('minus given wrong number of arguments!')
            #return sympy.Add(args[0],-args[1])
            return args[0] - args[1]

        opdict = {
            'plus': op_plus,
            'divide': operator.div,
            'times': op_times,
            'minus': op_minus,
            'root': sympy.sqrt,
            'power': sympy.Pow,
            'sin': sympy.sin,
            'cos': sympy.cos,
            'tan': sympy.tan,
            'cot': sympy.cot,
            'sinh': sympy.sinh,
            'cosh': sympy.cosh,
            'coth': sympy.coth,
            'tanh': sympy.tanh,
            'asin': sympy.asin,
            'acos': sympy.acos,
            'atan': sympy.atan,
            'atan2': sympy.atan2,
            'acot': sympy.acot,
            'asinh': sympy.asinh,
            'acosh': sympy.acosh,
            'atanh': sympy.atanh,
            'acoth': sympy.acoth,
            'exp': sympy.exp,
            'log': sympy.log,
            'ln': sympy.ln,
        }

        def parse_presentation_symbol(xml):
            """
            Parse <msub>, <msup>, <mi>, and <mn>
            """
            tag = gettag(xml)
            if tag == 'mn':
                return xml.text
            elif tag == 'mi':
                return xml.text
            elif tag == 'msub':
                return '_'.join([parse_presentation_symbol(y) for y in xml])
            elif tag == 'msup':
                return '^'.join([parse_presentation_symbol(y) for y in xml])
            raise Exception('[parse_presentation_symbol] unknown tag %s' % tag)

        # parser tree for Content MathML
        tag = gettag(xml)

        # first do compound objects

        if tag == 'apply':		# apply operator
            opstr = gettag(xml[0])
            if opstr in opdict:
                op = opdict[opstr]  # pylint: disable=invalid-name
                args = [self.make_sympy(expr) for expr in xml[1:]]
                try:
                    res = op(*args)
                except Exception as err:
                    self.args = args  # pylint: disable=attribute-defined-outside-init
                    self.op = op      # pylint: disable=attribute-defined-outside-init, invalid-name
                    raise Exception('[formula] error=%s failed to apply %s to args=%s' % (err, opstr, args))
                return res
            else:
                raise Exception('[formula]: unknown operator tag %s' % (opstr))

        elif tag == 'list':		# square bracket list
            if gettag(xml[0]) == 'matrix':
                return self.make_sympy(xml[0])
            else:
                return [self.make_sympy(expr) for expr in xml]

        elif tag == 'matrix':
            return sympy.Matrix([self.make_sympy(expr) for expr in xml])

        elif tag == 'vector':
            return [self.make_sympy(expr) for expr in xml]

        # atoms are below

        elif tag == 'cn':			# number
            return sympy.sympify(xml.text)

        elif tag == 'ci':			# variable (symbol)
            if len(xml) > 0 and (gettag(xml[0]) == 'msub' or gettag(xml[0]) == 'msup'):	 # subscript or superscript
                usym = parse_presentation_symbol(xml[0])
                sym = sympy.Symbol(str(usym))
            else:
                usym = six.text_type(xml.text)
                if 'hat' in usym:
                    sym = my_sympify(usym)
                else:
                    if usym == 'i' and self.options is not None and 'imaginary' in self.options:	 # i = sqrt(-1)
                        sym = sympy.I
                    else:
                        sym = sympy.Symbol(str(usym))
            return sym

        else:				# unknown tag
            raise Exception('[formula] unknown tag %s' % tag)

    sympy = property(make_sympy, None, None, 'sympy representation')
