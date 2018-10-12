# coding=utf-8
"""
Test the course_info xblock
"""
import ddt
import mock
from django.conf import settings
from django.urls import reverse
from django.http import QueryDict
from django.test.utils import override_settings

from ccx_keys.locator import CCXLocator
from lms.djangoapps.ccx.tests.factories import CcxFactory
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration_context
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES, override_waffle_flag
from openedx.core.lib.tests import attr
from openedx.features.course_experience import UNIFIED_COURSE_TAB_FLAG
from openedx.features.enterprise_support.tests.mixins.enterprise import EnterpriseTestConsentRequired
from pyquery import PyQuery as pq
from six import text_type
from student.models import CourseEnrollment
from student.tests.factories import AdminFactory
from util.date_utils import strftime_localized
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MIXED_MODULESTORE,
    TEST_DATA_SPLIT_MODULESTORE,
    ModuleStoreTestCase,
    SharedModuleStoreTestCase
)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from xmodule.modulestore.tests.utils import TEST_DATA_DIR
from xmodule.modulestore.xml_importer import import_course_from_xml

from .helpers import LoginEnrollmentTestCase

QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES


@attr(shard=1)
@override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
class CourseInfoTestCase(EnterpriseTestConsentRequired, LoginEnrollmentTestCase, SharedModuleStoreTestCase):
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
        url = reverse('info', args=[text_type(self.course.id)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("OOGIE BLOOGIE", resp.content)
        self.assertIn("You are not currently enrolled in this course", resp.content)

    def test_logged_in_enrolled(self):
        self.enroll(self.course)
        url = reverse('info', args=[text_type(self.course.id)])
        resp = self.client.get(url)
        self.assertNotIn("You are not currently enrolled in this course", resp.content)

    # TODO: LEARNER-611: If this is only tested under Course Info, does this need to move?
    @mock.patch('openedx.features.enterprise_support.api.enterprise_customer_for_request')
    def test_redirection_missing_enterprise_consent(self, mock_enterprise_customer_for_request):
        """
        Verify that users viewing the course info who are enrolled, but have not provided
        data sharing consent, are first redirected to a consent page, and then, once they've
        provided consent, are able to view the course info.
        """
        # ENT-924: Temporary solution to replace sensitive SSO usernames.
        mock_enterprise_customer_for_request.return_value = None

        self.setup_user()
        self.enroll(self.course)

        url = reverse('info', args=[text_type(self.course.id)])

        self.verify_consent_required(self.client, url)

    def test_anonymous_user(self):
        url = reverse('info', args=[text_type(self.course.id)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("OOGIE BLOOGIE", resp.content)

    def test_logged_in_not_enrolled(self):
        self.setup_user()
        url = reverse('info', args=[text_type(self.course.id)])
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
        url = reverse('info', args=[text_type(self.course.id)])
        response = self.client.get(url)
        start_date = strftime_localized(self.course.start, 'SHORT_DATE')
        expected_params = QueryDict(mutable=True)
        expected_params['notlive'] = start_date
        expected_url = '{url}?{params}'.format(
            url=reverse('dashboard'),
            params=expected_params.urlencode()
        )
        self.assertRedirects(response, expected_url)

    @mock.patch.dict(settings.FEATURES, {'DISABLE_START_DATES': False})
    @mock.patch("util.date_utils.strftime_localized")
    def test_non_live_course_other_language(self, mock_strftime_localized):
        """Ensure that a user accessing a non-live course sees a redirect to
        the student dashboard, not a 404, even if the localized date is unicode
        """
        self.setup_user()
        self.enroll(self.course)
        fake_unicode_start_time = u"üñîçø∂é_ßtå®t_tîµé"
        mock_strftime_localized.return_value = fake_unicode_start_time

        url = reverse('info', args=[text_type(self.course.id)])
        response = self.client.get(url)
        expected_params = QueryDict(mutable=True)
        expected_params['notlive'] = fake_unicode_start_time
        expected_url = u'{url}?{params}'.format(
            url=reverse('dashboard'),
            params=expected_params.urlencode()
        )
        self.assertRedirects(response, expected_url)

    def test_nonexistent_course(self):
        self.setup_user()
        url = reverse('info', args=['not/a/course'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


@attr(shard=1)
@override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
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

    def get_resume_course_url(self, course_info_url):
        """
        Retrieves course info page and returns the resume course url
        or None if the button doesn't exist.
        """
        info_page_response = self.client.get(course_info_url)
        content = pq(info_page_response.content)
        return content('.page-header-secondary .last-accessed-link').attr('href')

    def test_resume_course_visibility(self):
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

        # Assuring a non-authenticated user cannot see the resume course button.
        resume_course_url = self.get_resume_course_url(info_url)
        self.assertEqual(resume_course_url, None)

        # Assuring an unenrolled user cannot see the resume course button.
        self.setup_user()
        resume_course_url = self.get_resume_course_url(info_url)
        self.assertEqual(resume_course_url, None)

        # Assuring an enrolled user can see the resume course button.
        self.enroll(self.course)
        resume_course_url = self.get_resume_course_url(info_url)
        self.assertEqual(resume_course_url, section_url)


@attr(shard=1)
@override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
@ddt.ddt
class CourseInfoTitleTestCase(LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests of the CourseInfo page title site configuration options.
    """
    def setUp(self):
        super(CourseInfoTitleTestCase, self).setUp()
        self.course = CourseFactory.create(
            org="HogwartZ",
            number="Potions_3",
            display_organization="HogwartsX",
            display_coursenumber="Potions101",
            display_name="Introduction to Potions"
        )

    @ddt.data(
        # Default site configuration shows course number, org, and display name as subtitle.
        (dict(),
         "Welcome to HogwartsX's Potions101!", "Introduction to Potions"),

        # Show org in title
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=False,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=True,
              COURSE_HOMEPAGE_SHOW_ORG=True),
         "Welcome to HogwartsX's Potions101!", "Introduction to Potions"),

        # Don't show org in title
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=False,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=True,
              COURSE_HOMEPAGE_SHOW_ORG=False),
         "Welcome to Potions101!", "Introduction to Potions"),

        # Hide subtitle and org
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=False,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=False,
              COURSE_HOMEPAGE_SHOW_ORG=False),
         "Welcome to Potions101!", None),

        # Show display name as title, hide subtitle and org.
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=True,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=False,
              COURSE_HOMEPAGE_SHOW_ORG=False),
         "Welcome to Introduction to Potions!", None),

        # Show display name as title with org, hide subtitle.
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=True,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=False,
              COURSE_HOMEPAGE_SHOW_ORG=True),
         "Welcome to HogwartsX's Introduction to Potions!", None),

        # Show display name as title, hide org, and show course number as subtitle.
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=True,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=True,
              COURSE_HOMEPAGE_SHOW_ORG=False),
         "Welcome to Introduction to Potions!", 'Potions101'),

        # Show display name as title with org, and show course number as subtitle.
        (dict(COURSE_HOMEPAGE_INVERT_TITLE=True,
              COURSE_HOMEPAGE_SHOW_SUBTITLE=True,
              COURSE_HOMEPAGE_SHOW_ORG=True),
         "Welcome to HogwartsX's Introduction to Potions!", 'Potions101'),
    )
    @ddt.unpack
    def test_info_title(self, site_config, expected_title, expected_subtitle):
        """
        Test the info page on a course with all the multiple display options
        depeding on the current site configuration
        """
        url = reverse('info', args=(unicode(self.course.id),))
        with with_site_configuration_context(configuration=site_config):
            response = self.client.get(url)

        content = pq(response.content)

        self.assertEqual(
            expected_title,
            content('.page-title').contents()[0].strip(),
        )

        if expected_subtitle is None:
            self.assertEqual(
                [],
                content('.page-subtitle'),
            )
        else:
            self.assertEqual(
                expected_subtitle,
                content('.page-subtitle').contents()[0].strip(),
            )


@override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
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


@attr(shard=1)
@override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
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
        url = reverse('info', args=[text_type(self.xml_course_key)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.xml_data, resp.content)

    @mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_START_DATES': False})
    def test_anonymous_user_xml(self):
        url = reverse('info', args=[text_type(self.xml_course_key)])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(self.xml_data, resp.content)


@attr(shard=1)
@override_settings(FEATURES=dict(settings.FEATURES, EMBARGO=False))
@override_waffle_flag(UNIFIED_COURSE_TAB_FLAG, active=False)
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
        super(SelfPacedCourseInfoTestCase, self).setUp()
        self.setup_user()

    def fetch_course_info_with_queries(self, course, sql_queries, mongo_queries):
        """
        Fetch the given course's info page, asserting the number of SQL
        and Mongo queries.
        """
        url = reverse('info', args=[text_type(course.id)])
        with self.assertNumQueries(sql_queries, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
            with check_mongo_calls(mongo_queries):
                with mock.patch("openedx.core.djangoapps.theming.helpers.get_current_site", return_value=None):
                    resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_num_queries_instructor_paced(self):
        self.fetch_course_info_with_queries(self.instructor_paced_course, 29, 3)

    def test_num_queries_self_paced(self):
        self.fetch_course_info_with_queries(self.self_paced_course, 29, 3)
