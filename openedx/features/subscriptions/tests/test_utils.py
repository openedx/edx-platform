"""
Tests for subscription utility methods.
"""
from datetime import date, timedelta
from waffle.testutils import override_switch

from django.conf import settings

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.subscriptions.api.v1.tests.factories import UserSubscriptionFactory
from openedx.features.subscriptions.models import UserSubscription
from openedx.features.subscriptions.utils import (
    get_subscription_renew_url,
    is_course_accessible_with_subscription,
    track_subscription_enrollment,
)
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

class UtilsTests(ModuleStoreTestCase):
    """
    Subscription utility methods tests.
    """
    def setUp(self):
        """
        Prepare data for tests.
        """
        super(UtilsTests, self).setUp()
        self.site = SiteFactory()
        self.course = CourseFactory()
        self.user = UserFactory()
        CourseEnrollment.enroll(self.user, self.course.id)

    def test_track_subscription_enrollment(self):
        """
        Test method tracks enrollment through a subscription correctly.
        """
        user_subscription = UserSubscriptionFactory(
            site=self.site,
            user=self.user
        )
        track_subscription_enrollment(user_subscription.subscription_id, self.user, self.course.id, self.site)
        self.assertEqual(user_subscription.course_enrollments.count(), 1)

    @override_switch(settings.ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=False)
    def test_is_course_accessible_with_subscription_with_waffle_switch_off(self):
        """
        Test method correctly checks access to a subscription if subscription waffle switch is disabled.
        """
        self.assertTrue(is_course_accessible_with_subscription(self.user, self.course))

    @override_switch(settings.ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=True)
    def test_is_course_accessible_with_subscription_with_waffle_switch_on(self):
        """
        Test method correctly checks access to a subscription if subscription waffle switch is enabled.
        """
        self.client.logout()
        self.assertTrue(is_course_accessible_with_subscription(self.user, self.course))

    @override_switch(settings.ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=True)
    def test_is_course_accessible_with_subscription_with_no_subscription_course_enrollments(self):
        """
        Test method correctly checks access to a subscription if a course is not purchased through a subscription.
        """
        UserSubscriptionFactory(
            site=self.site,
            user=self.user
        )
        self.assertTrue(is_course_accessible_with_subscription(self.user, self.course))

    @override_switch(settings.ENABLE_SUBSCRIPTIONS_ON_RUNTIME_SWITCH, active=True)
    def test_is_course_accessible_with_subscription_with_inactive_subscription_course_enrollments(self):
        """
        Test method correctly checks access to a user is enrolled through an expired subscription.
        """
        user_subscription = UserSubscriptionFactory(
            site=self.site,
            user=self.user
        )
        track_subscription_enrollment(user_subscription.subscription_id, self.user, self.course.id, self.site)
        user_subscription.expiration_date = date.today() - timedelta(days=1)
        user_subscription.save()
        self.assertFalse(is_course_accessible_with_subscription(self.user, self.course))

    def test_get_subscription_renew_url(self):
        """
        Test method return correct subscription renew url.
        """
        test_ecommerce_api = 'http://example.com/api/v2'
        self.assertEqual(get_subscription_renew_url(1, self.user, test_ecommerce_api), '')
        lifetime_subscription = UserSubscriptionFactory(
            subscription_type=UserSubscription.LIMITED_ACCESS
        )
        self.assertEqual(get_subscription_renew_url(
            lifetime_subscription.subscription_id,
            self.user,
            test_ecommerce_api
        ), '')
        full_access_courses_subscription = UserSubscriptionFactory(
            subscription_type=UserSubscription.FULL_ACCESS_COURSES,
            user=self.user
        )
        subscription_renew_url = 'api/v2/subscriptions/renew_subscription/?subscription_id={subscription_id}'.format(
            subscription_id=full_access_courses_subscription.subscription_id
        )
        self.assertEqual(
            get_subscription_renew_url(
                full_access_courses_subscription.subscription_id,
                self.user,
                test_ecommerce_api
            ),
            subscription_renew_url
        )
