from django.test import TestCase
from django.contrib.auth.models import User, Group
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from django.test.utils import override_settings
from django.conf import settings
from courseware.tests.tests import mongo_store_config, xml_store_config

from student.models import CourseEnrollment, CourseEnrollmentAllowed
from courseware.access import get_access_group_name
from instructor.access import allow_access, revoke_access

# mock dependency
# get_access_group_name = lambda course, role: '{0}_{1}'.format(course.course_id, role)

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


    # def test_allow_disallow_multirole(self):


class MockCourse(object):
    def __init__(self, course_id):
        self.course_id = course_id
