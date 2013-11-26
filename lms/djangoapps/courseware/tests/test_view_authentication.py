import datetime
import pytz

from mock import patch

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from courseware.access import has_access
from courseware.roles import CourseBetaTesterRole, CourseInstructorRole, CourseStaffRole, GlobalStaff

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from courseware.tests.helpers import LoginEnrollmentTestCase, check_for_get_code
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestViewAuth(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that view authentication works properly.
    """

    ACCOUNT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

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

    def _check_non_staff_light(self, course):
        """
        Check that non-staff have access to light urls.

        `course` is an instance of CourseDescriptor.
        """
        urls = [reverse('about_course', kwargs={'course_id': course.id}), reverse('courses')]
        for url in urls:
            check_for_get_code(self, 200, url)

    def _check_non_staff_dark(self, course):
        """
        Check that non-staff don't have access to dark urls.
        """

        names = ['courseware', 'instructor_dashboard', 'progress']
        urls = self._reverse_urls(names, course)
        urls.extend([
            reverse('book', kwargs={'course_id': course.id,
                                    'book_index': index})
            for index, book in enumerate(course.textbooks)
        ])
        for url in urls:
            check_for_get_code(self, 404, url)

    def _check_staff(self, course):
        """
        Check that access is right for staff in course.
        """
        names = ['about_course', 'instructor_dashboard', 'progress']
        urls = self._reverse_urls(names, course)
        urls.extend([
            reverse('book', kwargs={'course_id': course.id,
                                    'book_index': index})
            for index, book in enumerate(course.textbooks)
        ])
        for url in urls:
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
        check_for_get_code(self, 404, url)

        # The courseware url should redirect, not 200
        url = self._reverse_urls(['courseware'], course)[0]
        check_for_get_code(self, 302, url)

    def setUp(self):

        self.course = CourseFactory.create(number='999', display_name='Robot_Super_Course')
        self.overview_chapter = ItemFactory.create(display_name='Overview')
        self.courseware_chapter = ItemFactory.create(display_name='courseware')

        self.test_course = CourseFactory.create(number='666', display_name='Robot_Sub_Course')
        self.sub_courseware_chapter = ItemFactory.create(parent_location=self.test_course.location,
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
        self.enroll(self.test_course)

        urls = [reverse('instructor_dashboard', kwargs={'course_id': self.course.id}),
                reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})]

        # Shouldn't be able to get to the instructor pages
        for url in urls:
            check_for_get_code(self, 404, url)

    def test_instructor_course_access(self):
        """
        Verify instructor can load the instructor dashboard, the grade views,
        and student profile pages for their course.
        """
        email, password = self.ACCOUNT_INFO[1]

        # Make the instructor staff in self.course
        CourseInstructorRole(self.course.location).add_users(User.objects.get(email=email))

        self.login(email, password)

        # Now should be able to get to self.course, but not  self.test_course
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})
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
        urls = [reverse('instructor_dashboard', kwargs={'course_id': self.course.id}),
                reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})]

        for url in urls:
            check_for_get_code(self, 200, url)

    @patch.dict('courseware.access.settings.MITX_FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_enrolled_student(self):
        """
        Make sure that before course start, students can't access course
        pages.
        """

        student_email, student_password = self.ACCOUNT_INFO[0]

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}
        test_course_data = {'start': tomorrow}
        self.course = self.update_course(self.course, course_data)
        self.test_course = self.update_course(self.test_course, test_course_data)

        self.assertFalse(self.course.has_started())
        self.assertFalse(self.test_course.has_started())

        # First, try with an enrolled student
        self.login(student_email, student_password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # shouldn't be able to get to anything except the light pages
        self._check_non_staff_light(self.course)
        self._check_non_staff_dark(self.course)
        self._check_non_staff_light(self.test_course)
        self._check_non_staff_dark(self.test_course)

    @patch.dict('courseware.access.settings.MITX_FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_instructor(self):
        """
        Make sure that before course start instructors can access the
        page for their course.
        """
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}
        test_course_data = {'start': tomorrow}
        self.course = self.update_course(self.course, course_data)
        self.test_course = self.update_course(self.test_course, test_course_data)

        # Make the instructor staff in  self.course
        CourseStaffRole(self.course.location).add_users(User.objects.get(email=instructor_email))

        self.logout()
        self.login(instructor_email, instructor_password)
        # Enroll in the classes---can't see courseware otherwise.
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # should now be able to get to everything for self.course
        self._check_non_staff_light(self.test_course)
        self._check_non_staff_dark(self.test_course)
        self._check_staff(self.course)

    @patch.dict('courseware.access.settings.MITX_FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_staff(self):
        """
        Make sure that before course start staff can access
        course pages.
        """
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}
        test_course_data = {'start': tomorrow}
        self.course = self.update_course(self.course, course_data)
        self.test_course = self.update_course(self.test_course, test_course_data)

        self.login(instructor_email, instructor_password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # now also make the instructor staff
        instructor = User.objects.get(email=instructor_email)
        instructor.is_staff = True
        instructor.save()

        # and now should be able to load both
        self._check_staff(self.course)
        self._check_staff(self.test_course)

    @patch.dict('courseware.access.settings.MITX_FEATURES', {'DISABLE_START_DATES': False})
    def test_enrollment_period(self):
        """
        Check that enrollment periods work.
        """
        student_email, student_password = self.ACCOUNT_INFO[0]
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        nextday = tomorrow + datetime.timedelta(days=1)
        yesterday = now - datetime.timedelta(days=1)

        course_data = {'enrollment_start': tomorrow, 'enrollment_end': nextday}
        test_course_data = {'enrollment_start': yesterday, 'enrollment_end': tomorrow}

        # self.course's enrollment period hasn't started
        self.course = self.update_course(self.course, course_data)
        # test_course course's has
        self.test_course = self.update_course(self.test_course, test_course_data)

        # First, try with an enrolled student
        self.login(student_email, student_password)
        self.assertFalse(self.enroll(self.course))
        self.assertTrue(self.enroll(self.test_course))

        # Make the instructor staff in the self.course
        instructor_role = CourseInstructorRole(self.course.location)
        instructor_role.add_users(User.objects.get(email=instructor_email))

        self.logout()
        self.login(instructor_email, instructor_password)
        self.assertTrue(self.enroll(self.course))

        # now make the instructor global staff, but not in the instructor group
        instructor_role.remove_users(User.objects.get(email=instructor_email))
        GlobalStaff().add_users(User.objects.get(email=instructor_email))

        # unenroll and try again
        self.unenroll(self.course)
        self.assertTrue(self.enroll(self.course))

    @patch.dict('courseware.access.settings.MITX_FEATURES', {'DISABLE_START_DATES': False})
    def test_beta_period(self):
        """
        Check that beta-test access works.
        """
        student_email, student_password = self.ACCOUNT_INFO[0]
        instructor_email, instructor_password = self.ACCOUNT_INFO[1]

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}

        # self.course's hasn't started
        self.course = self.update_course(self.course, course_data)
        self.assertFalse(self.course.has_started())

        # but should be accessible for beta testers
        self.course.days_early_for_beta = 2

        # student user shouldn't see it
        student_user = User.objects.get(email=student_email)
        self.assertFalse(has_access(student_user, self.course, 'load'))

        # now add the student to the beta test group
        CourseBetaTesterRole(self.course.location).add_users(student_user)

        # now the student should see it
        self.assertTrue(has_access(student_user, self.course, 'load'))
