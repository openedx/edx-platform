"""Tests for Tab classes"""
from mock import MagicMock
import xmodule.tabs as tabs
import unittest
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class TabTestCase(unittest.TestCase):
    """Base class for Tab-related test cases."""
    def setUp(self):

        self.course = MagicMock()
        self.course.id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.fake_dict_tab = {'fake_key': 'fake_value'}
        self.settings = MagicMock()
        self.settings.FEATURES = {}
        self.reverse = lambda name, args: "name/{0}/args/{1}".format(name, ",".join(str(a) for a in args))
        self.books = None

    def set_up_books(self, num_books):
        """Initializes the textbooks in the course and adds the given number of books to each textbook"""
        self.books = [MagicMock() for _ in range(num_books)]
        for book_index, book in enumerate(self.books):
            book.title = 'Book{0}'.format(book_index)
        self.course.textbooks = self.books
        self.course.pdf_textbooks = self.books
        self.course.html_textbooks = self.books

    def check_tab(
            self,
            tab_class,
            dict_tab,
            expected_link,
            expected_tab_id,
            expected_name='same',
            invalid_dict_tab=None,
    ):
        """
        Helper method to verify a tab class.

        'tab_class' is the class of the tab that is being tested
        'dict_tab' is the raw dictionary value of the tab
        'expected_link' is the expected value for the hyperlink of the tab
        'expected_tab_id' is the expected value for the unique id of the tab
        'expected_name' is the expected value for the name of the tab
        'invalid_dict_tab' is an invalid dictionary value for the tab.
            Can be 'None' if the given tab class does not have any keys to validate.
        """
        # create tab
        tab = tab_class(dict_tab)

        # name is as expected
        self.assertEqual(tab.name, expected_name)

        # link is as expected
        self.assertEqual(tab.link_func(self.course, self.reverse), expected_link)

        # verify active page name
        self.assertEqual(tab.tab_id, expected_tab_id)

        # validate tab
        self.assertTrue(tab.validate(dict_tab))
        if invalid_dict_tab:
            with self.assertRaises(tabs.InvalidTabsException):
                tab.validate(invalid_dict_tab)

        # check get and set methods
        self.check_get_and_set_methods(tab)

        # check to_json and from_json methods
        self.check_tab_json_methods(tab)

        # check equality methods
        self.check_tab_equality(tab, dict_tab)

        # return tab for any additional tests
        return tab

    def check_tab_equality(self, tab, dict_tab):
        """Tests the equality methods on the given tab"""
        self.assertEquals(tab, dict_tab)  # test __eq__
        ne_dict_tab = dict_tab
        ne_dict_tab['type'] = 'fake_type'
        self.assertNotEquals(tab, ne_dict_tab)  # test __ne__: incorrect type
        self.assertNotEquals(tab, {'fake_key': 'fake_value'})  # test __ne__: missing type

    def check_tab_json_methods(self, tab):
        """Tests the json from and to methods on the given tab"""
        serialized_tab = tab.to_json()
        deserialized_tab = tab.from_json(serialized_tab)
        self.assertEquals(serialized_tab, deserialized_tab)

    def check_can_display_results(
        self,
        tab,
        expected_value=True,
        for_authenticated_users_only=False,
        for_staff_only=False,
        for_enrolled_users_only=False
    ):
        """Checks can display results for various users"""
        if for_staff_only:
            self.assertEquals(
                expected_value,
                tab.can_display(
                    self.course, self.settings, is_user_authenticated=True, is_user_staff=True, is_user_enrolled=True
                )
            )
        if for_authenticated_users_only:
            self.assertEquals(
                expected_value,
                tab.can_display(
                    self.course, self.settings, is_user_authenticated=True, is_user_staff=False, is_user_enrolled=False
                )
            )
        if not for_staff_only and not for_authenticated_users_only and not for_enrolled_users_only:
            self.assertEquals(
                expected_value,
                tab.can_display(
                    self.course, self.settings, is_user_authenticated=False, is_user_staff=False, is_user_enrolled=False
                )
            )
        if for_enrolled_users_only:
            self.assertEquals(
                expected_value,
                tab.can_display(
                    self.course, self.settings, is_user_authenticated=True, is_user_staff=False, is_user_enrolled=True
                )
            )

    def check_get_and_set_methods(self, tab):
        """Test __getitem__ and __setitem__ calls"""
        self.assertEquals(tab['type'], tab.type)
        self.assertEquals(tab['tab_id'], tab.tab_id)
        with self.assertRaises(KeyError):
            _ = tab['invalid_key']

        self.check_get_and_set_method_for_key(tab, 'name')
        self.check_get_and_set_method_for_key(tab, 'tab_id')
        with self.assertRaises(KeyError):
            tab['invalid_key'] = 'New Value'

    def check_get_and_set_method_for_key(self, tab, key):
        """Test __getitem__ and __setitem__ for the given key"""
        old_value = tab[key]
        new_value = 'New Value'
        tab[key] = new_value
        self.assertEquals(tab[key], new_value)
        tab[key] = old_value
        self.assertEquals(tab[key], old_value)


