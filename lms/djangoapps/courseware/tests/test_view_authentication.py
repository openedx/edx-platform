import datetime
import pytz

from mock import patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

# Need access to internal func to put users in the right group
from courseware.access import has_access

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from student.tests.factories import UserFactory, CourseEnrollmentFactory

from courseware.tests.helpers import LoginEnrollmentTestCase, check_for_get_code
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.tests.factories import (
    BetaTesterFactory,
    StaffFactory,
    GlobalStaffFactory,
    InstructorFactory,
    OrgStaffFactory,
    OrgInstructorFactory,
)


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
                              'student_id': self.enrolled_user.id})
        check_for_get_code(self, 404, url)

        # The courseware url should redirect, not 200
        url = self._reverse_urls(['courseware'], course)[0]
        check_for_get_code(self, 302, url)

    def login(self, user):
        return super(TestViewAuth, self).login(user.email, 'test')

    def setUp(self):

        self.course = CourseFactory.create(number='999', display_name='Robot_Super_Course')
        self.overview_chapter = ItemFactory.create(display_name='Overview')
        self.courseware_chapter = ItemFactory.create(display_name='courseware')

        self.test_course = CourseFactory.create(number='666', display_name='Robot_Sub_Course')
        self.other_org_course = CourseFactory.create(org='Other_Org_Course')
        self.sub_courseware_chapter = ItemFactory.create(
            parent_location=self.test_course.location, display_name='courseware'
        )
        self.sub_overview_chapter = ItemFactory.create(
            parent_location=self.sub_courseware_chapter.location,
            display_name='Overview'
        )
        self.welcome_section = ItemFactory.create(
            parent_location=self.overview_chapter.location,
            display_name='Welcome'
        )

        self.global_staff_user = GlobalStaffFactory()
        self.unenrolled_user = UserFactory(last_name="Unenrolled")

        self.enrolled_user = UserFactory(last_name="Enrolled")
        CourseEnrollmentFactory(user=self.enrolled_user, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.enrolled_user, course_id=self.test_course.id)

        self.staff_user = StaffFactory(course=self.course.location)
        self.instructor_user = InstructorFactory(
            course=self.course.location)
        self.org_staff_user = OrgStaffFactory(course=self.course.location)
        self.org_instructor_user = OrgInstructorFactory(
            course=self.course.location)

    def test_redirection_unenrolled(self):
        """
        Verify unenrolled student is redirected to the 'about' section of the chapter
        instead of the 'Welcome' section after clicking on the courseware tab.
        """
        self.login(self.unenrolled_user)
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
        self.login(self.enrolled_user)

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
        self.login(self.enrolled_user)

        urls = [reverse('instructor_dashboard', kwargs={'course_id': self.course.id}),
                reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})]

        # Shouldn't be able to get to the instructor pages
        for url in urls:
            check_for_get_code(self, 404, url)

    def test_staff_course_access(self):
        """
        Verify staff can load the staff dashboard, the grade views,
        and student profile pages for their course.
        """
        self.login(self.staff_user)

        # Now should be able to get to self.course, but not  self.test_course
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})
        check_for_get_code(self, 404, url)

    def test_instructor_course_access(self):
        """
        Verify instructor can load the instructor dashboard, the grade views,
        and student profile pages for their course.
        """
        self.login(self.instructor_user)

        # Now should be able to get to self.course, but not  self.test_course
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})
        check_for_get_code(self, 404, url)

    def test_org_staff_access(self):
        """
        Verify org staff can load the instructor dashboard, the grade views,
        and student profile pages for course in their org.
        """
        self.login(self.org_staff_user)
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.other_org_course.id})
        check_for_get_code(self, 404, url)

    def test_org_instructor_access(self):
        """
        Verify org instructor can load the instructor dashboard, the grade views,
        and student profile pages for course in their org.
        """
        self.login(self.org_instructor_user)
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})
        check_for_get_code(self, 200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.other_org_course.id})
        check_for_get_code(self, 404, url)

    def test_global_staff_access(self):
        """
        Verify the global staff user can access any course.
        """
        self.login(self.global_staff_user)

        # and now should be able to load both
        urls = [reverse('instructor_dashboard', kwargs={'course_id': self.course.id}),
                reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id})]

        for url in urls:
            check_for_get_code(self, 200, url)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_enrolled_student(self):
        """
        Make sure that before course start, students can't access course
        pages.
        """

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
        self.login(self.enrolled_user)

        # shouldn't be able to get to anything except the light pages
        self._check_non_staff_light(self.course)
        self._check_non_staff_dark(self.course)
        self._check_non_staff_light(self.test_course)
        self._check_non_staff_dark(self.test_course)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_instructor(self):
        """
        Make sure that before course start instructors can access the
        page for their course.
        """
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}
        test_course_data = {'start': tomorrow}
        self.course = self.update_course(self.course, course_data)
        self.test_course = self.update_course(self.test_course, test_course_data)

        self.login(self.instructor_user)
        # Enroll in the classes---can't see courseware otherwise.
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # should now be able to get to everything for self.course
        self._check_non_staff_light(self.test_course)
        self._check_non_staff_dark(self.test_course)
        self._check_staff(self.course)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_global_staff(self):
        """
        Make sure that before course start staff can access
        course pages.
        """
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        course_data = {'start': tomorrow}
        test_course_data = {'start': tomorrow}
        self.course = self.update_course(self.course, course_data)
        self.test_course = self.update_course(self.test_course, test_course_data)

        self.login(self.global_staff_user)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # and now should be able to load both
        self._check_staff(self.course)
        self._check_staff(self.test_course)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_enrollment_period(self):
        """
        Check that enrollment periods work.
        """
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
        self.login(self.unenrolled_user)
        self.assertFalse(self.enroll(self.course))
        self.assertTrue(self.enroll(self.test_course))

        self.logout()
        self.login(self.instructor_user)
        self.assertTrue(self.enroll(self.course))

        # unenroll and try again
        self.login(self.global_staff_user)
        self.assertTrue(self.enroll(self.course))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestBetatesterAccess(ModuleStoreTestCase):

    def setUp(self):

        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)

        self.course = CourseFactory(days_early_for_beta=2, start=tomorrow)
        self.content = ItemFactory(parent=self.course)

        self.normal_student = UserFactory()
        self.beta_tester = BetaTesterFactory(course=self.course.location)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_course_beta_period(self):
        """
        Check that beta-test access works for courses.
        """
        self.assertFalse(self.course.has_started())

        # student user shouldn't see it
        self.assertFalse(has_access(self.normal_student, self.course, 'load'))

        # now the student should see it
        self.assertTrue(has_access(self.beta_tester, self.course, 'load'))

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_content_beta_period(self):
        """
        Check that beta-test access works for content.
        """
        # student user shouldn't see it
        self.assertFalse(has_access(self.normal_student, self.content, 'load', self.course.id))

        # now the student should see it
        self.assertTrue(has_access(self.beta_tester, self.content, 'load', self.course.id))
