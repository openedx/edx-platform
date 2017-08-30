"""
Test serialization of completion data.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.test.utils import override_settings
from rest_framework.test import APIClient

from opaque_keys.edx.keys import UsageKey
from progress import models

from student.tests.factories import AdminFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory


@override_settings(STUDENT_GRADEBOOK=True)
class CompletionViewTestCase(SharedModuleStoreTestCase):
    """
    Test that the CourseCompletionFacade handles modulestore data appropriately,
    and that it interacts properly with the serializer.
    """

    @classmethod
    def setUpClass(cls):
        super(CompletionViewTestCase, cls).setUpClass()
        cls.course = ToyCourseFactory.create()

    def setUp(self):
        super(CompletionViewTestCase, self).setUp()
        self.test_user = UserFactory.create(
            username='test_user',
            email='test_user@example.com',
            password='test_pass',
        )
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

    def test_unauthenticated(self):
        self.client.force_authenticate(None)
        detailresponse = self.client.get('/api/completion/v0/course/edX/toy/2012_Fall/')
        self.assertEqual(detailresponse.status_code, 403)
        listresponse = self.client.get('/api/completion/v0/course/')
        self.assertEqual(listresponse.status_code, 403)

    def test_wrong_user(self):
        user = UserFactory.create(username='wrong')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v0/course/?user=test_user')
        self.assertEqual(response.status_code, 404)

    def test_staff_access(self):
        user = AdminFactory.create(username='staff')
        self.client.force_authenticate(user)
        response = self.client.get('/api/completion/v0/course/?user=test_user')
        self.assertEqual(response.status_code, 200)
