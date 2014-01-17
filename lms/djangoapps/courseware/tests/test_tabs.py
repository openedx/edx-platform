from django.test import TestCase
from mock import MagicMock, Mock, patch

from courseware import tabs
from courseware.courses import get_course_by_id

from django.test.utils import override_settings
from django.core.urlresolvers import reverse

from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.helpers import get_request_for_user
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE


FAKE_REQUEST = None


def tab_constructor(active_page, course, user, tab={'name': 'same'}, generator=tabs._progress):
    return generator(tab, user, course, active_page, FAKE_REQUEST)


class ProgressTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.anonymous_user = MagicMock()
        self.course = MagicMock()
        self.user.is_authenticated.return_value = True
        self.anonymous_user.is_authenticated.return_value = False
        self.course.id = 'edX/toy/2012_Fall'
        self.tab = {'name': 'same'}
        self.progress_page = 'progress'
        self.stagnation_page = 'stagnation'

    def test_progress(self):

        self.assertEqual(tab_constructor(self.stagnation_page, self.course, self.anonymous_user), [])

        self.assertEqual(tab_constructor(self.progress_page, self.course, self.user)[0].name, 'same')

        tab_list = tab_constructor(self.progress_page, self.course, self.user)
        expected_link = reverse('progress', args=[self.course.id])
        self.assertEqual(tab_list[0].link, expected_link)

        self.assertEqual(tab_constructor(self.stagnation_page, self.course, self.user)[0].is_active, False)

        self.assertEqual(tab_constructor(self.progress_page, self.course, self.user)[0].is_active, True)


class WikiTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.course = MagicMock()
        self.course.id = 'edX/toy/2012_Fall'
        self.tab = {'name': 'same'}
        self.wiki_page = 'wiki'
        self.miki_page = 'miki'

    @override_settings(WIKI_ENABLED=True)
    def test_wiki_enabled(self):

        tab_list = tab_constructor(self.wiki_page, self.course, self.user, generator=tabs._wiki)
        self.assertEqual(tab_list[0].name, 'same')

        tab_list = tab_constructor(self.wiki_page, self.course, self.user, generator=tabs._wiki)
        expected_link = reverse('course_wiki', args=[self.course.id])
        self.assertEqual(tab_list[0].link, expected_link)

        tab_list = tab_constructor(self.wiki_page, self.course, self.user, generator=tabs._wiki)
        self.assertEqual(tab_list[0].is_active, True)

        tab_list = tab_constructor(self.miki_page, self.course, self.user, generator=tabs._wiki)
        self.assertEqual(tab_list[0].is_active, False)

    @override_settings(WIKI_ENABLED=False)
    def test_wiki_enabled_false(self):

        tab_list = tab_constructor(self.wiki_page, self.course, self.user, generator=tabs._wiki)
        self.assertEqual(tab_list, [])


class ExternalLinkTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.course = MagicMock()
        self.tabby = {'name': 'same', 'link': 'blink'}
        self.no_page = None
        self.true = True

    def test_external_link(self):

        tab_list = tab_constructor(
            self.no_page, self.course, self.user, tab=self.tabby, generator=tabs._external_link
        )
        self.assertEqual(tab_list[0].name, 'same')

        tab_list = tab_constructor(
            self.no_page, self.course, self.user, tab=self.tabby, generator=tabs._external_link
        )
        self.assertEqual(tab_list[0].link, 'blink')

        tab_list = tab_constructor(
            self.no_page, self.course, self.user, tab=self.tabby, generator=tabs._external_link
        )
        self.assertEqual(tab_list[0].is_active, False)

        tab_list = tab_constructor(
            self.true, self.course, self.user, tab=self.tabby, generator=tabs._external_link
        )
        self.assertEqual(tab_list[0].is_active, False)


