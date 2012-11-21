import numpy as np
import math
import fractions as fr
import decimal
import unittest
import json


def lcm(a, b):
    """ return lcm of a,b """
    return a * b / fr.gcd(a, b)


def section_to_fraction(distance):
    """ Convert float distance, that plane cut on axis
    to fraction. Return inverted fraction

    """
    # import ipdb; ipdb.set_trace()
    if np.isnan(distance):  # plane || to axis (or contains axis)
        print distance, 0
        # return inverted fration to a == nan == 1/0  => 0 / 1
        return fr.Fraction(0, 1)
    elif math.fabs(distance) <= 0.05:  # plane goes through origin, 0.02 - UI delta
        return fr.Fraction(1 if distance >= 0 else -1, 1)  # ERROR, need shift of coordinates
    else:
        # limit_denominator to closest nicest fraction
        # import ipdb; ipdb.set_trace()
        fract = fr.Fraction(distance).limit_denominator(10)  # 5 / 2 : numerator / denominator
        print 'Distance', distance, 'Inverted fraction', fract
        # return inverted fraction
        return fr.Fraction(fract.denominator, fract.numerator)


def sub_miller(sections):
    ''' Calculate miller indices.
        Plane does not intersect origin
    '''
    fracts = [section_to_fraction(section) for section in sections]

    print sections, fracts

    common_denominator = reduce(lcm, [fract.denominator for fract in fracts])
    print 'common_denominator:', common_denominator

    # 2) lead to a common denominator
    # 3) throw away denominator
    miller = [fract.numerator * math.fabs(common_denominator) / fract.denominator for fract in fracts]

    # import ipdb; ipdb.set_trace()
    # nice output:
    # output = '(' + ''.join(map(str, map(decimal.Decimal, miller))) + ')'
    # import ipdb; ipdb.set_trace()
    output = '(' + ','.join(map(str, map(decimal.Decimal, miller))) + ')'
    # print 'Miller indices:', output
    return output


def miller(points):
    """Calculate miller indices of plane
    """

    # print "\nCalculating miller indices:"
    # print 'Points:\n', points
    # calculate normal to plane
    N = np.cross(points[1] - points[0], points[2] - points[0])
    # print "Normal:", N

    # origin
    O = np.array([0, 0, 0])

    # point of plane
    P = points[0]

    # equation of a line for axes: O + (B-O) * t
    # t - parameters, B = [Bx, By, Bz]:
    B = map(np.array, [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]])

    # coordinates of intersections with axis:
    sections = [np.dot(P - O, N) / np.dot(B_axis, N) if np.dot(B_axis, N) != 0 else np.nan for B_axis in B]
    # import ipdb; ipdb.set_trace()

    if any(x == 0 for x in sections):  # Plane goes through origin.
        # Need to shift plane out of origin.
        # For this change origin position

        # 1) find cube vertex, not crossed by plane
        vertices = [
            # top
            np.array([1.0, 1.0, 1.0]),
            np.array([0.0, 0.0, 1.0]),
            np.array([1.0, 0.0, 1.0]),
            np.array([0.0, 1.0, 1.0]),
            # bottom, except 0,0,0
            np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 1.0, 0.0]),
            np.array([1.0, 1.0, 1.0]),
                    ]

        for vertex in vertices:
            if np.dot(vertex - O, N) != 0:  # vertex in plane
                new_origin = vertex
                break

        # get axis with center in new origin
        X = np.array([1 - new_origin[0], new_origin[1], new_origin[2]])
        Y = np.array([new_origin[0], 1 - new_origin[1], new_origin[2]])
        Z = np.array([new_origin[0], new_origin[1], 1 - new_origin[2]])

        # 2) calculate miller indexes by new origin
        new_axis = [X - new_origin, Y - new_origin, Z - new_origin]
        # coordinates of intersections with axis:
        sections = [np.dot(P - new_origin, N) / np.dot(B_axis, N) if np.dot(B_axis, N) != 0 else np.nan for B_axis in new_axis]
        # 3) fix signs of indexes
        #  0 -> 1, 1 -> -1
        sections = (1 - 2 * new_origin) * sections
    return sub_miller(sections)


def grade(user_input, correct_answer):
    '''
    Format:
    user_input: {"lattice":"sc","points":[["0.77","0.00","1.00"],["0.78","1.00","0.00"],["0.00","1.00","0.72"]]}
    "lattice" is one of: "", "sc", "bcc", "fcc"
    correct_answer: {'miller': '(00-1)', 'lattice': 'bcc'}
    '''
    def negative(s):
        # import ipdb; ipdb.set_trace()
        output = ''
        i = 1
        while i in range(1, len(s) - 1):
            if s[i] in (',', ' '):
                output += s[i]
            elif s[i] not in ('-', '0'):
                output += '-' + s[i]
            elif s[i] == '0':
                output += s[i]
            else:
                i += 1
                output += s[i]
            i += 1
            # import ipdb; ipdb.set_trace()
        return '(' + output + ')'

    user_answer = json.loads(user_input)

    if user_answer['lattice'] != correct_answer['lattice']:
        return False

    points = [map(float, p) for p in user_answer['points']]
    points = [np.array(point) for point in points]
    # import ipdb; ipdb.set_trace()
    print miller(points), (correct_answer['miller'].replace(' ', ''), negative(correct_answer['miller']).replace(' ', ''))

    if miller(points) in (correct_answer['miller'].replace(' ', ''), negative(correct_answer['miller']).replace(' ', '')):
        return True

    return False


