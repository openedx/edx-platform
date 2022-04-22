"""
This test file will run through some LMS test scenarios regarding access and navigation of the LMS
"""


import time

from unittest.mock import patch
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from common.djangoapps.student.tests.factories import GlobalStaffFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase, set_preview_mode
from openedx.features.course_experience import DISABLE_COURSE_OUTLINE_PAGE_FLAG


@set_preview_mode(True)
class TestNavigation(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that navigation state is saved properly.
    """
    @classmethod
    def setUpClass(cls):
        # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.test_course = CourseFactory.create()
            cls.test_course_proctored = CourseFactory.create()
            cls.course = CourseFactory.create()

    @classmethod
    def setUpTestData(cls):  # lint-amnesty, pylint: disable=super-method-not-called
        cls.chapter0 = ItemFactory.create(parent=cls.course,
                                          display_name='Overview')
        cls.chapter9 = ItemFactory.create(parent=cls.course,
                                          display_name='factory_chapter')
        cls.section0 = ItemFactory.create(parent=cls.chapter0,
                                          display_name='Welcome')
        cls.section9 = ItemFactory.create(parent=cls.chapter9,
                                          display_name='factory_section')
        cls.unit0 = ItemFactory.create(parent=cls.section0,
                                       display_name='New Unit 0')

        cls.chapterchrome = ItemFactory.create(parent=cls.course,
                                               display_name='Chrome')
        cls.chromelesssection = ItemFactory.create(parent=cls.chapterchrome,
                                                   display_name='chromeless',
                                                   chrome='none')
        cls.accordionsection = ItemFactory.create(parent=cls.chapterchrome,
                                                  display_name='accordion',
                                                  chrome='accordion')
        cls.tabssection = ItemFactory.create(parent=cls.chapterchrome,
                                             display_name='tabs',
                                             chrome='tabs')
        cls.defaultchromesection = ItemFactory.create(
            parent=cls.chapterchrome,
            display_name='defaultchrome',
        )
        cls.fullchromesection = ItemFactory.create(parent=cls.chapterchrome,
                                                   display_name='fullchrome',
                                                   chrome='accordion,tabs')
        cls.tabtest = ItemFactory.create(parent=cls.chapterchrome,
                                         display_name='pdf_textbooks_tab',
                                         default_tab='progress')

        cls.user = GlobalStaffFactory(password='test')

    def setUp(self):
        super().setUp()
        self.login(self.user.email, 'test')

    def assertTabActive(self, tabname, response):
        ''' Check if the progress tab is active in the tab set '''
        for line in response.content.decode('utf-8').split('\n'):
            if tabname in line and 'active' in line:
                return
        raise AssertionError(f"assertTabActive failed: {tabname} not active")

    def assertTabInactive(self, tabname, response):  # lint-amnesty, pylint: disable=useless-return
        ''' Check if the progress tab is active in the tab set '''
        for line in response.content.decode('utf-8').split('\n'):
            if tabname in line and 'active' in line:
                raise AssertionError("assertTabInactive failed: " + tabname + " active")
        return

    # TODO: LEARNER-71: Do we need to adjust or remove this test?
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_chrome_settings(self):
        '''
        Test settings for disabling and modifying navigation chrome in the courseware:
        - Accordion enabled, or disabled
        - Navigation tabs enabled, disabled, or redirected
        '''
        test_data = (
            ('tabs', False, True),
            ('none', False, False),
            ('accordion', True, False),
            ('fullchrome', True, True),
        )
        for (displayname, accordion, tabs) in test_data:
            response = self.client.get(reverse('courseware_section', kwargs={
                'course_id': str(self.course.id),
                'chapter': 'Chrome',
                'section': displayname,
            }))
            assert ('course-tabs' in response.content.decode('utf-8')) == tabs
            assert ('course-navigation' in response.content.decode('utf-8')) == accordion

        self.assertTabInactive('progress', response)
        self.assertTabActive('courseware', response)

        response = self.client.get(reverse('courseware_section', kwargs={
            'course_id': str(self.course.id),
            'chapter': 'Chrome',
            'section': 'pdf_textbooks_tab',
        }))

        self.assertTabActive('progress', response)
        self.assertTabInactive('courseware', response)

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=1)
    def test_inactive_session_timeout(self):
        """
        Verify that an inactive session times out and redirects to the
        login page
        """
        # make sure we can access courseware immediately
        resp = self.client.get(reverse('dashboard'))
        assert resp.status_code == 200

        # then wait a bit and see if we get timed out
        time.sleep(2)

        resp = self.client.get(reverse('dashboard'))

        # re-request, and we should get a redirect to login page
        self.assertRedirects(resp, settings.LOGIN_REDIRECT_URL + '?next=' + reverse('dashboard'))

    def test_redirects_first_time(self):
        """
        Verify that the first time we click on the courseware tab we are
        redirected to the 'Welcome' section.
        """
        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': str(self.course.id)}))
        self.assertRedirects(resp, reverse(
            'courseware_section', kwargs={'course_id': str(self.course.id),
                                          'chapter': 'Overview',
                                          'section': 'Welcome'}))

    def test_redirects_second_time(self):
        """
        Verify the accordion remembers we've already visited the Welcome section
        and redirects correspondingly.
        """
        section_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course.id),
                'chapter': 'Overview',
                'section': 'Welcome',
            },
        )
        self.client.get(section_url)
        resp = self.client.get(
            reverse('courseware', kwargs={'course_id': str(self.course.id)}),
        )
        self.assertRedirects(resp, section_url)

    def test_accordion_state(self):
        """
        Verify the accordion remembers which chapter you were last viewing.
        """
        # Now we directly navigate to a section in a chapter other than 'Overview'.
        section_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': str(self.course.id),
                'chapter': 'factory_chapter',
                'section': 'factory_section',
            }
        )
        self.assert_request_status_code(200, section_url)

        # And now hitting the courseware tab should redirect to 'factory_chapter'
        url = reverse(
            'courseware',
            kwargs={'course_id': str(self.course.id)}
        )
        resp = self.client.get(url)
        self.assertRedirects(resp, section_url)

    # TODO: LEARNER-71: Do we need to adjust or remove this test?
    @override_waffle_flag(DISABLE_COURSE_OUTLINE_PAGE_FLAG, active=True)
    def test_incomplete_course(self):
        test_course_id = str(self.test_course.id)

        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        response = self.assert_request_status_code(200, url)
        self.assertContains(response, "No content has been added to this course")

        section = ItemFactory.create(
            parent_location=self.test_course.location,
            display_name='New Section'
        )
        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        response = self.assert_request_status_code(200, url)
        self.assertNotContains(response, "No content has been added to this course")
        self.assertContains(response, "New Section")

        subsection = ItemFactory.create(
            parent_location=section.location,
            display_name='New Subsection',
        )
        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        response = self.assert_request_status_code(200, url)
        self.assertContains(response, "New Subsection")
        self.assertNotContains(response, "sequence-nav")

        ItemFactory.create(
            parent_location=subsection.location,
            display_name='New Unit',
        )
        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        self.assert_request_status_code(302, url)

    def test_proctoring_js_includes(self):
        """
        Make sure that proctoring JS does not get included on
        courseware pages if either the FEATURE flag is turned off
        or the course is not proctored enabled
        """
        test_course_id = str(self.test_course_proctored.id)

        with patch.dict(settings.FEATURES, {'ENABLE_SPECIAL_EXAMS': False}):
            url = reverse(
                'courseware',
                kwargs={'course_id': test_course_id}
            )
            resp = self.client.get(url)

            self.assertNotContains(resp, '/static/js/lms-proctoring.js')

        with patch.dict(settings.FEATURES, {'ENABLE_SPECIAL_EXAMS': True}):
            url = reverse(
                'courseware',
                kwargs={'course_id': test_course_id}
            )
            resp = self.client.get(url)

            self.assertNotContains(resp, '/static/js/lms-proctoring.js')

            # now set up a course which is proctored enabled

            self.test_course_proctored.enable_proctored_exams = True
            self.test_course_proctored.save()

            modulestore().update_item(self.test_course_proctored, self.user.id)

            resp = self.client.get(url)

            self.assertContains(resp, '/static/js/lms-proctoring.js')
