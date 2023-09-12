"""
Unit tests for instructor_dashboard.py.
"""


import datetime
import re

import ddt
import six
from django.conf import settings
from django.contrib.sites.models import Site
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch
from pyquery import PyQuery as pq
from pytz import UTC
from six import text_type
from six.moves import range

from common.test.utils import XssTestMixin
from common.djangoapps.course_modes.models import CourseMode
from edx_toggles.toggles.testutils import override_waffle_flag
from common.djangoapps.edxmako.shortcuts import render_to_response
from lms.djangoapps.courseware.tabs import get_course_tab_list
from lms.djangoapps.courseware.tests.factories import StaffFactory, StudentModuleFactory, UserFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from lms.djangoapps.grades.config.waffle import WRITABLE_GRADEBOOK, waffle_flags
from lms.djangoapps.instructor.toggles import DATA_DOWNLOAD_V2
from lms.djangoapps.instructor.views.gradebook_api import calculate_page_info
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseFinanceAdminRole
from common.djangoapps.student.tests.factories import AdminFactory, CourseAccessRoleFactory, CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls


def intercept_renderer(path, context):
    """
    Intercept calls to `render_to_response` and attach the context dict to the
    response for examination in unit tests.
    """
    # I think Django already does this for you in their TestClient, except
    # we're bypassing that by using edxmako.  Probably edxmako should be
    # integrated better with Django's rendering and event system.
    response = render_to_response(path, context)
    response.mako_context = context
    response.mako_template = path
    return response


