#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# File:   symmath_check.py
# Date:   02-May-12 (creation)
#
# Symbolic mathematical expression checker for edX.  Uses sympy to check for expression equality.
#
# Takes in math expressions given as Presentation MathML (from ASCIIMathML), converts to Content MathML using SnuggleTeX

import traceback
from .formula import *
import logging

log = logging.getLogger(__name__)

#-----------------------------------------------------------------------------
# check function interface
#
# This is one of the main entry points to call.


def symmath_check_simple(expect, ans, adict={}, symtab=None, extra_options=None):
    """
    Check a symbolic mathematical expression using sympy.
    The input is an ascii string (not MathML) converted to math using sympy.sympify.
    """

    options = {'__MATRIX__': False, '__ABC__': False, '__LOWER__': False}
    if extra_options:
        options.update(extra_options)
    for op in options:				# find options in expect string
        if op in expect:
            expect = expect.replace(op, '')
            options[op] = True
    expect = expect.replace('__OR__', '__or__')	 # backwards compatibility

    if options['__LOWER__']:
        expect = expect.lower()
        ans = ans.lower()

    try:
        ret = check(expect, ans,
                    matrix=options['__MATRIX__'],
                    abcsym=options['__ABC__'],
                    symtab=symtab,
                    )
    except Exception, err:
        return {'ok': False,
                'msg': 'Error %s<br/>Failed in evaluating check(%s,%s)' % (err, expect, ans)
                }
    return ret

#-----------------------------------------------------------------------------
# pretty generic checking function


def check(expect, given, numerical=False, matrix=False, normphase=False, abcsym=False, do_qubit=True, symtab=None, dosimplify=False):
    """
    Returns dict with

      'ok': True if check is good, False otherwise
      'msg': response message (in HTML)

    "expect" may have multiple possible acceptable answers, separated by "__OR__"

    """

    if "__or__" in expect:			# if multiple acceptable answers
        eset = expect.split('__or__')		# then see if any match
        for eone in eset:
            ret = check(eone, given, numerical, matrix, normphase, abcsym, do_qubit, symtab, dosimplify)
            if ret['ok']:
                return ret
        return ret

    flags = {}
    if "__autonorm__" in expect:
        flags['autonorm'] = True
        expect = expect.replace('__autonorm__', '')
        matrix = True

    threshold = 1.0e-3
    if "__threshold__" in expect:
        (expect, st) = expect.split('__threshold__')
        threshold = float(st)
        numerical = True

    if str(given) == '' and not str(expect) == '':
        return {'ok': False, 'msg': ''}

    try:
        xgiven = my_sympify(given, normphase, matrix, do_qubit=do_qubit, abcsym=abcsym, symtab=symtab)
    except Exception, err:
        return {'ok': False, 'msg': 'Error %s<br/> in evaluating your expression "%s"' % (err, given)}

    try:
        xexpect = my_sympify(expect, normphase, matrix, do_qubit=do_qubit, abcsym=abcsym, symtab=symtab)
    except Exception, err:
        return {'ok': False, 'msg': 'Error %s<br/> in evaluating OUR expression "%s"' % (err, expect)}

    if 'autonorm' in flags:	 # normalize trace of matrices
        try:
            xgiven /= xgiven.trace()
        except Exception, err:
            return {'ok': False, 'msg': 'Error %s<br/> in normalizing trace of your expression %s' % (err, to_latex(xgiven))}
        try:
            xexpect /= xexpect.trace()
        except Exception, err:
            return {'ok': False, 'msg': 'Error %s<br/> in normalizing trace of OUR expression %s' % (err, to_latex(xexpect))}

    msg = 'Your expression was evaluated as ' + to_latex(xgiven)
    # msg += '<br/>Expected ' + to_latex(xexpect)

    # msg += "<br/>flags=%s" % flags

    if matrix and numerical:
        xgiven = my_evalf(xgiven, chop=True)
        dm = my_evalf(sympy.Matrix(xexpect) - sympy.Matrix(xgiven), chop=True)
        msg += " = " + to_latex(xgiven)
        if abs(dm.vec().norm().evalf()) < threshold:
            return {'ok': True, 'msg': msg}
        else:
            pass
            #msg += "dm = " + to_latex(dm) + " diff = " + str(abs(dm.vec().norm().evalf()))
            #msg += "expect = " + to_latex(xexpect)
    elif dosimplify:
        if sympy.simplify(xexpect) == sympy.simplify(xgiven):
            return {'ok': True, 'msg': msg}
    elif numerical:
        if abs((xexpect - xgiven).evalf(chop=True)) < threshold:
            return {'ok': True, 'msg': msg}
    elif xexpect == xgiven:
        return {'ok': True, 'msg': msg}

    #msg += "<p/>expect='%s', given='%s'" % (expect,given)	# debugging
    # msg += "<p/> dot test " + to_latex(dot(sympy.Symbol('x'),sympy.Symbol('y')))
    return {'ok': False, 'msg': msg}

