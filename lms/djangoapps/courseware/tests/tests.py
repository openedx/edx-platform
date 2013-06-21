'''
Test for lms courseware app
'''
import logging
import json
import random

from urlparse import urlsplit, urlunsplit
from uuid import uuid4

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import RequestFactory
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import xmodule.modulestore.django

# Need access to internal func to put users in the right group
from courseware import grades
from courseware.model_data import ModelDataCache
from courseware.access import (has_access, _course_staff_group_name,
                               course_beta_test_group_name)

from student.models import Registration
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.xml import XMLModuleStore
import datetime
from django.utils.timezone import UTC

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
                'render_template': 'mitxmako.shortcuts.render_to_string'
            }
        }
    }
    store['direct'] = store['default']
    return store


def draft_mongo_store_config(data_dir):
    '''Defines default module store using DraftMongoModuleStore'''
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore_%s' % uuid4().hex,
                'fs_root': data_dir,
                'render_template': 'mitxmako.shortcuts.render_to_string',
            }
        },
        'direct': {
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
TEST_DATA_DRAFT_MONGO_MODULESTORE = draft_mongo_store_config(TEST_DATA_DIR)


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


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestNavigation(LoginEnrollmentTestCase):
    """Check that navigation state is saved properly"""

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        # Assume courses are there
        self.full = modulestore().get_course("edX/full/6.002_Spring_2012")
        self.toy = modulestore().get_course("edX/toy/2012_Fall")

        # Create two accounts
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
        self.enroll(self.toy)
        self.enroll(self.full)

        # First request should redirect to ToyVideos
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.toy.id}))

        # Don't use no-follow, because state should
        # only be saved once we actually hit the section
        self.assertRedirects(resp, reverse(
            'courseware_section', kwargs={'course_id': self.toy.id,
                                          'chapter': 'Overview',
                                          'section': 'Toy_Videos'}))

        # Hitting the couseware tab again should
        # redirect to the first chapter: 'Overview'
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.toy.id}))

        self.assertRedirectsNoFollow(resp, reverse('courseware_chapter',
                                     kwargs={'course_id': self.toy.id,
                                             'chapter': 'Overview'}))

        # Now we directly navigate to a section in a different chapter
        self.check_for_get_code(200, reverse('courseware_section',
                                             kwargs={'course_id': self.toy.id,
                                                     'chapter': 'secret:magic',
                                                     'section': 'toyvideo'}))

        # And now hitting the courseware tab should redirect to 'secret:magic'
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.toy.id}))

        self.assertRedirectsNoFollow(resp, reverse('courseware_chapter',
                                     kwargs={'course_id': self.toy.id,
                                             'chapter': 'secret:magic'}))


