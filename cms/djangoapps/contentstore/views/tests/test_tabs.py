""" Tests for tab functions (just primitive). """

import json
from contentstore.views import tabs
from contentstore.tests.utils import CourseTestCase
from django.test import TestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.courses import get_course_by_id
from xmodule.tabs import CourseTabList, WikiTab

class TabsPageTests(CourseTestCase):
    """Test cases for Tabs (a.k.a Pages) page"""

    def setUp(self):
        "Set the URL for tests"
        super(TabsPageTests, self).setUp()
        self.url = self.course_locator.url_reverse('tabs')

    def test_get_JSON_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            self.client.get(self.url)

    def test_view_index(self):
        "Basic check that the Pages page responds correctly"
        resp = self.client.get(
            self.url,
            HTTP_ACCEPT="text/html",
        )
        self.assertEqual(resp.status_code, 200)
        # NAATODO
        # How to verify contents?

    def test_reorder_tabs(self):
        orig_tab_ids = [tab.tab_id for tab in self.course.tabs]
        tab_ids = list(orig_tab_ids)

        # reorder the last two tabs
        last_tab_index = len(orig_tab_ids) - 1
        tab_ids[last_tab_index], tab_ids[last_tab_index-1] = tab_ids[last_tab_index-1], tab_ids[last_tab_index]

        resp = self.client.post(
            self.url,
            data=json.dumps({'tab_ids': tab_ids}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 204)

        self.reloadCourse()
        new_tab_ids = [tab.tab_id for tab in self.course.tabs]
        self.assertEqual(new_tab_ids, tab_ids)
        self.assertNotEqual(new_tab_ids, orig_tab_ids)

    def check_toggle_tab_visiblity(self, tab_type, new_is_hidden_setting):
        # find the tab
        old_tab = CourseTabList.get_tab_by_type(self.course.tabs, tab_type)

        # visibility should be different from new setting
        self.assertNotEqual(old_tab.is_hidden, new_is_hidden_setting)

        resp = self.client.post(
            self.url,
            data=json.dumps({'tab_id': old_tab.tab_id, 'is_hidden': new_is_hidden_setting}),
            content_type="application/json",
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(resp.status_code, 204)

        self.reloadCourse()
        new_tab = CourseTabList.get_tab_by_type(self.course.tabs, tab_type)

        # visibility should be toggled
        self.assertEqual(new_tab.is_hidden, new_is_hidden_setting)

    def test_toggle_tab_visibility(self):
        self.check_toggle_tab_visiblity(WikiTab.type, True)
        self.check_toggle_tab_visiblity(WikiTab.type, False)


class PrimitiveTabEdit(TestCase):
    """Tests for the primitive tab edit data manipulations"""

    def test_delete(self):
        """Test primitive tab deletion."""
        course = CourseFactory.create(org='edX', course='999')
        with self.assertRaises(ValueError):
            tabs.primitive_delete(course, 0)
        with self.assertRaises(ValueError):
            tabs.primitive_delete(course, 1)
        with self.assertRaises(IndexError):
            tabs.primitive_delete(course, 6)
        tabs.primitive_delete(course, 2)
        self.assertFalse({u'type': u'textbooks'} in course.tabs)
        # Check that discussion has shifted up
        self.assertEquals(course.tabs[2], {'type': 'discussion', 'name': 'Discussion'})

    def test_insert(self):
        """Test primitive tab insertion."""
        course = CourseFactory.create(org='edX', course='999')
        tabs.primitive_insert(course, 2, 'notes', 'aname')
        self.assertEquals(course.tabs[2], {'type': 'notes', 'name': 'aname'})
        with self.assertRaises(ValueError):
            tabs.primitive_insert(course, 0, 'notes', 'aname')
        with self.assertRaises(ValueError):
            tabs.primitive_insert(course, 3, 'static_tab', 'aname')

    def test_save(self):
        """Test course saving."""
        course = CourseFactory.create(org='edX', course='999')
        tabs.primitive_insert(course, 3, 'notes', 'aname')
        course2 = get_course_by_id(course.id)
        self.assertEquals(course2.tabs[3], {'type': 'notes', 'name': 'aname'})
