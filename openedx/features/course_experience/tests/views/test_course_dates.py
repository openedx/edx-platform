"""
Tests for course dates fragment.
"""


from datetime import datetime, timedelta

import six
from django.urls import reverse

from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

TEST_PASSWORD = 'test'


class TestCourseDatesFragmentView(ModuleStoreTestCase):
    """Tests for the course dates fragment view."""

    def setUp(self):
        super(TestCourseDatesFragmentView, self).setUp()
        with self.store.default_store(ModuleStoreEnum.Type.split):
            self.course = CourseFactory.create(
                org='edX',
                number='test',
                display_name='Test Course',
                start=datetime.now() - timedelta(days=30),
                end=datetime.now() + timedelta(days=30),
            )
        self.user = UserFactory(password=TEST_PASSWORD)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        self.dates_fragment_url = reverse(
            'openedx.course_experience.mobile_dates_fragment_view',
            kwargs={
                'course_id': six.text_type(self.course.id)
            }
        )

    def test_course_dates_fragment(self):
        response = self.client.get(self.dates_fragment_url)
        self.assertContains(response, 'Course End')

        self.client.logout()
        response = self.client.get(self.dates_fragment_url)
        self.assertEqual(response.status_code, 404)
