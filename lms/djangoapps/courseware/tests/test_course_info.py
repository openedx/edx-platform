"""
Test the course_info xblock
"""
import mock
from nose.plugins.attrib import attr
from pyquery import PyQuery as pq
from urllib import urlencode

from ccx_keys.locator import CCXLocator
from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from util.date_utils import strftime_localized
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE,
    TEST_DATA_MIXED_MODULESTORE
)
from xmodule.modulestore.tests.utils import TEST_DATA_DIR
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from student.models import CourseEnrollment
from student.tests.factories import AdminFactory

from .helpers import LoginEnrollmentTestCase

from lms.djangoapps.ccx.tests.factories import CcxFactory


@attr('shard_1')
class CourseInfoTestCase(LoginEnrollmentTestCase, SharedModuleStoreTestCase):
    """
    Tests for the Course Info page
    """

    @classmethod
    def setUpClass(cls):
        super(CourseInfoTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.page = ItemFactory.create(
            category="course_info", parent_location=cls.course.location,
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
class CourseInfoLastAccessedTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests of the CourseInfo last accessed link.
    """

    def setUp(self):
        super(CourseInfoLastAccessedTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.page = ItemFactory.create(
            category="course_info", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="updates"
        )

    def test_last_accessed_courseware_not_shown(self):
        """
        Test that the last accessed courseware link is not shown if there
        is no course content.
        """
        SelfPacedConfiguration(enable_course_home_improvements=True).save()
        url = reverse('info', args=(unicode(self.course.id),))
        response = self.client.get(url)
        content = pq(response.content)
        self.assertEqual(content('.page-header-secondary a').length, 0)

    def test_last_accessed_shown(self):
        SelfPacedConfiguration(enable_course_home_improvements=True).save()
        chapter = ItemFactory.create(
            category="chapter", parent_location=self.course.location
        )
        section = ItemFactory.create(
            category='section', parent_location=chapter.location
        )
        section_url = reverse(
            'courseware_section',
            kwargs={
                'section': section.url_name,
                'chapter': chapter.url_name,
                'course_id': self.course.id
            }
        )
        self.client.get(section_url)
        info_url = reverse('info', args=(unicode(self.course.id),))
        info_page_response = self.client.get(info_url)
        content = pq(info_page_response.content)
        self.assertEqual(content('.page-header-secondary .last-accessed-link').attr('href'), section_url)


@attr('shard_1')
class CourseInfoTitleTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests of the CourseInfo page title.
    """

    def setUp(self):
        super(CourseInfoTitleTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.page = ItemFactory.create(
            category="course_info", parent_location=self.course.location,
            data="OOGIE BLOOGIE", display_name="updates"
        )

    def test_info_title(self):
        """
        Test the info page on a course without any display_* settings against
        one that does.
        """
        url = reverse('info', args=(unicode(self.course.id),))
        response = self.client.get(url)
        content = pq(response.content)
        expected_title = "Welcome to {org}'s {course_name}!".format(
            org=self.course.display_org_with_default,
            course_name=self.course.display_number_with_default
        )
        display_course = CourseFactory.create(
            org="HogwartZ",
            number="Potions_3",
            display_organization="HogwartsX",
            display_coursenumber="Potions",
            display_name="Introduction_to_Potions"
        )
        display_url = reverse('info', args=(unicode(display_course.id),))
        display_response = self.client.get(display_url)
        display_content = pq(display_response.content)
        expected_display_title = "Welcome to {org}'s {course_name}!".format(
            org=display_course.display_org_with_default,
            course_name=display_course.display_number_with_default
        )
        self.assertIn(
            expected_title,
            content('h1.page-title').contents()
        )
        self.assertIn(
            expected_display_title,
            display_content('h1.page-title').contents()
        )
        self.assertIn(
            display_course.display_name_with_default,
            display_content('h2.page-subtitle').contents()
        )


class CourseInfoTestCaseCCX(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test for unenrolled student tries to access ccx.
    Note: Only CCX coach can enroll a student in CCX. In sum self-registration not allowed.
    """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(CourseInfoTestCaseCCX, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(CourseInfoTestCaseCCX, self).setUp()

        # Create ccx coach account
        self.coach = coach = AdminFactory.create(password="test")
        self.client.login(username=coach.username, password="test")

    def test_redirect_to_dashboard_unenrolled_ccx(self):
        """
        Assert that when unenroll student tries to access ccx do not allow him self-register.
        Redirect him to his student dashboard
        """
        # create ccx
        ccx = CcxFactory(course_id=self.course.id, coach=self.coach)
        ccx_locator = CCXLocator.from_course_locator(self.course.id, unicode(ccx.id))

        self.setup_user()
        url = reverse('info', args=[ccx_locator])
        response = self.client.get(url)
        expected = reverse('dashboard')
        self.assertRedirects(response, expected, status_code=302, target_status_code=200)


@attr('shard_1')
class CourseInfoTestCaseXML(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests for the Course Info page for an XML course
    """
    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def setUp(self):
        """
        Set up the tests
        """
        super(CourseInfoTestCaseXML, self).setUp()

        # The following test course (which lives at common/test/data/2014)
        # is closed; we're testing that a course info page still appears when
        # the course is already closed
        self.xml_course_key = self.store.make_course_key('edX', 'detached_pages', '2014')
        import_course_from_xml(
            self.store,
            'test_user',
            TEST_DATA_DIR,
            source_dirs=['2014'],
            static_content_store=None,
            target_id=self.xml_course_key,
            raise_on_failure=True,
            create_if_not_present=True,
        )

        # this text appears in that course's course info page
        # common/test/data/2014/info/updates.html
        self.xml_data = "course info 463139"

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
    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    @classmethod
    def setUpClass(cls):
        super(SelfPacedCourseInfoTestCase, cls).setUpClass()
        cls.instructor_paced_course = CourseFactory.create(self_paced=False)
        cls.self_paced_course = CourseFactory.create(self_paced=True)

    def setUp(self):
        SelfPacedConfiguration(enabled=True).save()
        super(SelfPacedCourseInfoTestCase, self).setUp()
        self.setup_user()

    def fetch_course_info_with_queries(self, course, sql_queries, mongo_queries):
        """
        Fetch the given course's info page, asserting the number of SQL
        and Mongo queries.
        """
        url = reverse('info', args=[unicode(course.id)])
        with self.assertNumQueries(sql_queries):
            with check_mongo_calls(mongo_queries):
                with mock.patch("openedx.core.djangoapps.theming.helpers.get_current_site", return_value=None):
                    resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_num_queries_instructor_paced(self):
        self.fetch_course_info_with_queries(self.instructor_paced_course, 23, 4)

    def test_num_queries_self_paced(self):
        self.fetch_course_info_with_queries(self.self_paced_course, 23, 4)
