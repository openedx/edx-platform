import datetime
import pytz
import random

import xmodule.modulestore.django

from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from courseware.access import (has_access, _course_staff_group_name,
                               course_beta_test_group_name)

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from helpers import LoginEnrollmentTestCase, check_for_get_code
from modulestore_config import TEST_DATA_MONGO_MODULESTORE


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestViewAuth(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that view authentication works properly.
    """

    ACCOUNT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    @classmethod
    def _instructor_urls(self, course):
        """
        `course` is an instance of CourseDescriptor whose section URLs are to be returned.

        Returns a list of URLs corresponding to sections in the passed in course.
        """

        urls = [reverse(name, kwargs={'course_id': course.id}) for name in (
            'instructor_dashboard',
            'gradebook',
            'grade_summary',)]

        email, _ = self.ACCOUNT_INFO[0]
        student_id = User.objects.get(email=email).id

        urls.append(reverse('student_progress',
                            kwargs={'course_id': course.id,
                                    'student_id': student_id}))
        return urls

    @staticmethod
    def _reverse_urls(names, course):
        """
        Reverse a list of course urls.

        `names` is a list of URL names that correspond to sections in a course.

        `course` is the instance of CourseDescriptor whose section URLs are to be returned.

        Returns a list URLs corresponding to section in the passed in course.

        """
        return [reverse(name, kwargs={'course_id': course.id})
                for name in names]

    def setUp(self):

        self.full = CourseFactory.create(number='666', display_name='Robot_Sub_Course')
        self.course = CourseFactory.create()
        self.overview_chapter = ItemFactory.create(display_name='Overview')
        self.courseware_chapter = ItemFactory.create(display_name='courseware')
        self.sub_courseware_chapter = ItemFactory.create(parent_location=self.full.location,
                                                         display_name='courseware')
        self.sub_overview_chapter = ItemFactory.create(parent_location=self.sub_courseware_chapter.location,
                                                       display_name='Overview')
        self.welcome_section = ItemFactory.create(parent_location=self.overview_chapter.location,
                                                  display_name='Welcome')

        # Create two accounts and activate them.
        for i in range(len(self.ACCOUNT_INFO)):
            username, email, password = 'u{0}'.format(i), self.ACCOUNT_INFO[i][0], self.ACCOUNT_INFO[i][1]
            self.create_account(username, email, password)
            self.activate_user(email)

    def test_redirection_unenrolled(self):
        """
        Verify unenrolled student is redirected to the 'about' section of the chapter
        instead of the 'Welcome' section after clicking on the courseware tab.
        """

        email, password = self.ACCOUNT_INFO[0]
        self.login(email, password)
        response = self.client.get(reverse('courseware',
                                           kwargs={'course_id': self.course.id}))
        self.assertRedirects(response,
                             reverse('about_course',
                                     args=[self.course.id]))

    def test_redirection_enrolled(self):
        """
        Verify enrolled student is redirected to the 'Welcome' section of
        the chapter after clicking on the courseware tab.
        """

        email, password = self.ACCOUNT_INFO[0]
        self.login(email, password)
        self.enroll(self.course)

        response = self.client.get(reverse('courseware',
                                           kwargs={'course_id': self.course.id}))

        self.assertRedirects(response,
                             reverse('courseware_section',
                                     kwargs={'course_id': self.course.id,
                                             'chapter': 'Overview',
                                             'section': 'Welcome'}))

    def test_instructor_page_access_nonstaff(self):
        """
        Verify non-staff cannot load the instructor
        dashboard, the grade views, and student profile pages.
        """

        email, password = self.ACCOUNT_INFO[0]
        self.login(email, password)

        self.enroll(self.course)
        self.enroll(self.full)

        # Randomly sample an instructor page
        url = random.choice(self._instructor_urls(self.course) +
                            self._instructor_urls(self.full))

        # Shouldn't be able to get to the instructor pages
        print 'checking for 404 on {0}'.format(url)
        check_for_get_code(self, 404, url)

    def test_instructor_course_access(self):
        """
        Verify instructor can load the instructor dashboard, the grade views,
        and student profile pages for their course.
        """

        email, password = self.ACCOUNT_INFO[1]

        # Make the instructor staff in self.course
        group_name = _course_staff_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(User.objects.get(email=email))

        self.login(email, password)

        # Now should be able to get to self.course, but not  self.full
        url = random.choice(self._instructor_urls(self.course))
        print 'checking for 200 on {0}'.format(url)
        check_for_get_code(self, 200, url)

        url = random.choice(self._instructor_urls(self.full))
        print 'checking for 404 on {0}'.format(url)
        check_for_get_code(self, 404, url)

    def test_instructor_as_staff_access(self):
        """
        Verify the instructor can load staff pages if he is given
        staff permissions.
        """

        email, password = self.ACCOUNT_INFO[1]
        self.login(email, password)

        # now make the instructor also staff
        instructor = User.objects.get(email=email)
        instructor.is_staff = True
        instructor.save()

        # and now should be able to load both
        url = random.choice(self._instructor_urls(self.course) +
                            self._instructor_urls(self.full))

        print 'checking for 200 on {0}'.format(url)
        check_for_get_code(self, 200, url)

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
        """
        Make sure that before course start, students can't access course
        pages, but instructors can.
        """
        self.run_wrapped(self._do_test_dark_launch)

    def test_enrollment_period(self):
        """
        Check that enrollment periods work.
        """
        self.run_wrapped(self._do_test_enrollment_period)

    def test_beta_period(self):
        """
        Check that beta-test access works.
        """
        self.run_wrapped(self._do_test_beta_period)

    def _do_test_dark_launch(self):
        """
        Actually do the test, relying on settings to be right.
        """

        student_email, student_password = self.ACCOUNT_INFO[0]
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}
        full_data = {'start': tomorrow}
        self.course = self.update_course(self.course, course_data)
        self.full = self.update_course(self.full, full_data)

        self.assertFalse(self.course.has_started())
        self.assertFalse(self.full.has_started())
        self.assertFalse(settings.MITX_FEATURES['DISABLE_START_DATES'])

        def dark_student_urls(course):
            """
            List of urls that students should be able to see only
            after launch, but staff should see before
            """
            urls = self._reverse_urls(['info', 'progress'], course)
            urls.extend([
                reverse('book', kwargs={'course_id': course.id,
                                        'book_index': index})
                for index, book in enumerate(course.textbooks)
            ])
            return urls

        def light_student_urls(course):
            """
            List of urls that students should be able to see before
            launch.
            """
            urls = self._reverse_urls(['about_course'], course)
            urls.append(reverse('courses'))

            return urls

        def instructor_urls(course):
            """
            List of urls that only instructors/staff should be able to see.
            """
            urls = self._reverse_urls(['instructor_dashboard',
                                       'gradebook', 'grade_summary'], course)
            return urls

        def check_non_staff_light(course):
            """
            Check that non-staff have access to light urls.
            """
            print '=== Checking non-staff access for {0}'.format(course.id)

            # Randomly sample a light url
            url = random.choice(light_student_urls(course))
            print 'checking for 200 on {0}'.format(url)
            check_for_get_code(self, 200, url)

        def check_non_staff_dark(course):
            """
            Check that non-staff don't have access to dark urls.
            """
            print '=== Checking non-staff access for {0}'.format(course.id)

            # Randomly sample a dark url
            url = random.choice(instructor_urls(course) +
                                dark_student_urls(course) +
                                self._reverse_urls(['courseware'], course))
            print 'checking for 404 on {0}'.format(url)
            check_for_get_code(self, 404, url)

        def check_staff(course):
            """
            Check that access is right for staff in course.
            """
            print '=== Checking staff access for {0}'.format(course.id)

            # Randomly sample a url
            url = random.choice(instructor_urls(course) +
                                dark_student_urls(course) +
                                light_student_urls(course))
            print 'checking for 200 on {0}'.format(url)
            check_for_get_code(self, 200, url)

            # The student progress tab is not accessible to a student
            # before launch, so the instructor view-as-student feature
            # should return a 404 as well.
            # TODO (vshnayder): If this is not the behavior we want, will need
            # to make access checking smarter and understand both the effective
            # user (the student), and the requesting user (the prof)
            url = reverse('student_progress',
                          kwargs={'course_id': course.id,
                                  'student_id': User.objects.get(email=self.ACCOUNT_INFO[0][0]).id})
            print 'checking for 404 on view-as-student: {0}'.format(url)
            check_for_get_code(self, 404, url)

            # The courseware url should redirect, not 200
            url = self._reverse_urls(['courseware'], course)[0]
            check_for_get_code(self, 302, url)

        # First, try with an enrolled student
        print '=== Testing student access....'
        self.login(student_email, student_password)
        self.enroll(self.course, True)
        self.enroll(self.full, True)

        # shouldn't be able to get to anything except the light pages
        check_non_staff_light(self.course)
        check_non_staff_dark(self.course)
        check_non_staff_light(self.full)
        check_non_staff_dark(self.full)

        print '=== Testing course instructor access....'
        # Make the instructor staff in  self.course
        group_name = _course_staff_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(User.objects.get(email=instructor_email))

        self.logout()
        self.login(instructor_email, instructor_password)
        # Enroll in the classes---can't see courseware otherwise.
        self.enroll(self.course, True)
        self.enroll(self.full, True)

        # should now be able to get to everything for self.course
        check_non_staff_light(self.full)
        check_non_staff_dark(self.full)
        check_staff(self.course)

        print '=== Testing staff access....'
        # now also make the instructor staff
        instructor = User.objects.get(email=instructor_email)
        instructor.is_staff = True
        instructor.save()

        # and now should be able to load both
        check_staff(self.course)
        check_staff(self.full)

    def _do_test_enrollment_period(self):
        """
        Actually do the test, relying on settings to be right.
        """

        student_email, student_password = self.ACCOUNT_INFO[0]
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        nextday = tomorrow + datetime.timedelta(days=1)
        yesterday = now - datetime.timedelta(days=1)

        course_data = {'enrollment_start': tomorrow, 'enrollment_end': nextday}
        full_data = {'enrollment_start': yesterday, 'enrollment_end': tomorrow}

        print "changing"
        # self.course's enrollment period hasn't started
        self.course = self.update_course(self.course, course_data)
        # full course's has
        self.full = self.update_course(self.full, full_data)

        print "login"
        # First, try with an enrolled student
        print '=== Testing student access....'
        self.login(student_email, student_password)
        self.assertFalse(self.enroll(self.course))
        self.assertTrue(self.enroll(self.full))

        print '=== Testing course instructor access....'
        # Make the instructor staff in the self.course
        group_name = _course_staff_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(User.objects.get(email=instructor_email))

        print "logout/login"
        self.logout()
        self.login(instructor_email, instructor_password)
        print "Instructor should be able to enroll in self.course"
        self.assertTrue(self.enroll(self.course))

        print '=== Testing staff access....'
        # now make the instructor global staff, but not in the instructor group
        group.user_set.remove(User.objects.get(email=instructor_email))
        instructor = User.objects.get(email=instructor_email)
        instructor.is_staff = True
        instructor.save()

        # unenroll and try again
        self.unenroll(self.course)
        self.assertTrue(self.enroll(self.course))

    def _do_test_beta_period(self):
        """
        Actually test beta periods, relying on settings to be right.
        """

        student_email, student_password = self.ACCOUNT_INFO[0]
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        # trust, but verify :)
        self.assertFalse(settings.MITX_FEATURES['DISABLE_START_DATES'])

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}

        # self.course's hasn't started
        self.course = self.update_course(self.course, course_data)
        self.assertFalse(self.course.has_started())

        # but should be accessible for beta testers
        self.course.lms.days_early_for_beta = 2

        # student user shouldn't see it
        student_user = User.objects.get(email=student_email)
        self.assertFalse(has_access(student_user, self.course, 'load'))

        # now add the student to the beta test group
        group_name = course_beta_test_group_name(self.course.location)
        group = Group.objects.create(name=group_name)
        group.user_set.add(student_user)

        # now the student should see it
        self.assertTrue(has_access(student_user, self.course, 'load'))
