# -*- coding: utf-8 -*-
"""Tests for the change enrollment step of the pipeline. """
from collections import namedtuple

import datetime
import unittest
import ddt
import pytz
from third_party_auth import pipeline
from shoppingcart.models import Order, PaidCourseRegistration  # pylint: disable=import-error
from social.apps.django_app import utils as social_utils
from django.conf import settings
from django.contrib.sessions.backends import cache
from django.test import RequestFactory
from django.test.utils import override_settings
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseModeFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.user_api.models import UserOrgTag


THIRD_PARTY_AUTH_CONFIGURED = (
    settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH') and
    getattr(settings, 'THIRD_PARTY_AUTH', {})
)


@unittest.skipUnless(THIRD_PARTY_AUTH_CONFIGURED, "Third party auth must be configured")
@ddt.ddt
class PipelineEnrollmentTest(ModuleStoreTestCase):
    """Test that the pipeline auto-enrolls students upon successful authentication. """

    BACKEND_NAME = "google-oauth2"

    def setUp(self):
        """Create a test course and user. """
        super(PipelineEnrollmentTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()

    @ddt.data(
        ([], "honor", u"False", u"False"),
        (["honor", "verified", "audit"], "honor", u"True", u"True"),
        (["professional"], None, u"Fålsœ", u"False")
    )
    @ddt.unpack
    def test_auto_enroll_step(self, course_modes, enrollment_mode, email_opt_in, email_opt_in_result):
        # Create the course modes for the test case
        for mode_slug in course_modes:
            CourseModeFactory.create(
                course_id=self.course.id,
                mode_slug=mode_slug,
                mode_display_name=mode_slug.capitalize()
            )

        # Simulate the pipeline step, passing in a course ID
        # to indicate that the user was trying to enroll
        # when they started the auth process.
        strategy = self._fake_strategy()
        strategy.session_set('enroll_course_id', unicode(self.course.id))
        strategy.session_set('email_opt_in', email_opt_in)

        result = pipeline.change_enrollment(strategy, 1, user=self.user)  # pylint: disable=assignment-from-no-return,redundant-keyword-arg
        self.assertEqual(result, {})

        # Check that the user was or was not enrolled
        # (this will vary based on the course mode)
        if enrollment_mode is not None:
            actual_mode, is_active = CourseEnrollment.enrollment_mode_for_user(self.user, self.course.id)
            self.assertTrue(is_active)
            self.assertEqual(actual_mode, enrollment_mode)
        else:
            self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

        # Check that the Email Opt In option was set
        tag = UserOrgTag.objects.get(user=self.user)
        self.assertIsNotNone(tag)
        self.assertEquals(tag.value, email_opt_in_result)

    def test_add_white_label_to_cart(self):
        # Create a white label course (honor with a minimum price)
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug="honor",
            mode_display_name="Honor",
            min_price=100
        )

        # Simulate the pipeline step for enrolling in this course
        strategy = self._fake_strategy()
        strategy.session_set('enroll_course_id', unicode(self.course.id))
        result = pipeline.change_enrollment(strategy, 1, user=self.user)  # pylint: disable=assignment-from-no-return,redundant-keyword-arg
        self.assertEqual(result, {})

        # Expect that the uesr is NOT enrolled in the course
        # because the user has not yet paid
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

        # Expect that the course was added to the shopping cart
        cart = Order.get_cart_for_user(self.user)
        self.assertTrue(cart.has_items(PaidCourseRegistration))
        order_item = PaidCourseRegistration.objects.get(order=cart)
        self.assertEqual(order_item.course_id, self.course.id)

    def test_auto_enroll_not_accessible(self):
        # Set the course open date in the future
        tomorrow = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=1)
        self.course.enrollment_start = tomorrow
        self.update_course(self.course, self.user.id)

        # Finish authentication and try to auto-enroll
        # This should fail silently, with no exception
        strategy = self._fake_strategy()
        strategy.session_set('enroll_course_id', unicode(self.course.id))
        result = pipeline.change_enrollment(strategy, 1, user=self.user)  # pylint: disable=assignment-from-no-return,redundant-keyword-arg
        self.assertEqual(result, {})

        # Verify that we were NOT enrolled
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    def test_no_course_id_skips_enroll(self):
        strategy = self._fake_strategy()
        result = pipeline.change_enrollment(strategy, 1, user=self.user)  # pylint: disable=assignment-from-no-return,redundant-keyword-arg
        self.assertEqual(result, {})
        self.assertFalse(CourseEnrollment.is_enrolled(self.user, self.course.id))

    def test_url_creation(self):
        strategy = self._fake_strategy()
        strategy.session_set('enroll_course_id', unicode(self.course.id))
        strategy.session_set('email_opt_in', u"False")
        backend = namedtuple('backend', 'name')
        backend.name = self.BACKEND_NAME
        response = pipeline.ensure_user_information(
            strategy=strategy,
            pipeline_index=1,
            details=None,
            response=None,
            uid=None,
            is_register=True,
            backend=backend
        )
        self.assertIsNotNone(response)
        self.assertEquals(response.status_code, 302)

        # Get the location
        _, url = response._headers['location']  # pylint: disable=W0212
        self.assertIn("email_opt_in=False", url)
        self.assertIn("course_id=".format(id=unicode(self.course.id)), url)

    def _fake_strategy(self):
        """Simulate the strategy passed to the pipeline step. """
        request = RequestFactory().get(pipeline.get_complete_url(self.BACKEND_NAME))
        request.user = self.user
        request.session = cache.SessionStore()

        return social_utils.load_strategy(
            backend=self.BACKEND_NAME, request=request
        )
