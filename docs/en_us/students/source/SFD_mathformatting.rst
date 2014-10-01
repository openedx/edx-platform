.. _Math Formatting:

#####################################################################
Student Guide to Entering Mathematical and Scientific Expressions
#####################################################################

For some math, science, and other problems, you'll enter a numerical or math expression, such as a formula, into a response field. You enter your response as plain text, and the edX system then converts your text into numbers and symbols that appear below the response field:

.. image:: /Images/Math4.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math5.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math3.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math2.png
 :alt: Image of a numerical input probem rendered by the parser
.. image:: /Images/Math1.png
 :alt: Image of a numerical input probem rendered by the parser

You may recognize parts of this system if you've used math programs before. 

****************************
Entering Math Expressions
****************************

When you enter your plain text into the response field, follow these guidelines:

* Use standard arithmetic operation symbols: the plus sign (+), minus sign (-), multiplication sign (*), and division sign (/).
* Indicate multiplication explicitly. That is, instead of ``mc^2`` type ``m*c^2``, and instead of ``5a+4b+3c`` type ``5*a+4*b+3*c``.
* Use parentheses to specify the order of operations and to make your expression as clear as possible.
* Use a caret (^) to indicate an exponent.
* Use an underscore (_) to indicate a subscript.
* Avoid whitespace.
* Don't use equal signs (=).
* Because the system is case-sensitive, make sure you use uppercase and lowercase letters carefully.
* Only use curved parentheses. Don't use brackets ([]) or braces ({}).

For more information about the types of characters you can use, see below.


============
Numbers
============

You can use the following types of numbers:

- Integers: 2520
- Fractions: 2/3
- Normal floats: 3.14
- Floats with no integer part: .98

The largest number you can use is **1.7977e+308**, which is the largest float
possible in the Python programming language. 

====================================
Scientific Notation and Affixes
====================================

To indicate scientific notation, enter the letter ``e`` and the exponent that you want. You can enter positive exponents as well as negative exponents. If you enter a negative exponent, make sure to include a minus sign.

For example, type ``0.012`` as ``1.2e-2`` and ``-440,000`` as ``-4.4e+5`` or ``-4.4e5``.

You can also use the following International System of Units (SI) affixes: 

.. list-table::

  * - Affix
    - Stands for
    - Example
  * - %
    - percent
    - 0.01 = 1e-2
  * - k
    - kilo
    - 1000 = 1e3
  * - M
    - mega
    - 1e6
  * - G
    - giga
    - 1e9
  * - T
    - tera
    - 1e12
  * - c
    - centi
    - 0.01 = 1e-2
  * - m
    - milli
    - 0.001 = 1e-3
  * - u
    - micro
    - 1e-6
  * - n
    - nano
    - 1e-9
  * - p
    - pico
    - 1e-12

============
Constants
============

You can use the following constants:

- ``i`` and ``j`` as ``sqrt(-1)``
- ``e`` as Euler's number (2.718...)
- ``g``: gravity (9.80 m/s^2)
- ``pi``
- ``k``: the Boltzmann constant (~1.38e-23 in Joules/Kelvin)
- ``c``: the speed of light in m/s (2.998e8)
- ``T``: the positive difference between 0K and 0°C (273.15)
- ``q``: the fundamental charge (~1.602e-19 Coloumbs)

==================
Greek Letters
==================

To use any of the following Greek letters, type the name of the letter in the response field.

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


============
Functions
============

To use a function, type the letters that represent the function, and then surround the expression in that function with parentheses. For example, to represent the square root of ``4*a+b``, type ``sqrt(4*a+b)``. 

You can use the following functions:

* Common functions: sqrt, log10, log2, ln, exp, abs
* Trigonometric functions: sin, cos, tan, sec, csc, cot
* Their inverses: arcsin, arccos, arctan, arcsec, arccsc, arccot
* Hyperbolic trigonometric functions and their inverses: sinh, cosh, tanh, sech, csch, coth, arcsinh, arccosh, arctanh, arcsech, arccsch, arccoth
* Factorials: Enter factorials as ``fact(3)`` or ``factorial(3)``. You must use integers. For example, you can't enter ``fact(1.5)``.
* A "parallel resistors" operator (``||``). For example, ``1 || 2`` represents the resistance of a pair of parallel resistors (of resistance 1 and 2 ohms), evaluating to 2/3 (ohms).
