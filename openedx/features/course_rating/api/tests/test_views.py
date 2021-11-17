"""
Unit tests for course rating api views.
"""
from unittest import TestCase
import pytest

from django.conf import settings
from django.contrib.auth.models import Group
from django.test.client import Client, RequestFactory
from django.urls import reverse
from rest_framework import status

from openedx.features.edly.tests.factories import EdlyUserFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.course_rating.tests.factories import USER_PASSWORD, CourseRatingFactory


pytestmark = pytest.mark.django_db


class CourseRatingViewSet(TestCase):
    """
    Unit tests for CourseRatingViewSet View.
    """

    def setUp(self):
        """
        Setup data for test cases.
        """
        self.user = EdlyUserFactory(password=USER_PASSWORD)
        self.request = RequestFactory()
        self.site = SiteFactory()
        self.request.site = self.site
        self.request.user = self.user
        self.client = Client(SERVER_NAME=self.request.site.domain)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.course = 'course-v1:edX+DemoX+Demo_Course'
        self.comment = 'Dummy test comment'
        self.user_course_rating = CourseRatingFactory(user=self.user, comment=self.comment, rating=5)
        self.url = reverse('course_rating_api:course_rating-list')
        super(CourseRatingViewSet, self).setUp()

    def test_without_permission(self):
        """
        Verify permission is required when accessing the endpoint.
        """
        self.client.logout()
        params = {
            'course': self.course,
            'user': self.user.id,
            'comment': self.comment,
            'rating': 5,
        }

        request = RequestFactory()
        request.site = SiteFactory()
        client = Client(SERVER_NAME=request.site.domain)
        response = client.post(self.url, params)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_request_data_authentication(self):
        """
        Verify authentication for request data.
        """
        response = self.client.post(self.url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_course_rating_creation(self):
        """
        Verify post request data.
        """
        params = {
            'course': self.course,
            'user': self.user.id,
            'comment': self.comment,
            'rating': 5,
        }
        response = self.client.post(self.url, params)
        assert response.status_code == status.HTTP_201_CREATED

    def test_course_rating_update(self):
        """
        Verify course rating update request is value only for admin users.
        """
        edly_user = EdlyUserFactory(password=USER_PASSWORD)
        params = {
            'course': self.course,
            'user': edly_user.id,
            'comment': 'This test new comment',
            'rating': 5,
        }
        response = self.client.post(self.url, params)
        assert response.status_code == status.HTTP_201_CREATED

        api_url = reverse(
            'course_rating_api:course_rating-detail',
            kwargs={
                'pk': response.json()['id']
            }
        )
        response = self.client.put(api_url, params, content_type='application/json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

        params['rating'] = 4
        edly_user = EdlyUserFactory(password=USER_PASSWORD, is_staff=True, is_superuser=True)
        request = RequestFactory()
        request.site = self.site
        request.user = edly_user
        client = Client(SERVER_NAME=request.site.domain)
        client.login(username=edly_user.username, password=USER_PASSWORD)

        response = client.put(api_url, params, content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['rating'] == params['rating']

        params['is_approved'] = True
        edly_user = EdlyUserFactory(password=USER_PASSWORD)
        request = RequestFactory()
        request.site = self.site
        request.user = edly_user
        edly_wp_admin_user_group, __ = Group.objects.get_or_create(name=settings.EDLY_WP_ADMIN_USERS_GROUP)
        request.user.groups.add(edly_wp_admin_user_group)
        client = Client(SERVER_NAME=request.site.domain)
        client.login(username=edly_user.username, password=USER_PASSWORD)
        response = client.put(api_url, params, content_type='application/json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['is_approved'] == params['is_approved']


class CourseAverageRatingAPIView(TestCase):
    """
    Unit tests for CourseAverageRatingAPIView View.
    """

    def setUp(self):
        """
        Setup data for test cases.
        """
        self.user = EdlyUserFactory(password=USER_PASSWORD)
        self.request = RequestFactory()
        self.site = SiteFactory()
        self.request.site = self.site
        self.request.user = self.user
        self.client = Client(SERVER_NAME=self.request.site.domain)
        self.client.login(username=self.user.username, password=USER_PASSWORD)
        self.course = 'course-v1:edX+DemoX+Demo_Course'
        self.comment = 'Dummy test comment'
        self.user_course_rating = CourseRatingFactory(user=self.user, comment=self.comment, rating=5)
        self.url = reverse('course_rating_api:course_average_rating')
        super(CourseAverageRatingAPIView, self).setUp()

    def test_request_data_(self):
        """
        Verify request data.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
