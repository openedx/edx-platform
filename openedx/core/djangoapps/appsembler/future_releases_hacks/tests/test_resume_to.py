"""
Tests for upgrade hack views
"""
import json
from unittest.mock import patch

from django.http.response import JsonResponse
from django.urls import reverse
from lms.djangoapps.course_blocks.transformers.tests.helpers import ModuleStoreTestCase
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    create_org_user,
    with_organization_context,
)
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestResumeTo(ModuleStoreTestCase):
    """
    Tests for `resume_to` view
    """
    def setUp(self):
        """
        Initialize tests data
        """
        super(TestResumeTo, self).setUp()

        with with_organization_context(site_color='blue1') as blue_org:
            self.user = create_org_user(blue_org)
        self.course = CourseFactory.create()
        self.enrollment = CourseEnrollmentFactory(mode='audit', course_id=self.course.id, user=self.user)

        self.blocks = {}

        self.store = modulestore()
        for shortcut in range(1, 4):  # 3 blocks
            self.blocks[str(shortcut)] = ItemFactory.create(category='html', parent=self.course, modulestore=self.store)
        assert len(self.blocks) == 3

    def _call_resume(self):
        """
        Common helper
        """
        url = reverse('resume_to', args=[self.course.id, self.blocks['2'].location])
        return self.client.get(url)

    @patch('openedx.core.djangoapps.appsembler.future_releases_hacks.views.jump_to')
    def test_resume_to_calls_jump_to(self, jump_to_mock):
        """
        Verify that `resume_to` calls `jump_to`
        """
        jump_to_mock.return_value = JsonResponse(data={"verify": "called"}, status=200)
        response = self._call_resume()
        data = json.loads(response.content.decode('utf8'))
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(data, {'verify': 'called'})

    def test_resume_to(self):
        """
        Verify that resume_to works fine
        """
        response = self._call_resume()
        expected_url = '/courses/{course_id}/courseware/html'.format(
            course_id=self.course.id,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(expected_url, response.url)

    def test_resume_to_deleted_item(self):
        """
        Verify that resume to will handle the Http404 raised by `jump_to` and redirect to course home page
        """
        # Delete the item pointed by the link
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            self.store.delete_item(self.blocks['2'].location, self.user.id)
            self.store.publish(self.blocks['2'].location, self.user.id)

        response = self._call_resume()
        expected_url = '/courses/{course_id}/course/'.format(
            course_id=self.course.id,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(expected_url, response.url)
