import datetime
import pytz

from django.core.urlresolvers import reverse
from mock import patch
from nose.plugins.attrib import attr

from courseware.access import has_access
from courseware.tests.helpers import CourseAccessTestMixin, LoginEnrollmentTestCase
from courseware.tests.factories import (
    BetaTesterFactory,
    StaffFactory,
    GlobalStaffFactory,
    InstructorFactory,
    OrgStaffFactory,
    OrgInstructorFactory,
)
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory


@attr(shard=1)
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
        return [reverse(name, kwargs={'course_id': course.id.to_deprecated_string()})
                for name in names]

    def _check_non_staff_light(self, course):
        """
        Check that non-staff have access to light urls.

        `course` is an instance of CourseDescriptor.
        """
        urls = [reverse('about_course', kwargs={'course_id': course.id.to_deprecated_string()}),
                reverse('courses')]
        for url in urls:
            self.assert_request_status_code(200, url)

    def _check_non_staff_dark(self, course):
        """
        Check that non-staff don't have access to dark urls.
        """

        names = ['courseware', 'instructor_dashboard', 'progress']
        urls = self._reverse_urls(names, course)
        urls.extend([
            reverse('book', kwargs={'course_id': course.id.to_deprecated_string(),
                                    'book_index': index})
            for index, __ in enumerate(course.textbooks)
        ])
        for url in urls:
            self.assert_request_status_code(404, url)

    def _check_staff(self, course):
        """
        Check that access is right for staff in course.
        """
        names = ['about_course', 'instructor_dashboard', 'progress']
        urls = self._reverse_urls(names, course)
        urls.extend([
            reverse('book', kwargs={'course_id': course.id.to_deprecated_string(),
                                    'book_index': index})
            for index in xrange(len(course.textbooks))
        ])
        for url in urls:
            self.assert_request_status_code(200, url)

        # The student progress tab is not accessible to a student
        # before launch, so the instructor view-as-student feature
        # should return a 404 as well.
        # TODO (vshnayder): If this is not the behavior we want, will need
        # to make access checking smarter and understand both the effective
        # user (the student), and the requesting user (the prof)
        url = reverse(
            'student_progress',
            kwargs={
                'course_id': course.id.to_deprecated_string(),
                'student_id': self.enrolled_user.id,
            }
        )
        self.assert_request_status_code(404, url)

        # The courseware url should redirect, not 200
        url = self._reverse_urls(['courseware'], course)[0]
        self.assert_request_status_code(302, url)

    def login(self, user):
        return super(TestViewAuth, self).login(user.email, 'test')

    def setUp(self):
        super(TestViewAuth, self).setUp()

        self.course = CourseFactory.create(number='999', display_name='Robot_Super_Course')
        self.courseware_chapter = ItemFactory.create(display_name='courseware')
        self.overview_chapter = ItemFactory.create(
            parent_location=self.course.location,
            display_name='Super Overview'
        )
        self.welcome_section = ItemFactory.create(
            parent_location=self.overview_chapter.location,
            display_name='Super Welcome'
        )
        self.welcome_unit = ItemFactory.create(
            parent_location=self.welcome_section.location,
            display_name='Super Unit'
        )
        self.course = modulestore().get_course(self.course.id)

        self.test_course = CourseFactory.create(org=self.course.id.org)
        self.other_org_course = CourseFactory.create(org='Other_Org_Course')
        self.sub_courseware_chapter = ItemFactory.create(
            parent_location=self.test_course.location,
            display_name='courseware'
        )
        self.sub_overview_chapter = ItemFactory.create(
            parent_location=self.sub_courseware_chapter.location,
            display_name='Overview'
        )
        self.sub_welcome_section = ItemFactory.create(
            parent_location=self.sub_overview_chapter.location,
            display_name='Welcome'
        )
        self.sub_welcome_unit = ItemFactory.create(
            parent_location=self.sub_welcome_section.location,
            display_name='New Unit'
        )
        self.test_course = modulestore().get_course(self.test_course.id)

        self.global_staff_user = GlobalStaffFactory()
        self.unenrolled_user = UserFactory(last_name="Unenrolled")

        self.enrolled_user = UserFactory(last_name="Enrolled")
        CourseEnrollmentFactory(user=self.enrolled_user, course_id=self.course.id)
        CourseEnrollmentFactory(user=self.enrolled_user, course_id=self.test_course.id)

        self.staff_user = StaffFactory(course_key=self.course.id)
        self.instructor_user = InstructorFactory(course_key=self.course.id)
        self.org_staff_user = OrgStaffFactory(course_key=self.course.id)
        self.org_instructor_user = OrgInstructorFactory(course_key=self.course.id)

    def test_redirection_unenrolled(self):
        """
        Verify unenrolled student is redirected to the 'about' section of the chapter
        instead of the 'Welcome' section after clicking on the courseware tab.
        """
        self.login(self.unenrolled_user)
        response = self.client.get(reverse('courseware',
                                           kwargs={'course_id': self.course.id.to_deprecated_string()}))
        self.assertRedirects(
            response,
            reverse(
                'about_course',
                args=[self.course.id.to_deprecated_string()]
            )
        )

    def test_redirection_enrolled(self):
        """
        Verify enrolled student is redirected to the 'Welcome' section of
        the chapter after clicking on the courseware tab.
        """
        self.login(self.enrolled_user)

        response = self.client.get(
            reverse(
                'courseware',
                kwargs={'course_id': self.course.id.to_deprecated_string()}
            )
        )

        self.assertRedirects(
            response,
            reverse(
                'courseware_section',
                kwargs={'course_id': self.course.id.to_deprecated_string(),
                        'chapter': self.overview_chapter.url_name,
                        'section': self.welcome_section.url_name}
            )
        )

    def test_instructor_page_access_nonstaff(self):
        """
        Verify non-staff cannot load the instructor
        dashboard, the grade views, and student profile pages.
        """
        self.login(self.enrolled_user)

        urls = [reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()}),
                reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id.to_deprecated_string()})]

        # Shouldn't be able to get to the instructor pages
        for url in urls:
            self.assert_request_status_code(404, url)

    def test_staff_course_access(self):
        """
        Verify staff can load the staff dashboard, the grade views,
        and student profile pages for their course.
        """
        self.login(self.staff_user)

        # Now should be able to get to self.course, but not  self.test_course
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id.to_deprecated_string()})
        self.assert_request_status_code(404, url)

    def test_instructor_course_access(self):
        """
        Verify instructor can load the instructor dashboard, the grade views,
        and student profile pages for their course.
        """
        self.login(self.instructor_user)

        # Now should be able to get to self.course, but not  self.test_course
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id.to_deprecated_string()})
        self.assert_request_status_code(404, url)

    def test_org_staff_access(self):
        """
        Verify org staff can load the instructor dashboard, the grade views,
        and student profile pages for course in their org.
        """
        self.login(self.org_staff_user)
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.other_org_course.id.to_deprecated_string()})
        self.assert_request_status_code(404, url)

    def test_org_instructor_access(self):
        """
        Verify org instructor can load the instructor dashboard, the grade views,
        and student profile pages for course in their org.
        """
        self.login(self.org_instructor_user)
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id.to_deprecated_string()})
        self.assert_request_status_code(200, url)

        url = reverse('instructor_dashboard', kwargs={'course_id': self.other_org_course.id.to_deprecated_string()})
        self.assert_request_status_code(404, url)

    def test_global_staff_access(self):
        """
        Verify the global staff user can access any course.
        """
        self.login(self.global_staff_user)

        # and now should be able to load both
        urls = [reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()}),
                reverse('instructor_dashboard', kwargs={'course_id': self.test_course.id.to_deprecated_string()})]

        for url in urls:
            self.assert_request_status_code(200, url)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_dark_launch_enrolled_student(self):
        """
        Make sure that before course start, students can't access course
        pages.
        """

        # Make courses start in the future
        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)
        self.course.start = tomorrow
        self.test_course.start = tomorrow
        self.course = self.update_course(self.course, self.user.id)
        self.test_course = self.update_course(self.test_course, self.user.id)

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
        self.course.start = tomorrow
        self.test_course.start = tomorrow
        self.course = self.update_course(self.course, self.user.id)
        self.test_course = self.update_course(self.test_course, self.user.id)

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

        self.course.start = tomorrow
        self.test_course.start = tomorrow
        self.course = self.update_course(self.course, self.user.id)
        self.test_course = self.update_course(self.test_course, self.user.id)

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

        # self.course's enrollment period hasn't started
        self.course.enrollment_start = tomorrow
        self.course.enrollment_end = nextday
        # test_course course's has
        self.test_course.enrollment_start = yesterday
        self.test_course.enrollment_end = tomorrow
        self.course = self.update_course(self.course, self.user.id)
        self.test_course = self.update_course(self.test_course, self.user.id)

        # First, try with an enrolled student
        self.login(self.unenrolled_user)
        self.assertFalse(self.enroll(self.course))
        self.assertTrue(self.enroll(self.test_course))

        # Then, try as an instructor
        self.logout()
        self.login(self.instructor_user)
        self.assertTrue(self.enroll(self.course))

        # Then, try as global staff
        self.logout()
        self.login(self.global_staff_user)
        self.assertTrue(self.enroll(self.course))


@attr(shard=1)
class TestBetatesterAccess(ModuleStoreTestCase, CourseAccessTestMixin):
    """
    Tests for the beta tester feature
    """
    def setUp(self):
        super(TestBetatesterAccess, self).setUp()

        now = datetime.datetime.now(pytz.UTC)
        tomorrow = now + datetime.timedelta(days=1)

        self.course = CourseFactory(days_early_for_beta=2, start=tomorrow)
        self.content = ItemFactory(parent=self.course)

        self.normal_student = UserFactory()
        self.beta_tester = BetaTesterFactory(course_key=self.course.id)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_course_beta_period(self):
        """
        Check that beta-test access works for courses.
        """
        self.assertFalse(self.course.has_started())
        self.assertCannotAccessCourse(self.normal_student, 'load', self.course)
        self.assertCanAccessCourse(self.beta_tester, 'load', self.course)

    @patch.dict('courseware.access.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_content_beta_period(self):
        """
        Check that beta-test access works for content.
        """
        # student user shouldn't see it
        self.assertFalse(has_access(self.normal_student, 'load', self.content, self.course.id))

        # now the student should see it
        self.assertTrue(has_access(self.beta_tester, 'load', self.content, self.course.id))
