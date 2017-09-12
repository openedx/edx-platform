"""
Test serialization of completion data.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from datetime import datetime, timedelta

from django.test.utils import override_settings
from oauth2_provider import models as dot_models
from rest_framework.test import APIClient

from opaque_keys.edx.keys import UsageKey
from progress import models

from student.tests.factories import AdminFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory


def _create_oauth2_token(user):
    """
    Create an OAuth2 Access Token for the specified user,
    to test OAuth2-based API authentication

    Returns the token as a string.
    """
    # Use django-oauth-toolkit (DOT) models to create the app and token:
    dot_app = dot_models.Application.objects.create(
        name='test app',
        user=UserFactory.create(),
        client_type='confidential',
        authorization_grant_type='authorization-code',
        redirect_uris='http://none.none'
    )
    dot_access_token = dot_models.AccessToken.objects.create(
        user=user,
        application=dot_app,
        expires=datetime.utcnow() + timedelta(weeks=1),
        scope='read',
        token='s3cur3t0k3n12345678901234567890'
    )
    return dot_access_token.token


@override_settings(STUDENT_GRADEBOOK=True)
class CompletionViewTestCase(SharedModuleStoreTestCase):
    """
    Test that the CompletionView renders completion data properly.

    Ensure that it handles authorization as well.
    """

    @classmethod
    def setUpClass(cls):
        super(CompletionViewTestCase, cls).setUpClass()
        cls.course = ToyCourseFactory.create()

    def setUp(self):
        super(CompletionViewTestCase, self).setUp()
        self.test_user = UserFactory.create()
        self.mark_completions()
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)

    def mark_completions(self):
        """
        Create completion data to test against.
        """
        models.CourseModuleCompletion.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            content_id=UsageKey.from_string('i4x://edX/toy/video/sample_video').map_into_course(self.course.id),
        )
        models.StudentProgress.objects.create(
            user=self.test_user,
            course_id=self.course.id,
            completions=1,
        )

    def test_list_view(self):
        response = self.client.get('/api/completion/v0/course/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': 1, 'previous': None, 'num_pages': 1, 'next': None},
            'results': [
                {
                    'course_key': 'edX/toy/2012_Fall',
                    'completion': {
                        'earned': 1.0,
                        'possible': 12.0,
                        'ratio': 1 / 12,
                    },
                }
            ],
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

    def test_list_view_oauth2(self):
        """
        Test the list view using OAuth2 Authentication
        """
        url = '/api/completion/v0/course/'
        # Try with no authentication:
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # Now, try with a valid token header:
        token = _create_oauth2_token(self.test_user)
        response = self.client.get(url, HTTP_AUTHORIZATION="Bearer {0}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['completion']['earned'], 1.0)  # pylint: disable=no-member

    def test_list_view_with_sequentials(self):
        response = self.client.get('/api/completion/v0/course/?requested_fields=sequential')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': 1, 'previous': None, 'num_pages': 1, 'next': None},
            'results': [
                {
                    'course_key': 'edX/toy/2012_Fall',
                    'completion': {
                        'earned': 1.0,
                        'possible': 12.0,
                        'ratio': 1 / 12,
                    },
                    'sequential': [
                        {
                            'course_key': u'edX/toy/2012_Fall',
                            'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                            'completion': {'earned': 1.0, 'possible': 5.0, 'ratio': 0.2},
                        },
                    ]
                }
            ],
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

    def test_detail_view(self):
        response = self.client.get('/api/completion/v0/course/edX/toy/2012_Fall/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'edX/toy/2012_Fall',
            'completion': {
                'earned': 1.0,
                'possible': 12.0,
                'ratio': 1 / 12,
            },
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

    def test_detail_view_oauth2(self):
        """
        Test the detail view using OAuth2 Authentication
        """
        url = '/api/completion/v0/course/edX/toy/2012_Fall/'
        # Try with no authentication:
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # Now, try with a valid token header:
        token = _create_oauth2_token(self.test_user)
        response = self.client.get(url, HTTP_AUTHORIZATION="Bearer {0}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['completion']['earned'], 1.0)  # pylint: disable=no-member

    def test_detail_view_with_sequentials(self):
        response = self.client.get('/api/completion/v0/course/edX/toy/2012_Fall/?requested_fields=sequential')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'edX/toy/2012_Fall',
            'completion': {
                'earned': 1.0,
                'possible': 12.0,
                'ratio': 1 / 12,
            },
            'sequential': [
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                    'completion': {'earned': 1.0, 'possible': 5.0, 'ratio': 0.2},
                },
            ]
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

    def test_invalid_optional_fields(self):
        response = self.client.get('/api/completion/v0/course/edX/toy/2012_Fall/?requested_fields=INVALID')
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated(self):
        self.client.force_authenticate(None)
        detailresponse = self.client.get('/api/completion/v0/course/edX/toy/2012_Fall/')
        self.assertEqual(detailresponse.status_code, 401)
        listresponse = self.client.get('/api/completion/v0/course/')
        self.assertEqual(listresponse.status_code, 401)

    def test_wrong_user(self):
        user = UserFactory.create(username='wrong')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v0/course/?user={}'.format(self.test_user.username))
        self.assertEqual(response.status_code, 404)

    def test_staff_access(self):
        user = AdminFactory.create(username='staff')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v0/course/?user={}'.format(self.test_user.username))
        self.assertEqual(response.status_code, 200)
