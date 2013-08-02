"""
Unit tests for instructor dashboard forum administration
"""


from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from django.contrib.auth.models import Group, User

from django.core.urlresolvers import reverse
from django_comment_common.models import Role, FORUM_ROLE_ADMINISTRATOR, \
    FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA, FORUM_ROLE_STUDENT
from django_comment_client.utils import has_forum_access

from courseware.access import _course_staff_group_name
from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_XML_MODULESTORE
from xmodule.modulestore.django import modulestore
import xmodule.modulestore.django


FORUM_ROLES = [FORUM_ROLE_ADMINISTRATOR, FORUM_ROLE_MODERATOR, FORUM_ROLE_COMMUNITY_TA]
FORUM_ADMIN_ACTION_SUFFIX = {FORUM_ROLE_ADMINISTRATOR: 'admin', FORUM_ROLE_MODERATOR: 'moderator', FORUM_ROLE_COMMUNITY_TA: 'community TA'}
FORUM_ADMIN_USER = {FORUM_ROLE_ADMINISTRATOR: 'forumadmin', FORUM_ROLE_MODERATOR: 'forummoderator', FORUM_ROLE_COMMUNITY_TA: 'forummoderator'}


def action_name(operation, rolename):
    if operation == 'List':
        return '{0} course forum {1}s'.format(operation, FORUM_ADMIN_ACTION_SUFFIX[rolename])
    else:
        return '{0} forum {1}'.format(operation, FORUM_ADMIN_ACTION_SUFFIX[rolename])


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestInstructorDashboardForumAdmin(LoginEnrollmentTestCase):
    '''
    Check for change in forum admin role memberships
    '''

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        self.course_id = "edX/toy/2012_Fall"
        self.toy = modulestore().get_course(self.course_id)

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(User.objects.get(email=self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        self.enroll(self.toy)

    def initialize_roles(self, course_id):
        self.admin_role = Role.objects.get_or_create(name=FORUM_ROLE_ADMINISTRATOR, course_id=course_id)[0]
        self.moderator_role = Role.objects.get_or_create(name=FORUM_ROLE_MODERATOR, course_id=course_id)[0]
        self.community_ta_role = Role.objects.get_or_create(name=FORUM_ROLE_COMMUNITY_TA, course_id=course_id)[0]

    def test_add_forum_admin_users_for_unknown_user(self):
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'unknown'
        for action in ['Add', 'Remove']:
            for rolename in FORUM_ROLES:
                response = self.client.post(url, {'action': action_name(action, rolename), FORUM_ADMIN_USER[rolename]: username})
                self.assertTrue(response.content.find('Error: unknown username "{0}"'.format(username)) >= 0)

    def test_add_forum_admin_users_for_missing_roles(self):
        course = self.toy
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u1'
        for action in ['Add', 'Remove']:
            for rolename in FORUM_ROLES:
                response = self.client.post(url, {'action': action_name(action, rolename), FORUM_ADMIN_USER[rolename]: username})
                self.assertTrue(response.content.find('Error: unknown rolename "{0}"'.format(rolename)) >= 0)

    def test_remove_forum_admin_users_for_missing_users(self):
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u1'
        action = 'Remove'
        for rolename in FORUM_ROLES:
            response = self.client.post(url, {'action': action_name(action, rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Error: user "{0}" does not have rolename "{1}"'.format(username, rolename)) >= 0)

    def test_add_and_remove_forum_admin_users(self):
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u2'
        for rolename in FORUM_ROLES:
            response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Added "{0}" to "{1}" forum role = "{2}"'.format(username, course.id, rolename)) >= 0)
            self.assertTrue(has_forum_access(username, course.id, rolename))
            response = self.client.post(url, {'action': action_name('Remove', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Removed "{0}" from "{1}" forum role = "{2}"'.format(username, course.id, rolename)) >= 0)
            self.assertFalse(has_forum_access(username, course.id, rolename))

    def test_add_and_read_forum_admin_users(self):
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u2'
        for rolename in FORUM_ROLES:
            # perform an add, and follow with a second identical add:
            self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(response.content.find('Error: user "{0}" already has rolename "{1}", cannot add'.format(username, rolename)) >= 0)
            self.assertTrue(has_forum_access(username, course.id, rolename))

    def test_add_nonstaff_forum_admin_users(self):
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u1'
        rolename = FORUM_ROLE_ADMINISTRATOR
        response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
        self.assertTrue(response.content.find('Error: user "{0}" should first be added as staff'.format(username)) >= 0)

    def test_list_forum_admin_users(self):
        course = self.toy
        self.initialize_roles(course.id)
        url = reverse('instructor_dashboard', kwargs={'course_id': course.id})
        username = 'u2'
        added_roles = [FORUM_ROLE_STUDENT]  # u2 is already added as a student to the discussion forums
        self.assertTrue(has_forum_access(username, course.id, 'Student'))
        for rolename in FORUM_ROLES:
            response = self.client.post(url, {'action': action_name('Add', rolename), FORUM_ADMIN_USER[rolename]: username})
            self.assertTrue(has_forum_access(username, course.id, rolename))
            response = self.client.post(url, {'action': action_name('List', rolename), FORUM_ADMIN_USER[rolename]: username})
            for header in ['Username', 'Full name', 'Roles']:
                self.assertTrue(response.content.find('<th>{0}</th>'.format(header)) > 0)
            self.assertTrue(response.content.find('<td>{0}</td>'.format(username)) >= 0)
            # concatenate all roles for user, in sorted order:
            added_roles.append(rolename)
            added_roles.sort()
            roles = ', '.join(added_roles)
            self.assertTrue(response.content.find('<td>{0}</td>'.format(roles)) >= 0, 'not finding roles "{0}"'.format(roles))
