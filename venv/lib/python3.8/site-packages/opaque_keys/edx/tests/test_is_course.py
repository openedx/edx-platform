"""
Test that the .is_course helper property does what it's supposed to
"""

from unittest import TestCase

from opaque_keys.edx.locator import CourseLocator, LibraryLocator, LibraryLocatorV2


class IsCourseTests(TestCase):
    """
    Test the .is_course property.

    This is because for historical reasons, isinstance(key, CourseKey) will
    sometimes return a library key (modulestore split mongo content libraries).
    """
    def test_is_course(self):
        course_key = CourseLocator("SchoolX", "course1", "2020")
        self.assertEqual(course_key.is_course, True)
        lib_key = LibraryLocator("SchoolX", "lib1")
        self.assertEqual(lib_key.is_course, False)
        lib2_key = LibraryLocatorV2("SchoolX", "lib-slug")
        self.assertEqual(lib2_key.is_course, False)
