import logging
import datetime
import pytz
import random

from uuid import uuid4

from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

import xmodule.modulestore.django

# Need access to internal func to put users in the right group
from courseware.access import (has_access, _course_staff_group_name,
                               course_beta_test_group_name)

from mongo_login_helpers import MongoLoginHelpers

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

log = logging.getLogger("mitx." + __name__)


def get_user(email):
    '''look up a user by email'''
    return User.objects.get(email=email)


def update_course(course, data):
        """
        Updates the version of course in the mongo modulestore
        with the metadata in data and returns the updated version.
        """

        store = xmodule.modulestore.django.modulestore()

        store.update_item(course.location, data)

        store.update_metadata(course.location, data)

        updated_course = store.get_instance(course.id, course.location)

        return updated_course


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


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestViewAuth(MongoLoginHelpers):
    """Check that view authentication works properly"""

    def setUp(self):
        xmodule.modulestore.django._MODULESTORES = {}

        self.full = CourseFactory.create(number='666', display_name='Robot_Sub_Course')
        self.course = CourseFactory.create()
        self.overview_chapter = ItemFactory.create(display_name='Overview')
        self.courseware_chapter = ItemFactory.create(display_name='courseware')
        self.sub_courseware_chapter = ItemFactory.create(parent_location=self.full.location,
                                                         display_name='courseware')
        self.sub_overview_chapter = ItemFactory.create(parent_location=self.sub_courseware_chapter.location,
                                                       display_name='Overview')
        self.progress_chapter = ItemFactory.create(parent_location=self.course.location,
                                                   display_name='progress')
        self.info_chapter = ItemFactory.create(parent_location=self.course.location,
                                               display_name='info')
        self.welcome_section = ItemFactory.create(parent_location=self.overview_chapter.location,
                                                  display_name='Welcome')
        self.somewhere_in_progress = ItemFactory.create(parent_location=self.progress_chapter.location,
                                                        display_name='1')

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
                                           kwargs={'course_id': self.course.id}))

        self.assertRedirectsNoFollow(response,
                                     reverse('about_course',
                                             args=[self.course.id]))
        self.enroll(self.course)
        self.enroll(self.full)
        # should work now -- redirect to first page
        response = self.client.get(reverse('courseware',
                                   kwargs={'course_id': self.course.id}))

        self.assertRedirectsNoFollow(response,
                                     reverse('courseware_section',
                                             kwargs={'course_id': self.course.id,
                                                     'chapter': 'Overview',
                                                     'section': 'Welcome'}))

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
        url = random.choice(instructor_urls(self.course) +
                            instructor_urls(self.full))

        # Shouldn't be able to get to the instructor pages
        print 'checking for 404 on {0}'.format(url)
        self.check_for_get_code(404, url)

        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(get_user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)

        # Now should be able to get to the toy course, but not the full course
        url = random.choice(instructor_urls(self.course))
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
        url = random.choice(instructor_urls(self.course) +
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
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        self.course.lms.start = tomorrow
        self.full.lms.start = tomorrow

        self.assertFalse(self.course.has_started())
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
        self.enroll(self.course)
        self.enroll(self.full)

        # shouldn't be able to get to anything except the light pages
        check_non_staff(self.course)
        check_non_staff(self.full)

        print '=== Testing course instructor access....'
        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(get_user(self.instructor))

        self.logout()
        self.login(self.instructor, self.password)
        # Enroll in the classes---can't see courseware otherwise.
        self.enroll(self.course)
        self.enroll(self.full)

        # should now be able to get to everything for self.course
        check_non_staff(self.full)
        check_staff(self.course)

        print '=== Testing staff access....'
        # now also make the instructor staff
        instructor = get_user(self.instructor)
        instructor.is_staff = True
        instructor.save()

        # and now should be able to load both
        check_staff(self.course)
        check_staff(self.full)

    def _do_test_enrollment_period(self):
        """Actually do the test, relying on settings to be right."""

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        nextday = tomorrow + datetime.timedelta(days=1)
        yesterday = now - datetime.timedelta(days=1)

        course_data = {'enrollment_start': tomorrow, 'enrollment_end': nextday}
        full_data = {'enrollment_start': yesterday, 'enrollment_end': tomorrow}

        print "changing"
        # self.course's enrollment period hasn't started
        self.course = update_course(self.course, course_data)
        # full course's has
        self.full = update_course(self.full, full_data)

        print "login"
        # First, try with an enrolled student
        print '=== Testing student access....'
        self.login(self.student, self.password)
        self.assertFalse(self.try_enroll(self.course))
        self.assertTrue(self.try_enroll(self.full))

        print '=== Testing course instructor access....'
        # Make the instructor staff in the toy course
        group_name = _course_staff_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(get_user(self.instructor))

        print "logout/login"
        self.logout()
        self.login(self.instructor, self.password)
        print "Instructor should be able to enroll in toy course"
        self.assertTrue(self.try_enroll(self.course))

        print '=== Testing staff access....'
        # now make the instructor global staff, but not in the instructor group
        group.user_set.remove(get_user(self.instructor))
        instructor = get_user(self.instructor)
        instructor.is_staff = True
        instructor.save()

        # unenroll and try again
        self.unenroll(self.course)
        self.assertTrue(self.try_enroll(self.course))

    def _do_test_beta_period(self):
        """Actually test beta periods, relying on settings to be right."""

        # trust, but verify :)
        self.assertFalse(settings.MITX_FEATURES['DISABLE_START_DATES'])

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        # nextday = tomorrow + 24 * 3600
        # yesterday = time.time() - 24 * 3600

        # self.course's hasn't started
        self.course.lms.start = tomorrow
        self.assertFalse(self.course.has_started())

        # but should be accessible for beta testers
        self.course.lms.days_early_for_beta = 2

        # student user shouldn't see it
        student_user = get_user(self.student)
        self.assertFalse(has_access(student_user, self.course, 'load'))

        # now add the student to the beta test group
        group_name = course_beta_test_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(student_user)

        # now the student should see it
        self.assertTrue(has_access(student_user, self.course, 'load'))
