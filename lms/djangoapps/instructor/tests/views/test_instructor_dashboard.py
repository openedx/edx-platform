"""
Unit tests for instructor_dashboard.py.
"""
import ddt
import datetime
from mock import patch
from nose.plugins.attrib import attr
from pytz import UTC

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edxmako.shortcuts import render_to_response

from courseware.tabs import get_course_tab_list
from courseware.tests.factories import UserFactory, StudentModuleFactory
from courseware.tests.helpers import LoginEnrollmentTestCase
from instructor.views.gradebook_api import calculate_page_info

from common.test.utils import XssTestMixin
from student.tests.factories import AdminFactory, CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from shoppingcart.models import PaidCourseRegistration, Order, CourseRegCodeItem
from course_modes.models import CourseMode
from student.roles import CourseFinanceAdminRole
from student.models import CourseEnrollment


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


@attr(shard=3)
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
        self.course_mode.save()
        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})

    def get_dashboard_enrollment_message(self):
        """
        Returns expected dashboard enrollment message with link to Insights.
        """
        return 'Enrollment data is now available in <a href="http://example.com/courses/{}" ' \
               'target="_blank">Example</a>.'.format(unicode(self.course.id))

    def get_dashboard_analytics_message(self):
        """
        Returns expected dashboard demographic message with link to Insights.
        """
        return 'For analytics about your course, go to <a href="http://example.com/courses/{}" ' \
               'target="_blank">Example</a>.'.format(unicode(self.course.id))

    def test_instructor_tab(self):
        """
        Verify that the instructor tab appears for staff only.
        """
        def has_instructor_tab(user, course):
            """Returns true if the "Instructor" tab is shown."""
            request = RequestFactory().request()
            request.user = user
            tabs = get_course_tab_list(request, course)
            return len([tab for tab in tabs if tab.name == 'Instructor']) == 1

        self.assertTrue(has_instructor_tab(self.instructor, self.course))
        student = UserFactory.create()
        self.assertFalse(has_instructor_tab(student, self.course))

    def test_default_currency_in_the_html_response(self):
        """
        Test that checks the default currency_symbol ($) in the response
        """
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        response = self.client.get(self.url)
        self.assertIn('${amount}'.format(amount=total_amount), response.content)

    def test_course_name_xss(self):
        """Test that the instructor dashboard correctly escapes course names
        with script tags.
        """
        response = self.client.get(self.url)
        self.assert_no_xss(response, '<script>alert("XSS")</script>')

    @override_settings(PAID_COURSE_REGISTRATION_CURRENCY=['PKR', 'Rs'])
    def test_override_currency_settings_in_the_html_response(self):
        """
        Test that checks the default currency_symbol ($) in the response
        """
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        response = self.client.get(self.url)
        self.assertIn('{currency}{amount}'.format(currency='Rs', amount=total_amount), response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': False})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_no_enrollments(self):
        """
        Test enrollment section is hidden.
        """
        response = self.client.get(self.url)
        # no enrollment information should be visible
        self.assertNotIn('<h3 class="hd hd-3">Enrollment Information</h3>', response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': True})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_show_enrollments_data(self):
        """
        Test enrollment data is shown.
        """
        response = self.client.get(self.url)

        # enrollment information visible
        self.assertIn('<h3 class="hd hd-3">Enrollment Information</h3>', response.content)
        self.assertIn('<th scope="row">Verified</th>', response.content)
        self.assertIn('<th scope="row">Audit</th>', response.content)
        self.assertIn('<th scope="row">Honor</th>', response.content)
        self.assertIn('<th scope="row">Professional</th>', response.content)

        # dashboard link hidden
        self.assertNotIn(self.get_dashboard_enrollment_message(), response.content)

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
        self.assertNotIn('<th scope="row">Verified</th>', response.content)
        self.assertNotIn('<th scope="row">Audit</th>', response.content)
        self.assertNotIn('<th scope="row">Honor</th>', response.content)
        self.assertNotIn('<th scope="row">Professional</th>', response.content)

        # link to dashboard shown
        expected_message = self.get_dashboard_enrollment_message()
        self.assertIn(expected_message, response.content)

    @override_settings(ANALYTICS_DASHBOARD_URL='')
    @override_settings(ANALYTICS_DASHBOARD_NAME='')
    def test_dashboard_analytics_tab_not_shown(self):
        """
        Test dashboard analytics tab isn't shown if insights isn't configured.
        """
        response = self.client.get(self.url)
        analytics_section = '<li class="nav-item"><a href="" data-section="instructor_analytics">Analytics</a></li>'
        self.assertNotIn(analytics_section, response.content)

    @override_settings(ANALYTICS_DASHBOARD_URL='http://example.com')
    @override_settings(ANALYTICS_DASHBOARD_NAME='Example')
    def test_dashboard_analytics_points_at_insights(self):
        """
        Test analytics dashboard message is shown
        """
        response = self.client.get(self.url)
        analytics_section = '<li class="nav-item"><a href="" data-section="instructor_analytics">Analytics</a></li>'
        self.assertIn(analytics_section, response.content)

        # link to dashboard shown
        expected_message = self.get_dashboard_analytics_message()
        self.assertIn(expected_message, response.content)

    def add_course_to_user_cart(self, cart, course_key):
        """
        adding course to user cart
        """
        reg_item = PaidCourseRegistration.add_to_order(cart, course_key)
        return reg_item

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_PAID_COURSE_REGISTRATION': True})
    def test_total_credit_cart_sales_amount(self):
        """
        Test to check the total amount for all the credit card purchases.
        """
        student = UserFactory.create()
        self.client.login(username=student.username, password="test")
        student_cart = Order.get_cart_for_user(student)
        item = self.add_course_to_user_cart(student_cart, self.course.id)
        resp = self.client.post(reverse('shoppingcart.views.update_user_cart'), {'ItemId': item.id, 'qty': 4})
        self.assertEqual(resp.status_code, 200)
        student_cart.purchase()

        self.client.login(username=self.instructor.username, password="test")
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        single_purchase_total = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        bulk_purchase_total = CourseRegCodeItem.get_total_amount_of_purchased_item(self.course.id)
        total_amount = single_purchase_total + bulk_purchase_total
        response = self.client.get(self.url)
        self.assertIn('{currency}{amount}'.format(currency='$', amount=total_amount), response.content)

    @ddt.data(
        (True, True, True),
        (True, False, False),
        (True, None, False),
        (False, True, False),
        (False, False, False),
        (False, None, False),
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

            self.assertEquals(
                expected_result,
                'CCX Coaches are able to create their own Custom Courses based on this course' in response.content
            )

    def test_grade_cutoffs(self):
        """
        Verify that grade cutoffs are displayed in the correct order.
        """
        response = self.client.get(self.url)
        self.assertIn('D: 0.5, C: 0.57, B: 0.63, A: 0.75', response.content)

    @patch('instructor.views.gradebook_api.MAX_STUDENTS_PER_PAGE_GRADE_BOOK', 2)
    def test_calculate_page_info(self):
        page = calculate_page_info(offset=0, total_students=2)
        self.assertEqual(page["offset"], 0)
        self.assertEqual(page["page_num"], 1)
        self.assertEqual(page["next_offset"], None)
        self.assertEqual(page["previous_offset"], None)
        self.assertEqual(page["total_pages"], 1)

    @patch('instructor.views.gradebook_api.render_to_response', intercept_renderer)
    @patch('instructor.views.gradebook_api.MAX_STUDENTS_PER_PAGE_GRADE_BOOK', 1)
    def test_spoc_gradebook_pages(self):
        for i in xrange(2):
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
        self.assertEqual(len(response.mako_context['students']), 1)  # pylint: disable=no-member


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
        for i in xrange(20):
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
        for i in xrange(10):
            problem = ItemFactory.create(
                category="problem",
                parent=vertical,
                display_name="A Problem Block %d" % i,
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
        with check_mongo_calls(7):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
