import unittest

import draganddrop


class Test_DragAndDrop(unittest.TestCase):

    def test_1(self):
        user_input = '{"laice": "bcc", "points": [["0.00", "1.00", "0.00"], ["1.00", "1.00", "0.00"], ["0.00", "0.00", "1.00"]]}'
        correct_answer = {}
        self.assertTrue(draganddrop.grade(user_input, correct_answer))


def suite():

    testcases = [Test_DragAndDrop]
    suites = []
    for testcase in testcases:
        suites.append(unittest.TestLoader().loadTestsFromTestCase(testcase))
    return unittest.TestSuite(suites)

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(suite())
