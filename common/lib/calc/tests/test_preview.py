# -*- coding: utf-8 -*-
"""
Unit tests for preview.py
"""

import unittest
import preview
import pyparsing


class PreviewTestUtility(unittest.TestCase):
    """
    Provide utilities for the preview test cases.
    """
    def assert_latex_rendered(self, to_be_tested, tall=False, latex=None, sans_parens=None):
        """
        Compare a `LatexRendered` object against the data it should store.
        """
        if sans_parens is None:
            sans_parens = latex
        self.assertEquals(to_be_tested.sans_parens, sans_parens)
        self.assertEquals(to_be_tested.latex, latex)
        self.assertEquals(to_be_tested.tall, tall)


class LatexRenderedTest(PreviewTestUtility):
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
        self.assert_latex_rendered(obj, tall=True, latex=math)

    def _each_parens(self, with_parens, math, parens, tall=False):
        """
        Helper method to test the way parens are wrapped.
        """
        obj = preview.LatexRendered(math, parens=parens, tall=tall)
        self.assert_latex_rendered(
            obj,
            tall=tall,
            latex=with_parens,
            sans_parens=math
        )

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


def _call_render_method(render_method, string_children):
    """
    Call `render_method` with LatexRendered version of `string_children`
    """
    children = [preview.LatexRendered(k) for k in string_children]
    return render_method(children)


