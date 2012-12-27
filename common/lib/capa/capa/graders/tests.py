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
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

    def test_position_and_targets(self):
        user_input = '{"use_targets": false, \
        "draggables": [{"1": "t1"}, {"name_with_icon": "t2"}]}'
        correct_answer = {'1':    't1', 'name_with_icon': 't2'}
        self.assertFalse(draganddrop.grade(user_input, correct_answer))

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


def suite():

    testcases = [Test_DragAndDrop]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
