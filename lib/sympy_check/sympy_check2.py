#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# File:   sympy_check2.py
# Date:   02-May-12
# Author: I. Chuang <ichuang@mit.edu>
#
# Use sympy to check for expression equality
#
# Takes in math expressions given as Presentation MathML (from ASCIIMathML), converts to Content MathML using SnuggleTeX

import os, sys, string, re
import traceback
from formula import *

#-----------------------------------------------------------------------------
# check function interface

def sympy_check(expect,ans,adict={},symtab=None,extra_options=None):

    options = {'__MATRIX__':False,'__ABC__':False,'__LOWER__':False}
    if extra_options: options.update(extra_options)
    for op in options:				# find options in expect string
        if op in expect:
            expect = expect.replace(op,'')
            options[op] = True
    expect = expect.replace('__OR__','__or__')	# backwards compatibility

    if options['__LOWER__']:
        expect = expect.lower()
        ans = ans.lower()

    try:
        ret = check(expect,ans,
                    matrix=options['__MATRIX__'],
                    abcsym=options['__ABC__'],
                    symtab=symtab,
                    )
    except Exception, err:
        return {'ok': False,
                'msg': 'Error %s<br/>Failed in evaluating check(%s,%s)' % (err,expect,ans)
                }
    return ret

#-----------------------------------------------------------------------------
# pretty generic checking function

def check(expect,given,numerical=False,matrix=False,normphase=False,abcsym=False,do_qubit=True,symtab=None,dosimplify=False):
    """
    Returns dict with

      'ok': True if check is good, False otherwise
      'msg': response message (in HTML)

    "expect" may have multiple possible acceptable answers, separated by "__OR__"
      
    """

    if "__or__" in expect:			# if multiple acceptable answers
        eset = expect.split('__or__')		# then see if any match
        for eone in eset:
            ret = check(eone,given,numerical,matrix,normphase,abcsym,do_qubit,symtab,dosimplify)
            if ret['ok']:
                return ret
        return ret

    flags = {}
    if "__autonorm__" in expect:
        flags['autonorm']=True
        expect = expect.replace('__autonorm__','')
        matrix = True

    threshold = 1.0e-3
    if "__threshold__" in expect:
        (expect,st) = expect.split('__threshold__')
        threshold = float(st)
        numerical=True

    if str(given)=='' and not (str(expect)==''):
        return {'ok': False, 'msg': ''}

    try:
        xgiven = my_sympify(given,normphase,matrix,do_qubit=do_qubit,abcsym=abcsym,symtab=symtab)
    except Exception,err:
        return {'ok': False,'msg': 'Error %s<br/> in evaluating your expression "%s"' % (err,given)}

    try:
        xexpect = my_sympify(expect,normphase,matrix,do_qubit=do_qubit,abcsym=abcsym,symtab=symtab)
    except Exception,err:
        return {'ok': False,'msg': 'Error %s<br/> in evaluating OUR expression "%s"' % (err,expect)}

    if 'autonorm' in flags:	# normalize trace of matrices
        try:
            xgiven /= xgiven.trace()
        except Exception, err:
            return {'ok': False,'msg': 'Error %s<br/> in normalizing trace of your expression %s' % (err,to_latex(xgiven))}
        try:
            xexpect /= xexpect.trace()
        except Exception, err:
            return {'ok': False,'msg': 'Error %s<br/> in normalizing trace of OUR expression %s' % (err,to_latex(xexpect))}

    msg = 'Your expression was evaluated as ' + to_latex(xgiven)
    # msg += '<br/>Expected ' + to_latex(xexpect)

    # msg += "<br/>flags=%s" % flags

    if matrix and numerical:
        xgiven = my_evalf(xgiven,chop=True)
        dm = my_evalf(sympy.Matrix(xexpect)-sympy.Matrix(xgiven),chop=True)
        msg += " = " + to_latex(xgiven)
        if abs(dm.vec().norm().evalf())<threshold:
            return {'ok': True,'msg': msg}
        else:
            pass
            #msg += "dm = " + to_latex(dm) + " diff = " + str(abs(dm.vec().norm().evalf()))
            #msg += "expect = " + to_latex(xexpect)
    elif dosimplify:
        if (sympy.simplify(xexpect)==sympy.simplify(xgiven)):
            return {'ok': True,'msg': msg}
    elif numerical:
        if (abs((xexpect-xgiven).evalf(chop=True))<threshold):
            return {'ok': True,'msg': msg}
    elif (xexpect==xgiven):
        return {'ok': True,'msg': msg}

    #msg += "<p/>expect='%s', given='%s'" % (expect,given)	# debugging
    # msg += "<p/> dot test " + to_latex(dot(sympy.Symbol('x'),sympy.Symbol('y')))
    return {'ok': False,'msg': msg }

#-----------------------------------------------------------------------------
# Check function interface, which takes pmathml input

