import json
import unittest
import itertools

def vsepr_parse_user_answer(user_input):
    return json.loads(user_input)


def vsepr_build_correct_answer(geometry, atoms):
    return {'geometry': geometry, 'atoms': atoms}


def vsepr_grade(user_input, correct_answer, convert_to_perepherial=False):
    """
        Allowed cases:
            c0, a, e
            c0, p
    """
    # import ipdb; ipdb.set_trace()
    # print user_input, type(user_input)
    # print correct_answer, type(correct_answer)
    if user_input['geometry'] != correct_answer['geometry']:
        return False

    if user_input['atoms']['c0'] != correct_answer['atoms']['c0']:
        return False

    if convert_to_perepherial:
        # convert user_input from (a,e,e1,e2) to (p)
        # correct_answer must be set in (p) using this flag
        c0 = user_input['atoms'].pop('c0')
        user_input['atoms'] = {'p' + str(i): v for i, v in enumerate(user_input['atoms'].values())}
        user_input['atoms']['c0'] = c0

    # special case for AX6
    if 'e10' in correct_answer['atoms']:  # need check e1x, e2x symmetry for AX6..
        a_user = {}
        a_correct = {}
        for ea_position in ['a', 'e1', 'e2']:  # collecting positions:
            a_user[ea_position] = [v for k, v in user_input['atoms'].items() if k.startswith(ea_position)]
            a_correct[ea_position] = [v for k, v in correct_answer['atoms'].items() if k.startswith(ea_position)]

        correct = [sorted(a_correct['a'])] + [sorted(a_correct['e1'])] + [sorted(a_correct['e2'])]
        for permutation in itertools.permutations(['a', 'e1', 'e2']):
            if correct == [sorted(a_user[permutation[0]])] + [sorted(a_user[permutation[1]])] + [sorted(a_user[permutation[2]])]:
                return True
        return False

    else:  # no need to checl e1x,e2x symmetry - convert them to ex
        if 'e10' in user_input['atoms']:  # e1x exists, it is AX6.. case
            e_index = 0
            for k, v in user_input['atoms'].items():
                if len(k) == 3:  # e1x
                    del user_input['atoms'][k]
                    user_input['atoms']['e' + str(e_index)] = v
                    e_index += 1

        # common case
        for ea_position in ['p', 'a', 'e']:
            # collecting atoms:
            a_user = [v for k, v in user_input['atoms'].items() if k.startswith(ea_position)]
            a_correct = [v for k, v in correct_answer['atoms'].items() if k.startswith(ea_position)]
            # print a_user, a_correct
            if len(a_user) != len(a_correct):
                return False
            if sorted(a_user) != sorted(a_correct):
                return False

        return True


class Test_Grade(unittest.TestCase):
    ''' test grade function '''

    def test_incorrect_geometry(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX4E0", atoms={"c0": "N", "p0": "H", "p1": "(ep)", "p2": "H", "p3": "H"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX3E0","atoms":{"c0":"B","p0":"F","p1":"B","p2":"F"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer))

    def test_incorrect_positions(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX4E0", atoms={"c0": "N", "p0": "H", "p1": "(ep)", "p2": "H", "p3": "H"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX4E0","atoms":{"c0":"B","p0":"F","p1":"B","p2":"F"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer))

    def test_correct_answer(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX4E0", atoms={"c0": "N", "p0": "H", "p1": "(ep)", "p2": "H", "p3": "H"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX4E0","atoms":{"c0":"N","p0":"H","p1":"(ep)","p2":"H", "p3":"H"}}')
        self.assertTrue(vsepr_grade(user_answer, correct_answer))

    def test_incorrect_position_order_p(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX4E0", atoms={"c0": "N", "p0": "H", "p1": "(ep)", "p2": "H", "p3": "H"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX4E0","atoms":{"c0":"N","p0":"H","p1":"H","p2":"(ep)", "p3":"H"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer))

    def test_correct_position_order_with_ignore_p_order(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX4E0", atoms={"c0": "N", "p0": "H", "p1": "(ep)", "p2": "H", "p3": "H"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX4E0","atoms":{"c0":"N","p0":"H","p1":"H","p2":"(ep)", "p3":"H"}}')
        self.assertTrue(vsepr_grade(user_answer, correct_answer, ignore_p_order=True))

    def test_incorrect_position_order_ae(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "test", "a1": "(ep)", "e0": "H", "e1": "H", "e2": "(ep)", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"Br","a0":"test","a1":"(ep)","e0":"H","e1":"(ep)","e2":"(ep)","e3":"(ep)"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer))

    def test_correct_position_order_with_ignore_a_order_not_e(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "(ep)", "a1": "test", "e0": "H", "e1": "H", "e2": "(ep)", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"Br","a0":"test","a1":"(ep)","e0":"H","e1":"H","e2":"(ep)","e3":"(ep)"}}')
        self.assertTrue(vsepr_grade(user_answer, correct_answer, ignore_a_order=True))

    def test_incorrect_position_order_with_ignore_a_order_not_e(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "(ep)", "a1": "test", "e0": "H", "e1": "H", "e2": "H", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"Br","a0":"test","a1":"(ep)","e0":"H","e1":"H","e2":"(ep)","e3":"H"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer, ignore_a_order=True))

    def test_correct_position_order_with_ignore_e_order_not_a(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "(ep)", "a1": "test", "e0": "H", "e1": "H", "e2": "H", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"Br","a0":"(ep)","a1":"test","e0":"H","e1":"H","e2":"(ep)","e3":"H"}}')
        self.assertTrue(vsepr_grade(user_answer, correct_answer, ignore_e_order=True))

    def test_incorrect_position_order_with_ignore_e_order__not_a(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "(ep)", "a1": "test", "e0": "H", "e1": "H", "e2": "H", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"Br","a0":"test","a1":"(ep)","e0":"H","e1":"H","e2":"(ep)","e3":"H"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer, ignore_e_order=True))

    def test_correct_position_order_with_ignore_ae_order(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "(ep)", "a1": "test", "e0": "H", "e1": "H", "e2": "H", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"Br","a0":"test","a1":"(ep)","e0":"H","e1":"H","e2":"(ep)","e3":"H"}}')
        self.assertTrue(vsepr_grade(user_answer, correct_answer, ignore_e_order=True, ignore_a_order=True))

    def test_incorrect_c0(self):
        correct_answer = vsepr_build_correct_answer(geometry="AX6E0", atoms={"c0": "Br", "a0": "(ep)", "a1": "test", "e0": "H", "e1": "H", "e2": "H", "e3": "(ep)"})
        user_answer = vsepr_parse_user_answer(u'{"geometry":"AX6E0","atoms":{"c0":"H","a0":"test","a1":"(ep)","e0":"H","e1":"H","e2":"(ep)","e3":"H"}}')
        self.assertFalse(vsepr_grade(user_answer, correct_answer, ignore_e_order=True, ignore_a_order=True))


def suite():

    testcases = [Test_Grade]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
