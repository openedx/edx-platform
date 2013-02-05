import string
import random
import collections

import factory
from django.test import TestCase                         

from django.contrib.auth.models import User
from student.models import UserProfile, CourseEnrollment
from django_comment_client.models import Role, Permission
import django_comment_client.permissions as p

class UserFactory(factory.Factory):
    FACTORY_FOR = User
    username = 'robot'
    password = '123456'
    email = 'robot@edx.org'
    is_active = True
    is_staff = False

class CourseEnrollmentFactory(factory.Factory):
    FACTORY_FOR = CourseEnrollment  
    user = factory.SubFactory(UserFactory)
    course_id = 'edX/toy/2012_Fall'

class RoleFactory(factory.Factory):
    FACTORY_FOR = Role
    name = 'Student'
    course_id = 'edX/toy/2012_Fall'

class PermissionFactory(factory.Factory):
    FACTORY_FOR = Permission  
    name = 'create_comment'


class PermissionsTestCase(TestCase):
    def setUp(self):
        self.course_id = "edX/toy/2012_Fall"

        self.student_role = RoleFactory(name='Student')
        self.moderator_role = RoleFactory(name='Moderator')
        self.student = UserFactory(username='student', email='student@edx.org')
        self.moderator = UserFactory(username='moderator', email='staff@edx.org', is_staff=True)
        self.update_thread_permission = PermissionFactory(name='update_thread')
        self.update_thread_permission.roles.add(self.student_role)
        self.update_thread_permission.roles.add(self.moderator_role)
        self.manage_moderator_permission = PermissionFactory(name='manage_moderator')
        self.manage_moderator_permission.roles.add(self.moderator_role)
        self.student_enrollment = CourseEnrollmentFactory(user=self.student)
        self.moderator_enrollment = CourseEnrollmentFactory(user=self.moderator)

        self.student_open_thread = {'content': {
                                    'closed': False,
                                    'user_id': str(self.student.id)}
                                    }
        self.student_closed_thread = {'content': {
                                    'closed': True,
                                    'user_id': str(self.student.id)}
                                    }

    def test_user_has_permission(self):
        s_ut = p.has_permission(self.student, 'update_thread', self.course_id)
        m_ut = p.has_permission(self.moderator, 'update_thread', self.course_id)
        s_mm = p.has_permission(self.student, 'manage_moderator', self.course_id)
        m_mm = p.has_permission(self.moderator, 'manage_moderator', self.course_id)
        self.assertTrue(s_ut)
        self.assertTrue(m_ut)
        self.assertFalse(s_mm)
        self.assertTrue(m_mm)

    def test_check_conditions(self):
        # Checks whether the discussion thread is open, or whether the author is user
        s_o = p.check_condition(self.student, 'is_open', self.course_id, self.student_open_thread)
        s_a = p.check_condition(self.student, 'is_author', self.course_id, self.student_open_thread)
        m_c = p.check_condition(self.moderator, 'is_open', self.course_id, self.student_closed_thread)
        m_a = p.check_condition(self.moderator,'is_author', self.course_id, self.student_open_thread)
        self.assertTrue(s_o)
        self.assertTrue(s_a)
        self.assertFalse(m_c)
        self.assertFalse(m_a)

    def test_check_conditions_and_permissions(self):
        # Check conditions
        ret = p.check_conditions_permissions(self.student,
                                            'is_open',
                                            self.course_id,
                                            data=self.student_open_thread)
        self.assertTrue(ret)

        # Check permissions
        ret = p.check_conditions_permissions(self.student, 
                                            'update_thread',
                                            self.course_id,
                                            data=self.student_open_thread)
        self.assertTrue(ret)

        # Check that a list of permissions/conditions will be OR'd
        ret = p.check_conditions_permissions(self.moderator, 
                                            ['is_open','manage_moderator'],
                                            self.course_id,
                                            data=self.student_open_thread)
        self.assertTrue(ret)

        # Check that a list of permissions will be OR'd
        ret = p.check_conditions_permissions(self.student, 
                                            ['update_thread','manage_moderator'],
                                            self.course_id,
                                            data=self.student_open_thread)
        self.assertTrue(ret)

        # Check that a list of list of permissions will be AND'd
        ret = p.check_conditions_permissions(self.student, 
                                            [['update_thread','manage_moderator']],
                                            self.course_id,
                                            data=self.student_open_thread)
        self.assertFalse(ret)

    def test_check_permissions_by_view(self):
        ret = p.check_permissions_by_view(self.student, self.course_id,
                                    self.student_open_thread, 'openclose_thread')
        self.assertFalse(ret)

        # Check a view permission that includes both a condition and a permission
        self.vote_permission = PermissionFactory(name='vote')
        self.vote_permission.roles.add(self.student_role)
        ret = p.check_permissions_by_view(self.student, self.course_id,
                                    self.student_open_thread, 'vote_for_comment')
        self.assertTrue(ret)