def sympy_check2(expect,ans,adict={},abname=''):

    msg = ''
    # msg += '<p/>abname=%s' % abname
    # msg += '<p/>adict=%s' % (repr(adict).replace('<','&lt;'))

    threshold = 1.0e-3
    DEBUG = True

    # parse expected answer
    try:
        fexpect = my_sympify(str(expect))
    except Exception,err:
        msg += '<p>Error %s in parsing OUR expected answer "%s"</p>' % (err,expect)
        return {'ok':False,'msg':msg}

    # if expected answer is a number, try parsing provided answer as a number also
    try:
        fans = my_sympify(str(ans))
    except Exception,err:
        fans = None

    if fexpect.is_number and fans and fans.is_number:
        if abs(abs(fans-fexpect)/fexpect)<threshold:
            return {'ok':True,'msg':msg}
        else:
            msg += '<p>You entered: %s</p>' % to_latex(fans)
            return {'ok':False,'msg':msg}

    if fexpect==fans:
        msg += '<p>You entered: %s</p>' % to_latex(fans)
        return {'ok':True,'msg':msg}

    # convert mathml answer to formula
    mmlbox = abname+'_fromjs'
    if mmlbox in adict:
        mmlans = adict[mmlbox]
    f = formula(mmlans)
    
    # get sympy representation of the formula
    # if DEBUG: msg += '<p/> mmlans=%s' % repr(mmlans).replace('<','&lt;')
    try:
        fsym = f.sympy
        msg += '<p>You entered: %s</p>' % to_latex(f.sympy)
    except Exception,err:
        msg += "<p>Error %s in converting to sympy</p>" % str(err).replace('<','&lt;')
        if DEBUG: msg += "<p><pre>%s</pre></p>" % traceback.format_exc()
        return {'ok':False,'msg':msg}

    # compare with expected
    if fexpect.is_number:
        if fsym.is_number:
            if abs(abs(fsym-fexpect)/fexpect)<threshold:
                return {'ok':True,'msg':msg}
            return {'ok':False,'msg':msg}
        msg += "<p>Expecting a numerical answer!</p>"
        msg += "<p>given = %s</p>" % repr(ans)
        msg += "<p>fsym = %s</p>" % repr(fsym)
        # msg += "<p>cmathml = <pre>%s</pre></p>" % str(f.cmathml).replace('<','&lt;')
        return {'ok':False,'msg':msg}

    if fexpect==fsym:
        return {'ok':True,'msg':msg}

    if type(fexpect)==list:
        try:
            xgiven = my_evalf(fsym,chop=True)
            dm = my_evalf(sympy.Matrix(fexpect)-sympy.Matrix(xgiven),chop=True)
            if abs(dm.vec().norm().evalf())<threshold:
                return {'ok': True,'msg': msg}
        except Exception,err:
            msg += "<p>Error %s in comparing expected (a list) and your answer</p>" % str(err).replace('<','&lt;')
            if DEBUG: msg += "<p/><pre>%s</pre>" % traceback.format_exc()
            return {'ok':False,'msg':msg}

    #diff = (fexpect-fsym).simplify()
    #fsym = fsym.simplify()
    #fexpect = fexpect.simplify()
    try:
        diff = (fexpect-fsym)
    except Exception,err:
        diff = None

    if DEBUG:
        msg += "<p>Got: %s</p>" % repr(fsym)
        # msg += "<p/>Got: %s" % str([type(x) for x in fsym.atoms()]).replace('<','&lt;')
        msg += "<p>Expecting: %s</p>" % repr(fexpect).replace('**','^').replace('hat(I)','hat(i)')
        # msg += "<p/>Expecting: %s" % str([type(x) for x in fexpect.atoms()]).replace('<','&lt;')
        if diff:
            msg += "<p>Difference: %s</p>" % to_latex(diff)

    return {'ok':False,'msg':msg,'ex':fexpect,'got':fsym}

def sctest1():
    x = "1/2*(1+(k_e* Q* q)/(m *g *h^2))"
    y = '''
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mstyle displaystyle="true">
    <mfrac>
      <mn>1</mn>
      <mn>2</mn>
    </mfrac>
    <mrow>
      <mo>(</mo>
      <mn>1</mn>
      <mo>+</mo>
      <mfrac>
        <mrow>
          <msub>
            <mi>k</mi>
            <mi>e</mi>
          </msub>
          <mo>⋅</mo>
          <mi>Q</mi>
          <mo>⋅</mo>
          <mi>q</mi>
        </mrow>
        <mrow>
          <mi>m</mi>
          <mo>⋅</mo>
          <mrow>
            <mi>g</mi>
            <mo>⋅</mo>
          </mrow>
          <msup>
            <mi>h</mi>
            <mn>2</mn>
          </msup>
        </mrow>
      </mfrac>
      <mo>)</mo>
    </mrow>
  </mstyle>
</math>
'''.strip()
    z = "1/2(1+(k_e* Q* q)/(m *g *h^2))"
    r = sympy_check2(x,z,{'a':z,'a_fromjs':y},'a')
    return r

