"""
Unit tests for calc.py
"""

import unittest
import numpy
import calc
from pyparsing import ParseException


class EvaluatorTest(unittest.TestCase):
    """
    Run tests for calc.evaluator
    Go through all functionalities as specifically as possible--
    work from number input to functions and complex expressions
    Also test custom variable substitutions (i.e.
      `evaluator({'x':3.0},{}, '3*x')`
    gives 9.0) and more.
    """

    def test_number_input(self):
        """
        Test different kinds of float inputs

        See also
          test_trailing_period (slightly different)
          test_exponential_answer
          test_si_suffix
        """
        easy_eval = lambda x: calc.evaluator({}, {}, x)

        self.assertEqual(easy_eval("13"), 13)
        self.assertEqual(easy_eval("3.14"), 3.14)
        self.assertEqual(easy_eval(".618033989"), 0.618033989)

        self.assertEqual(easy_eval("-13"), -13)
        self.assertEqual(easy_eval("-3.14"), -3.14)
        self.assertEqual(easy_eval("-.618033989"), -0.618033989)

    def test_period(self):
        """
        The string '.' should not evaluate to anything.
        """
        self.assertRaises(ParseException, calc.evaluator, {}, {}, '.')
        self.assertRaises(ParseException, calc.evaluator, {}, {}, '1+.')

    def test_trailing_period(self):
        """
        Test that things like '4.' will be 4 and not throw an error
        """
        try:
            self.assertEqual(4.0, calc.evaluator({}, {}, '4.'))
        except ParseException:
            self.fail("'4.' is a valid input, but threw an exception")

    def test_exponential_answer(self):
        """
        Test for correct interpretation of scientific notation
        """
        answer = 50
        correct_responses = ["50", "50.0", "5e1", "5e+1",
                             "50e0", "50.0e0", "500e-1"]
        incorrect_responses = ["", "3.9", "4.1", "0", "5.01e1"]

        for input_str in correct_responses:
            result = calc.evaluator({}, {}, input_str)
            fail_msg = "Expected '{0}' to equal {1}".format(
                input_str, answer)
            self.assertEqual(answer, result, msg=fail_msg)

        for input_str in incorrect_responses:
            result = calc.evaluator({}, {}, input_str)
            fail_msg = "Expected '{0}' to not equal {1}".format(
                input_str, answer)
            self.assertNotEqual(answer, result, msg=fail_msg)

    def test_si_suffix(self):
        """
        Test calc.py's unique functionality of interpreting si 'suffixes'.

        For instance 'k' stand for 'kilo-' so '1k' should be 1,000
        """
        test_mapping = [('4.2%', 0.042), ('2.25k', 2250), ('8.3M', 8300000),
                        ('9.9G', 9.9e9), ('1.2T', 1.2e12), ('7.4c', 0.074),
                        ('5.4m', 0.0054), ('8.7u', 0.0000087),
                        ('5.6n', 5.6e-9), ('4.2p', 4.2e-12)]

        for (expr, answer) in test_mapping:
            tolerance = answer * 1e-6  # Make rel. tolerance, because of floats
            fail_msg = "Failure in testing suffix '{0}': '{1}' was not {2}"
            fail_msg = fail_msg.format(expr[-1], expr, answer)
            self.assertAlmostEqual(calc.evaluator({}, {}, expr), answer,
                                   delta=tolerance, msg=fail_msg)

    def test_operator_sanity(self):
        """
        Test for simple things like '5+2' and '5/2'
        """
        var1 = 5.0
        var2 = 2.0
        operators = [('+', 7), ('-', 3), ('*', 10), ('/', 2.5), ('^', 25)]

        for (operator, answer) in operators:
            input_str = "{0} {1} {2}".format(var1, operator, var2)
            result = calc.evaluator({}, {}, input_str)
            fail_msg = "Failed on operator '{0}': '{1}' was not {2}".format(
                operator, input_str, answer)
            self.assertEqual(answer, result, msg=fail_msg)

    def test_raises_zero_division_err(self):
        """
        Ensure division by zero gives an error
        """
        self.assertRaises(ZeroDivisionError, calc.evaluator,
                          {}, {}, '1/0')
        self.assertRaises(ZeroDivisionError, calc.evaluator,
                          {}, {}, '1/0.0')
        self.assertRaises(ZeroDivisionError, calc.evaluator,
                          {'x': 0.0}, {}, '1/x')

    def test_parallel_resistors(self):
        """
        Test the parallel resistor operator ||

        The formula is given by
            a || b || c ...
            = 1 / (1/a + 1/b + 1/c + ...)
        It is the resistance of a parallel circuit of resistors with resistance
        a, b, c, etc&. See if this evaulates correctly.
        """
        self.assertEqual(calc.evaluator({}, {}, '1||1'), 0.5)
        self.assertEqual(calc.evaluator({}, {}, '1||1||2'), 0.4)
        self.assertEqual(calc.evaluator({}, {}, "j||1"), 0.5 + 0.5j)

    def test_parallel_resistors_with_zero(self):
        """
        Check the behavior of the || operator with 0
        """
        self.assertTrue(numpy.isnan(calc.evaluator({}, {}, '0||1')))
        self.assertTrue(numpy.isnan(calc.evaluator({}, {}, '0.0||1')))
        self.assertTrue(numpy.isnan(calc.evaluator({'x': 0.0}, {}, 'x||1')))

    def assert_function_values(self, fname, ins, outs, tolerance=1e-3):
        """
        Helper function to test many values at once

        Test the accuracy of evaluator's use of the function given by fname
        Specifically, the equality of `fname(ins[i])` against outs[i].
        This is used later to test a whole bunch of f(x) = y at a time
        """

        for (arg, val) in zip(ins, outs):
            input_str = "{0}({1})".format(fname, arg)
            result = calc.evaluator({}, {}, input_str)
            fail_msg = "Failed on function {0}: '{1}' was not {2}".format(
                fname, input_str, val)
            self.assertAlmostEqual(val, result, delta=tolerance, msg=fail_msg)

    def test_trig_functions(self):
        """
        Test the trig functions provided in calc.py

        which are: sin, cos, tan, arccos, arcsin, arctan
        """

        angles = ['-pi/4', '0', 'pi/6', 'pi/5', '5*pi/4', '9*pi/4', '1 + j']
        sin_values = [-0.707, 0, 0.5, 0.588, -0.707, 0.707, 1.298 + 0.635j]
        cos_values = [0.707, 1, 0.866, 0.809, -0.707, 0.707, 0.834 - 0.989j]
        tan_values = [-1, 0, 0.577, 0.727, 1, 1, 0.272 + 1.084j]
        # Cannot test tan(pi/2) b/c pi/2 is a float and not precise...

        self.assert_function_values('sin', angles, sin_values)
        self.assert_function_values('cos', angles, cos_values)
        self.assert_function_values('tan', angles, tan_values)

        # Include those where the real part is between -pi/2 and pi/2
        arcsin_inputs = ['-0.707', '0', '0.5', '0.588', '1.298 + 0.635*j']
        arcsin_angles = [-0.785, 0, 0.524, 0.629, 1 + 1j]
        self.assert_function_values('arcsin', arcsin_inputs, arcsin_angles)
        # Rather than throwing an exception, numpy.arcsin gives nan
        # self.assertTrue(numpy.isnan(calc.evaluator({}, {}, 'arcsin(-1.1)')))
        # self.assertTrue(numpy.isnan(calc.evaluator({}, {}, 'arcsin(1.1)')))
        # Disabled for now because they are giving a runtime warning... :-/

        # Include those where the real part is between 0 and pi
        arccos_inputs = ['1', '0.866', '0.809', '0.834-0.989*j']
        arccos_angles = [0, 0.524, 0.628, 1 + 1j]
        self.assert_function_values('arccos', arccos_inputs, arccos_angles)
        # self.assertTrue(numpy.isnan(calc.evaluator({}, {}, 'arccos(-1.1)')))
        # self.assertTrue(numpy.isnan(calc.evaluator({}, {}, 'arccos(1.1)')))

        # Has the same range as arcsin
        arctan_inputs = ['-1', '0', '0.577', '0.727', '0.272 + 1.084*j']
        arctan_angles = arcsin_angles
        self.assert_function_values('arctan', arctan_inputs, arctan_angles)

    def test_other_functions(self):
        """
        Test the non-trig functions provided in calc.py

        Specifically:
          sqrt, log10, log2, ln, abs,
          fact, factorial
        """

        # Test sqrt
        self.assert_function_values('sqrt',
                                    [0, 1, 2, 1024],  # -1
                                    [0, 1, 1.414, 32])  # 1j
        # sqrt(-1) is NAN not j (!!).

        # Test logs
        self.assert_function_values('log10',
                                    [0.1, 1, 3.162, 1000000, '1+j'],
                                    [-1, 0, 0.5, 6, 0.151 + 0.341j])
        self.assert_function_values('log2',
                                    [0.5, 1, 1.414, 1024, '1+j'],
                                    [-1, 0, 0.5, 10, 0.5 + 1.133j])
        self.assert_function_values('ln',
                                    [0.368, 1, 1.649, 2.718, 42, '1+j'],
                                    [-1, 0, 0.5, 1, 3.738, 0.347 + 0.785j])

        # Test abs
        self.assert_function_values('abs', [-1, 0, 1, 'j'], [1, 0, 1, 1])

        # Test factorial
        fact_inputs = [0, 1, 3, 7]
        fact_values = [1, 1, 6, 5040]
        self.assert_function_values('fact', fact_inputs, fact_values)
        self.assert_function_values('factorial', fact_inputs, fact_values)

        self.assertRaises(ValueError, calc.evaluator, {}, {}, "fact(-1)")
        self.assertRaises(ValueError, calc.evaluator, {}, {}, "fact(0.5)")
        self.assertRaises(ValueError, calc.evaluator, {}, {}, "factorial(-1)")
        self.assertRaises(ValueError, calc.evaluator, {}, {}, "factorial(0.5)")

    def test_constants(self):
        """
        Test the default constants provided in calc.py

        which are: j (complex number), e, pi, k, c, T, q
        """

        # Of the form ('expr', python value, tolerance (or None for exact))
        default_variables = [('j', 1j, None),
                             ('e', 2.7183, 1e-3),
                             ('pi', 3.1416, 1e-3),
                             # c = speed of light
                             ('c', 2.998e8, 1e5),
                             # 0 deg C = T Kelvin
                             ('T', 298.15, 0.01),
                             # Note k = scipy.constants.k = 1.3806488e-23
                             ('k', 1.3806488e-23, 1e-26),
                             # Note q = scipy.constants.e = 1.602176565e-19
                             ('q', 1.602176565e-19, 1e-22)]
        for (variable, value, tolerance) in default_variables:
            fail_msg = "Failed on constant '{0}', not within bounds".format(
                variable)
            result = calc.evaluator({}, {}, variable)
            if tolerance is None:
                self.assertEqual(value, result, msg=fail_msg)
            else:
                self.assertAlmostEqual(value, result,
                                       delta=tolerance, msg=fail_msg)

    def test_complex_expression(self):
        """
        Calculate combinations of operators and default functions
        """

        self.assertAlmostEqual(
            calc.evaluator({}, {}, "(2^2+1.0)/sqrt(5e0)*5-1"),
            10.180,
            delta=1e-3)

        self.assertAlmostEqual(
            calc.evaluator({}, {}, "1+1/(1+1/(1+1/(1+1)))"),
            1.6,
            delta=1e-3)
        self.assertAlmostEqual(
            calc.evaluator({}, {}, "10||sin(7+5)"),
            -0.567, delta=0.01)
        self.assertAlmostEqual(calc.evaluator({}, {}, "sin(e)"),
                               0.41, delta=0.01)
        self.assertAlmostEqual(calc.evaluator({}, {}, "k*T/q"),
                               0.025, delta=1e-3)
        self.assertAlmostEqual(calc.evaluator({}, {}, "e^(j*pi)"),
                               -1, delta=1e-5)

    def test_simple_vars(self):
        """
        Substitution of variables into simple equations
        """
        variables = {'x': 9.72, 'y': 7.91, 'loooooong': 6.4}

        # Should not change value of constant
        # even with different numbers of variables...
        self.assertEqual(calc.evaluator({'x': 9.72}, {}, '13'), 13)
        self.assertEqual(calc.evaluator({'x': 9.72, 'y': 7.91}, {}, '13'), 13)
        self.assertEqual(calc.evaluator(variables, {}, '13'), 13)

        # Easy evaluation
        self.assertEqual(calc.evaluator(variables, {}, 'x'), 9.72)
        self.assertEqual(calc.evaluator(variables, {}, 'y'), 7.91)
        self.assertEqual(calc.evaluator(variables, {}, 'loooooong'), 6.4)

        # Test a simple equation
        self.assertAlmostEqual(calc.evaluator(variables, {}, '3*x-y'),
                               21.25, delta=0.01)  # = 3 * 9.72 - 7.91
        self.assertAlmostEqual(calc.evaluator(variables, {}, 'x*y'),
                               76.89, delta=0.01)

        self.assertEqual(calc.evaluator({'x': 9.72, 'y': 7.91}, {}, "13"), 13)
        self.assertEqual(calc.evaluator(variables, {}, "13"), 13)
        self.assertEqual(
            calc.evaluator({
                'a': 2.2997471478310274, 'k': 9, 'm': 8,
                'x': 0.66009498411213041},
                {}, "5"),
            5)

    def test_variable_case_sensitivity(self):
        """
        Test the case sensitivity flag and corresponding behavior
        """
        self.assertEqual(
            calc.evaluator({'R1': 2.0, 'R3': 4.0}, {}, "r1*r3"),
            8.0)

        variables = {'t': 1.0}
        self.assertEqual(calc.evaluator(variables, {}, "t"), 1.0)
        self.assertEqual(calc.evaluator(variables, {}, "T"), 1.0)
        self.assertEqual(calc.evaluator(variables, {}, "t", cs=True), 1.0)
        # Recall 'T' is a default constant, with value 298.15
        self.assertAlmostEqual(calc.evaluator(variables, {}, "T", cs=True),
                               298, delta=0.2)

    def test_simple_funcs(self):
        """
        Subsitution of custom functions
        """
        variables = {'x': 4.712}
        functions = {'id': lambda x: x}
        self.assertEqual(calc.evaluator({}, functions, 'id(2.81)'), 2.81)
        self.assertEqual(calc.evaluator({}, functions, 'id(2.81)'), 2.81)
        self.assertEqual(calc.evaluator(variables, functions, 'id(x)'), 4.712)

        functions.update({'f': numpy.sin})
        self.assertAlmostEqual(calc.evaluator(variables, functions, 'f(x)'),
                               -1, delta=1e-3)

    def test_function_case_sensitivity(self):
        """
        Test the case sensitivity of functions
        """
        functions = {'f': lambda x: x,
                     'F': lambda x: x + 1}
        # Test case insensitive evaluation
        # Both evaulations should call the same function
        self.assertEqual(calc.evaluator({}, functions, 'f(6)'),
                         calc.evaluator({}, functions, 'F(6)'))
        # Test case sensitive evaluation
        self.assertNotEqual(calc.evaluator({}, functions, 'f(6)', cs=True),
                            calc.evaluator({}, functions, 'F(6)', cs=True))

    def test_undefined_vars(self):
        """
        Check to see if the evaluator catches undefined variables
        """
        variables = {'R1': 2.0, 'R3': 4.0}

        self.assertRaises(calc.UndefinedVariable, calc.evaluator,
                          {}, {}, "5+7 QWSEKO")
        self.assertRaises(calc.UndefinedVariable, calc.evaluator,
                          {'r1': 5}, {}, "r1+r2")
        self.assertRaises(calc.UndefinedVariable, calc.evaluator,
                          variables, {}, "r1*r3", cs=True)
