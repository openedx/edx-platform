"""
Test instructor.access
"""

from nose.tools import raises
from django.contrib.auth.models import Group
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from django.test.utils import override_settings
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE

from courseware.access import get_access_group_name
from django_comment_common.models import (Role,
                                          FORUM_ROLE_MODERATOR)
from instructor.access import (allow_access,
                               revoke_access,
                               list_with_level,
                               update_forum_role_membership)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessList(ModuleStoreTestCase):
    """ Test access listings. """
    def setUp(self):
        self.course = CourseFactory.create()

        self.instructors = [UserFactory.create() for _ in xrange(4)]
        for user in self.instructors:
            allow_access(self.course, user, 'instructor')
        self.beta_testers = [UserFactory.create() for _ in xrange(4)]
        for user in self.beta_testers:
            allow_access(self.course, user, 'beta')

    def test_list_instructors(self):
        instructors = list_with_level(self.course, 'instructor')
        self.assertEqual(set(instructors), set(self.instructors))

    def test_list_beta(self):
        beta_testers = list_with_level(self.course, 'beta')
        self.assertEqual(set(beta_testers), set(self.beta_testers))


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessAllow(ModuleStoreTestCase):
    """ Test access allow. """
    def setUp(self):
        self.course = CourseFactory.create()

    def test_allow(self):
        user = UserFactory()
        allow_access(self.course, user, 'staff')
        group = Group.objects.get(
            name=get_access_group_name(self.course, 'staff')
        )
        self.assertIn(user, group.user_set.all())

    def test_allow_twice(self):
        user = UserFactory()
        allow_access(self.course, user, 'staff')
        allow_access(self.course, user, 'staff')
        group = Group.objects.get(
            name=get_access_group_name(self.course, 'staff')
        )
        self.assertIn(user, group.user_set.all())

    def test_allow_beta(self):
        """ Test allow beta against list beta. """
        user = UserFactory()
        allow_access(self.course, user, 'beta')
        self.assertIn(user, list_with_level(self.course, 'beta'))

    @raises(ValueError)
    def test_allow_badlevel(self):
        user = UserFactory()
        allow_access(self.course, user, 'robot-not-a-level')
        group = Group.objects.get(name=get_access_group_name(self.course, 'robot-not-a-level'))
        self.assertIn(user, group.user_set.all())

    @raises(Exception)
    def test_allow_noneuser(self):
        user = None
        allow_access(self.course, user, 'staff')
        group = Group.objects.get(name=get_access_group_name(self.course, 'staff'))
        self.assertIn(user, group.user_set.all())

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessRevoke(ModuleStoreTestCase):
    """ Test access revoke. """
    def setUp(self):
        self.course = CourseFactory.create()

        self.staff = [UserFactory.create() for _ in xrange(4)]
        for user in self.staff:
            allow_access(self.course, user, 'staff')
        self.beta_testers = [UserFactory.create() for _ in xrange(4)]
        for user in self.beta_testers:
            allow_access(self.course, user, 'beta')

    def test_revoke(self):
        user = self.staff[0]
        revoke_access(self.course, user, 'staff')
        group = Group.objects.get(
            name=get_access_group_name(self.course, 'staff')
        )
        self.assertNotIn(user, group.user_set.all())

    def test_revoke_twice(self):
        user = self.staff[0]
        revoke_access(self.course, user, 'staff')
        group = Group.objects.get(
            name=get_access_group_name(self.course, 'staff')
        )
        self.assertNotIn(user, group.user_set.all())

    def test_revoke_beta(self):
        user = self.beta_testers[0]
        revoke_access(self.course, user, 'beta')
        self.assertNotIn(user, list_with_level(self.course, 'beta'))

    @raises(ValueError)
    def test_revoke_badrolename(self):
        user = UserFactory()
        revoke_access(self.course, user, 'robot-not-a-level')
        group = Group.objects.get(
            name=get_access_group_name(self.course, 'robot-not-a-level')
        )
        self.assertNotIn(user, group.user_set.all())


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessForum(ModuleStoreTestCase):
    """
    Test forum access control.
    """
    def setUp(self):
        self.course = CourseFactory.create()

        self.mod_role = Role.objects.create(
            course_id=self.course.id,
            name=FORUM_ROLE_MODERATOR
        )
        self.moderators = [UserFactory.create() for _ in xrange(4)]
        for user in self.moderators:
            self.mod_role.users.add(user)

    def test_allow(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())

    def test_allow_twice(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())

    @raises(Role.DoesNotExist)
    def test_allow_badrole(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, 'robot-not-a-real-role', 'allow')

    def test_revoke(self):
        user = self.moderators[0]
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    def test_revoke_twice(self):
        user = self.moderators[0]
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    def test_revoke_notallowed(self):
        user = UserFactory()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    @raises(Role.DoesNotExist)
    def test_revoke_badrole(self):
        user = self.moderators[0]
        update_forum_role_membership(self.course.id, user, 'robot-not-a-real-role', 'allow')

    @raises(ValueError)
    def test_bad_mode(self):
        user = UserFactory()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'robot-not-a-mode')
