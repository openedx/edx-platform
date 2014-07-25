.. _Math Response Formatting for Students:

#####################################
Math Response Formatting for Students
#####################################

In numerical input problems, the student's response may be more complicated than a
simple number. Expressions like ``sqrt(3)`` and even ``1+e^(sin(pi/2)+2*i)``
are valid, and evaluate to 1.73 and -0.13 + 2.47i, respectively.

The parser renders text that students enter into "beautiful math" that appears below the problem's response field:

.. image:: /Images/Math1.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math2.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math3.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math4.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math5.png
 :alt: Image of a numerical input probem rendered by the parser

Students can enter any of the following into the response field.

*******
Numbers
*******

- Integers: '2520'
- Fractions: 2/3
- Normal floats: '3.14'
- With no integer part: '.98'
- Scientific notation: '1.2e-2' (=0.012)
- More scientific notation: '-4.4e+5' = '-4.4e5' (=-440,000)
- SI suffixes: '2.25k' (=2,250). The full list:

  ====== ========== ===============
  Suffix Stands for Example
  ====== ========== ===============
  %      percent    0.01 = 1e-2
  k      kilo       1000 = 1e3
  M      mega       1e6
  G      giga       1e9
  T      tera       1e12
  c      centi      0.01 = 1e-2
  m      milli      0.001 = 1e-3
  u      micro      1e-6
  n      nano       1e-9
  p      pico       1e-12
  ====== ========== ===============

The largest possible number handled currently is exactly the largest float
possible (in the Python language). This number is 1.7977e+308. Any expression
containing larger values will not evaluate correctly, so it's best to avoid
this situation.

*********************
Default Constants
*********************

Simple and commonly used mathematical/scientific constants are included by
default. These include:

- ``i`` and ``j`` as ``sqrt(-1)``
- ``e`` as Euler's number (2.718...)
- ``g``: gravity (9.80 m/s^2)
- ``pi``
- ``k``: the Boltzmann constant (~1.38e-23 in Joules/Kelvin)
- ``c``: the speed of light in m/s (2.998e8)
- ``T``: the positive difference between 0K and 0°C (273.15)
- ``q``: the fundamental charge (~1.602e-19 Coloumbs)

**************
Greek Letters
**************

The parser automatically converts the following Greek letter names into the corresponding Greek characters:

.. list-table::
   :widths: 20 20 20 20
   :header-rows: 0

   * - alpha
     - beta
     - gamma
     - delta
   * - epsilon
     - varepsilon
     - zeta
     - eta
   * - theta
     - vartheta
     - iota
     - kappa
   * - lambda
     - mu
     - nu
     - xi
   * - pi
     - rho
     - sigma
     - tau
   * - upsilon
     - phi
     - varphi
     - chi
   * - psi
     - omega
     - 
     - 

.. note:: ``epsilon`` is the lunate version, whereas ``varepsilon`` looks like a backward 3.


****************************
Operators and Functions
****************************

* Use standard arithmetic operation symbols.
* Indicate multiplication explicitly by using an asterisk (*).
* Use a caret (^) to raise to a power.
* Use an underscore (_) to indicate a subscript.
* Use parentheses to specify the order of operations.

The normal operators apply (with normal order of operations):
``+ - * / ^``. Also provided is a special "parallel resistors" operator given
by ``||``. For example, an input of ``1 || 2`` would represent the resistance
of a pair of parallel resistors (of resistance 1 and 2 ohms), evaluating to 2/3
(ohms).

Currently, factorials written in the form '3!' are invalid, but
there is a workaround. Students can specify ``fact(3)`` or ``factorial(3)`` to
access the factorial function.

The default included functions are the following:

- Trig functions: sin, cos, tan, sec, csc, cot
- Their inverses: arcsin, arccos, arctan, arcsec, arccsc, arccot
- Other common functions: sqrt, log10, log2, ln, exp, abs
- Factorial: ``fact(3)`` or ``factorial(3)`` are valid. However, you must take
  care to only input integers. For example, ``fact(1.5)`` would fail.
- Hyperbolic trig functions and their inverses: sinh, cosh, tanh, sech, csch,
  coth, arcsinh, arccosh, arctanh, arcsech, arccsch, arccoth