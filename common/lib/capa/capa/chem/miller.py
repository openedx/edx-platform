# 1) Calculate miller indices by points coordinates
# 2) Grader for miller indeces and lattice type


import numpy as np
import math
import fractions as fr
import decimal
import unittest


def lcm(a, b):
    """ return lcm of a,b """
    return a * b / fr.gcd(a, b)


def section_to_fraction(distance):
    """ Convert float distance, that plane cut on axis
    to fraction. Return inverted fraction

    """
    if np.isnan(distance):  # plane || to axis (or contains axis)
        print distance, 0
        # return inverted fration to a == nan == 1/0  => 0 / 1
        return fr.Fraction(0, 1)
    elif distance == 0:  # plane goes through origin
        return fr.Fraction(1, 1)  # ERROR, need shift of coordinates
    else:
        # limit_denominator to closest nicest fraction
        fract = fr.Fraction(distance).limit_denominator()  # 5 / 2 : numerator / denominator
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
    output = '(' + ''.join(map(str, map(decimal.Decimal, miller))) + ')'
    print 'Miller indices:', output
    return output


def miller(points):
    """Calculate miller indices of plane
    """

    print "\nCalculating miller indices:"
    print 'Points:\n', points
    # calculate normal to plane
    N = np.cross(points[1] - points[0], points[2] - points[0])
    print "Normal:", N

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


class Test_Crystallography_Grader(unittest.TestCase):
    ''' test crystallography grade function '''

    def test_1(self):
        x = np.array([0.5, 0, 0])
        y = np.array([0, 0.5, 0])
        z = np.array([0, 0, 0.5])
        self.assertEqual(miller(np.array([x, y, z])), '(222)')

    def test_2(self):
        x = np.array([1, 0, 0])
        y = np.array([0, 1, 0])
        z = np.array([0, 0, 1])
        self.assertEqual(miller(np.array([x, y, z])), '(111)')

    def test_3(self):
        x = np.array([1, 0.5, 1])
        y = np.array([1, 1, 0.5])
        z = np.array([0.5, 1, 1])
        self.assertEqual(miller(np.array([x, y, z])), '(222)')

    def test_4(self):
        x = np.array([1. / 3, 1., 0])
        y = np.array([0, 2. / 3., 0])
        z = np.array([0, 1, 1. / 3])
        self.assertEqual(miller(np.array([x, y, z])), '(-33-3)')

    def test_5(self):
        x = np.array([1. / 3, 1., 0])
        y = np.array([0, 1. / 3., 0])
        z = np.array([0, 1, 1. / 3])
        self.assertEqual(miller(np.array([x, y, z])), '(-63-6)')

    def test_6(self):
        x = np.array([0, 1. / 4., 0])
        y = np.array([1. / 4, 0, 0])
        z = np.array([0, 0, 1. / 4])
        self.assertEqual(miller(np.array([x, y, z])), '(444)')

    def test_7(self):  # goes throug origin
        x = np.array([0, 1., 0])
        y = np.array([1., 0, 0])
        z = np.array([0.5, 1., 0])
        self.assertEqual(miller(np.array([x, y, z])), '(00-1)')

    def test_8(self):
        x = np.array([0, 1., 0.5])
        y = np.array([1., 0, 0.5])
        z = np.array([0.5, 1., 0.5])
        self.assertEqual(miller(np.array([x, y, z])), '(002)')

    def test_9(self):
        x = np.array([0, 1. / 4., 0])
        y = np.array([1. / 4, 0, 0])
        z = np.array([0, 0, 1. / 4])
        self.assertEqual(miller(np.array([x, y, z])), '(444)')

    def test_10(self):
        x = np.array([0, 1. / 4., 0])
        y = np.array([1. / 4, 0, 0])
        z = np.array([0, 0, 1. / 4])
        self.assertEqual(miller(np.array([x, y, z])), '(444)')


def suite():

    testcases = [Test_Crystallography_Grader]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())

