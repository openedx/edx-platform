from datetime import date, datetime, timedelta
import ddt

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.subscriptions.models import UserSubscription, UserSubscriptionHistory
from openedx.features.subscriptions.api.v1.tests.factories import UserSubscriptionFactory
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def _get_course_enrollments(number_of_enrollments, user):
    """
    Get required number of course_enrollments.
    """
    return [
        CourseEnrollmentFactory(
            user=user,
            is_active=True,
            mode='honor',
            course_id=CourseFactory(start=datetime.now() - timedelta(days=1)).id
        ) for index in range(number_of_enrollments)
    ]


@ddt.ddt
class UserSubscriptionsTests(ModuleStoreTestCase):
    """
    Tests for "UserSubscription" model.
    """
    def setUp(self):
        super(UserSubscriptionsTests, self).setUp()
        self.user = UserFactory()
        self.site = SiteFactory()

    @ddt.unpack
    @ddt.data(
        # Limited access subscriptions
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, None, True),
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, 3, True),
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, 4, False),
        (3, date.today() - timedelta(days=1), UserSubscription.LIMITED_ACCESS, 1, None, False),
        # Full access(Courses) subscriptions
        (3, date.today() + timedelta(days=1), UserSubscription.FULL_ACCESS_COURSES, 1, None, True),
        (3, date.today() - timedelta(days=1), UserSubscription.FULL_ACCESS_COURSES, 1, None, False),
        # Full access(Time period) subscriptions
        (3, None, UserSubscription.FULL_ACCESS_TIME_PERIOD, 1, None, True),
        (3, None, UserSubscription.FULL_ACCESS_TIME_PERIOD, 1, 4, False),
        # Lifetime access subscription
        (None, None, UserSubscription.LIFETIME_ACCESS, 1, None, True),
    )
    def test_is_active(self, max_allowed_courses, expiration_date, subscription_type, subscription_id, number_of_enrollments, expected_value):
        """
        Verify the method properly maps mode slugs to display names.
        """
        user_subscription = UserSubscriptionFactory(
            max_allowed_courses=max_allowed_courses,
            expiration_date=expiration_date,
            subscription_type=subscription_type,
            subscription_id=subscription_id,
            user=self.user,
            site=self.site
        )
        if number_of_enrollments:
            course_enrollments = _get_course_enrollments(number_of_enrollments, self.user)
            for enrollment in course_enrollments:
                user_subscription.course_enrollments.add(enrollment)

        self.assertEqual(user_subscription.is_active, expected_value)

    @ddt.unpack
    @ddt.data(
        # Limited access subscriptions
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, None, True),
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, 2, True),
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, 3, False),
        (3, date.today() - timedelta(days=1), UserSubscription.LIMITED_ACCESS, 1, None, False),
        # Full access(Courses) subscriptions
        (3, date.today() + timedelta(days=1), UserSubscription.FULL_ACCESS_COURSES, 1, None, True),
        (3, date.today() - timedelta(days=1), UserSubscription.FULL_ACCESS_COURSES, 1, None, False),
        # Full access(Time period) subscriptions
        (3, None, UserSubscription.FULL_ACCESS_TIME_PERIOD, 1, None, True),
        (3, None, UserSubscription.FULL_ACCESS_TIME_PERIOD, 1, 3, False),
        # Lifetime access subscription
        (None, None, UserSubscription.LIFETIME_ACCESS, 1, None, True),
    )
    def test_is_valid(self, max_allowed_courses, expiration_date, subscription_type, subscription_id, number_of_enrollments, expected_value):
        """
        Verify the method returns the slug if it has no known mapping.
        """
        user_subscription = UserSubscriptionFactory(
            max_allowed_courses=max_allowed_courses,
            expiration_date=expiration_date,
            subscription_type=subscription_type,
            subscription_id=subscription_id,
            user=self.user
        )
        if number_of_enrollments:
            course_enrollments = _get_course_enrollments(number_of_enrollments, self.user)
            for enrollment in course_enrollments:
                user_subscription.course_enrollments.add(enrollment)

        self.assertEqual(user_subscription.is_valid, expected_value)

    @ddt.unpack
    @ddt.data(
        # Limited access subscriptions
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, None, True),
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, 2, True),
        (3, date.today(), UserSubscription.LIMITED_ACCESS, 1, 3, False),
        (3, date.today() - timedelta(days=1), UserSubscription.LIMITED_ACCESS, 1, None, False),
        # Full access(Courses) subscriptions
        (3, date.today() + timedelta(days=1), UserSubscription.FULL_ACCESS_COURSES, 1, None, True),
        (3, date.today() - timedelta(days=1), UserSubscription.FULL_ACCESS_COURSES, 1, None, False),
        # Full access(Time period) subscriptions
        (3, None, UserSubscription.FULL_ACCESS_TIME_PERIOD, 1, None, True),
        (3, None, UserSubscription.FULL_ACCESS_TIME_PERIOD, 1, 3, False),
        # Lifetime access subscription
        (None, None, UserSubscription.LIFETIME_ACCESS, 1, None, True),
    )
    def test_get_valid_subscription(self, max_allowed_courses, expiration_date, subscription_type, subscription_id, number_of_enrollments, expected_value):
        """
        Verify that get_valid_subscription returns valid subscription correctly.
        """
        user_subscription = UserSubscriptionFactory(
            max_allowed_courses=max_allowed_courses,
            expiration_date=expiration_date,
            subscription_type=subscription_type,
            subscription_id=subscription_id,
            user=self.user,
            site=self.site
        )
        if number_of_enrollments:
            course_enrollments = _get_course_enrollments(number_of_enrollments, self.user)
            for enrollment in course_enrollments:
                user_subscription.course_enrollments.add(enrollment)

        self.assertEqual(UserSubscription.get_valid_subscriptions(self.user.id).count() == 1, expected_value)
        self.assertEqual(bool(UserSubscription.get_valid_subscriptions(self.user.id)), expected_value)

    def test_user_subscription_post_update_receiver(self):
        """
        Test that "UserSubscription" history is correctly maintained on update.
        """
        user_subscription_history = UserSubscriptionHistory.objects.filter(
            site=self.site
        )
        self.assertEqual(len(user_subscription_history), 0)
        user_subscription = UserSubscriptionFactory(
            max_allowed_courses=2,
            expiration_date=date.today(),
            subscription_type=UserSubscription.LIMITED_ACCESS,
            subscription_id=1,
            user=self.user,
            site=self.site
        )
        user_subscription_history = UserSubscriptionHistory.objects.filter(
            site=user_subscription.site,
        )
        self.assertEqual(len(user_subscription_history), 2)
        user_subscription.max_allowed_courses = 3
        user_subscription.save()

        user_subscription_history = UserSubscriptionHistory.objects.filter(
            site=user_subscription.site,
        ).all()

        self.assertEqual(len(user_subscription_history), 3)
