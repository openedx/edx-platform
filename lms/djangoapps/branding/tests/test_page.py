"""
Tests for branding page
"""

import datetime

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from django.test.utils import override_settings
from django.test.client import RequestFactory

from pytz import UTC
from mock import patch, Mock
from nose.plugins.attrib import attr
from edxmako.shortcuts import render_to_response

from branding.views import index
from edxmako.tests import mako_middleware_process_request
import student.views
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from django.core.urlresolvers import reverse
from courseware.tests.helpers import LoginEnrollmentTestCase

from util.milestones_helpers import (
    seed_milestone_relationship_types,
    set_prerequisite_courses,
)

FEATURES_WITH_STARTDATE = settings.FEATURES.copy()
FEATURES_WITH_STARTDATE['DISABLE_START_DATES'] = False
FEATURES_WO_STARTDATE = settings.FEATURES.copy()
FEATURES_WO_STARTDATE['DISABLE_START_DATES'] = True


def mock_render_to_response(*args, **kwargs):
    """
    Mock the render_to_response function
    """
    return render_to_response(*args, **kwargs)

RENDER_MOCK = Mock(side_effect=mock_render_to_response)


@attr('shard_1')
class AnonymousIndexPageTest(ModuleStoreTestCase):
    """
    Tests that anonymous users can access the '/' page,  Need courses with start date
    """
    def setUp(self):
        super(AnonymousIndexPageTest, self).setUp()
        self.factory = RequestFactory()
        self.course = CourseFactory.create(
            days_early_for_beta=5,
            enrollment_start=datetime.datetime.now(UTC) + datetime.timedelta(days=3),
            user_id=self.user.id,
        )

    @override_settings(FEATURES=FEATURES_WITH_STARTDATE)
    def test_none_user_index_access_with_startdate_fails(self):
        """
        This is a regression test for a bug where the incoming user is
        anonymous and start dates are being checked.  It replaces a previous
        test as it solves the issue in a different way
        """
        request = self.factory.get('/')
        request.user = AnonymousUser()

        mako_middleware_process_request(request)
        student.views.index(request)

    @override_settings(FEATURES=FEATURES_WITH_STARTDATE)
    def test_anon_user_with_startdate_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @override_settings(FEATURES=FEATURES_WO_STARTDATE)
    def test_anon_user_no_startdate_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_allow_x_frame_options(self):
        """
        Check the x-frame-option response header
        """

        # check to see that the default setting is to ALLOW iframing
        resp = self.client.get('/')
        self.assertEquals(resp['X-Frame-Options'], 'ALLOW')

    @override_settings(X_FRAME_OPTIONS='DENY')
    def test_deny_x_frame_options(self):
        """
        Check the x-frame-option response header
        """

        # check to see that the override value is honored
        resp = self.client.get('/')
        self.assertEquals(resp['X-Frame-Options'], 'DENY')

    def test_edge_redirect_to_login(self):
        """
        Test edge homepage redirect to lms login.
        """

        request = self.factory.get('/')
        request.user = AnonymousUser()

        # HTTP Host changed to edge.
        request.META["HTTP_HOST"] = "edge.edx.org"
        response = index(request)

        # Response should be instance of HttpResponseRedirect.
        self.assertIsInstance(response, HttpResponseRedirect)
        # Location should be "/login".
        self.assertEqual(response._headers.get("location")[1], "/login")  # pylint: disable=protected-access


