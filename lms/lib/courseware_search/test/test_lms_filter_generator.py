"""
Tests for the lms_filter_generator
"""
from mock import patch, Mock

from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.tests.factories import UserFactory
from student.models import CourseEnrollment
from lms.lib.courseware_search.lms_filter_generator import LmsSearchFilterGenerator


class LmsSearchFilterGeneratorTestCase(ModuleStoreTestCase):
    """ Test case class to test search result processor """

    def build_courses(self):
        """
        Build up a course tree with multiple test courses
        """

        self.courses = [
            CourseFactory.create(
                org='ElasticsearchFiltering',
                course='ES101F',
                run='test_run',
                display_name='Elasticsearch Filtering test course',
            ),

            CourseFactory.create(
                org='FilterTest',
                course='FT101',
                run='test_run',
                display_name='FilterTest test course',
            )
        ]

        self.chapter = ItemFactory.create(
            parent_location=self.courses[0].location,
            category='chapter',
            display_name="Week 1",
            publish_item=True,
        )

        self.chapter2 = ItemFactory.create(
            parent_location=self.courses[1].location,
            category='chapter',
            display_name="Week 1",
            publish_item=True,
        )

    def setUp(self):
        super(LmsSearchFilterGeneratorTestCase, self).setUp()
        self.build_courses()
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')

        for course in self.courses:
            CourseEnrollment.enroll(self.user, course.location.course_key)

    def test_course_id_not_provided(self):
        """
        Tests that we get the list of IDs of courses the user is enrolled in when the course ID is null or not provided
        """
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(user=self.user)

        self.assertTrue('start_date' in filter_dictionary)
        self.assertIn(unicode(self.courses[0].id), field_dictionary['course'])
        self.assertIn(unicode(self.courses[1].id), field_dictionary['course'])

    def test_course_id_provided(self):
        """
        Tests that we get the course ID when the course ID is provided
        """
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters(
            user=self.user,
            course_id=unicode(self.courses[0].id)
        )

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(unicode(self.courses[0].id), field_dictionary['course'])

    def test_user_not_provided(self):
        """
        Tests that we get empty list of courses in case the user is not provided
        """
        field_dictionary, filter_dictionary, _ = LmsSearchFilterGenerator.generate_field_filters()

        self.assertTrue('start_date' in filter_dictionary)
        self.assertEqual(0, len(field_dictionary['course']))

    def test_excludes_microsite(self):
        """
        By default there is the test microsite and the microsite with logistration
        to exclude
        """
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertIn('org', exclude_dictionary)
        exclude_orgs = exclude_dictionary['org']
        self.assertEqual(2, len(exclude_orgs))
        self.assertEqual('LogistrationX', exclude_orgs[0])
        self.assertEqual('TestMicrositeX', exclude_orgs[1])

    @patch('microsite_configuration.microsite.get_all_orgs', Mock(return_value=[]))
    def test_excludes_no_microsite(self):
        """ Test when no microsite is present - nothing to exclude """
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)

    @patch('microsite_configuration.microsite.get_value', Mock(return_value='TestMicrositeX'))
    def test_excludes_microsite_within(self):
        field_dictionary, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)
        self.assertIn('org', field_dictionary)
        self.assertEqual('TestMicrositeX', field_dictionary['org'])

    @patch(
        'microsite_configuration.microsite.get_all_orgs',
        Mock(return_value=["TestMicrosite1", "TestMicrosite2", "TestMicrosite3", "TestMicrosite4"])
    )
    def test_excludes_multi_microsites(self):
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertIn('org', exclude_dictionary)
        exclude_orgs = exclude_dictionary['org']
        self.assertEqual(4, len(exclude_orgs))
        self.assertIn('TestMicrosite1', exclude_orgs)
        self.assertIn('TestMicrosite2', exclude_orgs)
        self.assertIn('TestMicrosite3', exclude_orgs)
        self.assertIn('TestMicrosite4', exclude_orgs)

    @patch(
        'microsite_configuration.microsite.get_all_orgs',
        Mock(return_value=["TestMicrosite1", "TestMicrosite2", "TestMicrosite3", "TestMicrosite4"])
    )
    @patch('microsite_configuration.microsite.get_value', Mock(return_value='TestMicrosite3'))
    def test_excludes_multi_microsites_within(self):
        field_dictionary, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)
        self.assertIn('org', field_dictionary)
        self.assertEqual('TestMicrosite3', field_dictionary['org'])
