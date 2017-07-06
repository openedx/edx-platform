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
    """ Tests for search result processor """

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

    def test_excludes_site_org(self):
        """
        By default site orgs not belonging to current site org should be excluded.
        """
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertIn('org', exclude_dictionary)
        exclude_orgs = exclude_dictionary['org']
        self.assertEqual(2, len(exclude_orgs))
        self.assertEqual('LogistrationX', exclude_orgs[0])
        self.assertEqual('TestSiteX', exclude_orgs[1])

    @patch('openedx.core.djangoapps.site_configuration.helpers.get_all_orgs', Mock(return_value=[]))
    def test_no_excludes_with_no_orgs(self):
        """ Test when no org is present - nothing to exclude """
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)

    @patch('openedx.core.djangoapps.site_configuration.helpers.get_value', Mock(return_value='TestSiteX'))
    def test_excludes_org_within(self):
        field_dictionary, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)
        self.assertIn('org', field_dictionary)
        self.assertEqual('TestSiteX', field_dictionary['org'])

    @patch(
        'openedx.core.djangoapps.site_configuration.helpers.get_all_orgs',
        Mock(return_value=["TestSite1", "TestSite2", "TestSite3", "TestSite4"])
    )
    def test_excludes_multi_orgs(self):
        _, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertIn('org', exclude_dictionary)
        exclude_orgs = exclude_dictionary['org']
        self.assertEqual(4, len(exclude_orgs))
        self.assertIn('TestSite1', exclude_orgs)
        self.assertIn('TestSite2', exclude_orgs)
        self.assertIn('TestSite3', exclude_orgs)
        self.assertIn('TestSite4', exclude_orgs)

    @patch(
        'openedx.core.djangoapps.site_configuration.helpers.get_all_orgs',
        Mock(return_value=["TestSite1", "TestSite2", "TestSite3", "TestSite4"])
    )
    @patch('openedx.core.djangoapps.site_configuration.helpers.get_value', Mock(return_value='TestSite3'))
    def test_excludes_multi_orgs_within(self):
        field_dictionary, _, exclude_dictionary = LmsSearchFilterGenerator.generate_field_filters(user=self.user)
        self.assertNotIn('org', exclude_dictionary)
        self.assertIn('org', field_dictionary)
        self.assertEqual('TestSite3', field_dictionary['org'])