@attr('shard_1')
class PreRequisiteCourseCatalog(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test to simulate and verify fix for disappearing courses in
    course catalog when using pre-requisite courses
    """
    @patch.dict(settings.FEATURES, {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def setUp(self):
        super(PreRequisiteCourseCatalog, self).setUp()

        seed_milestone_relationship_types()

    @patch.dict(settings.FEATURES, {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_course_with_prereq(self):
        """
        Simulate having a course which has closed enrollments that has
        a pre-req course
        """
        pre_requisite_course = CourseFactory.create(
            org='edX',
            course='900',
            display_name='pre requisite course',
        )

        pre_requisite_courses = [unicode(pre_requisite_course.id)]

        # for this failure to occur, the enrollment window needs to be in the past
        course = CourseFactory.create(
            org='edX',
            course='1000',
            display_name='course that has pre requisite',
            # closed enrollment
            enrollment_start=datetime.datetime(2013, 1, 1),
            enrollment_end=datetime.datetime(2014, 1, 1),
            start=datetime.datetime(2013, 1, 1),
            end=datetime.datetime(2030, 1, 1),
            pre_requisite_courses=pre_requisite_courses,
        )
        set_prerequisite_courses(course.id, pre_requisite_courses)

        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

        # make sure both courses are visible in the catalog
        self.assertIn('pre requisite course', resp.content)
        self.assertIn('course that has pre requisite', resp.content)


@attr('shard_1')
class IndexPageCourseCardsSortingTests(ModuleStoreTestCase):
    """
    Test for Index page course cards sorting
    """
    def setUp(self):
        super(IndexPageCourseCardsSortingTests, self).setUp()
        self.starting_later = CourseFactory.create(
            org='MITx',
            number='1000',
            display_name='Starting later, Announced later',
            metadata={
                'start': datetime.datetime.now(UTC) + datetime.timedelta(days=4),
                'announcement': datetime.datetime.now(UTC) + datetime.timedelta(days=3),
            }
        )
        self.starting_earlier = CourseFactory.create(
            org='MITx',
            number='1001',
            display_name='Starting earlier, Announced earlier',
            metadata={
                'start': datetime.datetime.now(UTC) + datetime.timedelta(days=2),
                'announcement': datetime.datetime.now(UTC) + datetime.timedelta(days=1),
            }
        )
        self.course_with_default_start_date = CourseFactory.create(
            org='MITx',
            number='1002',
            display_name='Tech Beta Course',
        )
        self.factory = RequestFactory()

    @patch('student.views.render_to_response', RENDER_MOCK)
    @patch('courseware.views.render_to_response', RENDER_MOCK)
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_COURSE_DISCOVERY': False})
    def test_course_discovery_off(self):
        """
        Asserts that the Course Discovery UI elements follow the
        feature flag settings
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # assert that the course discovery UI is not present
        self.assertNotIn('Search for a course', response.content)

        # check the /courses view
        response = self.client.get(reverse('branding.views.courses'))
        self.assertEqual(response.status_code, 200)

        # assert that the course discovery UI is not present
        self.assertNotIn('Search for a course', response.content)
        self.assertNotIn('<aside aria-label="Refine Your Search" class="search-facets phone-menu">', response.content)

        # make sure we have the special css class on the section
        self.assertIn('<div class="courses no-course-discovery"', response.content)

    @patch('student.views.render_to_response', RENDER_MOCK)
    @patch('courseware.views.render_to_response', RENDER_MOCK)
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_COURSE_DISCOVERY': True})
    def test_course_discovery_on(self):
        """
        Asserts that the Course Discovery UI elements follow the
        feature flag settings
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        # assert that the course discovery UI is not present
        self.assertIn('Search for a course', response.content)

        # check the /courses view
        response = self.client.get(reverse('branding.views.courses'))
        self.assertEqual(response.status_code, 200)

        # assert that the course discovery UI is present
        self.assertIn('Search for a course', response.content)
        self.assertIn('<aside aria-label="Refine Your Search" class="search-facets phone-menu">', response.content)
        self.assertIn('<div class="courses"', response.content)

    @patch('student.views.render_to_response', RENDER_MOCK)
    @patch('courseware.views.render_to_response', RENDER_MOCK)
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_COURSE_DISCOVERY': False})
    def test_course_cards_sorted_by_default_sorting(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        ((template, context), _) = RENDER_MOCK.call_args  # pylint: disable=unpacking-non-sequence
        self.assertEqual(template, 'index.html')

        # by default the courses will be sorted by their creation dates, earliest first.
        self.assertEqual(context['courses'][0].id, self.starting_earlier.id)
        self.assertEqual(context['courses'][1].id, self.starting_later.id)
        self.assertEqual(context['courses'][2].id, self.course_with_default_start_date.id)

        # check the /courses view
        response = self.client.get(reverse('branding.views.courses'))
        self.assertEqual(response.status_code, 200)
        ((template, context), _) = RENDER_MOCK.call_args  # pylint: disable=unpacking-non-sequence
        self.assertEqual(template, 'courseware/courses.html')

        # by default the courses will be sorted by their creation dates, earliest first.
        self.assertEqual(context['courses'][0].id, self.starting_earlier.id)
        self.assertEqual(context['courses'][1].id, self.starting_later.id)
        self.assertEqual(context['courses'][2].id, self.course_with_default_start_date.id)

    @patch('student.views.render_to_response', RENDER_MOCK)
    @patch('courseware.views.render_to_response', RENDER_MOCK)
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_COURSE_SORTING_BY_START_DATE': False})
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_COURSE_DISCOVERY': False})
    def test_course_cards_sorted_by_start_date_disabled(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        ((template, context), _) = RENDER_MOCK.call_args  # pylint: disable=unpacking-non-sequence
        self.assertEqual(template, 'index.html')

        # now the courses will be sorted by their announcement dates.
        self.assertEqual(context['courses'][0].id, self.starting_later.id)
        self.assertEqual(context['courses'][1].id, self.starting_earlier.id)
        self.assertEqual(context['courses'][2].id, self.course_with_default_start_date.id)

        # check the /courses view as well
        response = self.client.get(reverse('branding.views.courses'))
        self.assertEqual(response.status_code, 200)
        ((template, context), _) = RENDER_MOCK.call_args  # pylint: disable=unpacking-non-sequence
        self.assertEqual(template, 'courseware/courses.html')

        # now the courses will be sorted by their announcement dates.
        self.assertEqual(context['courses'][0].id, self.starting_later.id)
        self.assertEqual(context['courses'][1].id, self.starting_earlier.id)
        self.assertEqual(context['courses'][2].id, self.course_with_default_start_date.id)
