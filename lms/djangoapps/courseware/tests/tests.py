import copy
import json
import os
import sys
import time

from nose import SkipTest
from path import path
from pprint import pprint
from urlparse import urlsplit, urlunsplit

from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch, Mock
from override_settings import override_settings

import xmodule.modulestore.django

# Need access to internal func to put users in the right group
from courseware.access import _course_staff_group_name

from student.models import Registration
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.timeparse import stringify_time

def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def registration(email):
    '''look up registration object by email'''
    return Registration.objects.get(user__email=email)


# A bit of a hack--want mongo modulestore for these tests, until
# jump_to works with the xmlmodulestore or we have an even better solution
# NOTE: this means this test requires mongo to be running.

def mongo_store_config(data_dir):
    return {
    'default': {
        'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
        'OPTIONS': {
            'default_class': 'xmodule.raw_module.RawDescriptor',
            'host': 'localhost',
            'db': 'xmodule',
            'collection': 'modulestore',
            'fs_root': data_dir,
            'render_template': 'mitxmako.shortcuts.render_to_string',
        }
    }
}

def xml_store_config(data_dir):
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
TEST_DATA_MONGO_MODULESTORE = mongo_store_config(TEST_DATA_DIR)
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)

REAL_DATA_DIR = settings.GITHUB_REPO_ROOT
REAL_DATA_MODULESTORE = mongo_store_config(REAL_DATA_DIR)

class ActivateLoginTestCase(TestCase):
    '''Check that we can activate and log in'''

    def assertRedirectsNoFollow(self, response, expected_url):
        """
        http://devblog.point2.com/2010/04/23/djangos-assertredirects-little-gotcha/

        Don't check that the redirected-to page loads--there should be other tests for that.

        Some of the code taken from django.test.testcases.py
        """
        self.assertEqual(response.status_code, 302,
                         'Response status code was {0} instead of 302'.format(response.status_code))
        url = response['Location']

        e_scheme, e_netloc, e_path, e_query, e_fragment = urlsplit(
                                                              expected_url)
        if not (e_scheme or e_netloc):
            expected_url = urlunsplit(('http', 'testserver', e_path,
                e_query, e_fragment))

        self.assertEqual(url, expected_url, "Response redirected to '{0}', expected '{1}'".format(
            url, expected_url))

    def setUp(self):
        email = 'view@test.com'
        password = 'foo'
        self.create_account('viewtest', email, password)
        self.activate_user(email)
        self.login(email, password)

    # ============ User creation and login ==============

    def _login(self, email, pw):
        '''Login.  View should always return 200.  The success/fail is in the
        returned json'''
        resp = self.client.post(reverse('login'),
                                {'email': email, 'password': pw})
        self.assertEqual(resp.status_code, 200)
        return resp

    def login(self, email, pw):
        '''Login, check that it worked.'''
        resp = self._login(email, pw)
        data = parse_json(resp)
        self.assertTrue(data['success'])
        return resp

    def logout(self):
        '''Logout, check that it worked.'''
        resp = self.client.get(reverse('logout'), {})
        # should redirect
        self.assertEqual(resp.status_code, 302)
        return resp

    def _create_account(self, username, email, pw):
        '''Try to create an account.  No error checking'''
        resp = self.client.post('/create_account', {
            'username': username,
            'email': email,
            'password': pw,
            'name': 'Fred Weasley',
            'terms_of_service': 'true',
            'honor_code': 'true',
        })
        return resp

    def create_account(self, username, email, pw):
        '''Create the account and check that it worked'''
        resp = self._create_account(username, email, pw)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)

        # Check both that the user is created, and inactive
        self.assertFalse(user(email).is_active)

        return resp

    def _activate_user(self, email):
        '''Look up the activation key for the user, then hit the activate view.
        No error checking'''
        activation_key = registration(email).activation_key

        # and now we try to activate
        resp = self.client.get(reverse('activate', kwargs={'key': activation_key}))
        return resp

    def activate_user(self, email):
        resp = self._activate_user(email)
        self.assertEqual(resp.status_code, 200)
        # Now make sure that the user is now actually activated
        self.assertTrue(user(email).is_active)

    def test_activate_login(self):
        '''The setup function does all the work'''
        pass

    def test_logout(self):
        '''Setup function does login'''
        self.logout()


