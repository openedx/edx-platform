"""
Test CRUD for authorization.
"""
from django.test.utils import override_settings
from django.contrib.auth.models import User, Group

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.modulestore_config import TEST_MODULESTORE
from contentstore.tests.utils import AjaxEnabledTestClient
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore import Location
from auth.authz import INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME
from auth import authz
import copy
from contentstore.views.access import has_access


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
        self.course_location = Location(['i4x', 'myu', 'mydept.mycourse', 'course', 'myrun'])
        self.course_locator = loc_mapper().translate_location(
            self.course_location.course_id, self.course_location, False, True
        )
        self.client.ajax_post(
            self.course_locator.url_reverse('course'),
            {
                'org': self.course_location.org, 
                'number': self.course_location.course,
                'display_name': 'My favorite course',
                'run': self.course_location.name,
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
        # first check the groupname for the course creator.
        self.assertTrue(
            self.user.groups.filter(
                name="{}_{}".format(INSTRUCTOR_ROLE_NAME, self.course_locator.package_id)
            ).exists(),
            "Didn't add creator as instructor."
        )
        users = copy.copy(self.users)
        user_by_role = {}
        # add the misc users to the course in different groups
        for role in [INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME]:
            user_by_role[role] = []
            groupnames, _ = authz.get_all_course_role_groupnames(self.course_locator, role)
            for groupname in groupnames:
                group, _ = Group.objects.get_or_create(name=groupname)
                user = users.pop()
                user_by_role[role].append(user)
                user.groups.add(group)
                user.save()
                self.assertTrue(has_access(user, self.course_locator), "{} does not have access".format(user))
                self.assertTrue(has_access(user, self.course_location), "{} does not have access".format(user))

        response = self.client.get_html(self.course_locator.url_reverse('course_team'))
        for role in [INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME]:
            for user in user_by_role[role]:
                self.assertContains(response, user.email)
        
        # test copying course permissions
        copy_course_location = Location(['i4x', 'copyu', 'copydept.mycourse', 'course', 'myrun'])
        copy_course_locator = loc_mapper().translate_location(
            copy_course_location.course_id, copy_course_location, False, True
        )
        # pylint: disable=protected-access
        authz._copy_course_group(self.course_locator, copy_course_locator)
        for role in [INSTRUCTOR_ROLE_NAME, STAFF_ROLE_NAME]:
            for user in user_by_role[role]:
                self.assertTrue(has_access(user, copy_course_locator), "{} no copy access".format(user))
                self.assertTrue(has_access(user, copy_course_location), "{} no copy access".format(user))
