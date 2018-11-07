# -*- coding: utf-8 -*-
"""
Test models, managers, and validators.
"""
from completion import waffle
from completion.test_utils import CompletionWaffleTestMixin
import ddt
from django.urls import reverse
from rest_framework.test import APIClient

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


@ddt.ddt
@skip_unless_lms
class CompletionBatchTestCase(CompletionWaffleTestMixin, ModuleStoreTestCase):
    """
    Test that BlockCompletion.objects.submit_batch_completion has the desired
    semantics.
    """
    ENROLLED_USERNAME = 'test_user'
    UNENROLLED_USERNAME = 'unenrolled_user'
    COURSE_KEY = 'TestX/101/Test'
    BLOCK_KEY = 'i4x://TestX/101/problem/Test_Problem'

    def setUp(self):
        """
        Create the test data.
        """
        super(CompletionBatchTestCase, self).setUp()
        self.url = reverse('completion_api:v1:completion-batch')

        # Enable the waffle flag for all tests
        self.override_waffle_switch(True)

        # Create course
        self.course = CourseFactory.create(org='TestX', number='101', display_name='Test')
        self.problem = ItemFactory.create(
            parent=self.course,
            category="problem",
            display_name="Test Problem",
        )

        # Create users
        self.staff_user = UserFactory(is_staff=True)
        self.enrolled_user = UserFactory(username=self.ENROLLED_USERNAME)
        self.unenrolled_user = UserFactory(username=self.UNENROLLED_USERNAME)

        # Enrol one user in the course
        CourseEnrollmentFactory.create(user=self.enrolled_user, course_id=self.course.id)

        # Login the enrolled user by for all tests
        self.client = APIClient()
        self.client.force_authenticate(user=self.enrolled_user)

    def test_enable_completion_tracking(self):
        """
        Test response when the waffle switch is disabled (default).
        """
        with waffle.waffle().override(waffle.ENABLE_COMPLETION_TRACKING, False):
            response = self.client.post(self.url, {'username': self.ENROLLED_USERNAME}, format='json')
        self.assertEqual(response.data, {
            "detail":
                "BlockCompletion.objects.submit_batch_completion should not be called when the feature is disabled."
        })
        self.assertEqual(response.status_code, 400)

    @ddt.data(
        # Valid submission
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 200, {'detail': 'ok'}
        ),
        # Blocks list can be empty, though it's a no-op
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': [],
            }, 200, {"detail": "ok"}
        ),
        # Course must be a valid key
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': "not:a:course:key",
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 400, {"detail": "Invalid course key: not:a:course:key"}
        ),
        # Block must be a valid key
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': {
                    'not:a:block:key': 1.0,
                }
            }, 400, {"detail": "Invalid block key: not:a:block:key"}
        ),
        # Block not in course
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': {
                    'i4x://some/other_course/problem/Test_Problem': 1.0,
                }
            },
            400,
            {
                "detail": "Block with key: 'i4x://some/other_course/problem/Test_Problem' is not in course {}".format(
                    COURSE_KEY,
                )
            }
        ),
        # Course key is required
        (
            {
                'username': ENROLLED_USERNAME,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 400, {"detail": "Key 'course_key' not found."}
        ),
        # Blocks is required
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': COURSE_KEY,
            }, 400, {"detail": "Key 'blocks' not found."}
        ),
        # Ordinary users can only update their own completions
        (
            {
                'username': UNENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 403, {"detail": "You do not have permission to perform this action."}
        ),
        # Username is required
        (
            {
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 403, {"detail": 'You do not have permission to perform this action.'}
        ),
        # Course does not exist
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': 'TestX/101/Test2',
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 400, {"detail": "User is not enrolled in course."}
        ),
    )
    @ddt.unpack
    def test_batch_submit(self, payload, expected_status, expected_data):
        """
        Test the batch submission response for student users.
        """
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.status_code, expected_status)

    @ddt.data(
        # Staff can submit completion on behalf of other users
        (
            {
                'username': ENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 200, {'detail': 'ok'}
        ),
        # User must be enrolled in the course
        (
            {
                'username': UNENROLLED_USERNAME,
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 400, {"detail": "User is not enrolled in course."}
        ),
        # Username is required
        (
            {
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 400, {"detail": "Key 'username' not found."}
        ),
        # User must not exist
        (
            {
                'username': 'doesntexist',
                'course_key': COURSE_KEY,
                'blocks': {
                    BLOCK_KEY: 1.0,
                }
            }, 404, {"detail": 'User matching query does not exist.'}
        ),
    )
    @ddt.unpack
    def test_batch_submit_staff(self, payload, expected_status, expected_data):
        """
        Test the batch submission response when logged in as a staff user.
        """
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.data, expected_data)
        self.assertEqual(response.status_code, expected_status)
