"""
Tests course_creators.admin.py.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
import mock

from course_creators.admin import CourseCreatorAdmin
from course_creators.models import CourseCreator
from auth.authz import is_user_in_creator_group


def mock_render_to_string(template_name, context):
    """Return a string that encodes template_name and context"""
    return str((template_name, context))


class CourseCreatorAdminTest(TestCase):
    """
    Tests for course creator admin.
    """

    def setUp(self):
        """ Test case setup """
        self.user = User.objects.create_user('test_user', 'test_user+courses@edx.org', 'foo')
        self.table_entry = CourseCreator(user=self.user)
        self.table_entry.save()

        self.admin = User.objects.create_user('Mark', 'admin+courses@edx.org', 'foo')
        self.admin.is_staff = True

        self.request = HttpRequest()
        self.request.user = self.admin

        self.creator_admin = CourseCreatorAdmin(self.table_entry, AdminSite())

    @mock.patch('course_creators.admin.render_to_string', mock.Mock(side_effect=mock_render_to_string, autospec=True))
    @mock.patch('django.contrib.auth.models.User.email_user')
    def test_change_status(self, email_user):
        """
        Tests that updates to state impact the creator group maintained in authz.py and that e-mails are sent.
        """
        STUDIO_REQUEST_EMAIL = 'mark@marky.mark' 
        
        def change_state(state, is_creator):
            """ Helper method for changing state """
            self.table_entry.state = state
            self.creator_admin.save_model(self.request, self.table_entry, None, True)
            self.assertEqual(is_creator, is_user_in_creator_group(self.user))
            
            context = {'studio_request_email': STUDIO_REQUEST_EMAIL}
            if state == CourseCreator.GRANTED:
                template = 'emails/course_creator_granted.txt'
            elif state == CourseCreator.DENIED:
                template = 'emails/course_creator_denied.txt'
            else:
                template = 'emails/course_creator_revoked.txt'
            email_user.assert_called_with(
                mock_render_to_string('emails/course_creator_subject.txt', context),
                mock_render_to_string(template, context),
                STUDIO_REQUEST_EMAIL
            )

        with mock.patch.dict(
            'django.conf.settings.MITX_FEATURES',
            {
                "ENABLE_CREATOR_GROUP": True,
                "STUDIO_REQUEST_EMAIL": STUDIO_REQUEST_EMAIL
            }):

            # User is initially unrequested.
            self.assertFalse(is_user_in_creator_group(self.user))

            change_state(CourseCreator.GRANTED, True)

            change_state(CourseCreator.DENIED, False)

            change_state(CourseCreator.GRANTED, True)

            change_state(CourseCreator.PENDING, False)

            change_state(CourseCreator.GRANTED, True)

            change_state(CourseCreator.UNREQUESTED, False)

    def test_add_permission(self):
        """
        Tests that staff cannot add entries
        """
        self.assertFalse(self.creator_admin.has_add_permission(self.request))

    def test_delete_permission(self):
        """
        Tests that staff cannot delete entries
        """
        self.assertFalse(self.creator_admin.has_delete_permission(self.request))

    def test_change_permission(self):
        """
        Tests that only staff can change entries
        """
        self.assertTrue(self.creator_admin.has_change_permission(self.request))

        self.request.user = self.user
        self.assertFalse(self.creator_admin.has_change_permission(self.request))
