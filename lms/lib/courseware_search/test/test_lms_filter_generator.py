"""
Tests for the lms_filter_generator
"""
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from lms.lib.courseware_search.lms_filter_generator import LmsSearchFilterGenerator


class LmsSearchFilterGeneratorTestCase(ModuleStoreTestCase):
    """ Test case class to test search result processor """

    def build_course(self):
        """
        Build up a course tree with an html control
        """

        CourseFactory.create(
            org='Elasticsearch',
            course='ES101',
            run='test_run',
            display_name='Elasticsearch test course',
        )

        CourseFactory.create(
            org='FilterTest',
            course='FT101',
            run='test_run',
            display_name='FilterTest test course',
        )

    def setUp(self):
        super(LmsSearchFilterGeneratorTestCase, self).setUp()
        self.build_course()

    def test_course_id_not_provided(self):
        sfg = LmsSearchFilterGenerator()
        filter_dictionary = sfg.field_dictionary(user=self.user)

        self.assertEqual(filter_dictionary['courses'], ['Elasticsearch/ES101/test_run', 'FilterTest/FT101/test_run'])