class RenderMethodsTest(PreviewTestUtility):
    """
    Test each of the `render_X` methods.

    They take a list of `LatexRendered`s and, depending on the type of node,
    combine them all together into one `LatexRendered`.

    For the simplest of cases, call them with `_call_render_method` above.
    """
    def test_number_simple(self):
        """ Simple numbers should pass through `render_number`. """
        out = _call_render_method(preview.render_number, ['3.1415'])
        self.assert_latex_rendered(out, latex='3.1415')

    def test_number_suffix(self):
        """ Suffixes should be escaped in `render_number`. """
        out = _call_render_method(preview.render_number, ['1.618', 'k'])
        self.assert_latex_rendered(out, latex=r'1.618\text{k}')

    def test_variable_simple(self):
        """ Simple valid variables should pass through `render_variable`. """
        render_variable = preview.variable_closure(['x', 'y'], lambda x: x.lower())
        out = _call_render_method(render_variable, ['x'])
        self.assert_latex_rendered(out, latex='x')

    def test_variable_unicode(self):
        """
        Simple valid unicode variables should pass through as well.

        Note: it isn't supported right now in the rest of the code (esp. the
        way we have set up pyparsing), but when it is, this should work.
        """
        var = "✖"
        render_variable = preview.variable_closure([var], lambda x: x.lower())
        out = _call_render_method(render_variable, [var])
        self.assert_latex_rendered(out, latex=var)

    def test_greek(self):
        """ Variable names that are greek should be formatted accordingly. """
        render_variable = preview.variable_closure(['pi'], lambda x: x.lower())
        out = _call_render_method(render_variable, ['pi'])
        self.assert_latex_rendered(out, latex=r'\pi ')

    def test_function_simple(self):
        """ Valid function names should be escaped in `render_function`. """
        render_function = preview.function_closure(['f'], lambda x: x.lower())
        out = _call_render_method(render_function, ['f', 'x'])
        self.assert_latex_rendered(out, latex=r'\text{f}(x)')

    def test_function_tall(self):
        r""" Functions surrounding a tall element should have \left, \right """
        render_function = preview.function_closure(['f'], lambda x: x.lower())
        out = render_function([
            preview.LatexRendered('f'),
            preview.LatexRendered('x^2', tall=True)
        ])
        self.assert_latex_rendered(out, latex=r'\text{f}\left(x^2\right)', tall=True)

    def test_function_sqrt(self):
        """ Sqrt function should be handled specially. """
        render_function = preview.function_closure(['sqrt'], lambda x: x.lower())
        out = _call_render_method(render_function, ['sqrt', 'x'])
        self.assert_latex_rendered(out, latex=r'\sqrt{x}')

    def test_function_log10(self):
        """ log10 function should be handled specially. """
        render_function = preview.function_closure(['log10'], lambda x: x.lower())
        out = _call_render_method(render_function, ['log10', 'x'])
        self.assert_latex_rendered(out, latex=r'\log_{10}(x)')

    def test_function_log2(self):
        """ log2 function should be handled specially. """
        render_function = preview.function_closure(['log2'], lambda x: x.lower())
        out = _call_render_method(render_function, ['log2', 'x'])
        self.assert_latex_rendered(out, latex=r'\log_2(x)')

    def test_power_simple(self):
        """ `render_power` should wrap the elements with braces correctly. """
        out = _call_render_method(
            preview.render_power,
            ['x', '^', 'y', '^', '2']
        )
        self.assert_latex_rendered(out, latex='x^{y^{2}}', tall=True)

    def test_power_parens(self):
        """ `render_power` should ignore the parenthesis of the last math. """
        children = ['x', '^', 'y', '^']  # (x+y)
        children = [preview.LatexRendered(k) for k in children]
        children.append(preview.LatexRendered('x+y', parens='('))

        out = preview.render_power(children)
        self.assert_latex_rendered(out, latex='x^{y^{x+y}}', tall=True)

    def test_parallel(self):
        r""" `render_power` should combine its elements with '\|'. """
        out = _call_render_method(preview.render_parallel, ['x', '||', 'y'])
        self.assert_latex_rendered(out, latex=r'x\|y')

    def test_product_mult_only(self):
        r""" `render_product` should combine a product with a '\cdot'. """
        out = _call_render_method(preview.render_product, ['x', '*', 'y'])
        self.assert_latex_rendered(out, latex=r'x\cdot y')

    def test_product_big_frac(self):
        """ `render_product` should combine a fraction with '\frac'. """
        out = _call_render_method(
            preview.render_product, list('w*x/y/z')
        )
        self.assert_latex_rendered(out, latex=r'\frac{w\cdot x}{y\cdot z}', tall=True)

    def test_product_single_frac(self):
        """ `render_product` should ignore parens if they are extraneous. """
        out = preview.render_product([
            preview.LatexRendered('x+1', parens='('),
            preview.LatexRendered('/'),
            preview.LatexRendered('y+1', parens='(')
        ])
        self.assert_latex_rendered(out, latex=r'\frac{x+1}{y+1}', tall=True)

    def test_product_keep_going(self):
        """ `render_product` should split into many '\frac's when needed. """
        out = _call_render_method(
            preview.render_product, list('p/q*r/s*t')
        )
        self.assert_latex_rendered(out, latex=r'\frac{p}{q}\cdot \frac{r}{s}\cdot t', tall=True)

    def test_sum(self):
        """ `render_sum` should combine its elements. """
        out = _call_render_method(preview.render_sum, list('-a+b-c+d'))
        self.assert_latex_rendered(out, latex=r'-a+b-c+d')

    def test_sum_tall(self):
        """ `render_sum` should pass on `tall`-ness. """
        out = preview.render_sum([
            preview.LatexRendered('x'),
            preview.LatexRendered('+'),
            preview.LatexRendered('y^2', tall=True)
        ])
        self.assert_latex_rendered(out, latex='x+y^2', tall=True)

    def test_atom_simple(self):
        """ `render_atom` should pass through items without parens. """
        out = _call_render_method(preview.render_atom, list('x'))
        self.assert_latex_rendered(out, latex='x')

    def test_atom_parens(self):
        """ Items wrapped in parens should have a `sans_parens` value. """
        out = _call_render_method(preview.render_atom, list('(x)'))
        self.assert_latex_rendered(out, latex='(x)', sans_parens='x')


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
        self.assertEquals('<nada/>', preview.latex_preview(''))
        self.assertEquals('<nada/>', preview.latex_preview('  '))
        self.assertEquals('<nada/>', preview.latex_preview(' \t '))

    def test_complicated(self):
        """
        Given complicated input, ensure that exactly the correct string is made.
        """
        self.assertEquals(
            preview.latex_preview('11*f(x)+x^2*(3||4)/sqrt(pi)'),
            r'11\cdot \text{f}(x)+\frac{x^{2}\cdot (3\|4)}{\sqrt{\pi }}'
        )

        self.assertEquals(
            preview.latex_preview('log10(1+3/4/Cos(x^2)*(x+1))', case_sensitive=True),
            r'\log_{10}\left(1+\frac{3}{4\cdot \text{Cos}\left(x^{2}\right)}\cdot (x+1)\right)'
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
