import unittest

import draganddrop


class Test_DragAndDrop(unittest.TestCase):

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
        correct_answer = draganddrop.DragAndDrop()
        correct_answer.correct_groups['filled_levels'] = ['1', '2', '3', '4', '5', '6']
        correct_answer.correct_positions['filled_levels'] = {'allowed': [
        's_left', 's_right', 's_sigma', 's_sigma_star', 'p_pi_1', 'p_pi_2']}

        correct_answer.correct_groups['spin_up'] = ['7', '8', '9', '10']
        correct_answer.correct_positions['spin_up'] = {'allowed':
            ['p_left_1', 'p_left_2', 'p_right_1', 'p_right_2']}

        correct_answer.correct_groups['sigma'] = ['11', '12']
        correct_answer.correct_positions['sigma'] = {'allowed':
            ['s_sigma_name', 'p_sigma_name']}

        correct_answer.correct_groups['sigma_star'] = ['13', '14']
        correct_answer.correct_positions['sigma_star'] = {'allowed':
            ['s_sigma_star_name', 'p_sigma_star_name']}

        correct_answer.correct_groups['pi'] = ['15']
        correct_answer.correct_positions['pi'] = {'allowed': ['p_pi_name']}

        correct_answer.correct_groups['pi_star'] = ['16']
        correct_answer.correct_positions['pi_star'] = {'allowed': ['p_pi_star_name']}

        self.assertTrue(draganddrop.grade(user_input, correct_answer))

    def test_lcao_extra_element_incorrect(self):
        """Describe carbon molecule in LCAO-MO"""
        user_input = '{"use_targets":true,"draggables":[{"1":"s_left"}, \
        {"5":"s_right"},{"4":"s_sigma"},{"6":"s_sigma_star"},{"7":"p_left_1"}, \
        {"8":"p_left_2"},{"17":"p_left_3"},{"10":"p_right_1"},{"9":"p_right_2"}, \
        {"2":"p_pi_1"},{"3":"p_pi_2"},{"11":"s_sigma_name"}, \
        {"13":"s_sigma_star_name"},{"15":"p_pi_name"},{"16":"p_pi_star_name"}, \
        {"12":"p_sigma_name"},{"14":"p_sigma_star_name"}]}'
        correct_answer = draganddrop.DragAndDrop()
        correct_answer.correct_groups['filled_levels'] = ['1', '2', '3', '4', '5', '6']
        correct_answer.correct_positions['filled_levels'] = {'allowed': [
        's_left', 's_right', 's_sigma', 's_sigma_star', 'p_pi_1', 'p_pi_2']}

        correct_answer.correct_groups['spin_up'] = ['7', '8', '9', '10']
        correct_answer.correct_positions['spin_up'] = {'allowed':
            ['p_left_1', 'p_left_2', 'p_right_1', 'p_right_2']}

        correct_answer.correct_groups['sigma'] = ['11', '12']
        correct_answer.correct_positions['sigma'] = {'allowed':
            ['s_sigma_name', 'p_sigma_name']}

        correct_answer.correct_groups['sigma_star'] = ['13', '14']
        correct_answer.correct_positions['sigma_star'] = {'allowed':
            ['s_sigma_star_name', 'p_sigma_star_name']}

        correct_answer.correct_groups['pi'] = ['15']
        correct_answer.correct_positions['pi'] = {'allowed': ['p_pi_name']}

        correct_answer.correct_groups['pi_star'] = ['16']
        correct_answer.correct_positions['pi_star'] = {'allowed': ['p_pi_star_name']}

        self.assertFalse(draganddrop.grade(user_input, correct_answer))


def suite():

    testcases = [Test_DragAndDrop]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
