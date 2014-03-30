""" Tests for tab functions (just primitive). """

from contentstore.views import tabs
from django.test import TestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.courses import get_course_by_id


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
