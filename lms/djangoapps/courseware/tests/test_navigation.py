"""
This test file will run through some LMS test scenarios regarding access and navigation of the LMS
"""
import time
from nose.plugins.attrib import attr

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.factories import GlobalStaffFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


@attr('shard_1')
class TestNavigation(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that navigation state is saved properly.
    """

    STUDENT_INFO = [('view@test.com', 'foo'), ('view2@test.com', 'foo')]

    def setUp(self):
        super(TestNavigation, self).setUp()
        self.test_course = CourseFactory.create()
        self.course = CourseFactory.create()
        self.chapter0 = ItemFactory.create(parent=self.course,
                                           display_name='Overview')
        self.chapter9 = ItemFactory.create(parent=self.course,
                                           display_name='factory_chapter')
        self.section0 = ItemFactory.create(parent=self.chapter0,
                                           display_name='Welcome')
        self.section9 = ItemFactory.create(parent=self.chapter9,
                                           display_name='factory_section')
        self.unit0 = ItemFactory.create(parent=self.section0,
                                        display_name='New Unit')

        self.chapterchrome = ItemFactory.create(parent=self.course,
                                                display_name='Chrome')
        self.chromelesssection = ItemFactory.create(parent=self.chapterchrome,
                                                    display_name='chromeless',
                                                    chrome='none')
        self.accordionsection = ItemFactory.create(parent=self.chapterchrome,
                                                   display_name='accordion',
                                                   chrome='accordion')
        self.tabssection = ItemFactory.create(parent=self.chapterchrome,
                                              display_name='tabs',
                                              chrome='tabs')
        self.defaultchromesection = ItemFactory.create(
            parent=self.chapterchrome,
            display_name='defaultchrome',
        )
        self.fullchromesection = ItemFactory.create(parent=self.chapterchrome,
                                                    display_name='fullchrome',
                                                    chrome='accordion,tabs')
        self.tabtest = ItemFactory.create(parent=self.chapterchrome,
                                          display_name='progress_tab',
                                          default_tab='progress')

        # Create student accounts and activate them.
        for i in range(len(self.STUDENT_INFO)):
            email, password = self.STUDENT_INFO[i]
            username = 'u{0}'.format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

        self.staff_user = GlobalStaffFactory()

    def assertTabActive(self, tabname, response):
        ''' Check if the progress tab is active in the tab set '''
        for line in response.content.split('\n'):
            if tabname in line and 'active' in line:
                return
        raise AssertionError("assertTabActive failed: {} not active".format(tabname))

    def assertTabInactive(self, tabname, response):
        ''' Check if the progress tab is active in the tab set '''
        for line in response.content.split('\n'):
            if tabname in line and 'active' in line:
                raise AssertionError("assertTabInactive failed: " + tabname + " active")
        return

    def test_chrome_settings(self):
        '''
        Test settings for disabling and modifying navigation chrome in the courseware:
        - Accordion enabled, or disabled
        - Navigation tabs enabled, disabled, or redirected
        '''
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)

        test_data = (
            ('tabs', False, True),
            ('none', False, False),
            ('fullchrome', True, True),
            ('accordion', True, False),
            ('fullchrome', True, True)
        )
        for (displayname, accordion, tabs) in test_data:
            response = self.client.get(reverse('courseware_section', kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'Chrome',
                'section': displayname,
            }))
            self.assertEquals('open_close_accordion' in response.content, accordion)
            self.assertEquals('course-tabs' in response.content, tabs)

        self.assertTabInactive('progress', response)
        self.assertTabActive('courseware', response)

        response = self.client.get(reverse('courseware_section', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'chapter': 'Chrome',
            'section': 'progress_tab',
        }))

        self.assertTabActive('progress', response)
        self.assertTabInactive('courseware', response)

    @override_settings(SESSION_INACTIVITY_TIMEOUT_IN_SECONDS=1)
    def test_inactive_session_timeout(self):
        """
        Verify that an inactive session times out and redirects to the
        login page
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)

        # make sure we can access courseware immediately
        resp = self.client.get(reverse('dashboard'))
        self.assertEquals(resp.status_code, 200)

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
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id.to_deprecated_string()}))

        self.assertRedirects(resp, reverse(
            'courseware_section', kwargs={'course_id': self.course.id.to_deprecated_string(),
                                          'chapter': 'Overview',
                                          'section': 'Welcome'}))

    def test_redirects_second_time(self):
        """
        Verify the accordion remembers we've already visited the Welcome section
        and redirects correpondingly.
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        self.client.get(reverse('courseware_section', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'chapter': 'Overview',
            'section': 'Welcome',
        }))

        resp = self.client.get(reverse('courseware',
                               kwargs={'course_id': self.course.id.to_deprecated_string()}))

        redirect_url = reverse(
            'courseware_chapter',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'Overview'
            }
        )
        self.assertRedirects(resp, redirect_url)

    def test_accordion_state(self):
        """
        Verify the accordion remembers which chapter you were last viewing.
        """
        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.test_course, True)

        # Now we directly navigate to a section in a chapter other than 'Overview'.
        url = reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'factory_chapter',
                'section': 'factory_section'
            }
        )
        self.assert_request_status_code(200, url)

        # And now hitting the courseware tab should redirect to 'factory_chapter'
        url = reverse(
            'courseware',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        resp = self.client.get(url)

        redirect_url = reverse(
            'courseware_chapter',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'factory_chapter',
            }
        )
        self.assertRedirects(resp, redirect_url)

    def test_incomplete_course(self):
        email = self.staff_user.email
        password = "test"
        self.login(email, password)
        self.enroll(self.test_course, True)

        test_course_id = self.test_course.id.to_deprecated_string()

        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        self.assert_request_status_code(200, url)

        section = ItemFactory.create(
            parent_location=self.test_course.location,
            display_name='New Section'
        )
        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        self.assert_request_status_code(200, url)

        subsection = ItemFactory.create(
            parent_location=section.location,
            display_name='New Subsection'
        )
        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        self.assert_request_status_code(200, url)

        ItemFactory.create(
            parent_location=subsection.location,
            display_name='New Unit'
        )
        url = reverse(
            'courseware',
            kwargs={'course_id': test_course_id}
        )
        self.assert_request_status_code(302, url)