@override_settings(MODULESTORE=TEST_DATA_DRAFT_MONGO_MODULESTORE)
class TestDraftModuleStore(TestCase):
    def test_get_items_with_course_items(self):
        store = modulestore()

        # fix was to allow get_items() to take the course_id parameter
        store.get_items(Location(None, None, 'vertical', None, None),
                        course_id='abc', depth=0)

        # test success is just getting through the above statement.
        # The bug was that 'course_id' argument was
        # not allowed to be passed in (i.e. was throwing exception)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestViewAuth(LoginEnrollmentTestCase):
    """Check that view authentication works properly"""

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.full = modulestore().get_course("edX/full/6.002_Spring_2012")
        self.toy = modulestore().get_course("edX/toy/2012_Fall")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

    def test_instructor_pages(self):
        """Make sure only instructors for the course
        or staff can load the instructor
        dashboard, the grade views, and student profile pages"""

        # First, try with an enrolled student
        self.login(self.student, self.password)
        # shouldn't work before enroll
        response = self.client.get(reverse('courseware',
                                   kwargs={'course_id': self.toy.id}))

        self.assertRedirectsNoFollow(response,
                                     reverse('about_course',
                                             args=[self.toy.id]))
        self.enroll(self.toy)
        self.enroll(self.full)
        # should work now -- redirect to first page
        response = self.client.get(reverse('courseware',
                                   kwargs={'course_id': self.toy.id}))
        self.assertRedirectsNoFollow(response,
                                     reverse('courseware_section',
                                             kwargs={'course_id': self.toy.id,
                                                     'chapter': 'Overview',
                                                     'section': 'Toy_Videos'}))

        def instructor_urls(course):
            "list of urls that only instructors/staff should be able to see"
            urls = [reverse(name, kwargs={'course_id': course.id}) for name in (
                'instructor_dashboard',
                'gradebook',
                'grade_summary',)]

            urls.append(reverse('student_progress',
                                kwargs={'course_id': course.id,
                                        'student_id': get_user(self.student).id}))
            return urls

        # Randomly sample an instructor page
        url = random.choice(instructor_urls(self.toy) +
                            instructor_urls(self.full))

        # Shouldn't be able to get to the instructor pages
        print 'checking for 404 on {0}'.format(url)
        self.check_for_get_code(404, url)

        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.toy.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(get_user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)

        # Now should be able to get to the toy course, but not the full course
        url = random.choice(instructor_urls(self.toy))
        print 'checking for 200 on {0}'.format(url)
        self.check_for_get_code(200, url)

        url = random.choice(instructor_urls(self.full))
        print 'checking for 404 on {0}'.format(url)
        self.check_for_get_code(404, url)

        # now also make the instructor staff
        instructor = get_user(self.instructor)
        instructor.is_staff = True
        instructor.save()

        # and now should be able to load both
        url = random.choice(instructor_urls(self.toy) +
                            instructor_urls(self.full))
        print 'checking for 200 on {0}'.format(url)
        self.check_for_get_code(200, url)

    def run_wrapped(self, test):
        """
        test.py turns off start dates.  Enable them.
        Because settings is global, be careful not to mess it up for other tests
        (Can't use override_settings because we're only changing part of the
        MITX_FEATURES dict)
        """
        oldDSD = settings.MITX_FEATURES['DISABLE_START_DATES']

        try:
            settings.MITX_FEATURES['DISABLE_START_DATES'] = False
            test()
        finally:
            settings.MITX_FEATURES['DISABLE_START_DATES'] = oldDSD

    def test_dark_launch(self):
        """Make sure that before course start, students can't access course
        pages, but instructors can"""
        self.run_wrapped(self._do_test_dark_launch)

    def test_enrollment_period(self):
        """Check that enrollment periods work"""
        self.run_wrapped(self._do_test_enrollment_period)

    def test_beta_period(self):
        """Check that beta-test access works"""
        self.run_wrapped(self._do_test_beta_period)

    def _do_test_dark_launch(self):
        """Actually do the test, relying on settings to be right."""

        # Make courses start in the future
        tomorrow = datetime.datetime.now(UTC()) + datetime.timedelta(days=1)
        self.toy.lms.start = tomorrow
        self.full.lms.start = tomorrow

        self.assertFalse(self.toy.has_started())
        self.assertFalse(self.full.has_started())
        self.assertFalse(settings.MITX_FEATURES['DISABLE_START_DATES'])

        def reverse_urls(names, course):
            """Reverse a list of course urls"""
            return [reverse(name, kwargs={'course_id': course.id})
                    for name in names]

        def dark_student_urls(course):
            """
            list of urls that students should be able to see only
            after launch, but staff should see before
            """
            urls = reverse_urls(['info', 'progress'], course)
            urls.extend([
                reverse('book', kwargs={'course_id': course.id,
                                        'book_index': index})
                for index, book in enumerate(course.textbooks)
            ])
            return urls

        def light_student_urls(course):
            """
            list of urls that students should be able to see before
            launch.
            """
            urls = reverse_urls(['about_course'], course)
            urls.append(reverse('courses'))

            return urls

        def instructor_urls(course):
            """list of urls that only instructors/staff should be able to see"""
            urls = reverse_urls(['instructor_dashboard',
                                 'gradebook', 'grade_summary'], course)
            return urls

        def check_non_staff(course):
            """Check that access is right for non-staff in course"""
            print '=== Checking non-staff access for {0}'.format(course.id)

            # Randomly sample a dark url
            url = random.choice(instructor_urls(course) +
                                dark_student_urls(course) +
                                reverse_urls(['courseware'], course))
            print 'checking for 404 on {0}'.format(url)
            self.check_for_get_code(404, url)

            # Randomly sample a light url
            url = random.choice(light_student_urls(course))
            print 'checking for 200 on {0}'.format(url)
            self.check_for_get_code(200, url)

        def check_staff(course):
            """Check that access is right for staff in course"""
            print '=== Checking staff access for {0}'.format(course.id)

            # Randomly sample a url
            url = random.choice(instructor_urls(course) +
                                dark_student_urls(course) +
                                light_student_urls(course))
            print 'checking for 200 on {0}'.format(url)
            self.check_for_get_code(200, url)

            # The student progress tab is not accessible to a student
            # before launch, so the instructor view-as-student feature
            # should return a 404 as well.
            # TODO (vshnayder): If this is not the behavior we want, will need
            # to make access checking smarter and understand both the effective
            # user (the student), and the requesting user (the prof)
            url = reverse('student_progress',
                          kwargs={'course_id': course.id,
                                  'student_id': get_user(self.student).id})
            print 'checking for 404 on view-as-student: {0}'.format(url)
            self.check_for_get_code(404, url)

            # The courseware url should redirect, not 200
            url = reverse_urls(['courseware'], course)[0]
            self.check_for_get_code(302, url)

        # First, try with an enrolled student
        print '=== Testing student access....'
        self.login(self.student, self.password)
        self.enroll(self.toy)
        self.enroll(self.full)

        # shouldn't be able to get to anything except the light pages
        check_non_staff(self.toy)
        check_non_staff(self.full)

        print '=== Testing course instructor access....'
        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.toy.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(get_user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        # Enroll in the classes---can't see courseware otherwise.
        self.enroll(self.toy)
        self.enroll(self.full)

        # should now be able to get to everything for toy course
        check_non_staff(self.full)
        check_staff(self.toy)

        print '=== Testing staff access....'
        # now also make the instructor staff
        instructor = get_user(self.instructor)
        instructor.is_staff = True
        instructor.save()

        # and now should be able to load both
        check_staff(self.toy)
        check_staff(self.full)

    def _do_test_enrollment_period(self):
        """Actually do the test, relying on settings to be right."""

        # Make courses start in the future
        tomorrow = datetime.datetime.now(UTC()) + datetime.timedelta(days=1)
        nextday = tomorrow + datetime.timedelta(days=1)
        yesterday = datetime.datetime.now(UTC()) - datetime.timedelta(days=1)

        print "changing"
        # toy course's enrollment period hasn't started
        self.toy.enrollment_start = tomorrow
        self.toy.enrollment_end = nextday

        # full course's has
        self.full.enrollment_start = yesterday
        self.full.enrollment_end = tomorrow

        print "login"
        # First, try with an enrolled student
        print '=== Testing student access....'
        self.login(self.student, self.password)
        self.assertFalse(self.try_enroll(self.toy))
        self.assertTrue(self.try_enroll(self.full))

        print '=== Testing course instructor access....'
        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.toy.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(get_user(self.instructor))

        print "logout/login"
        self.logout()
        self.login(self.instructor, self.password)
        print "Instructor should be able to enroll in toy course"
        self.assertTrue(self.try_enroll(self.toy))

        print '=== Testing staff access....'
        # now make the instructor global staff, but not in the instructor group
        group.user_set.remove(get_user(self.instructor))
        instructor = get_user(self.instructor)
        instructor.is_staff = True
        instructor.save()

        # unenroll and try again
        self.unenroll(self.toy)
        self.assertTrue(self.try_enroll(self.toy))

    def _do_test_beta_period(self):
        """Actually test beta periods, relying on settings to be right."""

        # trust, but verify :)
        self.assertFalse(settings.MITX_FEATURES['DISABLE_START_DATES'])

        # Make courses start in the future
        tomorrow = datetime.datetime.now(UTC()) + datetime.timedelta(days=1)

        # toy course's hasn't started
        self.toy.lms.start = tomorrow
        self.assertFalse(self.toy.has_started())

        # but should be accessible for beta testers
        self.toy.lms.days_early_for_beta = 2

        # student user shouldn't see it
        student_user = get_user(self.student)
        self.assertFalse(has_access(student_user, self.toy, 'load'))

        # now add the student to the beta test group
        group_name = course_beta_test_group_name(self.toy.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(student_user)

        # now the student should see it
        self.assertTrue(has_access(student_user, self.toy, 'load'))


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestSubmittingProblems(LoginEnrollmentTestCase):
    """Check that a course gets graded properly"""

    # Subclasses should specify the course slug
    course_slug = "UNKNOWN"
    course_when = "UNKNOWN"

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        course_name = "edX/%s/%s" % (self.course_slug, self.course_when)
        self.course = modulestore().get_course(course_name)
        assert self.course, "Couldn't load course %r" % course_name

        # create a test student
        self.student = 'view@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.activate_user(self.student)
        self.enroll(self.course)

        self.student_user = get_user(self.student)

        self.factory = RequestFactory()

    def problem_location(self, problem_url_name):
        return "i4x://edX/{}/problem/{}".format(self.course_slug, problem_url_name)

    def modx_url(self, problem_location, dispatch):
        return reverse(
                    'modx_dispatch',
                    kwargs={
                        'course_id': self.course.id,
                        'location': problem_location,
                        'dispatch': dispatch,
                        }
                    )

    def submit_question_answer(self, problem_url_name, responses):
        """
        Submit answers to a question.

        Responses is a dict mapping problem ids (not sure of the right term)
        to answers:
            {'2_1': 'Correct', '2_2': 'Incorrect'}

        """
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_check')
        answer_key_prefix = 'input_i4x-edX-{}-problem-{}_'.format(self.course_slug, problem_url_name)
        resp = self.client.post(modx_url,
            { (answer_key_prefix + k): v for k, v in responses.items() }
            )
        return resp

    def reset_question_answer(self, problem_url_name):
        '''resets specified problem for current user'''
        problem_location = self.problem_location(problem_url_name)
        modx_url = self.modx_url(problem_location, 'problem_reset')
        resp = self.client.post(modx_url)
        return resp


class TestCourseGrader(TestSubmittingProblems):
    """Check that a course gets graded properly"""

    course_slug = "graded"
    course_when = "2012_Fall"

    def get_grade_summary(self):
        '''calls grades.grade for current user and course'''
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student_user, self.course)

        fake_request = self.factory.get(reverse('progress',
                                        kwargs={'course_id': self.course.id}))

        return grades.grade(self.student_user, fake_request,
                            self.course, model_data_cache)

    def get_homework_scores(self):
        '''get scores for homeworks'''
        return self.get_grade_summary()['totaled_scores']['Homework']

    def get_progress_summary(self):
        '''return progress summary structure for current user and course'''
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.course.id, self.student_user, self.course)

        fake_request = self.factory.get(reverse('progress',
                                        kwargs={'course_id': self.course.id}))

        progress_summary = grades.progress_summary(self.student_user,
                                                   fake_request,
                                                   self.course,
                                                   model_data_cache)
        return progress_summary

    def check_grade_percent(self, percent):
        '''assert that percent grade is as expected'''
        grade_summary = self.get_grade_summary()
        self.assertEqual(grade_summary['percent'], percent)

    def test_get_graded(self):
        #### Check that the grader shows we have 0% in the course
        self.check_grade_percent(0)

        #### Submit the answers to a few problems as ajax calls
        def earned_hw_scores():
            """Global scores, each Score is a Problem Set"""
            return [s.earned for s in self.get_homework_scores()]

        def score_for_hw(hw_url_name):
            """returns list of scores for a given url"""
            hw_section = [section for section
                          in self.get_progress_summary()[0]['sections']
                          if section.get('url_name') == hw_url_name][0]
            return [s.earned for s in hw_section['scores']]

        # Only get half of the first problem correct
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Incorrect'})
        self.check_grade_percent(0.06)
        self.assertEqual(earned_hw_scores(), [1.0, 0, 0])  # Order matters
        self.assertEqual(score_for_hw('Homework1'), [1.0, 0.0])

        # Get both parts of the first problem correct
        self.reset_question_answer('H1P1')
        self.submit_question_answer('H1P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.13)
        self.assertEqual(earned_hw_scores(), [2.0, 0, 0])
        self.assertEqual(score_for_hw('Homework1'), [2.0, 0.0])

        # This problem is shown in an ABTest
        self.submit_question_answer('H1P2', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(earned_hw_scores(), [4.0, 0.0, 0])
        self.assertEqual(score_for_hw('Homework1'), [2.0, 2.0])

        # This problem is hidden in an ABTest.
        # Getting it correct doesn't change total grade
        self.submit_question_answer('H1P3', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.25)
        self.assertEqual(score_for_hw('Homework1'), [2.0, 2.0])

        # On the second homework, we only answer half of the questions.
        # Then it will be dropped when homework three becomes the higher percent
        # This problem is also weighted to be 4 points (instead of default of 2)
        # If the problem was unweighted the percent would have been 0.38 so we
        # know it works.
        self.submit_question_answer('H2P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.42)
        self.assertEqual(earned_hw_scores(), [4.0, 4.0, 0])

        # Third homework
        self.submit_question_answer('H3P1', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.42)  # Score didn't change
        self.assertEqual(earned_hw_scores(), [4.0, 4.0, 2.0])

        self.submit_question_answer('H3P2', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(0.5)  # Now homework2 dropped. Score changes
        self.assertEqual(earned_hw_scores(), [4.0, 4.0, 4.0])

        # Now we answer the final question (worth half of the grade)
        self.submit_question_answer('FinalQuestion', {'2_1': 'Correct', '2_2': 'Correct'})
        self.check_grade_percent(1.0)  # Hooray! We got 100%


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestSchematicResponse(TestSubmittingProblems):
    """Check that we can submit a schematic response, and it answers properly."""

    course_slug = "embedded_python"
    course_when = "2013_Spring"

    def test_schematic(self):
        resp = self.submit_question_answer('schematic_problem',
            { '2_1': json.dumps(
                [['transient', {'Z': [
                [0.0000004, 2.8],
                [0.0000009, 2.8],
                [0.0000014, 2.8],
                [0.0000019, 2.8],
                [0.0000024, 2.8],
                [0.0000029, 0.2],
                [0.0000034, 0.2],
                [0.0000039, 0.2]
                ]}]]
                )
            })
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

        self.reset_question_answer('schematic_problem')
        resp = self.submit_question_answer('schematic_problem',
            { '2_1': json.dumps(
                [['transient', {'Z': [
                [0.0000004, 2.8],
                [0.0000009, 0.0],  # wrong.
                [0.0000014, 2.8],
                [0.0000019, 2.8],
                [0.0000024, 2.8],
                [0.0000029, 0.2],
                [0.0000034, 0.2],
                [0.0000039, 0.2]
                ]}]]
                )
            })
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')

    def test_check_function(self):
        resp = self.submit_question_answer('cfn_problem', {'2_1': "0, 1, 2, 3, 4, 5, 'Outside of loop', 6"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

        self.reset_question_answer('cfn_problem')

        resp = self.submit_question_answer('cfn_problem', {'2_1': "xyzzy!"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')

    def test_computed_answer(self):
        resp = self.submit_question_answer('computed_answer', {'2_1': "Xyzzy"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'correct')

        self.reset_question_answer('computed_answer')

        resp = self.submit_question_answer('computed_answer', {'2_1': "NO!"})
        respdata = json.loads(resp.content)
        self.assertEqual(respdata['success'], 'incorrect')
