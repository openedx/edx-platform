"""
Test cases for Batch Notification Audience
"""
from django.contrib.auth import get_user_model
from unittest.mock import Mock
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.notifications.batch_notification_audience import BatchNotificationAudience
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


User = get_user_model()


class TestBatchNotificationAudience(ModuleStoreTestCase):
    """
    Tests Batch Notification Audience
    """
    CREATE_USER = False

    def setUp(self):
        """
        Creates user and setup test case
        """
        super().setUp()
        self.total = 20
        for i in range(self.total):
            UserFactory.create(username=f'user-{i}', email=f'user-{i}@example.com')

    def test_batch_generation(self):
        """
        Test that audience is generated in batches
        """
        callback = Mock()
        batch = BatchNotificationAudience(batch_size=10, callback=callback)
        batch.add_queryset(User.objects.all().values_list('id'))
        batch.generate_audience()
        assert callback.call_count == 2
