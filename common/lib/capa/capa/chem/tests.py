import codecs
from fractions import Fraction
from pyparsing import ParseException
import unittest

from chemcalc import (compare_chemical_expression, divide_chemical_expression,
                      render_to_html, chemical_equations_equal)

local_debug = None

def log(s, output_type=None):
    if local_debug:
        print s
        if output_type == 'html':
            f.write(s + '\n<br>\n')


class Test_Compare_Equations(unittest.TestCase):
    def test_simple_equation(self):
        self.assertTrue(chemical_equations_equal('H2 + O2 -> H2O2',
                                                 'O2 + H2 -> H2O2'))
        # left sides don't match
        self.assertFalse(chemical_equations_equal('H2 + O2 -> H2O2',
                                                  'O2 + 2H2 -> H2O2'))
        # right sides don't match
        self.assertFalse(chemical_equations_equal('H2 + O2 -> H2O2',
                                                  'O2 + H2 -> H2O'))

        # factors don't match
        self.assertFalse(chemical_equations_equal('H2 + O2 -> H2O2',
                                                  'O2 + H2 -> 2H2O2'))

    def test_different_factor(self):
        self.assertTrue(chemical_equations_equal('H2 + O2 -> H2O2',
                                                 '2O2 + 2H2 -> 2H2O2'))

        self.assertFalse(chemical_equations_equal('2H2 + O2 -> H2O2',
                                                 '2O2 + 2H2 -> 2H2O2'))


    def test_different_arrows(self):
        self.assertTrue(chemical_equations_equal('H2 + O2 -> H2O2',
                                                 '2O2 + 2H2 -> 2H2O2'))

        self.assertFalse(chemical_equations_equal('H2 + O2 -> H2O2',
                                                  'O2 + H2 <-> 2H2O2'))

    def test_exact_match(self):
        self.assertTrue(chemical_equations_equal('H2 + O2 -> H2O2',
                                                 '2O2 + 2H2 -> 2H2O2'))

        self.assertFalse(chemical_equations_equal('H2 + O2 -> H2O2',
                                                 '2O2 + 2H2 -> 2H2O2', exact=True))

        # order still doesn't matter
        self.assertTrue(chemical_equations_equal('H2 + O2 -> H2O2',
                                                 'O2 + H2 -> H2O2', exact=True))


    def test_syntax_errors(self):
        self.assertFalse(chemical_equations_equal('H2 + O2 a-> H2O2',
                                                  '2O2 + 2H2 -> 2H2O2'))

        self.assertFalse(chemical_equations_equal('H2O( -> H2O2',
                                                  'H2O -> H2O2'))


        self.assertFalse(chemical_equations_equal('H2 + O2 ==> H2O2',   # strange arrow
                                                  '2O2 + 2H2 -> 2H2O2'))