class Test_Crystallography_Miller(unittest.TestCase):
    ''' test crystallography grade function '''

    def test_1(self):
        user_input = '{"lattice": "bcc", "points": [["0.50", "0.00", "0.00"], ["0.00", "0.50", "0.00"], ["0.00", "0.00", "0.50"]]}'
        self.assertTrue(grade(user_input, {'miller': '(2,2,2)', 'lattice': 'bcc'}))

    def test_2(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "0.00"], ["0.00", "1.00", "0.00"], ["0.00", "0.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,1,1)', 'lattice': 'bcc'}))

    def test_3(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.50", "1.00"], ["1.00", "1.00", "0.50"], ["0.50", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(2,2,2)', 'lattice': 'bcc'}))

    def test_4(self):
        user_input = '{"lattice": "bcc", "points": [["0.33", "1.00", "0.00"], ["0.00", "0.664", "0.00"], ["0.00", "1.00", "0.33"]]}'
        self.assertTrue(grade(user_input, {'miller': '(-3, 3, -3)', 'lattice': 'bcc'}))

    def test_5(self):
        user_input = '{"lattice": "bcc", "points": [["0.33", "1.00", "0.00"], ["0.00", "0.33", "0.00"], ["0.00", "1.00", "0.33"]]}'
        self.assertTrue(grade(user_input, {'miller': '(-6,3,-6)', 'lattice': 'bcc'}))

    def test_6(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.25", "0.00"], ["0.25", "0.00", "0.00"], ["0.00", "0.00", "0.25"]]}'
        self.assertTrue(grade(user_input, {'miller': '(4,4,4)', 'lattice': 'bcc'}))

    def test_7(self):  # goes throug origin
        user_input = '{"lattice": "bcc", "points": [["0.00", "1.00", "0.00"], ["1.00", "0.00", "0.00"], ["0.50", "1.00", "0.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(0,0,-1)', 'lattice': 'bcc'}))

    def test_8(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "1.00", "0.50"], ["1.00", "0.00", "0.50"], ["0.50", "1.00", "0.50"]]}'
        self.assertTrue(grade(user_input, {'miller': '(0,0,2)', 'lattice': 'bcc'}))

    def test_9(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "1.00"], ["0.00", "1.00", "1.00"], ["1.00", "0.00", "0.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,1,0)', 'lattice': 'bcc'}))

    def test_10(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "1.00"], ["0.00", "0.00", "0.00"], ["0.00", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,1,-1)', 'lattice': 'bcc'}))

    def test_11(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "0.50"], ["1.00", "1.00", "0.00"], ["0.00", "1.00", "0.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(0,1,2)', 'lattice': 'bcc'}))

    def test_12(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "0.50"], ["0.00", "0.00", "0.50"], ["1.00", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(0,1,-2)', 'lattice': 'bcc'}))

    def test_13(self):
        user_input = '{"lattice": "bcc", "points": [["0.50", "0.00", "0.00"], ["0.50", "1.00", "0.00"], ["0.00", "0.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(2,0,1)', 'lattice': 'bcc'}))

    def test_14(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["0.00", "0.00", "1.00"], ["0.50", "1.00", "0.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(2,-1,0)', 'lattice': 'bcc'}))

    def test_15(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["1.00", "1.00", "0.00"], ["0.00", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,-1,1)', 'lattice': 'bcc'}))

    def test_16(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "0.00"], ["0.00", "1.00", "0.00"], ["1.00", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,1,-1)', 'lattice': 'bcc'}))

    def test_17(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["1.00", "0.00", "1.00"], ["1.00", "1.00", "0.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(-1,1,1)', 'lattice': 'bcc'}))

    def test_18(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["1.00", "1.00", "0.00"], ["0.00", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,-1,1)', 'lattice': 'bcc'}))

    def test_19(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["1.00", "1.00", "0.00"], ["0.00", "0.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(-1,1,0)', 'lattice': 'bcc'}))

    def test_20(self):
        user_input = '{"lattice": "bcc", "points": [["1.00", "0.00", "0.00"], ["1.00", "1.00", "0.00"], ["0.00", "0.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,0,1)', 'lattice': 'bcc'}))

    def test_21(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["0.00", "1.00", "0.00"], ["1.00", "0.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(-1,0,1)', 'lattice': 'bcc'}))

    def test_22(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "1.00", "0.00"], ["1.00", "1.00", "0.00"], ["0.00", "0.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(0,1,1)', 'lattice': 'bcc'}))

    def test_23(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["1.00", "0.00", "0.00"], ["1.00", "1.00", "1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(0,-1,1)', 'lattice': 'bcc'}))

    def test_24(self):
        user_input = '{"lattice": "bcc", "points": [["0.66", "0.00", "0.00"], ["0.00", "0.66", "0.00"], ["0.00", "0.00", "0.66"]]}'
        self.assertTrue(grade(user_input, {'miller': '(3,3,3)', 'lattice': 'bcc'}))

    def test_25(self):
        user_input = u'{"lattice":"","points":[["0.00","0.00","0.01"],["1.00","1.00","0.01"],["0.00","1.00","1.00"]]}'
        self.assertTrue(grade(user_input, {'miller': '(1,-1,1)', 'lattice': ''}))

    def test_wrong_lattice(self):
        user_input = '{"lattice": "bcc", "points": [["0.00", "0.00", "0.00"], ["1.00", "0.00", "0.00"], ["1.00", "1.00", "1.00"]]}'
        self.assertFalse(grade(user_input, {'miller': '(3,3,3)', 'lattice': 'fcc'}))


def suite():

    testcases = [Test_Crystallography_Miller]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