class ProgressTestCase(TabTestCase):
    """Test cases for Progress Tab."""

    def check_progress_tab(self):
        """Helper function for verifying the progress tab."""
        return self.check_tab(
            tab_class=tabs.ProgressTab,
            dict_tab={'type': tabs.ProgressTab.type, 'name': 'same'},
            expected_link=self.reverse('progress', args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=tabs.ProgressTab.type,
            invalid_dict_tab=None,
        )

    def test_progress(self):

        self.course.hide_progress_tab = False
        tab = self.check_progress_tab()
        self.check_can_display_results(
            tab, for_staff_only=True, for_enrolled_users_only=True
        )

        self.course.hide_progress_tab = True
        self.check_progress_tab()
        self.check_can_display_results(
            tab, for_staff_only=True, for_enrolled_users_only=True, expected_value=False
        )


class WikiTestCase(TabTestCase):
    """Test cases for Wiki Tab."""

    def check_wiki_tab(self):
        """Helper function for verifying the wiki tab."""
        return self.check_tab(
            tab_class=tabs.WikiTab,
            dict_tab={'type': tabs.WikiTab.type, 'name': 'same'},
            expected_link=self.reverse('course_wiki', args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=tabs.WikiTab.type,
            invalid_dict_tab=self.fake_dict_tab,
        )

    def test_wiki_enabled_and_public(self):
        """
        Test wiki tab when Enabled setting is True and the wiki is open to
        the public.
        """
        self.settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = True
        tab = self.check_wiki_tab()
        self.check_can_display_results(tab)

    def test_wiki_enabled_and_not_public(self):
        """
        Test wiki when it is enabled but not open to the public
        """
        self.settings.WIKI_ENABLED = True
        self.course.allow_public_wiki_access = False
        tab = self.check_wiki_tab()
        self.check_can_display_results(tab, for_enrolled_users_only=True, for_staff_only=True)

    def test_wiki_enabled_false(self):
        """Test wiki tab when Enabled setting is False"""

        self.settings.WIKI_ENABLED = False
        tab = self.check_wiki_tab()
        self.check_can_display_results(tab, expected_value=False)

    def test_wiki_visibility(self):
        """Test toggling of visibility of wiki tab"""

        wiki_tab = tabs.WikiTab()
        self.assertTrue(wiki_tab.is_hideable)
        wiki_tab.is_hidden = True
        self.assertTrue(wiki_tab['is_hidden'])
        self.check_tab_json_methods(wiki_tab)
        self.check_tab_equality(wiki_tab, wiki_tab.to_json())
        wiki_tab['is_hidden'] = False
        self.assertFalse(wiki_tab.is_hidden)


class ExternalLinkTestCase(TabTestCase):
    """Test cases for External Link Tab."""

    def test_external_link(self):

        link_value = 'link_value'
        tab = self.check_tab(
            tab_class=tabs.ExternalLinkTab,
            dict_tab={'type': tabs.ExternalLinkTab.type, 'name': 'same', 'link': link_value},
            expected_link=link_value,
            expected_tab_id=None,
            invalid_dict_tab=self.fake_dict_tab,
        )
        self.check_can_display_results(tab)
        self.check_get_and_set_method_for_key(tab, 'link')


class StaticTabTestCase(TabTestCase):
    """Test cases for Static Tab."""

    def test_static_tab(self):

        url_slug = 'schmug'

        tab = self.check_tab(
            tab_class=tabs.StaticTab,
            dict_tab={'type': tabs.StaticTab.type, 'name': 'same', 'url_slug': url_slug},
            expected_link=self.reverse('static_tab', args=[self.course.id.to_deprecated_string(), url_slug]),
            expected_tab_id='static_tab_schmug',
            invalid_dict_tab=self.fake_dict_tab,
        )
        self.check_can_display_results(tab)
        self.check_get_and_set_method_for_key(tab, 'url_slug')


class TextbooksTestCase(TabTestCase):
    """Test cases for Textbook Tab."""

    def setUp(self):
        super(TextbooksTestCase, self).setUp()

        self.set_up_books(2)

        self.dict_tab = MagicMock()
        self.course.tabs = [
            tabs.CoursewareTab(),
            tabs.CourseInfoTab(),
            tabs.TextbookTabs(),
            tabs.PDFTextbookTabs(),
            tabs.HtmlTextbookTabs(),
        ]
        self.num_textbook_tabs = sum(1 for tab in self.course.tabs if isinstance(tab, tabs.TextbookTabsBase))
        self.num_textbooks = self.num_textbook_tabs * len(self.books)

    def test_textbooks_enabled(self):

        type_to_reverse_name = {'textbook': 'book', 'pdftextbook': 'pdf_book', 'htmltextbook': 'html_book'}

        self.settings.FEATURES['ENABLE_TEXTBOOK'] = True
        num_textbooks_found = 0
        for tab in tabs.CourseTabList.iterate_displayable(self.course, self.settings):
            # verify all textbook type tabs
            if isinstance(tab, tabs.SingleTextbookTab):
                book_type, book_index = tab.tab_id.split("/", 1)
                expected_link = self.reverse(
                    type_to_reverse_name[book_type],
                    args=[self.course.id.to_deprecated_string(), book_index]
                )
                self.assertEqual(tab.link_func(self.course, self.reverse), expected_link)
                self.assertTrue(tab.name.startswith('Book{0}'.format(book_index)))
                num_textbooks_found = num_textbooks_found + 1
        self.assertEquals(num_textbooks_found, self.num_textbooks)

    def test_textbooks_disabled(self):

        self.settings.FEATURES['ENABLE_TEXTBOOK'] = False
        tab = tabs.TextbookTabs(self.dict_tab)
        self.check_can_display_results(tab, for_authenticated_users_only=True, expected_value=False)


class GradingTestCase(TabTestCase):
    """Test cases for Grading related Tabs."""

    def check_grading_tab(self, tab_class, name, link_value):
        """Helper function for verifying the grading tab."""
        return self.check_tab(
            tab_class=tab_class,
            dict_tab={'type': tab_class.type, 'name': name},
            expected_name=name,
            expected_link=self.reverse(link_value, args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=tab_class.type,
            invalid_dict_tab=None,
        )

    def test_grading_tabs(self):

        peer_grading_tab = self.check_grading_tab(
            tabs.PeerGradingTab,
            'Peer grading',
            'peer_grading'
        )
        self.check_can_display_results(peer_grading_tab, for_authenticated_users_only=True)
        open_ended_grading_tab = self.check_grading_tab(
            tabs.OpenEndedGradingTab,
            'Open Ended Panel',
            'open_ended_notifications'
        )
        self.check_can_display_results(open_ended_grading_tab, for_authenticated_users_only=True)
        staff_grading_tab = self.check_grading_tab(
            tabs.StaffGradingTab,
            'Staff grading',
            'staff_grading'
        )
        self.check_can_display_results(staff_grading_tab, for_staff_only=True)


class NotesTestCase(TabTestCase):
    """Test cases for Notes Tab."""

    def check_notes_tab(self):
        """Helper function for verifying the notes tab."""
        return self.check_tab(
            tab_class=tabs.NotesTab,
            dict_tab={'type': tabs.NotesTab.type, 'name': 'same'},
            expected_link=self.reverse('notes', args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=tabs.NotesTab.type,
            invalid_dict_tab=self.fake_dict_tab,
        )

    def test_notes_tabs_enabled(self):
        self.settings.FEATURES['ENABLE_STUDENT_NOTES'] = True
        tab = self.check_notes_tab()
        self.check_can_display_results(tab, for_authenticated_users_only=True)

    def test_notes_tabs_disabled(self):
        self.settings.FEATURES['ENABLE_STUDENT_NOTES'] = False
        tab = self.check_notes_tab()
        self.check_can_display_results(tab, expected_value=False)


class SyllabusTestCase(TabTestCase):
    """Test cases for Syllabus Tab."""

    def check_syllabus_tab(self, expected_can_display_value):
        """Helper function for verifying the syllabus tab."""

        name = 'Syllabus'
        tab = self.check_tab(
            tab_class=tabs.SyllabusTab,
            dict_tab={'type': tabs.SyllabusTab.type, 'name': name},
            expected_name=name,
            expected_link=self.reverse('syllabus', args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=tabs.SyllabusTab.type,
            invalid_dict_tab=None,
        )
        self.check_can_display_results(tab, expected_value=expected_can_display_value)

    def test_syllabus_tab_enabled(self):
        self.course.syllabus_present = True
        self.check_syllabus_tab(True)

    def test_syllabus_tab_disabled(self):
        self.course.syllabus_present = False
        self.check_syllabus_tab(False)


class InstructorTestCase(TabTestCase):
    """Test cases for Instructor Tab."""

    def test_instructor_tab(self):
        name = 'Instructor'
        tab = self.check_tab(
            tab_class=tabs.InstructorTab,
            dict_tab={'type': tabs.InstructorTab.type, 'name': name},
            expected_name=name,
            expected_link=self.reverse('instructor_dashboard', args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=tabs.InstructorTab.type,
            invalid_dict_tab=None,
        )
        self.check_can_display_results(tab, for_staff_only=True)


class KeyCheckerTestCase(unittest.TestCase):
    """Test cases for KeyChecker class"""

    def setUp(self):

        self.valid_keys = ['a', 'b']
        self.invalid_keys = ['a', 'v', 'g']
        self.dict_value = {'a': 1, 'b': 2, 'c': 3}

    def test_key_checker(self):

        self.assertTrue(tabs.key_checker(self.valid_keys)(self.dict_value, raise_error=False))
        self.assertFalse(tabs.key_checker(self.invalid_keys)(self.dict_value, raise_error=False))
        with self.assertRaises(tabs.InvalidTabsException):
            tabs.key_checker(self.invalid_keys)(self.dict_value)


class NeedNameTestCase(unittest.TestCase):
    """Test cases for NeedName validator"""

    def setUp(self):

        self.valid_dict1 = {'a': 1, 'name': 2}
        self.valid_dict2 = {'name': 1}
        self.valid_dict3 = {'a': 1, 'name': 2, 'b': 3}
        self.invalid_dict = {'a': 1, 'b': 2}

    def test_need_name(self):
        self.assertTrue(tabs.need_name(self.valid_dict1))
        self.assertTrue(tabs.need_name(self.valid_dict2))
        self.assertTrue(tabs.need_name(self.valid_dict3))
        with self.assertRaises(tabs.InvalidTabsException):
            tabs.need_name(self.invalid_dict)


class TabListTestCase(TabTestCase):
    """Base class for Test cases involving tab lists."""

    def setUp(self):
        super(TabListTestCase, self).setUp()

        # invalid tabs
        self.invalid_tabs = [
            # less than 2 tabs
            [{'type': tabs.CoursewareTab.type}],
            # missing course_info
            [{'type': tabs.CoursewareTab.type}, {'type': tabs.DiscussionTab.type, 'name': 'fake_name'}],
            # incorrect order
            [{'type': tabs.CourseInfoTab.type, 'name': 'fake_name'}, {'type': tabs.CoursewareTab.type}],
            # invalid type
            [{'type': tabs.CoursewareTab.type}, {'type': tabs.CourseInfoTab.type, 'name': 'fake_name'}, {'type': 'fake_type'}],
        ]

        # tab types that should appear only once
        unique_tab_types = [
            tabs.CourseInfoTab.type,
            tabs.CoursewareTab.type,
            tabs.NotesTab.type,
            tabs.TextbookTabs.type,
            tabs.PDFTextbookTabs.type,
            tabs.HtmlTextbookTabs.type,
        ]

        for unique_tab_type in unique_tab_types:
            self.invalid_tabs.append([
                {'type': tabs.CoursewareTab.type},
                {'type': tabs.CourseInfoTab.type, 'name': 'fake_name'},
                # add the unique tab multiple times
                {'type': unique_tab_type},
                {'type': unique_tab_type},
            ])

        # valid tabs
        self.valid_tabs = [
            # empty list
            [],
            # all valid tabs
            [
                {'type': tabs.CoursewareTab.type},
                {'type': tabs.CourseInfoTab.type, 'name': 'fake_name'},
                {'type': tabs.WikiTab.type, 'name': 'fake_name'},
                {'type': tabs.DiscussionTab.type, 'name': 'fake_name'},
                {'type': tabs.ExternalLinkTab.type, 'name': 'fake_name', 'link': 'fake_link'},
                {'type': tabs.TextbookTabs.type},
                {'type': tabs.PDFTextbookTabs.type},
                {'type': tabs.HtmlTextbookTabs.type},
                {'type': tabs.ProgressTab.type, 'name': 'fake_name'},
                {'type': tabs.StaticTab.type, 'name': 'fake_name', 'url_slug': 'schlug'},
                {'type': tabs.PeerGradingTab.type},
                {'type': tabs.StaffGradingTab.type},
                {'type': tabs.OpenEndedGradingTab.type},
                {'type': tabs.NotesTab.type, 'name': 'fake_name'},
                {'type': tabs.SyllabusTab.type},
            ],
            # with external discussion
            [
                {'type': tabs.CoursewareTab.type},
                {'type': tabs.CourseInfoTab.type, 'name': 'fake_name'},
                {'type': tabs.ExternalDiscussionTab.type, 'name': 'fake_name', 'link': 'fake_link'}
            ],
        ]

        self.all_valid_tab_list = tabs.CourseTabList().from_json(self.valid_tabs[1])


class ValidateTabsTestCase(TabListTestCase):
    """Test cases for validating tabs."""

    def test_validate_tabs(self):
        tab_list = tabs.CourseTabList()
        for invalid_tab_list in self.invalid_tabs:
            with self.assertRaises(tabs.InvalidTabsException):
                tab_list.from_json(invalid_tab_list)

        for valid_tab_list in self.valid_tabs:
            from_json_result = tab_list.from_json(valid_tab_list)
            self.assertEquals(len(from_json_result), len(valid_tab_list))


class CourseTabListTestCase(TabListTestCase):
    """Testing the generator method for iterating through displayable tabs"""

    def test_initialize_default_without_syllabus(self):
        self.course.tabs = []
        self.course.syllabus_present = False
        tabs.CourseTabList.initialize_default(self.course)
        self.assertTrue(tabs.SyllabusTab() not in self.course.tabs)

    def test_initialize_default_with_syllabus(self):
        self.course.tabs = []
        self.course.syllabus_present = True
        tabs.CourseTabList.initialize_default(self.course)
        self.assertTrue(tabs.SyllabusTab() in self.course.tabs)

    def test_initialize_default_with_external_link(self):
        self.course.tabs = []
        self.course.discussion_link = "other_discussion_link"
        tabs.CourseTabList.initialize_default(self.course)
        self.assertTrue(tabs.ExternalDiscussionTab(link_value="other_discussion_link") in self.course.tabs)
        self.assertTrue(tabs.DiscussionTab() not in self.course.tabs)

    def test_initialize_default_without_external_link(self):
        self.course.tabs = []
        self.course.discussion_link = ""
        tabs.CourseTabList.initialize_default(self.course)
        self.assertTrue(tabs.ExternalDiscussionTab() not in self.course.tabs)
        self.assertTrue(tabs.DiscussionTab() in self.course.tabs)

    def test_iterate_displayable(self):
        # enable all tab types
        self.settings.FEATURES['ENABLE_TEXTBOOK'] = True
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = True
        self.settings.FEATURES['ENABLE_STUDENT_NOTES'] = True
        self.course.hide_progress_tab = False

        # create 1 book per textbook type
        self.set_up_books(1)

        # initialize the course tabs to a list of all valid tabs
        self.course.tabs = self.all_valid_tab_list

        # enumerate the tabs using the CMS call
        for i, tab in enumerate(tabs.CourseTabList.iterate_displayable_cms(
            self.course,
            self.settings,
        )):
            self.assertEquals(tab.type, self.course.tabs[i].type)

       # enumerate the tabs and verify textbooks and the instructor tab
        for i, tab in enumerate(tabs.CourseTabList.iterate_displayable(
            self.course,
            self.settings,
        )):
            if getattr(tab, 'is_collection_item', False):
                # a collection item was found as a result of a collection tab
                self.assertTrue(getattr(self.course.tabs[i], 'is_collection', False))
            elif i == len(self.course.tabs):
                # the last tab must be the Instructor tab
                self.assertEquals(tab.type, tabs.InstructorTab.type)
            else:
                # all other tabs must match the expected type
                self.assertEquals(tab.type, self.course.tabs[i].type)

        # test including non-empty collections
        self.assertIn(
            tabs.HtmlTextbookTabs(),
            list(tabs.CourseTabList.iterate_displayable_cms(self.course, self.settings)),
        )

        # test not including empty collections
        self.course.html_textbooks = []
        self.assertNotIn(
            tabs.HtmlTextbookTabs(),
            list(tabs.CourseTabList.iterate_displayable_cms(self.course, self.settings)),
        )

    def test_get_tab_by_methods(self):
        """Tests the get_tab methods in CourseTabList"""
        self.course.tabs = self.all_valid_tab_list
        for tab in self.course.tabs:

            # get tab by type
            self.assertEquals(tabs.CourseTabList.get_tab_by_type(self.course.tabs, tab.type), tab)

            # get tab by id
            self.assertEquals(tabs.CourseTabList.get_tab_by_id(self.course.tabs, tab.tab_id), tab)


class DiscussionLinkTestCase(TabTestCase):
    """Test cases for discussion link tab."""

    def setUp(self):
        super(DiscussionLinkTestCase, self).setUp()

        self.tabs_with_discussion = [
            tabs.CoursewareTab(),
            tabs.CourseInfoTab(),
            tabs.DiscussionTab(),
            tabs.TextbookTabs(),
        ]
        self.tabs_without_discussion = [
            tabs.CoursewareTab(),
            tabs.CourseInfoTab(),
            tabs.TextbookTabs(),
        ]

    @staticmethod
    def _reverse(course):
        """Custom reverse function"""
        def reverse_discussion_link(viewname, args):
            """reverse lookup for discussion link"""
            if viewname == "django_comment_client.forum.views.forum_form_discussion" and args == [course.id.to_deprecated_string()]:
                return "default_discussion_link"
        return reverse_discussion_link

    def check_discussion(
        self, tab_list,
        expected_discussion_link,
        expected_can_display_value,
        discussion_link_in_course="",
        is_staff=True,
        is_enrolled=True,
    ):
        """Helper function to verify whether the discussion tab exists and can be displayed"""
        self.course.tabs = tab_list
        self.course.discussion_link = discussion_link_in_course
        discussion = tabs.CourseTabList.get_discussion(self.course)
        self.assertEquals(
            (
                discussion is not None and
                discussion.can_display(self.course, self.settings, True, is_staff, is_enrolled) and
                (discussion.link_func(self.course, self._reverse(self.course)) == expected_discussion_link)
            ),
            expected_can_display_value
        )

    def test_explicit_discussion_link(self):
        """Test that setting discussion_link overrides everything else"""
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = False
        self.check_discussion(
            tab_list=self.tabs_with_discussion,
            discussion_link_in_course="other_discussion_link",
            expected_discussion_link="other_discussion_link",
            expected_can_display_value=True,
        )

    def test_discussions_disabled(self):
        """Test that other cases return None with discussions disabled"""
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = False
        for tab_list in [[], self.tabs_with_discussion, self.tabs_without_discussion]:
            self.check_discussion(
                tab_list=tab_list,
                expected_discussion_link=not None,
                expected_can_display_value=False,
            )

    def test_tabs_with_discussion(self):
        """Test a course with a discussion tab configured"""
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = True
        self.check_discussion(
            tab_list=self.tabs_with_discussion,
            expected_discussion_link="default_discussion_link",
            expected_can_display_value=True,
        )

    def test_tabs_without_discussion(self):
        """Test a course with tabs configured but without a discussion tab"""
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = True
        self.check_discussion(
            tab_list=self.tabs_without_discussion,
            expected_discussion_link=not None,
            expected_can_display_value=False,
        )

    def test_tabs_enrolled_or_staff(self):
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = True
        for is_enrolled, is_staff in [(True, False), (False, True)]:
            self.check_discussion(
                tab_list=self.tabs_with_discussion,
                expected_discussion_link="default_discussion_link",
                expected_can_display_value=True,
                is_enrolled=is_enrolled,
                is_staff=is_staff
            )

    def test_tabs_not_enrolled_or_staff(self):
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = True
        is_enrolled = is_staff = False
        self.check_discussion(
            tab_list=self.tabs_with_discussion,
            expected_discussion_link="default_discussion_link",
            expected_can_display_value=False,
            is_enrolled=is_enrolled,
            is_staff=is_staff
        )
