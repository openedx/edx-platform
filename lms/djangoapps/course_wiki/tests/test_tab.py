"""
Tests for wiki views.
"""


from django.conf import settings
from django.test.client import RequestFactory

from lms.djangoapps.courseware.tabs import get_course_tab_list
from common.djangoapps.student.tests.factories import AdminFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class WikiTabTestCase(ModuleStoreTestCase):
    """Test cases for Wiki Tab."""

    def setUp(self):
        super(WikiTabTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.instructor = AdminFactory.create()
        self.user = UserFactory()

    def get_wiki_tab(self, user, course):
        """Returns true if the "Wiki" tab is shown."""
        request = RequestFactory().request()
        all_tabs = get_course_tab_list(user, course)
        wiki_tabs = [tab for tab in all_tabs if tab.name == 'Wiki']
        return wiki_tabs[0] if len(wiki_tabs) == 1 else None

    def test_wiki_enabled_and_public(self):
        """
        Test wiki tab when Enabled setting is True and the wiki is open to
        the public.
        """
        settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = True
        self.assertIsNotNone(self.get_wiki_tab(self.user, self.course))

    def test_wiki_enabled_and_not_public(self):
        """
        Test wiki when it is enabled but not open to the public
        """
        settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = False
        self.assertIsNone(self.get_wiki_tab(self.user, self.course))
        self.assertIsNotNone(self.get_wiki_tab(self.instructor, self.course))

    def test_wiki_enabled_false(self):
        """Test wiki tab when Enabled setting is False"""
        settings.WIKI_ENABLED = False
        self.assertIsNone(self.get_wiki_tab(self.user, self.course))
        self.assertIsNone(self.get_wiki_tab(self.instructor, self.course))

    def test_wiki_visibility(self):
        """Test toggling of visibility of wiki tab"""
        settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = True
        wiki_tab = self.get_wiki_tab(self.user, self.course)
        self.assertIsNotNone(wiki_tab)
        self.assertTrue(wiki_tab.is_hideable)
        wiki_tab.is_hidden = True
        self.assertTrue(wiki_tab['is_hidden'])
        wiki_tab['is_hidden'] = False
        self.assertFalse(wiki_tab.is_hidden)
