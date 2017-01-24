# -*- coding: utf-8 -*-
"""
Unit tests for preview.py
"""

import unittest
from calc import preview
import pyparsing


class LatexRenderedTest(unittest.TestCase):
    """
    Test the initializing code for LatexRendered.

    Specifically that it stores the correct data and handles parens well.
    """
    def test_simple(self):
        """
        Test that the data values are stored without changing.
        """
        math = 'x^2'
        obj = preview.LatexRendered(math, tall=True)
        self.assertEquals(obj.latex, math)
        self.assertEquals(obj.sans_parens, math)
        self.assertEquals(obj.tall, True)

    def _each_parens(self, with_parens, math, parens, tall=False):
        """
        Helper method to test the way parens are wrapped.
        """
        obj = preview.LatexRendered(math, parens=parens, tall=tall)
        self.assertEquals(obj.latex, with_parens)
        self.assertEquals(obj.sans_parens, math)
        self.assertEquals(obj.tall, tall)

    def test_parens(self):
        """ Test curvy parens. """
        self._each_parens('(x+y)', 'x+y', '(')

    def test_brackets(self):
        """ Test brackets. """
        self._each_parens('[x+y]', 'x+y', '[')

    def test_squiggles(self):
        """ Test curly braces. """
        self._each_parens(r'\{x+y\}', 'x+y', '{')

    def test_parens_tall(self):
        """ Test curvy parens with the tall parameter. """
        self._each_parens(r'\left(x^y\right)', 'x^y', '(', tall=True)

    def test_brackets_tall(self):
        """ Test brackets, also tall. """
        self._each_parens(r'\left[x^y\right]', 'x^y', '[', tall=True)

    def test_squiggles_tall(self):
        """ Test tall curly braces. """
        self._each_parens(r'\left\{x^y\right\}', 'x^y', '{', tall=True)

    def test_bad_parens(self):
        """ Check that we get an error with invalid parens. """
        with self.assertRaisesRegexp(Exception, 'Unknown parenthesis'):
            preview.LatexRendered('x^2', parens='not parens')