class Test_Compare_Expressions(unittest.TestCase):

    def test_compare_incorrect_order_of_atoms_in_molecule(self):
        self.assertFalse(compare_chemical_expression("H2O + CO2", "O2C + OH2"))

    def test_compare_same_order_no_phases_no_factors_no_ions(self):
        self.assertTrue(compare_chemical_expression("H2O + CO2", "CO2+H2O"))

    def test_compare_different_order_no_phases_no_factors_no_ions(self):
        self.assertTrue(compare_chemical_expression("H2O + CO2", "CO2 + H2O"))

    def test_compare_different_order_three_multimolecule(self):
        self.assertTrue(compare_chemical_expression("H2O + Fe(OH)3 +  CO2", "CO2 + H2O + Fe(OH)3"))

    def test_compare_same_factors(self):
        self.assertTrue(compare_chemical_expression("3H2O +  2CO2", "2CO2 + 3H2O "))

    def test_compare_different_factors(self):
        self.assertFalse(compare_chemical_expression("2H2O +  3CO2", "2CO2 + 3H2O "))

    def test_compare_correct_ions(self):
        self.assertTrue(compare_chemical_expression("H^+ + OH^-", " OH^- + H^+ "))

    def test_compare_wrong_ions(self):
        self.assertFalse(compare_chemical_expression("H^+ + OH^-", " OH^- + H^- "))

    def test_compare_parent_groups_ions(self):
        self.assertTrue(compare_chemical_expression("Fe(OH)^2- + (OH)^-", " (OH)^- + Fe(OH)^2- "))

    def test_compare_correct_factors_ions_and_one(self):
        self.assertTrue(compare_chemical_expression("3H^+ + 2OH^-", " 2OH^- + 3H^+ "))

    def test_compare_wrong_factors_ions(self):
        self.assertFalse(compare_chemical_expression("2H^+ + 3OH^-", " 2OH^- + 3H^+ "))

    def test_compare_float_factors(self):
        self.assertTrue(compare_chemical_expression("7/2H^+ + 3/5OH^-", " 3/5OH^- + 7/2H^+ "))

    # Phases tests
    def test_compare_phases_ignored(self):
        self.assertTrue(compare_chemical_expression(
            "H2O(s) + CO2", "H2O+CO2", ignore_state=True))

    def test_compare_phases_not_ignored_explicitly(self):
        self.assertFalse(compare_chemical_expression(
            "H2O(s) + CO2", "H2O+CO2", ignore_state=False))

    def test_compare_phases_not_ignored(self):  # same as previous
        self.assertFalse(compare_chemical_expression(
            "H2O(s) + CO2", "H2O+CO2"))

    def test_compare_phases_not_ignored_explicitly(self):
        self.assertTrue(compare_chemical_expression(
            "H2O(s) + CO2", "H2O(s)+CO2", ignore_state=False))

    # all in one cases
    def test_complex_additivity(self):
        self.assertTrue(compare_chemical_expression(
            "5(H1H212)^70010- + 2H20 + 7/2HCl + H2O",
            "7/2HCl + 2H20 + H2O + 5(H1H212)^70010-"))

    def test_complex_additivity_wrong(self):
        self.assertFalse(compare_chemical_expression(
            "5(H1H212)^70010- + 2H20 + 7/2HCl + H2O",
            "2H20 + 7/2HCl + H2O + 5(H1H212)^70011-"))

    def test_complex_all_grammar(self):
        self.assertTrue(compare_chemical_expression(
            "5[Ni(NH3)4]^2+ + 5/2SO4^2-",
            "5/2SO4^2- + 5[Ni(NH3)4]^2+"))

    # special cases

    def test_compare_one_superscript_explicitly_set(self):
        self.assertTrue(compare_chemical_expression("H^+ + OH^1-", " OH^- + H^+ "))

    def test_compare_equal_factors_differently_set(self):
        self.assertTrue(compare_chemical_expression("6/2H^+ + OH^-", " OH^- + 3H^+ "))

    def test_compare_one_subscript_explicitly_set(self):
        self.assertFalse(compare_chemical_expression("H2 + CO2", "H2 + C102"))


class Test_Divide_Expressions(unittest.TestCase):
    ''' as compare_ use divide_,
    tests here must consider different
    division (not equality) cases '''

    def test_divide_by_zero(self):
        self.assertFalse(divide_chemical_expression(
            "0H2O", "H2O"))

    def test_divide_wrong_factors(self):
        self.assertFalse(divide_chemical_expression(
            "5(H1H212)^70010- + 10H2O", "5H2O + 10(H1H212)^70010-"))

    def test_divide_right(self):
        self.assertEqual(divide_chemical_expression(
            "5(H1H212)^70010- + 10H2O", "10H2O + 5(H1H212)^70010-"), 1)

    def test_divide_wrong_reagents(self):
        self.assertFalse(divide_chemical_expression(
            "H2O + CO2", "CO2"))

    def test_divide_right_simple(self):
        self.assertEqual(divide_chemical_expression(
            "H2O + CO2", "H2O+CO2"), 1)

    def test_divide_right_phases(self):
        self.assertEqual(divide_chemical_expression(
            "H2O(s) + CO2", "2H2O(s)+2CO2"), Fraction(1, 2))

    def test_divide_right_phases_other_order(self):
        self.assertEqual(divide_chemical_expression(
            "2H2O(s) + 2CO2", "H2O(s)+CO2"), 2)

    def test_divide_wrong_phases(self):
        self.assertFalse(divide_chemical_expression(
            "H2O(s) + CO2", "2H2O+2CO2(s)"))

    def test_divide_wrong_phases_but_phases_ignored(self):
        self.assertEqual(divide_chemical_expression(
            "H2O(s) + CO2", "2H2O+2CO2(s)", ignore_state=True), Fraction(1, 2))

    def test_divide_order(self):
        self.assertEqual(divide_chemical_expression(
            "2CO2 + H2O", "2H2O+4CO2"), Fraction(1, 2))

    def test_divide_fract_to_int(self):
        self.assertEqual(divide_chemical_expression(
            "3/2CO2 + H2O", "2H2O+3CO2"), Fraction(1, 2))

    def test_divide_fract_to_frac(self):
        self.assertEqual(divide_chemical_expression(
            "3/4CO2 + H2O", "2H2O+9/6CO2"), Fraction(1, 2))

    def test_divide_fract_to_frac_wrog(self):
        self.assertFalse(divide_chemical_expression(
            "6/2CO2 + H2O", "2H2O+9/6CO2"), 2)


