"""
Test serialization of completion data.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime, timedelta
from unittest import expectedFailure

from django.test.utils import override_settings
from oauth2_provider import models as dot_models
from rest_framework.test import APIClient

from student.tests.factories import AdminFactory, UserFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory
from .. import models
from .. test_utils import CompletionWaffleTestMixin


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
class CompletionViewTestCase(CompletionWaffleTestMixin, SharedModuleStoreTestCase):
    """
    Test that the CompletionView renders completion data properly.

    Ensure that it handles authorization as well.
    """

    @classmethod
    def setUpClass(cls):
        super(CompletionViewTestCase, cls).setUpClass()
        cls.course = ToyCourseFactory.create()
        cls.other_org_course = ToyCourseFactory.create(org='otherOrg')
        cls.future_course = ToyCourseFactory.create(org='futureOrg', start=datetime.utcnow() + timedelta(weeks=1))

    def setUp(self):
        super(CompletionViewTestCase, self).setUp()
        self.override_waffle_switch(True)
        self.override_aggregation_switch(True)
        self.test_user = UserFactory.create()
        CourseEnrollment.enroll(self.test_user, self.course.id)
        self.mark_completions()
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)

    def mark_completions(self):
        """
        Create completion data to test against.
        """
        models.AggregateCompletion.objects.submit_completion(
            user=self.test_user,
            course_key=self.course.id,
            block_key=self.course.id.make_usage_key(block_type='sequential', block_id='vertical_sequential'),
            aggregation_name='sequential',
            earned=1.0,
            possible=5.0,
        )
        models.AggregateCompletion.objects.submit_completion(
            user=self.test_user,
            course_key=self.course.id,
            block_key=self.course.location,
            aggregation_name='course',
            earned=1.0,
            possible=12.0,
        )

    def test_list_view(self):
        response = self.client.get('/api/completion/v1/course/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': 1, 'previous': None, 'num_pages': 1, 'next': None},
            'results': [
                {
                    'course_key': 'edX/toy/2012_Fall',
                    'completion': {
                        'earned': 1.0,
                        'possible': 12.0,
                        'percent': 1 / 12,
                    },
                }
            ],
        }
        self.assertEqual(response.data, expected)

    def test_list_view_oauth2(self):
        """
        Test the list view using OAuth2 Authentication
        """
        url = '/api/completion/v1/course/'
        # Try with no authentication:
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # Now, try with a valid token header:
        token = _create_oauth2_token(self.test_user)
        response = self.client.get(url, HTTP_AUTHORIZATION="Bearer {0}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['completion']['earned'], 1.0)

    @expectedFailure
    def test_list_view_enrolled_no_progress(self):
        """
        Test that the completion API returns a record for each course the user is enrolled in,
        even if no progress records exist yet.

        @expectedFailure:

        This test depends on being able to fill in missing data to get an appropriate value for
        "possible" or "percent".  Actual calculation of AggregateCompletion values is coming in a
        later story (OC-3098)

        """
        CourseEnrollment.enroll(self.test_user, self.other_org_course.id)
        response = self.client.get('/api/completion/v1/course/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': 2, 'previous': None, 'num_pages': 1, 'next': None},
            'results': [
                {
                    'course_key': 'edX/toy/2012_Fall',
                    'completion': {
                        'earned': 1.0,
                        'possible': 12.0,
                        'percent': 1 / 12,
                    },
                },
                {
                    'course_key': 'otherOrg/toy/2012_Fall',
                    'completion': {
                        'earned': 0.0,
                        'possible': 12.0,
                        'percent': 0.0,
                    },
                }
            ],
        }
        self.assertEqual(response.data, expected)

    def test_list_view_with_sequentials(self):
        response = self.client.get('/api/completion/v1/course/?requested_fields=sequential')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': 1, 'previous': None, 'num_pages': 1, 'next': None},
            'results': [
                {
                    'course_key': 'edX/toy/2012_Fall',
                    'completion': {
                        'earned': 1.0,
                        'possible': 12.0,
                        'percent': 1 / 12,
                    },
                    'sequential': [
                        {
                            'course_key': u'edX/toy/2012_Fall',
                            'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                            'completion': {'earned': 1.0, 'possible': 5.0, 'percent': 0.2},
                        },
                    ]
                }
            ],
        }
        self.assertEqual(response.data, expected)

    def test_detail_view(self):
        response = self.client.get('/api/completion/v1/course/edX/toy/2012_Fall/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'edX/toy/2012_Fall',
            'completion': {
                'earned': 1.0,
                'possible': 12.0,
                'percent': 1 / 12,
            },
        }
        self.assertEqual(response.data, expected)

    def test_detail_view_oauth2(self):
        """
        Test the detail view using OAuth2 Authentication
        """
        url = '/api/completion/v1/course/edX/toy/2012_Fall/'
        # Try with no authentication:
        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        # Now, try with a valid token header:
        token = _create_oauth2_token(self.test_user)
        response = self.client.get(url, HTTP_AUTHORIZATION="Bearer {0}".format(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['completion']['earned'], 1.0)

    def test_detail_view_unenrolled(self):
        """
        Test that unenrolling from the course will return a 404 for course completions,
        even if there are existing progress records.
        """
        CourseEnrollment.unenroll(self.test_user, self.course.id)
        response = self.client.get('/api/completion/v1/course/edX/toy/2012_Fall/')
        self.assertEqual(response.status_code, 404)

    def test_detail_view_not_enrolled(self):
        """
        Test that requesting course completions for a course the user is not enrolled in
        will return a 404.
        """
        response = self.client.get('/api/completion/v1/course/otherOrg/toy/2012_Fall/')
        self.assertEqual(response.status_code, 404)

    @expectedFailure
    def test_detail_view_no_completion(self):
        """
        Test that requesting course completions for a course which has started, but the user has not yet started,
        will return an empty completion record with its "possible" field filled in.

        @expectedFailure:

        This test depends on being able to fill in missing data to get an appropriate value for
        "possible" or "percent".  Actual calculation of AggregateCompletion values is coming in a
        later story (OC-3098)
        """
        CourseEnrollment.enroll(self.test_user, self.other_org_course.id)
        response = self.client.get('/api/completion/v1/course/otherOrg/toy/2012_Fall/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'otherOrg/toy/2012_Fall',
            'completion': {
                'earned': 0.0,
                'possible': 12.0,
                'percent': 0.0,
            },
        }
        self.assertEqual(response.data, expected)

    @expectedFailure
    def test_detail_view_future_course(self):
        """
        Test that requesting course completions for a course with a start date in the future
        (also that a user has not started) will return an empty completion record.

        @expectedFailure:
        The completion record *should* report "possible: 0.0" because the user is not allowed to see the course blocks
        for future courses, and so can't see what the possible scores may be.  And indeed this is what manual testing
        demontrates, so something is different about this unit test environment, which needs to be addressed.
        """
        CourseEnrollment.enroll(self.test_user, self.future_course.id)
        response = self.client.get('/api/completion/v1/course/futureOrg/toy/2012_Fall/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'futureOrg/toy/2012_Fall',
            'completion': {
                'earned': 0.0,
                'possible': 0.0,
                'percent': 1.0,
            },
        }
        self.assertEqual(response.data, expected)

    def test_detail_view_with_sequentials(self):
        response = self.client.get('/api/completion/v1/course/edX/toy/2012_Fall/?requested_fields=sequential')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'edX/toy/2012_Fall',
            'completion': {
                'earned': 1.0,
                'possible': 12.0,
                'percent': 1 / 12,
            },
            'sequential': [
                {
                    'course_key': u'edX/toy/2012_Fall',
                    'block_key': u'i4x://edX/toy/sequential/vertical_sequential',
                    'completion': {'earned': 1.0, 'possible': 5.0, 'percent': 0.2},
                },
            ]
        }
        self.assertEqual(response.data, expected)

    def test_invalid_optional_fields(self):
        response = self.client.get('/api/completion/v1/course/edX/toy/2012_Fall/?requested_fields=INVALID')
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated(self):
        self.client.force_authenticate(None)
        detailresponse = self.client.get('/api/completion/v1/course/edX/toy/2012_Fall/')
        self.assertEqual(detailresponse.status_code, 401)
        listresponse = self.client.get('/api/completion/v1/course/')
        self.assertEqual(listresponse.status_code, 401)

    def test_wrong_user(self):
        user = UserFactory.create(username='wrong')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v1/course/?username={}'.format(self.test_user.username))
        self.assertEqual(response.status_code, 404)

    def test_staff_access(self):
        user = AdminFactory.create(username='staff')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v1/course/?username={}'.format(self.test_user.username))
        self.assertEqual(response.status_code, 200)
        expected_completion = {'earned': 1.0, 'possible': 12.0, 'percent': 1 / 12}
        self.assertEqual(response.data['results'][0]['completion'], expected_completion)
