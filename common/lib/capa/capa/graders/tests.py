import unittest

import draganddrop


class Test_DragAndDrop(unittest.TestCase):

    def test_targets_true(self):
        user_input = '{"use_targets": "true", "draggables": \
        ["1": "t1", "name_with_icon": "t2"]}'
        correct_answer = {'1':              't1', 'name_with_icon': 't2'}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))

        def test_targets_true(self):
        user_input = '{"use_targets": "true", "draggables": \
        ["1": "t1", "name_with_icon": "t2"]}'
        correct_answer = {'1':              't1', 'name_with_icon': 't2'}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))


def suite():

    testcases = [Test_DragAndDrop]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
