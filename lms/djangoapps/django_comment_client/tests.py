from django.contrib.auth.models import User, Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings

from mock import Mock

from override_settings import override_settings

import xmodule.modulestore.django

from student.models import CourseEnrollment

from django.db.models.signals import m2m_changed, pre_delete, pre_save, post_delete, post_save
from django.dispatch.dispatcher import _make_id
import string
import random
from .permissions import has_permission
from .models import Role, Permission

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml import XMLModuleStore

import comment_client

from courseware.tests.tests import PageLoader, TEST_DATA_XML_MODULESTORE

#@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
#class TestCohorting(PageLoader):
#    """Check that cohorting works properly"""
#
#    def setUp(self):
#        xmodule.modulestore.django._MODULESTORES = {}
#
#        # Assume courses are there
#        self.toy = modulestore().get_course("edX/toy/2012_Fall")
#
#        # Create two accounts
#        self.student = 'view@test.com'
#        self.student2 = 'view2@test.com'
#        self.password = 'foo'
#        self.create_account('u1', self.student, self.password)
#        self.create_account('u2', self.student2, self.password)
#        self.activate_user(self.student)
#        self.activate_user(self.student2)
#
#    def test_create_thread(self):
#        my_save = Mock()
#        comment_client.perform_request = my_save
#
#        resp = self.client.post(
#            reverse('django_comment_client.base.views.create_thread',
#                    kwargs={'course_id': 'edX/toy/2012_Fall',
#                            'commentable_id': 'General'}),
#                                        {'some': "some",
#                                         'data': 'data'})
#        self.assertTrue(my_save.called)
#
#        #self.assertEqual(resp.status_code, 200)
#        #self.assertEqual(my_save.something, "expected", "complaint if not true")
#
#        self.toy.metadata["cohort_config"] = {"cohorted": True}
#
#        # call the view again ...
#
#       # assert that different things happened



class PermissionsTestCase(TestCase):
    def random_str(self, length=15, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(length))

    def setUp(self):

        self.course_id = "edX/toy/2012_Fall"

        self.moderator_role = Role.objects.get_or_create(name="Moderator", course_id=self.course_id)[0]
        self.student_role = Role.objects.get_or_create(name="Student", course_id=self.course_id)[0]

        self.student = User.objects.create(username=self.random_str(),
                            password="123456", email="john@yahoo.com")
        self.moderator = User.objects.create(username=self.random_str(),
                            password="123456", email="staff@edx.org")
        self.moderator.is_staff = True
        self.moderator.save()
        self.student_enrollment = CourseEnrollment.objects.create(user=self.student, course_id=self.course_id)
        self.moderator_enrollment = CourseEnrollment.objects.create(user=self.moderator, course_id=self.course_id)

    def tearDown(self):
        self.student_enrollment.delete()
        self.moderator_enrollment.delete()

# Do we need to have this? We shouldn't be deleting students, ever
#        self.student.delete()
#        self.moderator.delete()

    def testDefaultRoles(self):
        self.assertTrue(self.student_role in self.student.roles.all())
        self.assertTrue(self.moderator_role in self.moderator.roles.all())

    def testPermission(self):
        name = self.random_str()
        self.moderator_role.add_permission(name)
        self.assertTrue(has_permission(self.moderator, name, self.course_id))

        self.student_role.add_permission(name)
        self.assertTrue(has_permission(self.student, name, self.course_id))
