# lint-amnesty, pylint: disable=missing-module-docstring
from unittest import TestCase

from six.moves import range

from .symmath_check import symmath_check


class SymmathCheckTest(TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    def test_symmath_check_integers(self):
        number_list = [i for i in range(-100, 100)]  # lint-amnesty, pylint: disable=unnecessary-comprehension
        self._symmath_check_numbers(number_list)

    def test_symmath_check_floats(self):
        number_list = [i + 0.01 for i in range(-100, 100)]
        self._symmath_check_numbers(number_list)

    def test_symmath_check_same_symbols(self):
        expected_str = "x+2*y"
        dynamath = '''
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mstyle displaystyle="true">
  <mrow>
    <mi>x</mi>
    <mo>+</mo>
    <mn>2</mn>
    <mo>*</mo>
    <mi>y</mi>
  </mrow>
</mstyle>
</math>'''.strip()

        # Expect that the exact same symbolic string is marked correct
        result = symmath_check(expected_str, expected_str, dynamath=[dynamath])
        assert (('ok' in result) and result['ok'])

    def test_symmath_check_equivalent_symbols(self):
        expected_str = "x+2*y"
        input_str = "x+y+y"
        dynamath = '''
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mstyle displaystyle="true">
  <mrow>
    <mi>x</mi>
    <mo>+</mo>
    <mi>y</mi>
    <mo>+</mo>
    <mi>y</mi>
  </mrow>
</mstyle>
</math>'''.strip()

        # Expect that equivalent symbolic strings are marked correct
        result = symmath_check(expected_str, input_str, dynamath=[dynamath])
        assert (('ok' in result) and result['ok'])

    def test_symmath_check_different_symbols(self):
        expected_str = "0"
        input_str = "x+y"
        dynamath = '''
<math xmlns="http://www.w3.org/1998/Math/MathML">
  <mstyle displaystyle="true">
  <mrow>
    <mi>x</mi>
    <mo>+</mo>
    <mi>y</mi>
  </mrow>
</mstyle>
</math>'''.strip()

        # Expect that an incorrect response is marked incorrect
        result = symmath_check(expected_str, input_str, dynamath=[dynamath])
        assert (('ok' in result) and (not result['ok']))
        assert 'fail' not in result['msg']

    def _symmath_check_numbers(self, number_list):  # lint-amnesty, pylint: disable=missing-function-docstring

        for n in number_list:

            # expect = ans, so should say the answer is correct
            expect = n
            ans = n
            result = symmath_check(str(expect), str(ans))
            assert (('ok' in result) and result['ok']), ('%f should == %f' % (expect, ans))

            # Change expect so that it != ans
            expect += 0.1
            result = symmath_check(str(expect), str(ans))
            assert (('ok' in result) and (not result['ok'])), ('%f should != %f' % (expect, ans))
