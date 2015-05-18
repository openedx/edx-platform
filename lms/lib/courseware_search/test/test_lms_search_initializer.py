"""
Tests for the lms_search_initializer
"""

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.modulestore.django import modulestore

from courseware.tests.factories import UserFactory
from courseware.tests.test_masquerade import StaffMasqueradeTestCase
from courseware.masquerade import handle_ajax

from lms.lib.courseware_search.lms_search_initializer import LmsSearchInitializer
from lms.lib.courseware_search.lms_filter_generator import LmsSearchFilterGenerator


class LmsSearchInitializerTestCase(StaffMasqueradeTestCase):
    """ Test case class to test search initializer """

    def build_course(self):
        """
        Build up a course tree with an html control
        """
        self.global_staff = UserFactory(is_staff=True)

        self.course = CourseFactory.create(
            org='Elasticsearch',
            course='ES101',
            run='test_run',
            display_name='Elasticsearch test course',
        )
        self.section = ItemFactory.create(
            parent=self.course,
            category='chapter',
            display_name='Test Section',
        )
        self.subsection = ItemFactory.create(
            parent=self.section,
            category='sequential',
            display_name='Test Subsection',
        )
        self.vertical = ItemFactory.create(
            parent=self.subsection,
            category='vertical',
            display_name='Test Unit',
        )
        self.html = ItemFactory.create(
            parent=self.vertical,
            category='html',
            display_name='Test Html control 1',
        )
        self.html = ItemFactory.create(
            parent=self.vertical,
            category='html',
            display_name='Test Html control 2',
        )

    def setUp(self):
        super(LmsSearchInitializerTestCase, self).setUp()
        self.build_course()
        self.user_partition = UserPartition(
            id=0,
            name='Test User Partition',
            description='',
            groups=[Group(0, 'Group 1'), Group(1, 'Group 2')],
            scheme_id='cohort'
        )
        self.course.user_partitions.append(self.user_partition)
        modulestore().update_item(self.course, self.global_staff.id)  # pylint: disable=no-member

    def test_staff_masquerading_added_to_group(self):
        """
        Tests that initializer sets masquerading for a staff user in a group.
        """
        # Verify that there is no masquerading group initially
        _, filter_directory, _ = LmsSearchFilterGenerator.generate_field_filters(  # pylint: disable=unused-variable
            user=self.global_staff,
            course_id=unicode(self.course.id)
        )
        self.assertIsNone(filter_directory['content_groups'])

        # Install a masquerading group
        request = self._create_mock_json_request(
            self.global_staff,
            body='{"role": "student", "user_partition_id": 0, "group_id": 1}'
        )
        handle_ajax(request, unicode(self.course.id))

        # Call initializer
        LmsSearchInitializer.set_search_enviroment(
            request=request,
            course_id=unicode(self.course.id)
        )

        # Verify that there is masquerading group after masquerade
        _, filter_directory, _ = LmsSearchFilterGenerator.generate_field_filters(  # pylint: disable=unused-variable
            user=self.global_staff,
            course_id=unicode(self.course.id)
        )
        self.assertEqual(filter_directory['content_groups'], [unicode(1)])

    def test_staff_masquerading_as_a_staff_user(self):
        """
        Tests that initializer sets masquerading for a staff user as staff.
        """

        # Install a masquerading group
        request = self._create_mock_json_request(
            self.global_staff,
            body='{"role": "staff"}'
        )
        handle_ajax(request, unicode(self.course.id))

        # Call initializer
        LmsSearchInitializer.set_search_enviroment(
            request=request,
            course_id=unicode(self.course.id)
        )

        # Verify that there is masquerading group after masquerade
        _, filter_directory, _ = LmsSearchFilterGenerator.generate_field_filters(  # pylint: disable=unused-variable
            user=self.global_staff,
            course_id=unicode(self.course.id)
        )
        self.assertNotIn('content_groups', filter_directory)

    def test_staff_masquerading_as_a_student_user(self):
        """
        Tests that initializer sets masquerading for a staff user as student.
        """

        # Install a masquerading group
        request = self._create_mock_json_request(
            self.global_staff,
            body='{"role": "student"}'
        )
        handle_ajax(request, unicode(self.course.id))

        # Call initializer
        LmsSearchInitializer.set_search_enviroment(
            request=request,
            course_id=unicode(self.course.id)
        )

        # Verify that there is masquerading group after masquerade
        _, filter_directory, _ = LmsSearchFilterGenerator.generate_field_filters(  # pylint: disable=unused-variable
            user=self.global_staff,
            course_id=unicode(self.course.id)
        )
        self.assertEqual(filter_directory['content_groups'], None)
