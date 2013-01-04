import unittest

import draganddrop
from draganddrop import PositionsCompare


class Test_PositionsCompare(unittest.TestCase):
    """ describe"""

    def test_nested_list_and_list1(self):
        self.assertEqual(PositionsCompare([[1, 2], 40]), PositionsCompare([1, 3]))

    def test_nested_list_and_list2(self):
        self.assertNotEqual(PositionsCompare([1, 12]), PositionsCompare([1, 1]))

    def test_list_and_list1(self):
        self.assertNotEqual(PositionsCompare([[1, 2], 12]), PositionsCompare([1, 15]))

    def test_list_and_list2(self):
        self.assertEqual(PositionsCompare([1, 11]), PositionsCompare([1, 1]))

    def test_numerical_list_and_string_list(self):
        self.assertNotEqual(PositionsCompare([1, 2]), PositionsCompare(["1"]))

    def test_string_and_string_list1(self):
        self.assertEqual(PositionsCompare("1"), PositionsCompare(["1"]))

    def test_string_and_string_list2(self):
        self.assertEqual(PositionsCompare("abc"), PositionsCompare("abc"))

    def test_string_and_string_list3(self):
        self.assertNotEqual(PositionsCompare("abd"), PositionsCompare("abe"))

    def test_float_and_string(self):
        self.assertNotEqual(PositionsCompare([3.5, 5.7]), PositionsCompare(["1"]))

    def test_floats_and_ints(self):
        self.assertEqual(PositionsCompare([3.5, 4.5]), PositionsCompare([5, 7]))


class Test_DragAndDrop_Grade(unittest.TestCase):

    def test_targets_true(self):
        user_input = '{"use_targets": true, "draggables": [{"1": "t1"}, \
         {"name_with_icon": "t2"}]}'
        correct_answer = {'1':              't1', 'name_with_icon': 't2'}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_targets_false(self):
        user_input = '{"use_targets": true, "draggables": [{"1": "t1"}, \
        {"name_with_icon": "t2"}]}'
        correct_answer = {'1':              't3', 'name_with_icon': 't2'}
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

    def test_multiple_images_per_target_true(self):
        user_input = '{"use_targets": true, \
        "draggables": [{"1": "t1"}, {"name_with_icon": "t1"}]}'
        correct_answer = {'1':              't1', 'name_with_icon': 't1'}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_multiple_images_per_target_false(self):
        user_input = '{"use_targets": true, \
        "draggables": [{"1": "t1"}, {"name_with_icon": "t1"}]}'
        correct_answer = {'1':              't2', 'name_with_icon': 't1'}
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

    def test_targets_and_positions(self):
        user_input = '{"use_targets": true, "draggables": [{"1": [10,10]}, \
         {"name_with_icon": [[10,10],4]}]}'
        correct_answer = {'1':  [10, 10], 'name_with_icon': [[10, 10], 4]}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_position_and_targets(self):
        user_input = '{"use_targets": false, \
        "draggables": [{"1": "t1"}, {"name_with_icon": "t2"}]}'
        correct_answer = {'1':    't1', 'name_with_icon': 't2'}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_positions_exact(self):
        user_input = '{"use_targets": false, "draggables": \
        [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'
        correct_answer = {'1':   [10, 10], 'name_with_icon': [20, 20]}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_positions_false(self):
        user_input = '{"use_targets": false, "draggables": \
        [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'
        correct_answer = {'1':   [25, 25], 'name_with_icon': [20, 20]}
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

    def test_positions_true_in_radius(self):
        user_input = '{"use_targets": false, "draggables": \
        [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'
        correct_answer = {'1':   [14, 14], 'name_with_icon': [20, 20]}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_positions_true_in_manual_radius(self):
        user_input = '{"use_targets": false, "draggables": \
        [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'
        correct_answer = {'1':   [[40, 10], 30], 'name_with_icon': [20, 20]}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_positions_false_in_manual_radius(self):
        user_input = '{"use_targets": false, "draggables": \
        [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'
        correct_answer = {'1': [[40, 10], 29], 'name_with_icon': [20, 20]}
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

    def test_correct_answer_not_has_key_from_user_answer(self):
        user_input = '{"use_targets": true, "draggables": [{"1": "t1"}, \
        {"name_with_icon": "t2"}]}'
        correct_answer = {'3':   't3', 'name_with_icon': 't2'}
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

    def test_anywhere(self):
        """Draggables can be places anywhere on base image.
            Place grass in the middle of the image and ant in the
            right upper corner."""
        user_input = '{"use_targets": false, "draggables": \
        [{"ant":[610.5,57.449951171875]},{"grass":[322.5,199.449951171875]}]}'
        correct_answer = {'grass':     [[300, 200], 200], 'ant': [[500, 0], 200]}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_lcao_correct(self):
        """Describe carbon molecule in LCAO-MO"""
        user_input = '{"use_targets":true,"draggables":[{"1":"s_left"}, \
        {"5":"s_right"},{"4":"s_sigma"},{"6":"s_sigma_star"},{"7":"p_left_1"}, \
        {"8":"p_left_2"},{"10":"p_right_1"},{"9":"p_right_2"}, \
        {"2":"p_pi_1"},{"3":"p_pi_2"},{"11":"s_sigma_name"}, \
        {"13":"s_sigma_star_name"},{"15":"p_pi_name"},{"16":"p_pi_star_name"}, \
        {"12":"p_sigma_name"},{"14":"p_sigma_star_name"}]}'

        correct_answer = [{
        'draggables': ['1', '2', '3', '4', '5', '6'],
        'targets': [
            's_left', 's_right', 's_sigma', 's_sigma_star', 'p_pi_1', 'p_pi_2'
        ],
            'rule': 'anyof'
        }, {
            'draggables': ['7', '8', '9', '10'],
            'targets': ['p_left_1', 'p_left_2', 'p_right_1', 'p_right_2'],
            'rule': 'anyof'
        }, {
            'draggables': ['11', '12'],
            'targets': ['s_sigma_name', 'p_sigma_name'],
            'rule': 'anyof'
        }, {
            'draggables': ['13', '14'],
            'targets': ['s_sigma_star_name', 'p_sigma_star_name'],
            'rule': 'anyof'
        }, {
            'draggables': ['15'],
            'targets': ['p_pi_name'],
            'rule': 'anyof'
        }, {
            'draggables': ['16'],
            'targets': ['p_pi_star_name'],
            'rule': 'anyof'
        }]

        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_lcao_extra_element_incorrect(self):
        """Describe carbon molecule in LCAO-MO"""
        user_input = '{"use_targets":true,"draggables":[{"1":"s_left"}, \
        {"5":"s_right"},{"4":"s_sigma"},{"6":"s_sigma_star"},{"7":"p_left_1"}, \
        {"8":"p_left_2"},{"17":"p_left_3"},{"10":"p_right_1"},{"9":"p_right_2"}, \
        {"2":"p_pi_1"},{"3":"p_pi_2"},{"11":"s_sigma_name"}, \
        {"13":"s_sigma_star_name"},{"15":"p_pi_name"},{"16":"p_pi_star_name"}, \
        {"12":"p_sigma_name"},{"14":"p_sigma_star_name"}]}'

        correct_answer = [{
        'draggables': ['1', '2', '3', '4', '5', '6'],
        'targets': [
            's_left', 's_right', 's_sigma', 's_sigma_star', 'p_pi_1', 'p_pi_2'
            ],
            'rule': 'anyof'
        }, {
            'draggables': ['7', '8', '9', '10'],
            'targets': ['p_left_1', 'p_left_2', 'p_right_1','p_right_2'],
            'rule': 'anyof'
        }, {
            'draggables': ['11', '12'],
            'targets': ['s_sigma_name', 'p_sigma_name'],
            'rule': 'anyof'
        }, {
            'draggables': ['13', '14'],
            'targets': ['s_sigma_star_name', 'p_sigma_star_name'],
            'rule': 'anyof'
        }, {
            'draggables': ['15'],
            'targets': ['p_pi_name'],
            'rule': 'anyof'
        }, {
            'draggables': ['16'],
            'targets': ['p_pi_star_name'],
            'rule': 'anyof'
        }]

        self.assertFalse(draganddrop.grade(user_input, correct_answer))