@ddt.ddt
class TestInstructorDashboard(ModuleStoreTestCase, LoginEnrollmentTestCase, XssTestMixin):
    """
    Tests for the instructor dashboard (not legacy).
    """

    def setUp(self):
        """
        Set up tests
        """
        super(TestInstructorDashboard, self).setUp()
        self.course = CourseFactory.create(
            grading_policy={"GRADE_CUTOFFS": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5}},
            display_name='<script>alert("XSS")</script>'
        )

        self.course_mode = CourseMode(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE.name,
            min_price=40
        )
        self.course_info = CourseFactory.create(
            org="ACME",
            number="001",
            run="2017",
            name="How to defeat the Road Runner"
        )
        self.course_mode.save()
        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': text_type(self.course.id)})

    def get_dashboard_enrollment_message(self):
        """
        Returns expected dashboard enrollment message with link to Insights.
        """
        return u'Enrollment data is now available in <a href="http://example.com/courses/{}" ' \
               'rel="noopener" target="_blank">Example</a>.'.format(text_type(self.course.id))

    def get_dashboard_analytics_message(self):
        """
        Returns expected dashboard demographic message with link to Insights.
        """
        return u'For analytics about your course, go to <a href="http://example.com/courses/{}" ' \
               'rel="noopener" target="_blank">Example</a>.'.format(text_type(self.course.id))

    def test_instructor_tab(self):
        """
        Verify that the instructor tab appears for staff only.
        """
        def has_instructor_tab(user, course):
            """Returns true if the "Instructor" tab is shown."""
            tabs = get_course_tab_list(user, course)
            return len([tab for tab in tabs if tab.name == 'Instructor']) == 1

        self.assertTrue(has_instructor_tab(self.instructor, self.course))

        staff = StaffFactory(course_key=self.course.id)
        self.assertTrue(has_instructor_tab(staff, self.course))

        student = UserFactory.create()
        self.assertFalse(has_instructor_tab(student, self.course))

        researcher = UserFactory.create()
        CourseAccessRoleFactory(
            course_id=self.course.id,
            user=researcher,
            role='data_researcher',
            org=self.course.id.org
        )
        self.assertTrue(has_instructor_tab(researcher, self.course))

        org_researcher = UserFactory.create()
        CourseAccessRoleFactory(
            course_id=None,
            user=org_researcher,
            role='data_researcher',
            org=self.course.id.org
        )
        self.assertTrue(has_instructor_tab(org_researcher, self.course))

    @ddt.data(
        ('staff', False, False),
        ('instructor', False, False),
        ('data_researcher', True, False),
        ('global_staff', True, False),
        ('staff', False, True),
        ('instructor', False, True),
        ('data_researcher', True, True),
        ('global_staff', True, True),
    )
    @ddt.unpack
    def test_data_download(self, access_role, can_access, waffle_status):
        """
        Verify that the Data Download tab only shows up for certain roles
        """
        with override_waffle_flag(DATA_DOWNLOAD_V2, waffle_status):
            download_section = '<li class="nav-item"><button type="button" class="btn-link data_download" ' \
                               'data-section="data_download">Data Download</button></li>'
            if waffle_status:
                download_section = '<li class="nav-item"><button type="button" class="btn-link data_download_2" '\
                                   'data-section="data_download_2">Data Download</button></li>'
            user = UserFactory.create(is_staff=access_role == 'global_staff')
            CourseAccessRoleFactory(
                course_id=self.course.id,
                user=user,
                role=access_role,
                org=self.course.id.org
            )
            self.client.login(username=user.username, password="test")
            response = self.client.get(self.url)
            if can_access:
                self.assertContains(response, download_section)
            else:
                self.assertNotContains(response, download_section)
            
    #### EOL ####
    def test_data_download_eol(self):
        """
        Verify that the xblockcompletion report is visible
        """
        from lms.djangoapps.instructor.views.instructor_dashboard import _section_data_download
        user = UserFactory.create(is_staff=True)
        CourseAccessRoleFactory(
            course_id=self.course.id,
            user=user,
            role='staff',
            org=self.course.id.org
        )
        self.client.login(username=user.username, password="test")
        response = _section_data_download(self.course, {})
        try:
            from xblockcompletion import views
            self.assertTrue(response['has_xblockcompletion'])
        except ImportError:
            self.assertFalse(response['has_xblockcompletion'])
    #### EOL ####

    @override_settings(ANALYTICS_DASHBOARD_URL='http://example.com')
    @override_settings(ANALYTICS_DASHBOARD_NAME='Example')
    def test_data_download_only(self):
        """
        Verify that only the data download tab is visible for data researchers.
        """
        user = UserFactory.create()
        CourseAccessRoleFactory(
            course_id=self.course.id,
            user=user,
            role='data_researcher',
            org=self.course.id.org
        )
        self.client.login(username=user.username, password="test")
        response = self.client.get(self.url)
        matches = re.findall(
            rb'<li class="nav-item"><button type="button" class="btn-link .*" data-section=".*">.*',
            response.content
        )
        assert len(matches) == 1

    @ddt.data(
        ("How to defeat the Road Runner", "2017", "001", "ACME"),
    )
    @ddt.unpack
    def test_instructor_course_info(self, display_name, run, number, org):
        """
        Verify that it shows the correct course information
        """
        url = reverse(
            'instructor_dashboard',
            kwargs={
                'course_id': six.text_type(self.course_info.id)
            }
        )

        response = self.client.get(url)
        content = pq(response.content)

        self.assertEqual(
            display_name,
            content('#field-course-display-name b').contents()[0].strip()
        )

        self.assertEqual(
            run,
            content('#field-course-name b').contents()[0].strip()
        )

        self.assertEqual(
            number,
            content('#field-course-number b').contents()[0].strip()
        )

        self.assertEqual(
            org,
            content('#field-course-organization b').contents()[0].strip()
        )

    @ddt.data(True, False)
    def test_membership_reason_field_visibility(self, enbale_reason_field):
        """
        Verify that reason field is enabled by site configuration flag 'ENABLE_MANUAL_ENROLLMENT_REASON_FIELD'
        """

        configuration_values = {
            "ENABLE_MANUAL_ENROLLMENT_REASON_FIELD": enbale_reason_field
        }
        site = Site.objects.first()
        SiteConfiguration.objects.create(
            site=site,
            site_values=configuration_values,
            enabled=True
        )

        url = reverse(
            'instructor_dashboard',
            kwargs={
                'course_id': six.text_type(self.course_info.id)
            }
        )
        response = self.client.get(url)
        reason_field = '<textarea rows="2" id="reason-field-id" name="reason-field" ' \
                       'placeholder="Reason" spellcheck="false"></textarea>'
        if enbale_reason_field:
            self.assertContains(response, reason_field)
        else:
            self.assertNotContains(response, reason_field)

    def test_membership_site_configuration_role(self):
        """
        Verify that the role choices set via site configuration are loaded in the membership tab
        of the instructor dashboard
        """

        configuration_values = {
            "MANUAL_ENROLLMENT_ROLE_CHOICES": [
                "role1",
                "role2",
            ]
        }
        site = Site.objects.first()
        SiteConfiguration.objects.create(
            site=site,
            site_values=configuration_values,
            enabled=True
        )
        url = reverse(
            'instructor_dashboard',
            kwargs={
                'course_id': six.text_type(self.course_info.id)
            }
        )

        response = self.client.get(url)
        self.assertContains(response, '<option value="role1">role1</option>')
        self.assertContains(response, '<option value="role2">role2</option>')

    def test_membership_default_role(self):
        """
        Verify that in the absence of site configuration role choices, default values of role choices are loaded
        in the membership tab of the instructor dashboard
        """

        url = reverse(
            'instructor_dashboard',
            kwargs={
                'course_id': six.text_type(self.course_info.id)
            }
        )

        response = self.client.get(url)
        self.assertContains(response, '<option value="Learner">Learner</option>')
        self.assertContains(response, '<option value="Support">Support</option>')
        self.assertContains(response, '<option value="Partner">Partner</option>')

    def test_student_admin_staff_instructor(self):
        """
        Verify that staff users are not able to see course-wide options, while still
        seeing individual learner options.
        """
        # Original (instructor) user can see both specific grades, and course-wide grade adjustment tools
        response = self.client.get(self.url)
        self.assertContains(response, '<h4 class="hd hd-4">Adjust all enrolled learners')
        self.assertContains(response, '<h4 class="hd hd-4">View a specific learner&#39;s grades and progress')

        # But staff user can only see specific grades
        staff = StaffFactory(course_key=self.course.id)
        self.client.login(username=staff.username, password="test")
        response = self.client.get(self.url)
        self.assertNotContains(response, '<h4 class="hd hd-4">Adjust all enrolled learners')
        self.assertContains(response, '<h4 class="hd hd-4">View a specific learner&#39;s grades and progress')

    @patch(
        'lms.djangoapps.instructor.views.instructor_dashboard.settings.WRITABLE_GRADEBOOK_URL',
        'http://gradebook.local.edx.org'
    )
    def test_staff_can_see_writable_gradebook(self):
        """
        Test that, when the writable gradebook feature is enabled and
        deployed in another domain, a staff member can see it.
        """
        waffle_flag = waffle_flags()[WRITABLE_GRADEBOOK]
        with override_waffle_flag(waffle_flag, active=True):
            response = self.client.get(self.url)

        expected_gradebook_url = 'http://gradebook.local.edx.org/{}'.format(self.course.id)
        self.assertContains(response, expected_gradebook_url)
        self.assertContains(response, 'View Gradebook')

    GRADEBOOK_LEARNER_COUNT_MESSAGE = (
        'Note: This feature is available only to courses with a small number ' +
        'of enrolled learners.'
    )

    @patch(
        'lms.djangoapps.instructor.views.instructor_dashboard.settings.WRITABLE_GRADEBOOK_URL',
        settings.LMS_ROOT_URL + '/gradebook'
    )
    def test_staff_can_see_writable_gradebook_as_subdirectory(self):
        """
        Test that, when the writable gradebook feature is enabled and
        deployed in a subdirectory, a staff member can see it.
        """
        waffle_flag = waffle_flags()[WRITABLE_GRADEBOOK]
        with override_waffle_flag(waffle_flag, active=True):
            response = self.client.get(self.url)

        expected_gradebook_url = '{}/{}'.format(settings.WRITABLE_GRADEBOOK_URL, self.course.id)
        self.assertContains(response, expected_gradebook_url)
        self.assertContains(response, 'View Gradebook')

    GRADEBOOK_LEARNER_COUNT_MESSAGE = (
        'Note: This feature is available only to courses with a small number ' +
        'of enrolled learners.'
    )

    def test_gradebook_learner_count_message(self):
        """
        Test that, when the writable gradebook featue is NOT enabled, there IS
        a message that the feature is only available for courses with small
        numbers of learners.
        """
        response = self.client.get(self.url)
        self.assertContains(
            response,
            self.GRADEBOOK_LEARNER_COUNT_MESSAGE,
        )
        self.assertContains(response, 'View Gradebook')

    @patch(
        'lms.djangoapps.instructor.views.instructor_dashboard.settings.WRITABLE_GRADEBOOK_URL',
        'http://gradebook.local.edx.org'
    )
    def test_no_gradebook_learner_count_message(self):
        """
        Test that, when the writable gradebook featue IS enabled, there is NOT
        a message that the feature is only available for courses with small
        numbers of learners.
        """
        waffle_flag = waffle_flags()[WRITABLE_GRADEBOOK]
        with override_waffle_flag(waffle_flag, active=True):
            response = self.client.get(self.url)
        self.assertNotIn(
            TestInstructorDashboard.GRADEBOOK_LEARNER_COUNT_MESSAGE,
            response.content.decode('utf-8')
        )
        self.assertContains(response, 'View Gradebook')

    def test_course_name_xss(self):
        """Test that the instructor dashboard correctly escapes course names
        with script tags.
        """
        response = self.client.get(self.url)
        self.assert_no_xss(response, '<script>alert("XSS")</script>')

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': False})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_no_enrollments(self):
        """
        Test enrollment section is hidden.
        """
        response = self.client.get(self.url)
        # no enrollment information should be visible
        self.assertNotContains(response, '<h3 class="hd hd-3">Enrollment Information</h3>')

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': True})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_show_enrollments_data(self):
        """
        Test enrollment data is shown.
        """
        response = self.client.get(self.url)

        # enrollment information visible
        self.assertContains(response, '<h4 class="hd hd-4">Enrollment Information</h4>')
        self.assertContains(response, '<th scope="row">Verified</th>')
        self.assertContains(response, '<th scope="row">Audit</th>')
        self.assertContains(response, '<th scope="row">Honor</th>')
        self.assertContains(response, '<th scope="row">Professional</th>')

        # dashboard link hidden
        self.assertNotContains(response, self.get_dashboard_enrollment_message())

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': True})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_show_enrollment_data_for_prof_ed(self):
        # Create both "professional" (meaning professional + verification)
        # and "no-id-professional" (meaning professional without verification)
        # These should be aggregated for display purposes.
        users = [UserFactory() for _ in range(2)]
        CourseEnrollment.enroll(users[0], self.course.id, mode="professional")
        CourseEnrollment.enroll(users[1], self.course.id, mode="no-id-professional")
        response = self.client.get(self.url)

        # Check that the number of professional enrollments is two
        self.assertContains(response, '<th scope="row">Professional</th><td>2</td>')

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': False})
    @override_settings(ANALYTICS_DASHBOARD_URL='http://example.com')
    @override_settings(ANALYTICS_DASHBOARD_NAME='Example')
    def test_show_dashboard_enrollment_message(self):
        """
        Test enrollment dashboard message is shown and data is hidden.
        """
        response = self.client.get(self.url)

        # enrollment information hidden
        self.assertNotContains(response, '<th scope="row">Verified</th>')
        self.assertNotContains(response, '<th scope="row">Audit</th>')
        self.assertNotContains(response, '<th scope="row">Honor</th>')
        self.assertNotContains(response, '<th scope="row">Professional</th>')

        # link to dashboard shown
        expected_message = self.get_dashboard_enrollment_message()
        self.assertIn(expected_message, response.content.decode(response.charset))

    @override_settings(ANALYTICS_DASHBOARD_URL='')
    @override_settings(ANALYTICS_DASHBOARD_NAME='')
    def test_dashboard_analytics_tab_not_shown(self):
        """
        Test dashboard analytics tab isn't shown if insights isn't configured.
        """
        response = self.client.get(self.url)
        analytics_section = '<li class="nav-item"><a href="" data-section="instructor_analytics">Analytics</a></li>'
        self.assertNotContains(response, analytics_section)

    @override_settings(ANALYTICS_DASHBOARD_URL='http://example.com')
    @override_settings(ANALYTICS_DASHBOARD_NAME='Example')
    def test_dashboard_analytics_points_at_insights(self):
        """
        Test analytics dashboard message is shown
        """
        response = self.client.get(self.url)
        analytics_section = '<li class="nav-item"><button type="button" class="btn-link instructor_analytics"' \
                            ' data-section="instructor_analytics">Analytics</button></li>'
        self.assertContains(response, analytics_section)

        # link to dashboard shown
        expected_message = self.get_dashboard_analytics_message()
        self.assertIn(expected_message, response.content.decode(response.charset))

    @ddt.data(
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
    )
    @ddt.unpack
    def test_ccx_coaches_option_on_admin_list_management_instructor(
            self, ccx_feature_flag, enable_ccx, expected_result
    ):
        """
        Test whether the "CCX Coaches" option is visible or hidden depending on the value of course.enable_ccx.
        """
        with patch.dict(settings.FEATURES, {'CUSTOM_COURSES_EDX': ccx_feature_flag}):
            self.course.enable_ccx = enable_ccx
            self.store.update_item(self.course, self.instructor.id)

            response = self.client.get(self.url)

            self.assertEqual(expected_result,
                             'CCX Coaches are able to create their own Custom Courses based on this course'
                             in response.content.decode('utf-8'))

    def test_grade_cutoffs(self):
        """
        Verify that grade cutoffs are displayed in the correct order.
        """
        response = self.client.get(self.url)
        self.assertContains(response, 'D: 0.5, C: 0.57, B: 0.63, A: 0.75')

    @patch('lms.djangoapps.instructor.views.gradebook_api.MAX_STUDENTS_PER_PAGE_GRADE_BOOK', 2)
    def test_calculate_page_info(self):
        page = calculate_page_info(offset=0, total_students=2)
        self.assertEqual(page["offset"], 0)
        self.assertEqual(page["page_num"], 1)
        self.assertEqual(page["next_offset"], None)
        self.assertEqual(page["previous_offset"], None)
        self.assertEqual(page["total_pages"], 1)

    @patch('lms.djangoapps.instructor.views.gradebook_api.render_to_response', intercept_renderer)
    @patch('lms.djangoapps.instructor.views.gradebook_api.MAX_STUDENTS_PER_PAGE_GRADE_BOOK', 1)
    def test_spoc_gradebook_pages(self):
        for i in range(2):
            username = "user_%d" % i
            student = UserFactory.create(username=username)
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        url = reverse(
            'spoc_gradebook',
            kwargs={'course_id': self.course.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Max number of student per page is one.  Patched setting MAX_STUDENTS_PER_PAGE_GRADE_BOOK = 1
        self.assertEqual(len(response.mako_context['students']), 1)

    def test_open_response_assessment_page(self):
        """
        Test that Open Responses is available only if course contains at least one ORA block
        """
        ora_section = (
            '<li class="nav-item">'
            '<button type="button" class="btn-link open_response_assessment" data-section="open_response_assessment">'
            'Open Responses'
            '</button>'
            '</li>'
        )

        response = self.client.get(self.url)
        self.assertNotContains(response, ora_section)

        ItemFactory.create(parent_location=self.course.location, category="openassessment")
        response = self.client.get(self.url)
        self.assertContains(response, ora_section)

    def test_open_response_assessment_page_orphan(self):
        """
        Tests that the open responses tab loads if the course contains an
        orphaned openassessment block
        """
        # create non-orphaned openassessment block
        ItemFactory.create(
            parent_location=self.course.location,
            category="openassessment",
        )
        # create orphan
        self.store.create_item(
            self.user.id, self.course.id, 'openassessment', "orphan"
        )
        response = self.client.get(self.url)
        # assert we don't get a 500 error
        self.assertEqual(200, response.status_code)


@ddt.ddt
class TestInstructorDashboardPerformance(ModuleStoreTestCase, LoginEnrollmentTestCase, XssTestMixin):
    """
    Tests for the instructor dashboard from the performance point of view.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(TestInstructorDashboardPerformance, self).setUp()
        self.course = CourseFactory.create(
            grading_policy={"GRADE_CUTOFFS": {"A": 0.75, "B": 0.63, "C": 0.57, "D": 0.5}},
            display_name='<script>alert("XSS")</script>',
            default_store=ModuleStoreEnum.Type.split
        )

        self.course_mode = CourseMode(
            course_id=self.course.id,
            mode_slug=CourseMode.DEFAULT_MODE_SLUG,
            mode_display_name=CourseMode.DEFAULT_MODE.name,
            min_price=40
        )
        self.course_mode.save()
        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

    def test_spoc_gradebook_mongo_calls(self):
        """
        Test that the MongoDB cache is used in API to return grades
        """
        # prepare course structure
        course = ItemFactory.create(
            parent_location=self.course.location,
            category="course",
            display_name="Test course",
        )

        students = []
        for i in range(20):
            username = "user_%d" % i
            student = UserFactory.create(username=username)
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
            students.append(student)

        chapter = ItemFactory.create(
            parent=course,
            category='chapter',
            display_name="Chapter",
            publish_item=True,
            start=datetime.datetime(2015, 3, 1, tzinfo=UTC),
        )
        sequential = ItemFactory.create(
            parent=chapter,
            category='sequential',
            display_name="Lesson",
            publish_item=True,
            start=datetime.datetime(2015, 3, 1, tzinfo=UTC),
            metadata={'graded': True, 'format': 'Homework'},
        )
        vertical = ItemFactory.create(
            parent=sequential,
            category='vertical',
            display_name='Subsection',
            publish_item=True,
            start=datetime.datetime(2015, 4, 1, tzinfo=UTC),
        )
        for i in range(10):
            problem = ItemFactory.create(
                category="problem",
                parent=vertical,
                display_name=u"A Problem Block %d" % i,
                weight=1,
                publish_item=False,
                metadata={'rerandomize': 'always'},
            )
            for j in students:
                grade = i % 2
                StudentModuleFactory.create(
                    grade=grade,
                    max_grade=1,
                    student=j,
                    course_id=self.course.id,
                    module_state_key=problem.location
                )

        # check MongoDB calls count
        url = reverse('spoc_gradebook', kwargs={'course_id': self.course.id})
        with check_mongo_calls(9):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
