from datetime import date
from django.test import TestCase

from openedx.features.subscriptions.api.v1.serializers import UserSubscriptionSerializer
from openedx.features.subscriptions.api.v1.tests.factories import UserSubscriptionFactory


class UserSubscriptionSerializerTests(TestCase):
    """
    Tests for "UserSubscriptionSerializer" serializer.
    """

    def test_user_subscription_seriaizer(self):
        """
        Verify a validator checking non-existent courses.
        """
        user_subscription = UserSubscriptionFactory()
        self.assertEqual(
            UserSubscriptionSerializer(user_subscription).data,
            {
                'expiration_date': str(user_subscription.expiration_date),
                'max_allowed_courses': user_subscription.max_allowed_courses,
                'subscription_id': user_subscription.subscription_id,
                'subscription_type': user_subscription.subscription_type,
                'user': user_subscription.user.id,
                'course_enrollments': [],
            }
        )
