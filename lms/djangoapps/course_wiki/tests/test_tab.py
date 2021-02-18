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
        super(WikiTabTestCase, self).setUp()  # lint-amnesty, pylint: disable=super-with-arguments
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
        assert self.get_wiki_tab(self.user, self.course) is not None

    def test_wiki_enabled_and_not_public(self):
        """
        Test wiki when it is enabled but not open to the public
        """
        settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = False
        assert self.get_wiki_tab(self.user, self.course) is None
        assert self.get_wiki_tab(self.instructor, self.course) is not None

    def test_wiki_enabled_false(self):
        """Test wiki tab when Enabled setting is False"""
        settings.WIKI_ENABLED = False
        assert self.get_wiki_tab(self.user, self.course) is None
        assert self.get_wiki_tab(self.instructor, self.course) is None

    def test_wiki_visibility(self):
        """Test toggling of visibility of wiki tab"""
        settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = True
        wiki_tab = self.get_wiki_tab(self.user, self.course)
        assert wiki_tab is not None
        assert wiki_tab.is_hideable
        wiki_tab.is_hidden = True
        assert wiki_tab['is_hidden']
        wiki_tab['is_hidden'] = False
        assert not wiki_tab.is_hidden