class Test_Render_Equations(unittest.TestCase):

    def test_render1(self):
        s = "H2O + CO2"
        out = render_to_html(s)
        correct = u'<span class="math">H<sub>2</sub>O+CO<sub>2</sub></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render_uncorrect_reaction(self):
        s = "O2C + OH2"
        out = render_to_html(s)
        correct = u'<span class="math">O<sub>2</sub>C+OH<sub>2</sub></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render2(self):
        s = "CO2 + H2O + Fe(OH)3"
        out = render_to_html(s)
        correct = u'<span class="math">CO<sub>2</sub>+H<sub>2</sub>O+Fe(OH)<sub>3</sub></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render3(self):
        s = "3H2O + 2CO2"
        out = render_to_html(s)
        correct = u'<span class="math">3H<sub>2</sub>O+2CO<sub>2</sub></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render4(self):
        s = "H^+ + OH^-"
        out = render_to_html(s)
        correct = u'<span class="math">H<sup>+</sup>+OH<sup>-</sup></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render5(self):
        s = "Fe(OH)^2- + (OH)^-"
        out = render_to_html(s)
        correct = u'<span class="math">Fe(OH)<sup>2-</sup>+(OH)<sup>-</sup></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render6(self):
        s = "7/2H^+ + 3/5OH^-"
        out = render_to_html(s)
        correct = u'<span class="math"><sup>7</sup>&frasl;<sub>2</sub>H<sup>+</sup>+<sup>3</sup>&frasl;<sub>5</sub>OH<sup>-</sup></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render7(self):
        s = "5(H1H212)^70010- + 2H2O + 7/2HCl + H2O"
        out = render_to_html(s)
        correct = u'<span class="math">5(H<sub>1</sub>H<sub>212</sub>)<sup>70010-</sup>+2H<sub>2</sub>O+<sup>7</sup>&frasl;<sub>2</sub>HCl+H<sub>2</sub>O</span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render8(self):
        s = "H2O(s) + CO2"
        out = render_to_html(s)
        correct = u'<span class="math">H<sub>2</sub>O(s)+CO<sub>2</sub></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render9(self):
        s = "5[Ni(NH3)4]^2+ + 5/2SO4^2-"
        #import ipdb; ipdb.set_trace()
        out = render_to_html(s)
        correct = u'<span class="math">5[Ni(NH<sub>3</sub>)<sub>4</sub>]<sup>2+</sup>+<sup>5</sup>&frasl;<sub>2</sub>SO<sub>4</sub><sup>2-</sup></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render_error(self):
        s = "5.2H20"
        out = render_to_html(s)
        correct = u'<span class="math"><span class="inline-error inline">5.2H20</span></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render_simple_brackets(self):
        s = "(Ar)"
        out = render_to_html(s)
        correct = u'<span class="math">(Ar)</span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render_eq1(self):
        s = "H^+ + OH^- -> H2O"
        out = render_to_html(s)
        correct = u'<span class="math">H<sup>+</sup>+OH<sup>-</sup>\u2192H<sub>2</sub>O</span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

    def test_render_eq2(self):
        s = "H^+ + OH^- <-> H2O"
        out = render_to_html(s)
        correct = u'<span class="math">H<sup>+</sup>+OH<sup>-</sup>\u2194H<sub>2</sub>O</span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)

        
    def test_render_eq3(self):
        s = "H^+ + OH^- <= H2O"   # unsupported arrow
        out = render_to_html(s)
        correct = u'<span class="math"><span class="inline-error inline">H^+ + OH^- <= H2O</span></span>'
        log(out + ' ------- ' + correct, 'html')
        self.assertEqual(out, correct)



def suite():

    testcases = [Test_Compare_Expressions, Test_Divide_Expressions, Test_Render_Equations]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    local_debug = True
    with codecs.open('render.html', 'w', encoding='utf-8') as f:
        unittest.TextTestRunner(verbosity=2).run(suite())
    # open render.html to look at rendered equations