class LatexPreviewTest(unittest.TestCase):
    """
    Run integrative tests for `latex_preview`.

    All functionality was tested `RenderMethodsTest`, but see if it combines
    all together correctly.
    """
    def test_no_input(self):
        """
        With no input (including just whitespace), see that no error is thrown.
        """
        self.assertEquals('', preview.latex_preview(''))
        self.assertEquals('', preview.latex_preview('  '))
        self.assertEquals('', preview.latex_preview(' \t '))

    def test_number_simple(self):
        """ Simple numbers should pass through. """
        self.assertEquals(preview.latex_preview('3.1415'), '3.1415')

    def test_number_suffix(self):
        """ Suffixes should be escaped. """
        self.assertEquals(preview.latex_preview('1.618k'), r'1.618\text{k}')

    def test_number_sci_notation(self):
        """ Numbers with scientific notation should display nicely """
        self.assertEquals(
            preview.latex_preview('6.0221413E+23'),
            r'6.0221413\!\times\!10^{+23}'
        )
        self.assertEquals(
            preview.latex_preview('-6.0221413E+23'),
            r'-6.0221413\!\times\!10^{+23}'
        )

    def test_number_sci_notation_suffix(self):
        """ Test numbers with both of these. """
        self.assertEquals(
            preview.latex_preview('6.0221413E+23k'),
            r'6.0221413\!\times\!10^{+23}\text{k}'
        )
        self.assertEquals(
            preview.latex_preview('-6.0221413E+23k'),
            r'-6.0221413\!\times\!10^{+23}\text{k}'
        )

    def test_variable_simple(self):
        """ Simple valid variables should pass through. """
        self.assertEquals(preview.latex_preview('x', variables=['x']), 'x')

    def test_greek(self):
        """ Variable names that are greek should be formatted accordingly. """
        self.assertEquals(preview.latex_preview('pi'), r'\pi')

    def test_variable_subscript(self):
        """ Things like 'epsilon_max' should display nicely """
        self.assertEquals(
            preview.latex_preview('epsilon_max', variables=['epsilon_max']),
            r'\epsilon_{max}'
        )

    def test_function_simple(self):
        """ Valid function names should be escaped. """
        self.assertEquals(
            preview.latex_preview('f(3)', functions=['f']),
            r'\text{f}(3)'
        )

    def test_function_tall(self):
        r""" Functions surrounding a tall element should have \left, \right """
        self.assertEquals(
            preview.latex_preview('f(3^2)', functions=['f']),
            r'\text{f}\left(3^{2}\right)'
        )

    def test_function_sqrt(self):
        """ Sqrt function should be handled specially. """
        self.assertEquals(preview.latex_preview('sqrt(3)'), r'\sqrt{3}')

    def test_function_log10(self):
        """ log10 function should be handled specially. """
        self.assertEquals(preview.latex_preview('log10(3)'), r'\log_{10}(3)')

    def test_function_log2(self):
        """ log2 function should be handled specially. """
        self.assertEquals(preview.latex_preview('log2(3)'), r'\log_2(3)')

    def test_power_simple(self):
        """ Powers should wrap the elements with braces correctly. """
        self.assertEquals(preview.latex_preview('2^3^4'), '2^{3^{4}}')

    def test_power_parens(self):
        """ Powers should ignore the parenthesis of the last math. """
        self.assertEquals(preview.latex_preview('2^3^(4+5)'), '2^{3^{4+5}}')

    def test_parallel(self):
        r""" Parallel items should combine with '\|'. """
        self.assertEquals(preview.latex_preview('2||3'), r'2\|3')

    def test_product_mult_only(self):
        r""" Simple products should combine with a '\cdot'. """
        self.assertEquals(preview.latex_preview('2*3'), r'2\cdot 3')

    def test_product_big_frac(self):
        """ Division should combine with '\frac'. """
        self.assertEquals(
            preview.latex_preview('2*3/4/5'),
            r'\frac{2\cdot 3}{4\cdot 5}'
        )

    def test_product_single_frac(self):
        """ Division should ignore parens if they are extraneous. """
        self.assertEquals(
            preview.latex_preview('(2+3)/(4+5)'),
            r'\frac{2+3}{4+5}'
        )

    def test_product_keep_going(self):
        """
        Complex products/quotients should split into many '\frac's when needed.
        """
        self.assertEquals(
            preview.latex_preview('2/3*4/5*6'),
            r'\frac{2}{3}\cdot \frac{4}{5}\cdot 6'
        )

    def test_sum(self):
        """ Sums should combine its elements. """
        # Use 'x' as the first term (instead of, say, '1'), so it can't be
        # interpreted as a negative number.
        self.assertEquals(
            preview.latex_preview('-x+2-3+4', variables=['x']),
            '-x+2-3+4'
        )

    def test_sum_tall(self):
        """ A complicated expression should not hide the tallness. """
        self.assertEquals(
            preview.latex_preview('(2+3^2)'),
            r'\left(2+3^{2}\right)'
        )

    def test_complicated(self):
        """
        Given complicated input, ensure that exactly the correct string is made.
        """
        self.assertEquals(
            preview.latex_preview('11*f(x)+x^2*(3||4)/sqrt(pi)'),
            r'11\cdot \text{f}(x)+\frac{x^{2}\cdot (3\|4)}{\sqrt{\pi}}'
        )

        self.assertEquals(
            preview.latex_preview('log10(1+3/4/Cos(x^2)*(x+1))',
                                  case_sensitive=True),
            (r'\log_{10}\left(1+\frac{3}{4\cdot \text{Cos}\left(x^{2}\right)}'
             r'\cdot (x+1)\right)')
        )

    def test_syntax_errors(self):
        """
        Test a lot of math strings that give syntax errors

        Rather than have a lot of self.assertRaises, make a loop and keep track
        of those that do not throw a `ParseException`, and assert at the end.
        """
        bad_math_list = [
            '11+',
            '11*',
            'f((x)',
            'sqrt(x^)',
            '3f(x)',  # Not 3*f(x)
            '3|4',
            '3|||4'
        ]
        bad_exceptions = {}
        for math in bad_math_list:
            try:
                preview.latex_preview(math)
            except pyparsing.ParseException:
                pass  # This is what we were expecting. (not excepting :P)
            except Exception as error:  # pragma: no cover
                bad_exceptions[math] = error
            else:  # pragma: no cover
                # If there is no exception thrown, this is a problem
                bad_exceptions[math] = None

        self.assertEquals({}, bad_exceptions)
