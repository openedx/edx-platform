from unittest import TestCase
from symmath_check import symmath_check

class SymmathCheckTest(TestCase):
    def test_symmath_check_integers(self):
        number_list = [i for i in range(-100, 100)]
        self._symmath_check_numbers(number_list)

    def test_symmath_check_floats(self):
        number_list = [i + 0.01 for i in range(-100, 100)]
        self._symmath_check_numbers(number_list)

    def _symmath_check_numbers(self, number_list):

        for n in number_list:

            # expect = ans, so should say the answer is correct
            expect = n
            ans = n
            result = symmath_check(str(expect), str(ans))
            self.assertTrue('ok' in result and result['ok'],
                            "%f should == %f" % (expect, ans))

            # Change expect so that it != ans
            expect += 0.1
            result = symmath_check(str(expect), str(ans))
            self.assertTrue('ok' in result and not result['ok'],
                            "%f should != %f" % (expect, ans))
