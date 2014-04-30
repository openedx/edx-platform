"""
Test CRUD for authorization.
"""
import copy

from django.test.utils import override_settings
from django.contrib.auth.models import User

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.modulestore_config import TEST_MODULESTORE
from contentstore.tests.utils import AjaxEnabledTestClient
from xmodule.modulestore.locations import SlashSeparatedCourseKey
from contentstore.utils import reverse_url, reverse_course_url
from student.roles import CourseInstructorRole, CourseStaffRole
from contentstore.views.access import has_course_access
from student import auth


@override_settings(MODULESTORE=TEST_MODULESTORE)
class TestCourseAccess(ModuleStoreTestCase):
    """
    Course-based access (as opposed to access of a non-course xblock)
    """
    def setUp(self):
        """
        Create a staff user and log them in (creating the client).

        Create a pool of users w/o granting them any permissions
        """
        super(TestCourseAccess, self).setUp()
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.client = AjaxEnabledTestClient()
        self.client.login(username=uname, password=password)

        # create a course via the view handler which has a different strategy for permissions than the factory
        self.course_key = SlashSeparatedCourseKey('myu', 'mydept.mycourse', 'myrun')
        course_url = reverse_url('course_handler')
        self.client.ajax_post(course_url,
            {
                'org': self.course_key.org,
                'number': self.course_key.course,
                'display_name': 'My favorite course',
                'run': self.course_key.run,
            }
        )

        self.users = self._create_users()

    def _create_users(self):
        """
        Create 8 users and return them
        """
        users = []
        for i in range(8):
            username = "user{}".format(i)
            email = "test+user{}@edx.org".format(i)
            user = User.objects.create_user(username, email, 'foo')
            user.is_active = True
            user.save()
            users.append(user)
        return users

    def tearDown(self):
        """
        Reverse the setup
        """
        self.client.logout()
        ModuleStoreTestCase.tearDown(self)

    def test_get_all_users(self):
        """
        Test getting all authors for a course where their permissions run the gamut of allowed group
        types.
        """
        # first check the course creator.has explicit access (don't use has_access as is_staff
        # will trump the actual test)
        self.assertTrue(
            CourseInstructorRole(self.course_key).has_user(self.user),
            "Didn't add creator as instructor."
        )
        users = copy.copy(self.users)
        # doesn't use role.users_with_role b/c it's verifying the roles.py behavior
        user_by_role = {}
        # add the misc users to the course in different groups
        for role in [CourseInstructorRole, CourseStaffRole]:
            user_by_role[role] = []
            # pylint: disable=protected-access
            group = role(self.course_key)
            # NOTE: this loop breaks the roles.py abstraction by purposely assigning
            # users to one of each possible groupname in order to test that has_course_access
            # and remove_user work
            user = users.pop()
            group.add_users(user)
            user_by_role[role].append(user)
            self.assertTrue(has_course_access(user, self.course_key), "{} does not have access".format(user))

        course_team_url = reverse_course_url('course_team_handler', self.course_key)
        response = self.client.get_html(course_team_url)
        for role in [CourseInstructorRole, CourseStaffRole]:
            for user in user_by_role[role]:
                self.assertContains(response, user.email)

        # test copying course permissions
        copy_course_key = SlashSeparatedCourseKey('copyu', 'copydept.mycourse', 'myrun')
        for role in [CourseInstructorRole, CourseStaffRole]:
            auth.add_users(
                self.user,
                role(copy_course_key),
                *role(self.course_key).users_with_role()
            )
        # verify access in copy course and verify that removal from source course w/ the various
        # groupnames works
        for role in [CourseInstructorRole, CourseStaffRole]:
            for user in user_by_role[role]:
                # forcefully decache the groups: premise is that any real request will not have
                # multiple objects repr the same user but this test somehow uses different instance
                # in above add_users call
                if hasattr(user, '_roles'):
                    del user._roles

                self.assertTrue(has_course_access(user, copy_course_key), "{} no copy access".format(user))
                auth.remove_users(self.user, role(self.course_key), user)
                self.assertFalse(has_course_access(user, self.course_key), "{} remove didn't work".format(user))