class StaticTabTestCase(ModuleStoreTestCase):

    def setUp(self):

        self.user = MagicMock()
        self.course = MagicMock()
        self.tabby = {'name': 'same', 'url_slug': 'schmug'}
        self.course.id = 'edX/toy/2012_Fall'
        self.schmug = 'static_tab_schmug'
        self.schlug = 'static_tab_schlug'

    def test_static_tab(self):

        tab_list = tab_constructor(
            self.schmug, self.course, self.user, tab=self.tabby, generator=tabs._static_tab
        )
        self.assertEqual(tab_list[0].name, 'same')

        tab_list = tab_constructor(
            self.schmug, self.course, self.user, tab=self.tabby, generator=tabs._static_tab
        )
        expected_link = reverse('static_tab', args=[self.course.id, self.tabby['url_slug']])
        self.assertEqual(tab_list[0].link, expected_link)

        tab_list = tab_constructor(
            self.schmug, self.course, self.user, tab=self.tabby, generator=tabs._static_tab
        )
        self.assertEqual(tab_list[0].is_active, True)

        tab_list = tab_constructor(
            self.schlug, self.course, self.user, tab=self.tabby, generator=tabs._static_tab
        )
        self.assertEqual(tab_list[0].is_active, False)

    @override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
    def test_get_static_tab_contents(self):
        course = get_course_by_id('edX/toy/2012_Fall')
        request = get_request_for_user(UserFactory.create())
        tab = tabs.get_static_tab_by_slug(course, 'resources')

        # Test render works okay
        tab_content = tabs.get_static_tab_contents(request, course, tab)
        self.assertIn('edX/toy/2012_Fall', tab_content)
        self.assertIn('static_tab', tab_content)

        # Test when render raises an exception
        with patch('courseware.tabs.get_module') as mock_module_render:
            mock_module_render.return_value = MagicMock(
                render=Mock(side_effect=Exception('Render failed!'))
            )
            course_info = tabs.get_static_tab_contents(request, course, tab)
            self.assertIsInstance(course_info, basestring)


class TextbooksTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.anonymous_user = MagicMock()
        self.course = MagicMock()
        self.tab = MagicMock()
        A = MagicMock()
        T = MagicMock()
        A.title = 'Algebra'
        T.title = 'Topology'
        self.course.textbooks = [A, T]
        self.user.is_authenticated.return_value = True
        self.anonymous_user.is_authenticated.return_value = False
        self.course.id = 'edX/toy/2012_Fall'
        self.textbook_0 = 'textbook/0'
        self.textbook_1 = 'textbook/1'
        self.prohibited_page = 'you_shouldnt_be_seein_this'

    @override_settings(FEATURES={'ENABLE_TEXTBOOK': True})
    def test_textbooks1(self):

        tab_list = tab_constructor(
            self.textbook_0, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list[0].name, 'Algebra')

        tab_list = tab_constructor(
            self.textbook_0, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        expected_link = reverse('book', args=[self.course.id, 0])
        self.assertEqual(tab_list[0].link, expected_link)

        tab_list = tab_constructor(
            self.textbook_0, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list[0].is_active, True)

        tab_list = tab_constructor(
            self.prohibited_page, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list[0].is_active, False)

        tab_list = tab_constructor(
            self.textbook_1, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list[1].name, 'Topology')

        tab_list = tab_constructor(
            self.textbook_1, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        expected_link = reverse('book', args=[self.course.id, 1])
        self.assertEqual(tab_list[1].link, expected_link)

        tab_list = tab_constructor(
            self.textbook_1, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list[1].is_active, True)

        tab_list = tab_constructor(
            self.prohibited_page, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list[1].is_active, False)

    @override_settings(FEATURES={'ENABLE_TEXTBOOK': False})
    def test_textbooks0(self):

        tab_list = tab_constructor(
            self.prohibited_page, self.course, self.user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list, [])

        tab_list = tab_constructor(
            self.prohibited_page, self.course, self.anonymous_user, tab=self.tab, generator=tabs._textbooks
        )
        self.assertEqual(tab_list, [])


class KeyCheckerTestCase(TestCase):

    def setUp(self):

        self.valid_keys = ['a', 'b']
        self.invalid_keys = ['a', 'v', 'g']
        self.dictio = {'a': 1, 'b': 2, 'c': 3}

    def test_key_checker(self):

        self.assertIsNone(tabs.key_checker(self.valid_keys)(self.dictio))
        self.assertRaises(tabs.InvalidTabsException,
                          tabs.key_checker(self.invalid_keys), self.dictio)


class NullValidatorTestCase(TestCase):

    def setUp(self):

        self.dummy = {}

        def test_null_validator(self):
            self.assertIsNone(tabs.null_validator(self.dummy))


class ValidateTabsTestCase(TestCase):

    def setUp(self):

        self.courses = [MagicMock() for i in range(0, 5)]

        self.courses[0].tabs = None

        self.courses[1].tabs = [{'type': 'courseware'}, {'type': 'fax'}]

        self.courses[2].tabs = [{'type': 'shadow'}, {'type': 'course_info'}]

        self.courses[3].tabs = [{'type': 'courseware'}, {'type': 'course_info', 'name': 'alice'},
                                {'type': 'wiki', 'name': 'alice'}, {'type': 'discussion', 'name': 'alice'},
                                {'type': 'external_link', 'name': 'alice', 'link': 'blink'},
                                {'type': 'textbooks'}, {'type': 'progress', 'name': 'alice'},
                                {'type': 'static_tab', 'name': 'alice', 'url_slug': 'schlug'},
                                {'type': 'staff_grading'}]

        self.courses[4].tabs = [{'type': 'courseware'}, {'type': 'course_info'}, {'type': 'flying'}]

    def test_validate_tabs(self):
        self.assertIsNone(tabs.validate_tabs(self.courses[0]))
        self.assertRaises(tabs.InvalidTabsException, tabs.validate_tabs, self.courses[1])
        self.assertRaises(tabs.InvalidTabsException, tabs.validate_tabs, self.courses[2])
        self.assertIsNone(tabs.validate_tabs(self.courses[3]))
        self.assertRaises(tabs.InvalidTabsException, tabs.validate_tabs, self.courses[4])


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class DiscussionLinkTestCase(ModuleStoreTestCase):

    def setUp(self):
        self.tabs_with_discussion = [
            {'type': 'courseware'},
            {'type': 'course_info'},
            {'type': 'discussion'},
            {'type': 'textbooks'},
        ]
        self.tabs_without_discussion = [
            {'type': 'courseware'},
            {'type': 'course_info'},
            {'type': 'textbooks'},
        ]

    @staticmethod
    def _patch_reverse(course):
        def patched_reverse(viewname, args):
            if viewname == "django_comment_client.forum.views.forum_form_discussion" and args == [course.id]:
                return "default_discussion_link"
            else:
                return None
        return patch("courseware.tabs.reverse", patched_reverse)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": False})
    def test_explicit_discussion_link(self):
        """Test that setting discussion_link overrides everything else"""
        course = CourseFactory.create(discussion_link="other_discussion_link", tabs=self.tabs_with_discussion)
        self.assertEqual(tabs.get_discussion_link(course), "other_discussion_link")

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": False})
    def test_discussions_disabled(self):
        """Test that other cases return None with discussions disabled"""
        for i, t in enumerate([None, self.tabs_with_discussion, self.tabs_without_discussion]):
            course = CourseFactory.create(tabs=t, number=str(i))
            self.assertEqual(tabs.get_discussion_link(course), None)

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_no_tabs(self):
        """Test a course without tabs configured"""
        course = CourseFactory.create(tabs=None)
        with self._patch_reverse(course):
            self.assertEqual(tabs.get_discussion_link(course), "default_discussion_link")

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_tabs_with_discussion(self):
        """Test a course with a discussion tab configured"""
        course = CourseFactory.create(tabs=self.tabs_with_discussion)
        with self._patch_reverse(course):
            self.assertEqual(tabs.get_discussion_link(course), "default_discussion_link")

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def test_tabs_without_discussion(self):
        """Test a course with tabs configured but without a discussion tab"""
        course = CourseFactory.create(tabs=self.tabs_without_discussion)
        self.assertEqual(tabs.get_discussion_link(course), None)
