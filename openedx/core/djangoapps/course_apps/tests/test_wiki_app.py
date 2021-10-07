"""
Tests for wiki course app.
"""

from common.djangoapps.student.tests.factories import AdminFactory, UserFactory
from lms.djangoapps.course_wiki.plugins.course_app import WikiCourseApp
from openedx.core.djangolib.testing.utils import skip_unless_cms
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@skip_unless_cms
class WikiCourseAppTestCase(ModuleStoreTestCase):
    """Test cases for Wiki CourseApp."""

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        self.instructor = AdminFactory.create()
        self.user = UserFactory()

    def get_wiki_tab(self, course_key):
        """
        Reload the course and fetch the wiki tab if present.
        """
        course = self.store.get_course(course_key)
        return next((tab for tab in course.tabs if tab.type == 'wiki'), None)

    def test_app_disabled_by_default(self):
        """
        Test that the wiki tab is disabled by default.
        """
        assert not WikiCourseApp.is_enabled(self.course.id)

    def test_app_enabling(self):
        """
        Test that enabling and disable the app enabled/disables the tab.
        """
        WikiCourseApp.set_enabled(self.course.id, True, self.instructor)
        wiki_tab = self.get_wiki_tab(self.course.id)
        assert not wiki_tab.is_hidden
        WikiCourseApp.set_enabled(self.course.id, False, self.instructor)
        wiki_tab = self.get_wiki_tab(self.course.id)
        assert wiki_tab.is_hidden

    def test_app_adds_wiki(self):
        """
        Test that enabling the app for a course that doesn't have the wiki tab
        adds the wiki tab.
        """
        self.course.tabs = [tab for tab in self.course.tabs if tab.type != 'wiki']
        self.store.update_item(self.course, self.instructor.id)
        assert self.get_wiki_tab(self.course.id) is None
        WikiCourseApp.set_enabled(self.course.id, True, self.instructor)
        assert self.get_wiki_tab(self.course.id) is not None
