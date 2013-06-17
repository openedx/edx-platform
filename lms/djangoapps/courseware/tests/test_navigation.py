import logging
import json
import random

from urlparse import urlsplit, urlunsplit
from uuid import uuid4

from django.contrib.auth.models import User
from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import xmodule.modulestore.django

from student.models import Registration
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml import XMLModuleStore

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from mongo_login_helpers import *

log = logging.getLogger("mitx." + __name__)


def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def get_user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def get_registration(email):
    '''look up registration object by email'''
    return Registration.objects.get(user__email=email)


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


def xml_store_config(data_dir):
    '''Defines default module store using XMLModuleStore'''
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
# TEST_DATA_DRAFT_MONGO_MODULESTORE = draft_mongo_store_config(TEST_DATA_DIR)


class LoginEnrollmentTestCase(TestCase):

    '''
    Base TestCase providing support for user creation,
    activation, login, and course enrollment
    '''

    def assertRedirectsNoFollow(self, response, expected_url):
        """
        http://devblog.point2.com/2010/04/23/djangos-assertredirects-little-gotcha/

        Don't check that the redirected-to page loads--there should be other tests for that.

        Some of the code taken from django.test.testcases.py
        """
        self.assertEqual(response.status_code, 302,
                         'Response status code was %d instead of 302'
                         % (response.status_code))
        url = response['Location']

        e_scheme, e_netloc, e_path, e_query, e_fragment = urlsplit(expected_url)
        if not (e_scheme or e_netloc):
            expected_url = urlunsplit(('http', 'testserver',
                                       e_path, e_query, e_fragment))

        self.assertEqual(url, expected_url,
                         "Response redirected to '%s', expected '%s'" %
                         (url, expected_url))

    def setup_viewtest_user(self):
        '''create a user account, activate, and log in'''
        self.viewtest_email = 'view@test.com'
        self.viewtest_password = 'foo'
        self.viewtest_username = 'viewtest'
        self.create_account(self.viewtest_username,
                            self.viewtest_email, self.viewtest_password)
        self.activate_user(self.viewtest_email)
        self.login(self.viewtest_email, self.viewtest_password)

    # ============ User creation and login ==============

    def _login(self, email, password):
        '''Login.  View should always return 200.  The success/fail is in the
        returned json'''
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': password})
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, password):
        '''Login, check that it worked.'''
        resp = self._login(email, password)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def logout(self):
        '''Logout, check that it worked.'''
        resp = self.client.get(reverse('logout'), {})
        # should redirect
        self.assertEqual(resp.status_code, 302)
        return resp

    def _create_account(self, username, email, password):
        '''Try to create an account.  No error checking'''
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': password,
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, password):
        '''Create the account and check that it worked'''
        resp = self._create_account(username, email, password)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(get_user(email).is_active)

        return resp

    def _activate_user(self, email):
        '''Look up the activation key for the user, then hit the activate view.
        No error checking'''
        activation_key = get_registration(email).activation_key

        # and now we try to activate
        url = reverse('activate', kwargs={'key': activation_key})
        resp = self.client.get(url)
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(get_user(email).is_active)

    def try_enroll(self, course):
        """Try to enroll.  Return bool success instead of asserting it."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'enroll',
            'course_id': course.id,
        })
        print ('Enrollment in %s result status code: %s'
               % (course.location.url(), str(resp.status_code)))
        return resp.status_code == 200

    def enroll(self, course):
        """Enroll the currently logged-in user, and check that it worked."""
        result = self.try_enroll(course)
        self.assertTrue(result)

    def unenroll(self, course):
        """Unenroll the currently logged-in user, and check that it worked."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'unenroll',
            'course_id': course.id,
        })
        self.assertTrue(resp.status_code == 200)

    def check_for_get_code(self, code, url):
        """
        Check that we got the expected code when accessing url via GET.
        Returns the response.
        """
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp

    def check_for_post_code(self, code, url, data={}):
        """
        Check that we got the expected code when accessing url via POST.
        Returns the response.
        """
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, code,
                         "got code %d for url '%s'. Expected code %d"
                         % (resp.status_code, url, code))
        return resp


class ActivateLoginTest(LoginEnrollmentTestCase):
    '''Test logging in and logging out'''
    def setUp(self):
        self.setup_viewtest_user()

    def test_activate_login(self):
        '''Test login -- the setup function does all the work'''
        pass

    def test_logout(self):
        '''Test logout -- setup function does login'''
        self.logout()


