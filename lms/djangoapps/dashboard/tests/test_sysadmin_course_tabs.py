"""Tests for the Edit Course Tabs Feature on the Sysadmin Page"""
import unittest
from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse

from dashboard.tests.test_sysadmin import SysadminBaseTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@unittest.skipUnless(
    settings.FEATURES.get('ENABLE_SYSADMIN_DASHBOARD'),
    'ENABLE_SYSADMIN_DASHBOARD not set',
)
class TestSysadminCourseTabs(SysadminBaseTestCase):
    """Tests all code paths in sysadmin_course_tabs"""

    def setUp(self):
        super(TestSysadminCourseTabs, self).setUp()
        self.course = CourseFactory.create()
        self._setstaff_login()

    def test_get_course_tabs_valid_course_id(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'get_current_tabs',
            'course_id': unicode(self.course.id),
        })
        self.assertIn('number, type, name', response.content.decode('utf-8'))

    def test_get_course_tabs_invalid_course_id(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'get_current_tabs',
            'course_id': u'InvalidCourseID',
        })
        self.assertIn('Error - Invalid Course ID', response.content.decode('utf-8'))

    def test_delete_tab_valid_course_id(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'delete_tab',
            'course_id': unicode(self.course.id),
            'tab_delete': u'3',
        })
        self.assertIn("Tab 3 for course {course_key} successfully deleted".format(
            course_key=unicode(self.course.id),
        ), response.content.decode('utf-8'))

    def test_delete_tab_invalid_course_id(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'delete_tab',
            'course_id': u'InvalidCourseID',
            'tab_delete': u'3',
        })
        self.assertIn('Error - Invalid Course ID', response.content.decode('utf-8'))

    def test_delete_tab_invalid_args(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'delete_tab',
            'course_id': unicode(self.course.id),
            'tab_delete': u'',
        })
        self.assertIn('Error - Invalid arguments. Expecting one argument [tab-number]', response.content.decode('utf-8'))

    def test_delete_tab_throws_exception(self):
        with patch('dashboard.sysadmin_extensions.sysadmin_course_tabs.primitive_delete') as mock_primitive_delete:
            mock_primitive_delete.side_effect = ValueError()
            response = self.client.post(reverse('sysadmin_courses'), {
                'action': 'delete_tab',
                'course_id': unicode(self.course.id),
                'tab_delete': u'3',
            })
        self.assertIn("Command Failed - ", response.content.decode('utf-8'))

    def test_insert_tab_valid_course_id(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'insert_tab',
            'course_id': unicode(self.course.id),
            'tab_insert': u'3, progress, Course Progress',
        })
        self.assertIn("Tab 3, progress, Course Progress for course {course_key} successfully created".format(
            course_key=unicode(self.course.id),
        ), response.content.decode('utf-8'))

    def test_insert_tab_invalid_course_id(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'insert_tab',
            'course_id': u'InvalidCourseID',
            'tab_insert': u'3, progress, Course Progress',
        })
        self.assertIn("Error - Invalid Course ID", response.content.decode('utf-8'))

    def test_insert_tab_invalid_number_args(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'insert_tab',
            'course_id': unicode(self.course.id),
            'tab_insert': u'3, progress, Course Progress, extra arg',
        })
        self.assertIn("Error - Invalid number of arguments. Expecting [tab-number], [tab-type], [tab-name]".format(
            course_key=unicode(self.course.id),
        ), response.content.decode('utf-8'))

    def test_insert_tab_invalid_args(self):
        response = self.client.post(reverse('sysadmin_courses'), {
            'action': 'insert_tab',
            'course_id': unicode(self.course.id),
            'tab_insert': u'three, progress, Course Progress',
        })
        self.assertIn("Error - Invalid arguments. Expecting [tab-number], [tab-type], [tab-name]".format(
            course_key=unicode(self.course.id),
        ), response.content.decode('utf-8'))

    def test_insert_tab_throws_exception(self):
        with patch('dashboard.sysadmin_extensions.sysadmin_course_tabs.primitive_insert') as mock_primitive_insert:
            mock_primitive_insert.side_effect = ValueError()
            response = self.client.post(reverse('sysadmin_courses'), {
                'action': 'insert_tab',
                'course_id': unicode(self.course.id),
                'tab_insert': u'3, progress, Course Progress',
            })
        self.assertIn('Command Failed - ', response.content.decode('utf-8'))
