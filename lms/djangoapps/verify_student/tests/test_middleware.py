from django.http import HttpResponse, SimpleCookie

from course_modes.models import CourseMode
from openedx.core.djangolib.testing.utils import get_mock_request
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..middleware import CourseUpsellMiddleware


class TestCourseUpsellMiddleware(SharedModuleStoreTestCase):
    @classmethod
    def setUpClass(cls):
        super(TestCourseUpsellMiddleware, cls).setUpClass()

        # create courses
        cls.courses = []
        for _ in range(2):
            cls.courses.append(CourseFactory())

        # create users
        cls.verified_user = UserFactory()
        cls.non_verified_user = UserFactory()

        # create enrollments
        for course in cls.courses:
            CourseEnrollmentFactory(
                course_id=course.id, user=cls.non_verified_user, is_active=True, mode=CourseMode.HONOR,
            )
            CourseEnrollmentFactory(
                course_id=course.id, user=cls.verified_user, is_active=True, mode=CourseMode.VERIFIED,
            )

    def setUp(self):
        super(TestCourseUpsellMiddleware, self).setUp()

        self.request = get_mock_request()
        self.request.session = {}
        self.request.META['PATH_INFO'] = u'/courses/some/course/run/course/'
        self.client.response = HttpResponse()
        self.client.response.cookies = SimpleCookie()

    def test_cookie_nonexistent_for_verified(self):
        self.request.user = self.verified_user
        response = CourseUpsellMiddleware().process_response(self.request, self.client.response)
        self.assertTrue(len(response.cookies), 0)

    def test_cookie_exists_for_unverified(self):
        self.request.user = self.non_verified_user
        response = CourseUpsellMiddleware().process_response(self.request, self.client.response)
        self.assertTrue(len(response.cookies), 1)
        for course in self.courses:
            self.assertIn(unicode(course.id), response.cookies['upsell_courses'].value)
