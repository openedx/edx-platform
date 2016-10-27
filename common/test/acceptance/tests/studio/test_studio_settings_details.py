"""
Acceptance tests for Studio's Settings Details pages
"""
from datetime import datetime, timedelta
from flaky import flaky
from nose.plugins.attrib import attr
from unittest import skip

from common.test.acceptance.fixtures.config import ConfigModelFixture
from common.test.acceptance.fixtures.course import CourseFixture
from common.test.acceptance.pages.studio.settings import SettingsPage
from common.test.acceptance.pages.studio.overview import CourseOutlinePage
from common.test.acceptance.tests.studio.base_studio_test import StudioCourseTest
from common.test.acceptance.tests.helpers import (
    generate_course_key,
    select_option_by_value,
    is_option_value_selected,
    element_has_text,
)

import logging
log = logging.getLogger('SettingsPage')

@attr(shard=4)
class StudioSettingsDetailsTest(StudioCourseTest):
    """Base class for settings and details page tests."""

    def setUp(self, is_staff=True):
        super(StudioSettingsDetailsTest, self).setUp(is_staff=is_staff)
        self.settings_detail = SettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        # Before every test, make sure to visit the page first
        self.settings_detail.visit()
        self.assertTrue(self.settings_detail.is_browser_on_page())


@attr(shard=4)
class SettingsMilestonesTest(StudioSettingsDetailsTest):
    """
    Tests for milestones feature in Studio's settings tab
    """
    @flaky(max_runs=30, min_passes=30)  # SOL-1811
    def test_prerequisite_course_save_successfully(self):
        """
         Scenario: Selecting course from Pre-Requisite course drop down save the selected course as pre-requisite
         course.
            Given that I am on the Schedule & Details page on studio
            When I select an item in pre-requisite course drop down and click Save Changes button
            Then My selected item should be saved as pre-requisite course
            And My selected item should be selected after refreshing the page.'
        """
        course_number = self.unique_id
        CourseFixture(
            org='test_org',
            number=course_number,
            run='test_run',
            display_name='Test Course' + course_number
        ).install()

        pre_requisite_course_key = generate_course_key(
            org='test_org',
            number=course_number,
            run='test_run'
        )
        pre_requisite_course_id = unicode(pre_requisite_course_key)

        # Refresh the page to load the new course fixture and populate the prrequisite course dropdown
        # Then select the prerequisite course and save the changes
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        select_option_by_value(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        )
        self.settings_detail.save_changes()
        self.assertEqual(
            'Your changes have been saved.',
            self.settings_detail.alert_confirmation_title.text
        )

        log.debug('***********************************************************')
        log.debug(datetime.now().time())

        # Refresh the page again and confirm the prerequisite course selection is properly reflected
        self.settings_detail.refresh_page()

        #Preselected course id
        logging.debug("\n\n\nPre selected course id '{}'\n\n\n".format(
            pre_requisite_course_id
        ))

        #license div
        logging.debug("\n\n\nHTML of wrapper-license '{}'\n\n\n".format(
            self.settings_detail.q(css='.wrapper-license').html
        ))

        # Course org
        logging.debug("\n\n\nCourse org '{}'\n\n\n".format(
            self.settings_detail.q(css='#course-organization').attrs('value')[0]
        ))

        # Course DropDown logs
        logging.debug("\n\n\nHTML of dropdown '{}'\n\n\n".format(
            self.settings_detail.q(css='#pre-requisite-course').html
        ))
        logging.debug("\n\n\nOptions of dropdown '{}'\n\n\n".format(
            self.settings_detail.q(css='#pre-requisite-course option').html
        ))
        logging.debug("\n\n\noptions Selected of dropdown '{}'\n\n\n".format(
            self.settings_detail.q(css='#pre-requisite-course option').selected
        ))

        #single options logs
        logging.debug("\n\n\nValue of dropdown '{}'\n\n\n".format(
            self.settings_detail.q(css='#pre-requisite-course').attrs('val')
        ))
        logging.debug("\n\n\nselected of dropdown '{}'\n\n\n".format(
            self.settings_detail.q(css='#pre-requisite-course').attrs('selected')
        ))

        self.settings_detail.wait_for_prerequisite_course_options()
        self.assertTrue(is_option_value_selected(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        ))

        # Set the prerequisite course back to None and save the changes
        select_option_by_value(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=''
        )
        self.settings_detail.save_changes()
        self.assertEqual(
            'Your changes have been saved.',
            self.settings_detail.alert_confirmation_title.text
        )

        # Refresh the page again to confirm the None selection is properly reflected
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        self.assertTrue(is_option_value_selected(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=''
        ))

        # Re-pick the prerequisite course and confirm no errors are thrown (covers a discovered bug)
        select_option_by_value(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        )
        self.settings_detail.save_changes()
        self.assertEqual(
            'Your changes have been saved.',
            self.settings_detail.alert_confirmation_title.text
        )

        # Refresh the page again to confirm the prerequisite course selection is properly reflected
        self.settings_detail.refresh_page()
        self.settings_detail.wait_for_prerequisite_course_options()
        dropdown_status = is_option_value_selected(
            browser_query=self.settings_detail.pre_requisite_course_options,
            value=pre_requisite_course_id
        )
        self.assertTrue(dropdown_status)