class PageLoaderTestCase(LoginEnrollmentTestCase):
    ''' Base class that adds a function to load all pages in a modulestore '''

    def check_random_page_loads(self, module_store):
        '''
        Choose a page in the course randomly, and assert that it loads
        '''
       # enroll in the course before trying to access pages
        courses = module_store.get_courses()
        self.assertEqual(len(courses), 1)
        course = courses[0]
        self.enroll(course)
        course_id = course.id

        # Search for items in the course
        # None is treated as a wildcard
        course_loc = course.location
        location_query = Location(course_loc.tag, course_loc.org,
                                  course_loc.course, None, None, None)

        items = module_store.get_items(location_query)

        if len(items) < 1:
            self.fail('Could not retrieve any items from course')
        else:
            descriptor = random.choice(items)

        # We have ancillary course information now as modules
        # and we can't simply use 'jump_to' to view them
        if descriptor.location.category == 'about':
            self._assert_loads('about_course',
                               {'course_id': course_id},
                               descriptor)

        elif descriptor.location.category == 'static_tab':
            kwargs = {'course_id': course_id,
                      'tab_slug': descriptor.location.name}
            self._assert_loads('static_tab', kwargs, descriptor)

        elif descriptor.location.category == 'course_info':
            self._assert_loads('info', {'course_id': course_id},
                               descriptor)

        elif descriptor.location.category == 'custom_tag_template':
            pass

        else:

            kwargs = {'course_id': course_id,
                      'location': descriptor.location.url()}

            self._assert_loads('jump_to', kwargs, descriptor,
                               expect_redirect=True,
                               check_content=True)

    def _assert_loads(self, django_url, kwargs, descriptor,
                      expect_redirect=False,
                      check_content=False):
        '''
        Assert that the url loads correctly.
        If expect_redirect, then also check that we were redirected.
        If check_content, then check that we don't get
        an error message about unavailable modules.
        '''

        url = reverse(django_url, kwargs=kwargs)
        response = self.client.get(url, follow=True)

        if response.status_code != 200:
            self.fail('Status %d for page %s' %
                      (response.status_code, descriptor.location.url()))

        if expect_redirect:
            self.assertEqual(response.redirect_chain[0][1], 302)

        if check_content:
            unavailable_msg = "this module is temporarily unavailable"
            self.assertEqual(response.content.find(unavailable_msg), -1)
            self.assertFalse(isinstance(descriptor, ErrorDescriptor))


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestCoursesLoadTestCase_XmlModulestore(PageLoaderTestCase):
    '''Check that all pages in test courses load properly from XML'''

    def setUp(self):
        super(TestCoursesLoadTestCase_XmlModulestore, self).setUp()
        self.setup_viewtest_user()
        xmodule.modulestore.django._MODULESTORES = {}

    def test_toy_course_loads(self):
        module_class = 'xmodule.hidden_module.HiddenDescriptor'
        module_store = XMLModuleStore(TEST_DATA_DIR,
                                      default_class=module_class,
                                      course_dirs=['toy'],
                                      load_error_modules=True)

        self.check_random_page_loads(module_store)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestCoursesLoadTestCase_MongoModulestore(PageLoaderTestCase):
    '''Check that all pages in test courses load properly from Mongo'''

    def setUp(self):
        super(TestCoursesLoadTestCase_MongoModulestore, self).setUp()
        self.setup_viewtest_user()
        xmodule.modulestore.django._MODULESTORES = {}
        modulestore().collection.drop()

    def test_toy_course_loads(self):
        module_store = modulestore()
        import_from_xml(module_store, TEST_DATA_DIR, ['toy'])
        self.check_random_page_loads(module_store)

    def test_full_textbooks_loads(self):
        module_store = modulestore()
        import_from_xml(module_store, TEST_DATA_DIR, ['full'])

        course = module_store.get_item(Location(['i4x', 'edX', 'full', 'course', '6.002_Spring_2012', None]))

        self.assertGreater(len(course.textbooks), 0)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestNavigation(MongoLoginHelpers):

    """Check that navigation state is saved properly"""

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.course = CourseFactory.create()
        self.full = CourseFactory.create(display_name='Robot_Sub_Course')
        self.chapter0 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='Overview')
        self.chapter9 = ItemFactory.create(parent_location=self.course.location,
                                           display_name='factory_chapter')
        self.section0 = ItemFactory.create(parent_location=self.chapter0.location,
                                           display_name='Welcome')
        self.section9 = ItemFactory.create(parent_location=self.chapter9.location,
                                           display_name='factory_section')

        #Create two accounts
        self.student = 'view@test.com'
        self.student2 = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.student2, self.password)
        self.activate_user(self.student)
        self.activate_user(self.student2)

    def test_accordion_state(self):
        """Make sure that the accordion remembers where you were properly"""
        self.login(self.student, self.password)
        self.enroll(self.course)
        self.enroll(self.full)

        # First request should redirect to ToyVideos

        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id}))

        # Don't use no-follow, because state should
        # only be saved once we actually hit the section
        self.assertRedirects(resp, reverse(
            'courseware_section', kwargs={'course_id': self.course.id,
                                          'chapter': 'Overview',
                                          'section': 'Welcome'}))

        # Hitting the couseware tab again should
        # redirect to the first chapter: 'Overview'
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id}))

        self.assertRedirectsNoFollow(resp, reverse('courseware_chapter',
                                     kwargs={'course_id': self.course.id,
                                             'chapter': 'Overview'}))

        # Now we directly navigate to a section in a different chapter
        self.check_for_get_code(200, reverse('courseware_section',
                                             kwargs={'course_id': self.course.id,
                                                     'chapter': 'factory_chapter',
                                                     'section': 'factory_section'}))

        # And now hitting the courseware tab should redirect to 'secret:magic'
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id}))

        self.assertRedirectsNoFollow(resp, reverse('courseware_chapter',
                                     kwargs={'course_id': self.course.id,
                                             'chapter': 'factory_chapter'}))
