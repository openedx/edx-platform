"""
Test serialization of completion data.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from datetime import datetime, timedelta
from collections import OrderedDict

from django.test.utils import override_settings
from oauth2_provider import models as dot_models
from rest_framework.test import APIClient
from unittest import expectedFailure
import ddt

from opaque_keys.edx.keys import UsageKey
from progress import models

from edx_solutions_api_integration.test_utils import SignalDisconnectTestMixin
from student.tests.factories import AdminFactory, UserFactory
from student.models import CourseEnrollment
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
        cls.otherOrgCourse = ToyCourseFactory.create(org='otherOrg')
        cls.futureCourse = ToyCourseFactory.create(org='futureOrg', start=datetime.utcnow() + timedelta(weeks=1))

    def setUp(self):
        super(CompletionViewTestCase, self).setUp()
        self.test_user = UserFactory.create()
        CourseEnrollment.enroll(self.test_user, self.course.id)
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
        models.StudentProgress.objects.get_or_create(
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

    def test_list_view_enrolled_no_progress(self):
        """
        Test that the completion API returns a record for each course the user is enrolled in,
        even if no progress records exist yet.
        """
        CourseEnrollment.enroll(self.test_user, self.otherOrgCourse.id)
        response = self.client.get('/api/completion/v0/course/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': 2, 'previous': None, 'num_pages': 1, 'next': None},
            'results': [
                {
                    'course_key': 'edX/toy/2012_Fall',
                    'completion': {
                        'earned': 1.0,
                        'possible': 12.0,
                        'ratio': 1 / 12,
                    },
                },
                {
                    'course_key': 'otherOrg/toy/2012_Fall',
                    'completion': {
                        'earned': 0.0,
                        'possible': 12.0,
                        'ratio': 0.0,
                    },
                }
            ],
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

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

    def test_detail_view_unenrolled(self):
        """
        Test that unenrolling from the course will return a 404 for course completions,
        even if there are existing progress records.
        """
        CourseEnrollment.unenroll(self.test_user, self.course.id)
        response = self.client.get('/api/completion/v0/course/edX/toy/2012_Fall/')
        self.assertEqual(response.status_code, 404)

    def test_detail_view_not_enrolled(self):
        """
        Test that requesting course completions for a course the user is not enrolled in
        will return a 404.
        """
        response = self.client.get('/api/completion/v0/course/otherOrg/toy/2012_Fall/')
        self.assertEqual(response.status_code, 404)

    def test_detail_view_no_completion(self):
        """
        Test that requesting course completions for a course which has started, but the user has not yet started,
        will return an empty completion record with its "possible" field filled in.
        """
        CourseEnrollment.enroll(self.test_user, self.otherOrgCourse.id)
        response = self.client.get('/api/completion/v0/course/otherOrg/toy/2012_Fall/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'otherOrg/toy/2012_Fall',
            'completion': {
                'earned': 0.0,
                'possible': 12.0,
                'ratio': 0.0,
            },
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

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
        CourseEnrollment.enroll(self.test_user, self.futureCourse.id)
        response = self.client.get('/api/completion/v0/course/futureOrg/toy/2012_Fall/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'course_key': 'futureOrg/toy/2012_Fall',
            'completion': {
                'earned': 0.0,
                'possible': 0.0,
                'ratio': 1.0,
            },
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member

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
        response = self.client.get('/api/completion/v0/course/?username={}'.format(self.test_user.username))
        self.assertEqual(response.status_code, 404)

    def test_staff_access(self):
        user = AdminFactory.create(username='staff')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v0/course/?username={}'.format(self.test_user.username))
        self.assertEqual(response.status_code, 200)
        expected_completion = {'earned': 1.0, 'possible': 12.0, 'ratio': 1 / 12}
        self.assertEqual(response.data['results'][0]['completion'], expected_completion)  # pylint: disable=no-member


class CompletionBlockUpdateViewTestCase(SharedModuleStoreTestCase):
    """
    Test that CompletionBlockUpdateView can be used to mark XBlocks as completed.

    Ensure that it handles authorization as well.
    """

    usage_key = 'i4x://edX/toy/video/sample_video'
    ENABLED_SIGNALS = ['course_published']

    @classmethod
    def setUpClass(cls):
        super(CompletionBlockUpdateViewTestCase, cls).setUpClass()
        cls.course = ToyCourseFactory.create()

    def setUp(self):
        super(CompletionBlockUpdateViewTestCase, self).setUp()
        self.test_user = UserFactory.create()
        CourseEnrollment.enroll(self.test_user, self.course.id)
        self.client = APIClient()
        self.client.force_authenticate(user=self.test_user)
        self.update_url = '/api/completion/v0/course/{}/blocks/{}/'.format(self.course.id, self.usage_key)

    def test_create_view(self):
        # Ensure Solutions signals are always connected.
        SignalDisconnectTestMixin.connect_signals()

        completion_query_url = '/api/completion/v0/course/edX/toy/2012_Fall/?requested_fields=sequential'
        before_response = self.client.get(completion_query_url)
        self.assertEqual(before_response.status_code, 200)

        before_data = before_response.data  # pylint: disable=no-member
        self.assertEqual(before_data['completion']['earned'], 0)
        self.assertEqual(before_data['completion']['possible'], 12)
        self.assertEqual(before_data['completion']['ratio'], 0)
        self.assertEqual(before_data['sequential'][0]['completion']['earned'], 0)

        create_response = self.client.post(self.update_url, {'completion': 1})
        self.assertEqual(create_response.status_code, 201)

        after_response = self.client.get(completion_query_url)
        self.assertEqual(after_response.status_code, 200)
        after_data = after_response.data  # pylint: disable=no-member
        self.assertEqual(after_data['completion']['earned'], 1)
        self.assertEqual(after_data['completion']['possible'], 12)
        self.assertEqual(after_data['completion']['ratio'], 1 / 12)
        self.assertEqual(after_data['sequential'][0]['completion']['earned'], 1)

        # Disconnect signals again.
        SignalDisconnectTestMixin.disconnect_signals()

    def test_create_view_oauth2(self):
        """
        Test the create view using OAuth2 Authentication
        """
        url = '/api/completion/v0/course/{}/blocks/{}/'.format(self.course.id, self.usage_key)

        self.client.logout()
        response = self.client.post(url, {'completion': 1})
        self.assertEqual(response.status_code, 401)

        # Now, try with a valid token header:
        token = _create_oauth2_token(self.test_user)
        response = self.client.post(url, {'completion': 1}, HTTP_AUTHORIZATION="Bearer {0}".format(token))
        self.assertEqual(response.status_code, 201)

    def test_unauthenticated(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.update_url, {'completion': 1})
        self.assertEqual(response.status_code, 401)


@ddt.ddt
class CompletionMobileViewTestCase(SharedModuleStoreTestCase):
    """
    Tests the CompletionView with mobile courses.
    """

    @classmethod
    def setUpClass(cls):
        super(CompletionMobileViewTestCase, cls).setUpClass()
        cls.non_mobile_course = ToyCourseFactory.create()
        cls.mobile_course = ToyCourseFactory.create(mobile_available=True, course='mobile', run='2018_Spring')

    def setUp(self):
        super(CompletionMobileViewTestCase, self).setUp()
        self.test_user = UserFactory.create()
        CourseEnrollment.enroll(self.test_user, self.non_mobile_course.id)
        CourseEnrollment.enroll(self.test_user, self.mobile_course.id)
        self.mobile_client = APIClient()
        self.mobile_client.force_authenticate(user=self.test_user)

    @ddt.data(
        (
            1,
            [
                OrderedDict(
                    [
                        (
                            u'course_key', u'edX/mobile/2018_Spring'
                        ),
                        (
                            u'completion',
                            OrderedDict(
                                [
                                    (u'earned', 0.0),
                                    (u'possible', 12.0),
                                    (u'ratio', 0.0)
                                ]
                            )
                        )
                    ])
            ],
            True
        ),
        (
            2,
            [
                OrderedDict(
                    [
                        (
                            u'course_key', u'edX/mobile/2018_Spring'
                        ),
                        (
                            u'completion',
                            OrderedDict(
                                [
                                    (u'earned', 0.0),
                                    (u'possible', 12.0),
                                    (u'ratio', 0.0),
                                ])
                        )
                    ]),
                OrderedDict(
                    [
                        (
                            u'course_key', u'edX/toy/2012_Fall'
                        ),
                        (
                            u'completion',
                            OrderedDict(
                                [
                                    (u'earned', 0.0),
                                    (u'possible', 12.0),
                                    (u'ratio', 0.0),
                                ])
                        )
                    ])
            ],
            False
        )
    )
    @ddt.unpack
    def test_list_view_mobile_only(self, expected_count, expected_results, test_mobile_only_parameter):
        if test_mobile_only_parameter:
            response = self.mobile_client.get('/api/completion/v0/course/?mobile_only=true')
        else:
            response = self.mobile_client.get('/api/completion/v0/course/')
        self.assertEqual(response.status_code, 200)
        expected = {
            'pagination': {'count': expected_count, 'previous': None, 'num_pages': 1, 'next': None},
            'results': expected_results,
        }
        self.assertEqual(response.data, expected)  # pylint: disable=no-member
