from django.test import TestCase
from nose.tools import raises
from django.contrib.auth.models import User, Group
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from django.test.utils import override_settings
from django.conf import settings
from uuid import uuid4

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from courseware.access import get_access_group_name
from django_comment_common.models import (Role,
                                          FORUM_ROLE_ADMINISTRATOR,
                                          FORUM_ROLE_MODERATOR,
                                          FORUM_ROLE_COMMUNITY_TA)
from instructor.access import allow_access, revoke_access, list_with_level, update_forum_role_membership

# mock dependency
# get_access_group_name = lambda course, role: '{0}_{1}'.format(course.course_id, role)


# moved here from old courseware/tests/tests.py
# when it disappeared this test broke.
def mongo_store_config(data_dir):
    '''
    Defines default module store using MongoModuleStore

    Use of this config requires mongo to be running
    '''
    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore_%s' % uuid4().hex,
                'fs_root': data_dir,
                'render_template': 'mitxmako.shortcuts.render_to_string',
            }
        }
    }
    store['direct'] = store['default']
    return store

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
# TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessControlDB(ModuleStoreTestCase):
    '''Test instructor access administration against database effects'''

    def setUp(self):
        # self.course_id = 'jus:/a/fake/c::rse/id'
        # self.course = MockCourse('jus:/a/fake/c::rse/id')
        self.course = CourseFactory.create()

    def test_allow(self):
        user = UserFactory()
        level = 'staff'

        allow_access(self.course, user, level)

        self.assertIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())

    def test_allow_twice(self):
        user = UserFactory()
        level = 'staff'

        allow_access(self.course, user, level)
        self.assertIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())
        allow_access(self.course, user, level)
        self.assertIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())

    def test_allow_revoke(self):
        user = UserFactory()
        level = 'staff'

        allow_access(self.course, user, level)
        self.assertIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())
        revoke_access(self.course, user, level)
        self.assertNotIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())
        allow_access(self.course, user, level)
        self.assertIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())
        revoke_access(self.course, user, level)
        self.assertNotIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())

    def test_revoke_without_group(self):
        user = UserFactory()
        level = 'staff'

        revoke_access(self.course, user, level)
        self.assertNotIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())

    def test_revoke_with_group(self):
        user = UserFactory()
        level = 'staff'

        Group(name=get_access_group_name(self.course, level))
        revoke_access(self.course, user, level)
        self.assertNotIn(user, Group.objects.get(name=get_access_group_name(self.course, 'staff')).user_set.all())

    def test_allow_disallow_multiuser(self):
        users = [UserFactory() for _ in xrange(3)]
        levels = ['staff', 'instructor', 'staff']
        antilevels = ['instructor', 'staff', 'instructor']

        allow_access(self.course, users[0], levels[0])
        allow_access(self.course, users[1], levels[1])
        allow_access(self.course, users[2], levels[2])
        self.assertIn(users[0], Group.objects.get(name=get_access_group_name(self.course, levels[0])).user_set.all())
        self.assertIn(users[1], Group.objects.get(name=get_access_group_name(self.course, levels[1])).user_set.all())
        self.assertIn(users[2], Group.objects.get(name=get_access_group_name(self.course, levels[2])).user_set.all())

        revoke_access(self.course, users[0], levels[0])
        revoke_access(self.course, users[0], antilevels[0])
        self.assertNotIn(users[0], Group.objects.get(name=get_access_group_name(self.course, levels[0])).user_set.all())
        self.assertIn(users[1], Group.objects.get(name=get_access_group_name(self.course, levels[1])).user_set.all())
        self.assertIn(users[2], Group.objects.get(name=get_access_group_name(self.course, levels[2])).user_set.all())

        revoke_access(self.course, users[1], levels[1])
        allow_access(self.course, users[0], antilevels[0])
        self.assertNotIn(users[0], Group.objects.get(name=get_access_group_name(self.course, levels[0])).user_set.all())
        self.assertIn(users[0], Group.objects.get(name=get_access_group_name(self.course, antilevels[0])).user_set.all())
        self.assertNotIn(users[1], Group.objects.get(name=get_access_group_name(self.course, levels[1])).user_set.all())
        self.assertIn(users[2], Group.objects.get(name=get_access_group_name(self.course, levels[2])).user_set.all())


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessControlPrefilledDB(ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()

        # setup instructors
        self.instructors = set([UserFactory.create(), UserFactory.create()])
        [allow_access(self.course, user, 'instructor') for user in self.instructors]

    def test_list_with_level(self):
        instructors = set(list_with_level(self.course, 'instructor'))
        self.assertEqual(instructors, self.instructors)

    def test_list_with_level_not_yet_group(self):
        instructors = set(list_with_level(self.course, 'staff'))
        self.assertEqual(instructors, set())

    def test_list_with_level_bad_group(self):
        self.assertEqual(set(list_with_level(self.course, 'robot-definitely-not-a-group')), set())

    def test_list_with_level_beta(self):
        beta_testers_result = set(list_with_level(self.course, 'beta'))
        self.assertEqual(set(), beta_testers_result)

        beta_testers = set([UserFactory.create(), UserFactory.create()])
        [allow_access(self.course, user, 'beta') for user in beta_testers]
        beta_testers_result = set(list_with_level(self.course, 'beta'))
        self.assertEqual(beta_testers, beta_testers_result)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorAccessForumDB(ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()

        self.moderators = set([UserFactory.create() for _ in xrange(4)])
        self.mod_role = Role.objects.create(course_id=self.course.id, name=FORUM_ROLE_MODERATOR)
        [self.mod_role.users.add(user) for user in self.moderators]

    def test_update_forum_role_membership_allow_existing_role(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())

    def test_update_forum_role_membership_allow_existing_role_allowed_user(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'allow')
        self.assertIn(user, self.mod_role.users.all())

    @raises(Role.DoesNotExist)
    def test_update_forum_role_membership_allow_not_existing_role(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_COMMUNITY_TA, 'allow')

    def test_update_forum_role_membership_revoke_existing_role(self):
        user = iter(self.moderators).next()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    def test_update_forum_role_membership_revoke_existing_role_revoked_user(self):
        user = iter(self.moderators).next()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'revoke')
        self.assertNotIn(user, self.mod_role.users.all())

    @raises(Role.DoesNotExist)
    def test_update_forum_role_membership_revoke_not_existing_role(self):
        user = iter(self.moderators).next()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_COMMUNITY_TA, 'revoke')

    @raises(Role.DoesNotExist)
    def test_update_forum_role_membership_bad_role_allow(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, 'robot-definitely-not-a-forum-role', 'allow')

    @raises(Role.DoesNotExist)
    def test_update_forum_role_membership_bad_role_revoke(self):
        user = UserFactory.create()
        update_forum_role_membership(self.course.id, user, 'robot-definitely-not-a-forum-role', 'revoke')

    @raises(ValueError)
    def test_update_forum_role_membership_bad_mode(self):
        user = iter(self.moderators).next()
        update_forum_role_membership(self.course.id, user, FORUM_ROLE_MODERATOR, 'robot-not-a-mode')
