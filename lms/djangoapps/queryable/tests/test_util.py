from django.test import TestCase
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE

from queryable import util


class TestUtilApproxEqual(TestCase):
    """
    Check the approx_equal function
    """

    def test_default_tolerance(self):
        """
        Check that function with default tolerance
        """
        self.assertTrue(util.approx_equal(1.00001,1.0))
        self.assertTrue(util.approx_equal(1.0,1.00001))

        self.assertFalse(util.approx_equal(1.0,2.0))
        self.assertFalse(util.approx_equal(1.0,1.0002))


    def test_smaller_default_tolerance(self):
        """
        Set tolerance smaller than default and check if still correct
        """
        
        self.assertTrue(util.approx_equal(1.0,1.0,1))
        self.assertTrue(util.approx_equal(1.0,1.000001,0.000001))


    def test_bigger_default_tolerance(self):
        """
        Set tolerance bigger than default and check if still correct
        """

        self.assertFalse(util.approx_equal(1.0,2.0,0.75))
        self.assertFalse(util.approx_equal(2.0,1.0,0.75))


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestUtilGetAssignmentToProblemMap(TestCase):
    """
    Tests the get_assignemnt_to_problem_map
    """

    def setUp(self):
        self.course = CourseFactory.create()


    def test_empty_course(self):
        """
        Test for course with nothing in it
        """
        problems_map = util.get_assignment_to_problem_map(self.course.id)
        
        self.assertEqual(problems_map, {})


    def test_single_assignment(self):
        """
        Test returns the problems for a course with a single assignment
        """
        section = ItemFactory.create(
            parent_location=self.course.location.url(),
            category="chapter")

        subsection = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential",
        )
        subsection_metadata = own_metadata(subsection)
        subsection_metadata['graded'] = True
        subsection_metadata['format'] = "Homework"
        modulestore().update_metadata(subsection.location, subsection_metadata)

        unit = ItemFactory.create(
            parent_location=subsection.location.url(),
            category="vertical",
        )

        problem1 = ItemFactory.create(
            parent_location=unit.location.url(),
            category="problem",
        )
        problem2 = ItemFactory.create(
            parent_location=unit.location.url(),
            category="problem",
        )

        problems_map = util.get_assignment_to_problem_map(self.course.id)

        answer = {
            'Homework' : [
                [problem1.location.url(), problem2.location.url()],
                ],
            }

        self.assertEqual(problems_map,answer)


    def test_two_assignments_same_type(self):
        """
        Test if has two assignments
        """
        section = ItemFactory.create(
            parent_location=self.course.location.url(),
            category="chapter")

        subsection1 = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential")
        subsection_metadata1 = own_metadata(subsection1)
        subsection_metadata1['graded'] = True
        subsection_metadata1['format'] = "Homework"
        modulestore().update_metadata(subsection1.location, subsection_metadata1)

        unit1 = ItemFactory.create(
            parent_location=subsection1.location.url(),
            category="vertical")
        problem1 = ItemFactory.create(
            parent_location=unit1.location.url(),
            category="problem")

        subsection2 = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential")
        subsection_metadata2 = own_metadata(subsection2)
        subsection_metadata2['graded'] = True
        subsection_metadata2['format'] = "Homework"
        modulestore().update_metadata(subsection2.location, subsection_metadata2)

        unit2 = ItemFactory.create(
            parent_location=subsection2.location.url(),
            category="vertical")
        problem2 = ItemFactory.create(
            parent_location=unit2.location.url(),
            category="problem")

        problems_map = util.get_assignment_to_problem_map(self.course.id)

        answer = {
            'Homework' : [
                [problem1.location.url()],
                [problem2.location.url()],
                ],
            }

        self.assertEqual(problems_map,answer)


    def test_two_assignments_different_types(self):
        """
        Creates two assignments of different types
        """
        section = ItemFactory.create(
            parent_location=self.course.location.url(),
            category="chapter")

        subsection1 = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential")
        subsection_metadata1 = own_metadata(subsection1)
        subsection_metadata1['graded'] = True
        subsection_metadata1['format'] = "Homework"
        modulestore().update_metadata(subsection1.location, subsection_metadata1)

        unit1 = ItemFactory.create(
            parent_location=subsection1.location.url(),
            category="vertical")
        problem1 = ItemFactory.create(
            parent_location=unit1.location.url(),
            category="problem")

        subsection2 = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential")
        subsection_metadata2 = own_metadata(subsection2)
        subsection_metadata2['graded'] = True
        subsection_metadata2['format'] = "Quiz"
        modulestore().update_metadata(subsection2.location, subsection_metadata2)

        unit2 = ItemFactory.create(
            parent_location=subsection2.location.url(),
            category="vertical")
        problem2 = ItemFactory.create(
            parent_location=unit2.location.url(),
            category="problem")

        problems_map = util.get_assignment_to_problem_map(self.course.id)

        answer = {
            'Homework' : [
                [problem1.location.url()],
                ],
            'Quiz' : [
                [problem2.location.url()],
                ],
            }

        self.assertEqual(problems_map,answer)



    def test_return_only_graded_subsections(self):
        """
        Make sure only returns problems and assignments that are graded
        """
        section = ItemFactory.create(
            parent_location=self.course.location.url(),
            category="chapter")

        subsection1 = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential")
        subsection_metadata1 = own_metadata(subsection1)
        subsection_metadata1['graded'] = True
        subsection_metadata1['format'] = "Homework"
        modulestore().update_metadata(subsection1.location, subsection_metadata1)

        unit1 = ItemFactory.create(
            parent_location=subsection1.location.url(),
            category="vertical")
        problem1 = ItemFactory.create(
            parent_location=unit1.location.url(),
            category="problem")

        subsection2 = ItemFactory.create(
            parent_location=section.location.url(),
            category="sequential")
        subsection_metadata2 = own_metadata(subsection2)
        subsection_metadata2['format'] = "Quiz"
        modulestore().update_metadata(subsection2.location, subsection_metadata2)

        unit2 = ItemFactory.create(
            parent_location=subsection2.location.url(),
            category="vertical")
        problem2 = ItemFactory.create(
            parent_location=unit2.location.url(),
            category="problem")

        problems_map = util.get_assignment_to_problem_map(self.course.id)

        answer = {
            'Homework' : [
                [problem1.location.url()],
                ],
            }

        self.assertEqual(problems_map,answer)

