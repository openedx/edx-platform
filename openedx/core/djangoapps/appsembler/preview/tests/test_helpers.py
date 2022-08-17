"""
Tests for helpers.
"""
from unittest.mock import patch

import ddt
import pytest
from completion.exceptions import UnavailableCompletionData
from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
from django.contrib.auth import get_user_model
from django.test.client import RequestFactory
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    create_org_user,
    with_organization_context,
)
from openedx.core.djangoapps.appsembler.future_releases_hacks.helpers import get_key_to_last_completed_block
from student.helpers import get_resume_urls_for_enrollments
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..helpers import is_preview_mode, PREVIEW_GET_PARAM

User = get_user_model()


def test_no_request():
    assert not is_preview_mode(), 'default to non-preview if no request is provided'


def test_request_non_preview_mode():
    request = RequestFactory().get('/test')
    request.user = User()
    assert not is_preview_mode(current_request=request), 'default to non-preview'


@pytest.mark.parametrize('preview_param', [True, 'true', 'True'])
def test_request_preview_mode_case_insensitive(preview_param):
    request = RequestFactory().get('/test', data={'preview': preview_param})
    request.user = User()
    is_preview_result = is_preview_mode(current_request=request)
    assert is_preview_result, 'Should respect case-insensitive `preview=true` param'


def test_request_preview_mode_without_user():
    request = RequestFactory().get('/test', data={'preview': 'true'})
    is_preview_result = is_preview_mode(current_request=request)
    assert not is_preview_result, 'Disable preview mode for unauthenticated users'


def test_request_preview_mode_crum():
    """
    Ensure `crum.get_current_request` is used when no request is provided via parameters.
    """
    request = RequestFactory().get('/test', data={PREVIEW_GET_PARAM: 'true'})
    request.user = User()
    with patch('crum.get_current_request', return_value=request):
        assert is_preview_mode(), 'Should default to `crum` request'


def test_request_preview_mode_test_yes():
    """
    Ensure `crum.get_current_request` should be `live` if provided anything other than yes.
    """
    request = RequestFactory().get('/test', data={PREVIEW_GET_PARAM: 'yes'})
    request.user = User()
    assert not is_preview_mode(current_request=request), 'Anything is falsy, except for `true`'


@ddt.ddt
class TestResumeCourseProcess(ModuleStoreTestCase, CompletionWaffleTestMixin):
    """
    We've overridden completion.get_key_to_last_completed_block with a new version in
    openedx.core.djangoapps.appsembler.preview.helpers . This is to test that change along with the affected
    method student.helpers.get_resume_urls_for_enrollments
    """
    def setUp(self):
        """
        Initialize tests data
        """
        super(TestResumeCourseProcess, self).setUp()
        self.override_waffle_switch(True)

        with with_organization_context(site_color='blue1') as blue_org:
            self.user = create_org_user(blue_org)
        self.course = CourseFactory.create()
        self.enrollment = CourseEnrollmentFactory(mode='audit', course_id=self.course.id, user=self.user)

        self.blocks = {}

        self.store = modulestore()
        for shortcut in range(1, 4):  # 3 blocks
            self.blocks[str(shortcut)] = ItemFactory.create(category='html', parent=self.course, modulestore=self.store)
        assert len(self.blocks) == 3

        # Only first and second blocks are completed
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=self.blocks['1'].location,
            completion=1.0,
        )
        BlockCompletion.objects.submit_completion(
            user=self.user,
            block_key=self.blocks['2'].location,
            completion=0.75,
        )
        self.completion1 = BlockCompletion.objects.get(block_key=self.blocks['1'].scope_ids.usage_id)
        assert self.completion1.completion == 1.0
        self.completion2 = BlockCompletion.objects.get(block_key=self.blocks['2'].scope_ids.usage_id)
        assert self.completion2.completion == 0.75

    def test_can_get_key_to_last_completed_block(self):
        """
        Test happy scenario for get_key_to_last_completed_block
        """
        last_block_key = get_key_to_last_completed_block(self.user, self.course.id)
        self.assertEqual(last_block_key, self.blocks['2'].location)

    def test_getting_last_completed_course_block_in_untouched_enrollment_throws(self):
        """
        Test get_key_to_last_completed_block with no enrollment
        """
        course_key = CourseKey.from_string("edX/NotACourse/2049_T2")

        with self.assertRaises(UnavailableCompletionData):
            get_key_to_last_completed_block(self.user, course_key)

    def test_get_resume_urls_for_enrollments(self):
        """
        Verify that get_resume_urls_for_enrollments returns the expected URLs
        """
        result = get_resume_urls_for_enrollments(self.user, [self.enrollment])
        assert len(result) == 1
        assert result == {
            self.course.id: '/courses/{course_key}/jump_to/{location}'.format(
                course_key=self.course.id,
                location=self.blocks['2'].location
            )
        }

    def test_get_resume_urls_for_enrollments_deleted_item(self):
        """
        Verify that get_resume_urls_for_enrollments returns empty URL when the block is deleted from the course
        """
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.delete_item(self.blocks['2'].location, self.user.id)
            self.store.publish(self.blocks['2'].location, self.user.id)

        result = get_resume_urls_for_enrollments(self.user, [self.enrollment])
        assert len(result) == 1
        assert result == {
            self.course.id: ''
        }