class PageLoader(ActivateLoginTestCase):
    ''' Base class that adds a function to load all pages in a modulestore '''

    def _enroll(self, course):
        """Post to the enrollment view, and return the parsed json response"""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'enroll',
            'course_id': course.id,
            })
        return parse_json(resp)

    def try_enroll(self, course):
        """Try to enroll.  Return bool success instead of asserting it."""
        data = self._enroll(course)
        print 'Enrollment in {0} result: {1}'.format(course.location.url(), data)
        return data['success']

    def enroll(self, course):
        """Enroll the currently logged-in user, and check that it worked."""
        data = self._enroll(course)
        self.assertTrue(data['success'])

    def unenroll(self, course):
        """Unenroll the currently logged-in user, and check that it worked."""
        resp = self.client.post('/change_enrollment', {
            'enrollment_action': 'unenroll',
            'course_id': course.id,
            })
        data = parse_json(resp)
        self.assertTrue(data['success'])


    def check_for_get_code(self, code, url):
        """
        Check that we got the expected code.  Hacks around our broken 404
        handling.
        """
        resp = self.client.get(url)
        # HACK: workaround the bug that returns 200 instead of 404.
        # TODO (vshnayder): once we're returning 404s, get rid of this if.
        if code != 404:
            self.assertEqual(resp.status_code, code)
            # And 'page not found' shouldn't be in the returned page
            self.assertTrue(resp.content.lower().find('page not found') == -1)
        else:
            # look for "page not found" instead of the status code
            #print resp.content
            self.assertTrue(resp.content.lower().find('page not found') != -1)


    def check_pages_load(self, course_name, data_dir, modstore):
        """Make all locations in course load"""
        print "Checking course {0} in {1}".format(course_name, data_dir)
        import_from_xml(modstore, data_dir, [course_name])

        # enroll in the course before trying to access pages
        courses = modstore.get_courses()
        self.assertEqual(len(courses), 1)
        course = courses[0]
        self.enroll(course)
        course_id = course.id

        n = 0
        num_bad = 0
        all_ok = True
        for descriptor in modstore.get_items(
                Location(None, None, None, None, None)):
            n += 1
            print "Checking ", descriptor.location.url()
            #print descriptor.__class__, descriptor.location
            resp = self.client.get(reverse('jump_to',
                                   kwargs={'course_id': course_id,
                                           'location': descriptor.location.url()}))
            msg = str(resp.status_code)

            if resp.status_code != 302:
                msg = "ERROR " + msg
                all_ok = False
                num_bad += 1
            print msg
            self.assertTrue(all_ok)  # fail fast

        print "{0}/{1} good".format(n - num_bad, n)
        self.assertTrue(all_ok)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestCoursesLoadTestCase(PageLoader):
    '''Check that all pages in test courses load properly'''

    def setUp(self):
        ActivateLoginTestCase.setUp(self)
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

    def test_toy_course_loads(self):
        self.check_pages_load('toy', TEST_DATA_DIR, modulestore())

    def test_full_course_loads(self):
        self.check_pages_load('full', TEST_DATA_DIR, modulestore())


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestNavigation(PageLoader):
    """Check that navigation state is saved properly"""

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        def find_course(name):
            """Assumes the course is present"""
            return [c for c in courses if c.location.course==name][0]

        self.full = find_course("full")
        self.toy = find_course("toy")

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
        resp = self.client.get(reverse('courseware', kwargs={'course_id': self.toy.id}))

        # Don't use no-follow, because state should only be saved once we actually hit the section
        self.assertRedirects(resp, reverse(
            'courseware_section', kwargs={'course_id': self.toy.id,
                                          'chapter': 'Overview',
                                          'section': 'Toy_Videos'}))

        # Hitting the couseware tab again should redirect to the first chapter: 'Overview'
        resp = self.client.get(reverse('courseware', kwargs={'course_id': self.toy.id}))
        self.assertRedirectsNoFollow(resp, reverse('courseware_chapter',
                                                   kwargs={'course_id': self.toy.id, 'chapter': 'Overview'}))

        # Now we directly navigate to a section in a different chapter
        self.check_for_get_code(200, reverse('courseware_section',
                                             kwargs={'course_id': self.toy.id,
                                                     'chapter':'secret:magic', 'section':'toyvideo'}))

        # And now hitting the courseware tab should redirect to 'secret:magic'
        resp = self.client.get(reverse('courseware', kwargs={'course_id': self.toy.id}))
        self.assertRedirectsNoFollow(resp, reverse('courseware_chapter',
                                                   kwargs={'course_id': self.toy.id, 'chapter': 'secret:magic'}))


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestViewAuth(PageLoader):
    """Check that view authentication works properly"""

    # NOTE: setUpClass() runs before override_settings takes effect, so
    # can't do imports there without manually hacking settings.

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}
        courses = modulestore().get_courses()

        def find_course(name):
            """Assumes the course is present"""
            return [c for c in courses if c.location.course==name][0]

        self.full = find_course("full")
        self.toy = find_course("toy")

        # Create two accounts
        self.student = 'view@test.com'
        self.instructor = 'view2@test.com'
        self.password = 'foo'
        self.create_account('u1', self.student, self.password)
        self.create_account('u2', self.instructor, self.password)
        self.activate_user(self.student)
        self.activate_user(self.instructor)

    def test_instructor_pages(self):
        """Make sure only instructors for the course or staff can load the instructor
        dashboard, the grade views, and student profile pages"""

        # First, try with an enrolled student
        self.login(self.student, self.password)
        # shouldn't work before enroll
        response = self.client.get(reverse('courseware', kwargs={'course_id': self.toy.id}))
        self.assertRedirectsNoFollow(response, reverse('about_course', args=[self.toy.id]))
        self.enroll(self.toy)
        self.enroll(self.full)
        # should work now -- redirect to first page
        response = self.client.get(reverse('courseware', kwargs={'course_id': self.toy.id}))
        self.assertRedirectsNoFollow(response, reverse('courseware_section', kwargs={'course_id': self.toy.id,
                                                                                     'chapter': 'Overview',
                                                                                     'section': 'Toy_Videos'}))

        def instructor_urls(course):
            "list of urls that only instructors/staff should be able to see"
            urls = [reverse(name, kwargs={'course_id': course.id}) for name in (
                'instructor_dashboard',
                'gradebook',
                'grade_summary',)]
            urls.append(reverse('student_progress', kwargs={'course_id': course.id,
                                                     'student_id': user(self.student).id}))
            return urls

        # shouldn't be able to get to the instructor pages
        for url in instructor_urls(self.toy) + instructor_urls(self.full):
            print 'checking for 404 on {0}'.format(url)
            self.check_for_get_code(404, url)

        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)

        # Now should be able to get to the toy course, but not the full course
        for url in instructor_urls(self.toy):
            print 'checking for 200 on {0}'.format(url)
            self.check_for_get_code(200, url)

        for url in instructor_urls(self.full):
            print 'checking for 404 on {0}'.format(url)
            self.check_for_get_code(404, url)


        # now also make the instructor staff
        u = user(self.instructor)
        u.is_staff = True
        u.save()

        # and now should be able to load both
        for url in instructor_urls(self.toy) + instructor_urls(self.full):
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


    def _do_test_dark_launch(self):
        """Actually do the test, relying on settings to be right."""

        # Make courses start in the future
        tomorrow = time.time() + 24*3600
        self.toy.metadata['start'] = stringify_time(time.gmtime(tomorrow))
        self.full.metadata['start'] = stringify_time(time.gmtime(tomorrow))

        self.assertFalse(self.toy.has_started())
        self.assertFalse(self.full.has_started())
        self.assertFalse(settings.MITX_FEATURES['DISABLE_START_DATES'])

        def reverse_urls(names, course):
            """Reverse a list of course urls"""
            return [reverse(name, kwargs={'course_id': course.id}) for name in names]

        def dark_student_urls(course):
            """
            list of urls that students should be able to see only
            after launch, but staff should see before
            """
            urls = reverse_urls(['info', 'progress'], course)
            urls.extend([
                reverse('book', kwargs={'course_id': course.id, 'book_index': book.title})
                for book in course.textbooks
            ])
            return urls

        def light_student_urls(course):
            """
            list of urls that students should be able to see before
            launch.
            """
            urls = reverse_urls(['about_course'], course)
            urls.append(reverse('courses'))
            # Need separate test for change_enrollment, since it's a POST view
            #urls.append(reverse('change_enrollment'))

            return urls

        def instructor_urls(course):
            """list of urls that only instructors/staff should be able to see"""
            urls = reverse_urls(['instructor_dashboard','gradebook','grade_summary'],
                                course)
            return urls

        def check_non_staff(course):
            """Check that access is right for non-staff in course"""
            print '=== Checking non-staff access for {0}'.format(course.id)
            for url in instructor_urls(course) + dark_student_urls(course) + reverse_urls(['courseware'], course):
                print 'checking for 404 on {0}'.format(url)
                self.check_for_get_code(404, url)

            for url in light_student_urls(course):
                print 'checking for 200 on {0}'.format(url)
                self.check_for_get_code(200, url)

        def check_staff(course):
            """Check that access is right for staff in course"""
            print '=== Checking staff access for {0}'.format(course.id)
            for url in (instructor_urls(course) +
                        dark_student_urls(course) +
                        light_student_urls(course)):
                print 'checking for 200 on {0}'.format(url)
                self.check_for_get_code(200, url)

            # The student progress tab is not accessible to a student
            # before launch, so the instructor view-as-student feature should return a 404 as well.
            # TODO (vshnayder): If this is not the behavior we want, will need
            # to make access checking smarter and understand both the effective
            # user (the student), and the requesting user (the prof)
            url = reverse('student_progress', kwargs={'course_id': course.id,
                                                     'student_id': user(self.student).id})
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
        g = Group.objects.create(name=group_name)
        g.user_set.add(user(self.instructor))

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
        u = user(self.instructor)
        u.is_staff = True
        u.save()

        # and now should be able to load both
        check_staff(self.toy)
        check_staff(self.full)

    def _do_test_enrollment_period(self):
        """Actually do the test, relying on settings to be right."""

        # Make courses start in the future
        tomorrow = time.time() + 24 * 3600
        nextday = tomorrow + 24 * 3600
        yesterday = time.time() - 24 * 3600

        print "changing"
        # toy course's enrollment period hasn't started
        self.toy.enrollment_start = time.gmtime(tomorrow)
        self.toy.enrollment_end = time.gmtime(nextday)

        # full course's has
        self.full.enrollment_start = time.gmtime(yesterday)
        self.full.enrollment_end = time.gmtime(tomorrow)

        print "login"
        # First, try with an enrolled student
        print '=== Testing student access....'
        self.login(self.student, self.password)
        self.assertFalse(self.try_enroll(self.toy))
        self.assertTrue(self.try_enroll(self.full))

        print '=== Testing course instructor access....'
        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.toy.location)
        g = Group.objects.create(name=group_name)
        g.user_set.add(user(self.instructor))

        print "logout/login"
        self.logout()
        self.login(self.instructor, self.password)
        print "Instructor should be able to enroll in toy course"
        self.assertTrue(self.try_enroll(self.toy))

        print '=== Testing staff access....'
        # now make the instructor global staff, but not in the instructor group
        g.user_set.remove(user(self.instructor))
        u = user(self.instructor)
        u.is_staff = True
        u.save()

        # unenroll and try again
        self.unenroll(self.toy)
        self.assertTrue(self.try_enroll(self.toy))


@override_settings(MODULESTORE=REAL_DATA_MODULESTORE)
class RealCoursesLoadTestCase(PageLoader):
    '''Check that all pages in real courses load properly'''

    def setUp(self):
        ActivateLoginTestCase.setUp(self)
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()

    def test_real_courses_loads(self):
        '''See if any real courses are available at the REAL_DATA_DIR.
        If they are, check them.'''

        # TODO: Disabled test for now..  Fix once things are cleaned up.
        raise SkipTest
        # TODO: adjust staticfiles_dirs
        if not os.path.isdir(REAL_DATA_DIR):
            # No data present.  Just pass.
            return

        courses = [course_dir for course_dir in os.listdir(REAL_DATA_DIR)
                   if os.path.isdir(REAL_DATA_DIR / course_dir)]
        for course in courses:
            self.check_pages_load(course, REAL_DATA_DIR, modulestore())


    # ========= TODO: check ajax interaction here too?
