from factory import DjangoModelFactory
import unittest
import nose.tools
import json

from django.http import Http404
from django.test.client import Client
from django.test.utils import override_settings
import mitxmako.middleware

from courseware.models import XModuleContentField
import instructor.hint_manager as view
from student.tests.factories import UserFactory, AdminFactory
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class HintsFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleContentField
    definition_id = 'i4x://Me/19.002/crowdsource_hinter/crowdsource_hinter_001'
    field_name = 'hints'
    value = json.dumps({'1.0': 
                               {'1': ['Hint 1', 2],
                                '3': ['Hint 3', 12]},
                        '2.0':
                               {'4': ['Hint 4', 3]}
                        })

class ModQueueFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleContentField
    definition_id = 'i4x://Me/19.002/crowdsource_hinter/crowdsource_hinter_001'
    field_name = 'mod_queue'
    value = json.dumps({'2.0':
                               {'2': ['Hint 2', 1]}
                        })

class PKFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleContentField
    definition_id = 'i4x://Me/19.002/crowdsource_hinter/crowdsource_hinter_001'
    field_name = 'hint_pk'
    value = 5
            
@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class HintManagerTest(ModuleStoreTestCase):

    def setUp(self):
        """
        Makes a course, which will be the same for all tests.
        Set up mako middleware, which is necessary for template rendering to happen.
        """
        course = CourseFactory.create(org='Me', number='19.002', display_name='test_course')
        # mitxmako.middleware.MakoMiddleware()


    def test_student_block(self):
        """
        Makes sure that students cannot see the hint management view.
        """
        c = Client()
        user = UserFactory.create(username='robot', email='robot@edx.org', password='test')
        c.login(username='robot', password='test')
        out = c.get('/courses/Me/19.002/test_course/hint_manager')
        print out
        self.assertTrue('Sorry, but students are not allowed to access the hint manager!' in out.content)

    def test_staff_access(self):
        """
        Makes sure that staff can access the hint management view.
        """
        c = Client()
        user = UserFactory.create(username='robot', email='robot@edx.org', password='test', is_staff=True)
        c.login(username='robot', password='test')
        out = c.get('/courses/Me/19.002/test_course/hint_manager')
        print out
        self.assertTrue('Hints Awaiting Moderation' in out.content)



