"""
Test the course_info xblock
"""
import mock
from nose.plugins.attrib import attr
from urllib import urlencode

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from util.date_utils import strftime_localized
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_CLOSED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from student.models import CourseEnrollment

from .helpers import LoginEnrollmentTestCase


@attr('shard_1')
class CourseInfoTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for the Course Info page
    """
    def setUp(self):
        super(CourseInfoTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.page = ItemFactory.create(
            category="course_info", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="updates"
        )

    def test_logged_in_unenrolled(self):
        self.setup_user()
        url = reverse('info', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)
        self.assertIn("You are not currently enrolled in this course", resp.content)

    def test_logged_in_enrolled(self):
        self.enroll(self.course)
        url = reverse('info', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertNotIn("You are not currently enrolled in this course", resp.content)

    def test_anonymous_user(self):
        url = reverse('info', args=[self.course.id.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("OOGIE BLOOGIE", resp.content)

    def test_logged_in_not_enrolled(self):
        self.setup_user()
        url = reverse('info', args=[self.course.id.to_deprecated_string()])
        self.client.get(url)

        # Check whether the user has been enrolled in the course.
        # There was a bug in which users would be automatically enrolled
        # with is_active=False (same as if they enrolled and immediately unenrolled).
        # This verifies that the user doesn't have *any* enrollment record.
        enrollment_exists = CourseEnrollment.objects.filter(
            user=self.user, course_id=self.course.id
        ).exists()
        self.assertFalse(enrollment_exists)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    def test_non_live_course(self):
        """Ensure that a user accessing a non-live course sees a redirect to
        the student dashboard, not a 404.
        """
        self.setup_user()
        self.enroll(self.course)
        url = reverse('info', args=[unicode(self.course.id)])
        response = self.client.get(url)
        start_date = strftime_localized(self.course.start, 'SHORT_DATE')
        self.assertRedirects(response, '{0}?{1}'.format(reverse('dashboard'), urlencode({'notlive': start_date})))

    def test_nonexistent_course(self):
        self.setup_user()
        url = reverse('info', args=['not/a/course'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@attr('shard_1')
class CourseInfoTestCaseXML(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for the Course Info page for an XML course
    """
    MODULESTORE = TEST_DATA_MIXED_CLOSED_MODULESTORE

    # The following XML test course (which lives at common/test/data/2014)
    # is closed; we're testing that a course info page still appears when
    # the course is already closed
    xml_course_key = SlashSeparatedCourseKey('edX', 'detached_pages', '2014')

    # this text appears in that course's course info page
    # common/test/data/2014/info/updates.html
    xml_data = "course info 463139"

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_logged_in_xml(self):
        self.setup_user()
        url = reverse('info', args=[self.xml_course_key.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('info', args=[self.xml_course_key.to_deprecated_string()])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.xml_data, resp.content)


@attr('shard_1')
@override_settings(FEATURES=dict(settings.FEATURES, EMBARGO=False))
class SelfPacedCourseInfoTestCase(LoginEnrollmentTestCase, SharedModuleStoreTestCase):
    """
    Tests for the info page of self-paced courses.
    """

    def setUp(self):
        super(SelfPacedCourseInfoTestCase, self).setUp()
        self.instructor_paced_course = CourseFactory.create(self_paced=False)
        self.self_paced_course = CourseFactory.create(self_paced=True)
        self.setup_user()

    def fetch_course_info_with_queries(self, course, sql_queries, mongo_queries):
        """
        Fetch the given course's info page, asserting the number of SQL
        and Mongo queries.
        """
        url = reverse('info', args=[unicode(course.id)])
        with self.assertNumQueries(sql_queries):
            with check_mongo_calls(mongo_queries):
                resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_num_queries_instructor_paced(self):
        self.fetch_course_info_with_queries(self.instructor_paced_course, 17, 4)

    def test_num_queries_self_paced(self):
        self.fetch_course_info_with_queries(self.self_paced_course, 17, 4)