#-----------------------------------------------------------------------------
# helper function to convert all <p> to <span class='inline-error'>


def make_error_message(msg):
    # msg = msg.replace('<p>','<p><span class="inline-error">').replace('</p>','</span></p>')
    msg = '<div class="capa_alert">%s</div>' % msg
    return msg


def is_within_tolerance(expected, actual, tolerance):
    if expected == 0:
        return abs(actual) < tolerance
    else:
        return abs(abs(actual - expected) / expected) < tolerance

#-----------------------------------------------------------------------------
# Check function interface, which takes pmathml input
#
# This is one of the main entry points to call.


def symmath_check(expect, ans, dynamath=None, options=None, debug=None, xml=None):
    """
    Check a symbolic mathematical expression using sympy.
    The input may be presentation MathML.  Uses formula.

    This is the default Symbolic Response checking function

    Desc of args:
    expect is a sympy string representing the correct answer. It is interpreted
     using my_sympify (from formula.py), which reads strings as sympy input
     (e.g. 'integrate(x^2, (x,1,2))' would be valid, and evaluate to give 1.5)

    ans is student-typed answer. It is expected to be ascii math, but the code
     below would support a sympy string.

    dynamath is the PMathML string converted by MathJax. It is used if
     evaluation with ans is not sufficient.

    options is a string with these possible substrings, set as an xml property
     of the problem:
     -matrix - make a sympy matrix, rather than a list of lists, if possible
     -qubit - passed to my_sympify
     -imaginary - used in formla, presumably to signal to use i as sqrt(-1)?
     -numerical - force numerical comparison.
    """

    msg = ''
    # msg += '<p/>abname=%s' % abname
    # msg += '<p/>adict=%s' % (repr(adict).replace('<','&lt;'))

    threshold = 1.0e-3   # for numerical comparison (also with matrices)
    DEBUG = debug

    if xml is not None:
        DEBUG = xml.get('debug', False)  	# override debug flag using attribute in symbolicmath xml
        if DEBUG in ['0', 'False']:
            DEBUG = False

    # options
    if options is None:
        options = ''
    do_matrix = 'matrix' in options
    do_qubit = 'qubit' in options
    do_numerical = 'numerical' in options

    # parse expected answer
    try:
        fexpect = my_sympify(str(expect), matrix=do_matrix, do_qubit=do_qubit)
    except Exception, err:
        msg += '<p>Error %s in parsing OUR expected answer "%s"</p>' % (err, expect)
        return {'ok': False, 'msg': make_error_message(msg)}

    ###### Sympy input #######
    # if expected answer is a number, try parsing provided answer as a number also
    try:
        fans = my_sympify(str(ans), matrix=do_matrix, do_qubit=do_qubit)
    except Exception, err:
        fans = None

    # do a numerical comparison if both expected and answer are numbers
    if hasattr(fexpect, 'is_number') and fexpect.is_number \
       and hasattr(fans, 'is_number') and fans.is_number:
        if is_within_tolerance(fexpect, fans, threshold):
            return {'ok': True, 'msg': msg}
        else:
            msg += '<p>You entered: %s</p>' % to_latex(fans)
            return {'ok': False, 'msg': msg}

    if do_numerical:		# numerical answer expected - force numerical comparison
        if is_within_tolerance(fexpect, fans, threshold):
            return {'ok': True, 'msg': msg}
        else:
            msg += '<p>You entered: %s (note that a numerical answer is expected)</p>' % to_latex(fans)
            return {'ok': False, 'msg': msg}

    if fexpect == fans:
        msg += '<p>You entered: %s</p>' % to_latex(fans)
        return {'ok': True, 'msg': msg}

    ###### PMathML input ######
    # convert mathml answer to formula
    try:
        mmlans = dynamath[0] if dynamath else None
    except Exception, err:
        mmlans = None
    if not mmlans:
        return {'ok': False, 'msg': '[symmath_check] failed to get MathML for input; dynamath=%s' % dynamath}

    f = formula(mmlans, options=options)

    # get sympy representation of the formula
    # if DEBUG: msg += '<p/> mmlans=%s' % repr(mmlans).replace('<','&lt;')
    try:
        fsym = f.sympy
        msg += '<p>You entered: %s</p>' % to_latex(f.sympy)
    except Exception, err:
        log.exception("Error evaluating expression '%s' as a valid equation", ans)
        msg += "<p>Error in evaluating your expression '%s' as a valid equation</p>" % (ans)
        if "Illegal math" in str(err):
            msg += "<p>Illegal math expression</p>"
        if DEBUG:
            msg += 'Error: %s' % str(err).replace('<', '&lt;')
            msg += '<hr>'
            msg += '<p><font color="blue">DEBUG messages:</p>'
            msg += "<p><pre>%s</pre></p>" % traceback.format_exc()
            msg += '<p>cmathml=<pre>%s</pre></p>' % f.cmathml.replace('<', '&lt;')
            msg += '<p>pmathml=<pre>%s</pre></p>' % mmlans.replace('<', '&lt;')
            msg += '<hr>'
        return {'ok': False, 'msg': make_error_message(msg)}

    # do numerical comparison with expected
    if hasattr(fexpect, 'is_number') and fexpect.is_number:
        if hasattr(fsym, 'is_number') and fsym.is_number:
            if abs(abs(fsym - fexpect) / fexpect) < threshold:
                return {'ok': True, 'msg': msg}
            return {'ok': False, 'msg': msg}
        msg += "<p>Expecting a numerical answer!</p>"
        msg += "<p>given = %s</p>" % repr(ans)
        msg += "<p>fsym = %s</p>" % repr(fsym)
        # msg += "<p>cmathml = <pre>%s</pre></p>" % str(f.cmathml).replace('<','&lt;')
        return {'ok': False, 'msg': make_error_message(msg)}

    # Here is a good spot for adding calls to X.simplify() or X.expand(),
    #  allowing equivalence over binomial expansion or trig identities

    # exactly the same?
    if fexpect == fsym:
        return {'ok': True, 'msg': msg}

    if isinstance(fexpect, list):
        try:
            xgiven = my_evalf(fsym, chop=True)
            dm = my_evalf(sympy.Matrix(fexpect) - sympy.Matrix(xgiven), chop=True)
            if abs(dm.vec().norm().evalf()) < threshold:
                return {'ok': True, 'msg': msg}
        except sympy.ShapeError:
            msg += "<p>Error - your input vector or matrix has the wrong dimensions"
            return {'ok': False, 'msg': make_error_message(msg)}
        except Exception, err:
            msg += "<p>Error %s in comparing expected (a list) and your answer</p>" % str(err).replace('<', '&lt;')
            if DEBUG:
                msg += "<p/><pre>%s</pre>" % traceback.format_exc()
            return {'ok': False, 'msg': make_error_message(msg)}

    #diff = (fexpect-fsym).simplify()
    #fsym = fsym.simplify()
    #fexpect = fexpect.simplify()
    try:
        diff = (fexpect - fsym)
    except Exception, err:
        diff = None

    if DEBUG:
        msg += '<hr>'
        msg += '<p><font color="blue">DEBUG messages:</p>'
        msg += "<p>Got: %s</p>" % repr(fsym)
        # msg += "<p/>Got: %s" % str([type(x) for x in fsym.atoms()]).replace('<','&lt;')
        msg += "<p>Expecting: %s</p>" % repr(fexpect).replace('**', '^').replace('hat(I)', 'hat(i)')
        # msg += "<p/>Expecting: %s" % str([type(x) for x in fexpect.atoms()]).replace('<','&lt;')
        if diff:
            msg += "<p>Difference: %s</p>" % to_latex(diff)
        msg += '<hr>'

    # Used to return more keys: 'ex': fexpect, 'got': fsym
    return {'ok': False, 'msg': msg}