class Test_DragAndDrop_Populate(unittest.TestCase):

    def test_1(self):
        dnd = draganddrop.DragAndDrop()
        correct_answer = {'1': [[40, 10], 29], 'name_with_icon': [20, 20]}
        user_input = '{"use_targets": false, "draggables": \
        [{"1": [10, 10]}, {"name_with_icon": [20, 20]}]}'
        dnd.populate(correct_answer, user_input)

        correct_groups = {'1': ['name_with_icon'], '0': ['1']}
        correct_positions = {'1': {'exact': [[20, 20]]}, '0': {'exact': [[[40, 10], 29]]}}
        user_groups = {'1': [u'name_with_icon'], '0': [u'1']}
        user_positions = {'1': {'user': [[20, 20]]}, '0': {'user': [[10, 10]]}}

        self.assertEqual(correct_groups, dnd.correct_groups)
        self.assertEqual(correct_positions, dnd.correct_positions)
        self.assertEqual(user_groups, dnd.user_groups)
        self.assertEqual(user_positions, dnd.user_positions)


class Test_DraAndDrop_Compare_Positions(unittest.TestCase):

    def test_1(self):
        dnd = draganddrop.DragAndDrop()
        self.assertTrue(dnd.compare_positions(correct=[[1, 1], [2, 3]],
                                              user=[[2, 3], [1, 1]],
                                              flag='anyof'))

    def test_2a(self):
        dnd = draganddrop.DragAndDrop()
        self.assertTrue(dnd.compare_positions(correct=[[1, 1], [2, 3]],
                                               user=[[2, 3], [1, 1]],
                                               flag='exact'))

    def test_2b(self):
        dnd = draganddrop.DragAndDrop()
        self.assertFalse(dnd.compare_positions(correct=[[1, 1], [2, 3]],
                                               user=[[2, 13], [1, 1]],
                                               flag='exact'))

    def test_3(self):
        dnd = draganddrop.DragAndDrop()
        self.assertFalse(dnd.compare_positions(correct=["a", "b"],
                                               user=["a", "b", "c"],
                                               flag='anyof'))

    def test_4(self):
        dnd = draganddrop.DragAndDrop()
        self.assertTrue(dnd.compare_positions(correct=["a", "b", "c"],
                                              user=["a", "b"],
                                              flag='anyof'))

    def test_5(self):
        dnd = draganddrop.DragAndDrop()
        self.assertFalse(dnd.compare_positions(correct=["a", "b", "c"],
                                               user=["a", "c", "b"],
                                               flag='exact'))

    def test_6(self):
        dnd = draganddrop.DragAndDrop()
        self.assertTrue(dnd.compare_positions(correct=["a", "b", "c"],
                                               user=["a", "c", "b"],
                                               flag='anyof'))

    def test_7(self):
        dnd = draganddrop.DragAndDrop()
        self.assertFalse(dnd.compare_positions(correct=["a", "b", "b"],
                                               user=["a", "c", "b"],
                                               flag='anyof'))


def suite():

    testcases = [Test_PositionsCompare,
                 Test_DragAndDrop_Populate,
                 Test_DragAndDrop_Grade,
                 Test_DraAndDrop_Compare_Positions]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
