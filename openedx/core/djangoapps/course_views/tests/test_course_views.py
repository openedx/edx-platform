""" Tests of specific tabs. """

from mock import MagicMock, patch
import unittest

from courseware.tabs import (
    CoursewareViewType, CourseInfoViewType, ProgressCourseViewType,
    StaticCourseViewType, ExternalDiscussionCourseViewType, ExternalLinkCourseViewType
)
import xmodule.tabs as xmodule_tabs
import openedx.core.djangoapps.course_views.course_views as tabs
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TabTestCase(ModuleStoreTestCase):
    """Base class for Tab-related test cases."""
    def setUp(self):
        super(TabTestCase, self).setUp()

        self.course = CourseFactory.create(org='edX', course='toy', run='2012_Fall')
        self.fake_dict_tab = {'fake_key': 'fake_value'}
        self.settings = MagicMock()
        self.settings.FEATURES = {}
        self.reverse = lambda name, args: "name/{0}/args/{1}".format(name, ",".join(str(a) for a in args))
        self.books = None

    def create_mock_user(self, is_authenticated=True, is_staff=True, is_enrolled=True):
        """
        Creates a mock user with the specified properties.
        """
        user = UserFactory()
        user.name = 'mock_user'
        user.is_staff = is_staff
        user.is_enrolled = is_enrolled
        user.is_authenticated = lambda: is_authenticated
        return user

    def is_tab_enabled(self, tab, course, settings, user):
        """
        Returns true if the specified tab is enabled.
        """
        return tab.is_enabled(course, settings, user=user)

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
        if issubclass(tab_class, tabs.CourseViewType):
            tab = tab_class.create_tab(tab_dict=dict_tab)
        else:
            tab = tab_class(tab_dict=dict_tab)

        # name is as expected
        self.assertEqual(tab.name, expected_name)

        # link is as expected
        self.assertEqual(tab.link_func(self.course, self.reverse), expected_link)

        # verify active page name
        self.assertEqual(tab.tab_id, expected_tab_id)

        # validate tab
        self.assertTrue(tab.validate(dict_tab))
        if invalid_dict_tab:
            with self.assertRaises(xmodule_tabs.InvalidTabsException):
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
            user = self.create_mock_user(is_authenticated=True, is_staff=True, is_enrolled=True)
            self.assertEquals(expected_value, self.is_tab_enabled(tab, self.course, self.settings, user))
        if for_authenticated_users_only:
            user = self.create_mock_user(is_authenticated=True, is_staff=False, is_enrolled=False)
            self.assertEquals(expected_value, self.is_tab_enabled(tab, self.course, self.settings, user))
        if not for_staff_only and not for_authenticated_users_only and not for_enrolled_users_only:
            user = self.create_mock_user(is_authenticated=False, is_staff=False, is_enrolled=False)
            self.assertEquals(expected_value, self.is_tab_enabled(tab, self.course, self.settings, user))
        if for_enrolled_users_only:
            user = self.create_mock_user(is_authenticated=True, is_staff=False, is_enrolled=True)
            self.assertEquals(expected_value, self.is_tab_enabled(tab, self.course, self.settings, user))

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


class TabListTestCase(TabTestCase):
    """Base class for Test cases involving tab lists."""

    def setUp(self):
        super(TabListTestCase, self).setUp()

        # invalid tabs
        self.invalid_tabs = [
            # less than 2 tabs
            [{'type': CoursewareViewType.name}],
            # missing course_info
            [{'type': CoursewareViewType.name}, {'type': 'discussion', 'name': 'fake_name'}],
            # incorrect order
            [{'type': CourseInfoViewType.name, 'name': 'fake_name'}, {'type': CoursewareViewType.name}],
        ]

        # tab types that should appear only once
        unique_tab_types = [
            CoursewareViewType.name,
            CourseInfoViewType.name,
            'textbooks',
            'pdf_textbooks',
            'html_textbooks',
        ]

        for unique_tab_type in unique_tab_types:
            self.invalid_tabs.append([
                {'type': CoursewareViewType.name},
                {'type': CourseInfoViewType.name, 'name': 'fake_name'},
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
                {'type': CoursewareViewType.name},
                {'type': CourseInfoViewType.name, 'name': 'fake_name'},
                {'type': 'discussion', 'name': 'fake_name'},
                {'type': ExternalLinkCourseViewType.name, 'name': 'fake_name', 'link': 'fake_link'},
                {'type': 'textbooks'},
                {'type': 'pdf_textbooks'},
                {'type': 'html_textbooks'},
                {'type': ProgressCourseViewType.name, 'name': 'fake_name'},
                {'type': StaticCourseViewType.name, 'name': 'fake_name', 'url_slug': 'schlug'},
                {'type': 'syllabus'},
            ],
            # with external discussion
            [
                {'type': CoursewareViewType.name},
                {'type': CourseInfoViewType.name, 'name': 'fake_name'},
                {'type': ExternalDiscussionCourseViewType.name, 'name': 'fake_name', 'link': 'fake_link'}
            ],
        ]

        self.all_valid_tab_list = xmodule_tabs.CourseTabList().from_json(self.valid_tabs[1])


class ValidateTabsTestCase(TabListTestCase):
    """Test cases for validating tabs."""

    def test_validate_tabs(self):
        tab_list = xmodule_tabs.CourseTabList()
        for invalid_tab_list in self.invalid_tabs:
            with self.assertRaises(xmodule_tabs.InvalidTabsException):
                tab_list.from_json(invalid_tab_list)

        for valid_tab_list in self.valid_tabs:
            from_json_result = tab_list.from_json(valid_tab_list)
            self.assertEquals(len(from_json_result), len(valid_tab_list))

    def test_invalid_tab_type(self):
        """
        Verifies that having an unrecognized tab type does not cause
        the tabs to be undisplayable.
        """
        tab_list = xmodule_tabs.CourseTabList()
        self.assertEquals(
            len(tab_list.from_json([
                {'type': CoursewareViewType.name},
                {'type': CourseInfoViewType.name, 'name': 'fake_name'},
                {'type': 'no_such_type'}
            ])),
            2
        )


class ProgressTestCase(TabTestCase):
    """Test cases for Progress Tab."""

    def check_progress_tab(self):
        """Helper function for verifying the progress tab."""
        return self.check_tab(
            tab_class=ProgressCourseViewType,
            dict_tab={'type': ProgressCourseViewType.name, 'name': 'same'},
            expected_link=self.reverse('progress', args=[self.course.id.to_deprecated_string()]),
            expected_tab_id=ProgressCourseViewType.name,
            invalid_dict_tab=None,
        )

    @patch('student.models.CourseEnrollment.is_enrolled')
    def test_progress(self, is_enrolled):
        is_enrolled.return_value = True
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


class StaticTabTestCase(TabTestCase):
    """Test cases for Static Tab."""

    def test_static_tab(self):

        url_slug = 'schmug'

        tab = self.check_tab(
            tab_class=StaticCourseViewType,
            dict_tab={'type': StaticCourseViewType.name, 'name': 'same', 'url_slug': url_slug},
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
            xmodule_tabs.CourseTab.from_json({'type': 'textbooks'}),
            xmodule_tabs.CourseTab.from_json({'type': 'pdf_textbooks'}),
            xmodule_tabs.CourseTab.from_json({'type': 'html_textbooks'}),
        ]
        self.num_textbook_tabs = sum(1 for tab in self.course.tabs if tab.type in [
            'textbooks', 'pdf_textbooks', 'html_textbooks'
        ])
        self.num_textbooks = self.num_textbook_tabs * len(self.books)

    def test_textbooks_enabled(self):

        type_to_reverse_name = {'textbook': 'book', 'pdftextbook': 'pdf_book', 'htmltextbook': 'html_book'}

        self.settings.FEATURES['ENABLE_TEXTBOOK'] = True
        num_textbooks_found = 0
        user = self.create_mock_user(is_authenticated=True, is_staff=False, is_enrolled=True)
        for tab in xmodule_tabs.CourseTabList.iterate_displayable(self.course, self.settings, user=user):
            # verify all textbook type tabs
            if tab.type == 'single_textbook':
                book_type, book_index = tab.tab_id.split("/", 1)
                expected_link = self.reverse(
                    type_to_reverse_name[book_type],
                    args=[self.course.id.to_deprecated_string(), book_index]
                )
                self.assertEqual(tab.link_func(self.course, self.reverse), expected_link)
                self.assertTrue(tab.name.startswith('Book{0}'.format(book_index)))
                num_textbooks_found = num_textbooks_found + 1
        self.assertEquals(num_textbooks_found, self.num_textbooks)


class KeyCheckerTestCase(unittest.TestCase):
    """Test cases for KeyChecker class"""

    def setUp(self):
        super(KeyCheckerTestCase, self).setUp()

        self.valid_keys = ['a', 'b']
        self.invalid_keys = ['a', 'v', 'g']
        self.dict_value = {'a': 1, 'b': 2, 'c': 3}

    def test_key_checker(self):

        self.assertTrue(xmodule_tabs.key_checker(self.valid_keys)(self.dict_value, raise_error=False))
        self.assertFalse(xmodule_tabs.key_checker(self.invalid_keys)(self.dict_value, raise_error=False))
        with self.assertRaises(xmodule_tabs.InvalidTabsException):
            xmodule_tabs.key_checker(self.invalid_keys)(self.dict_value)


class NeedNameTestCase(unittest.TestCase):
    """Test cases for NeedName validator"""

    def setUp(self):
        super(NeedNameTestCase, self).setUp()

        self.valid_dict1 = {'a': 1, 'name': 2}
        self.valid_dict2 = {'name': 1}
        self.valid_dict3 = {'a': 1, 'name': 2, 'b': 3}
        self.invalid_dict = {'a': 1, 'b': 2}

    def test_need_name(self):
        self.assertTrue(xmodule_tabs.need_name(self.valid_dict1))
        self.assertTrue(xmodule_tabs.need_name(self.valid_dict2))
        self.assertTrue(xmodule_tabs.need_name(self.valid_dict3))
        with self.assertRaises(xmodule_tabs.InvalidTabsException):
            xmodule_tabs.need_name(self.invalid_dict)


class CourseTabListTestCase(TabListTestCase):
    """Testing the generator method for iterating through displayable tabs"""

    def has_tab(self, tab_list, tab_type):
        """ Searches the given lab_list for a given tab_type. """
        for tab in tab_list:
            if tab.type == tab_type:
                return True
        return False

    def test_initialize_default_without_syllabus(self):
        self.course.tabs = []
        self.course.syllabus_present = False
        xmodule_tabs.CourseTabList.initialize_default(self.course)
        self.assertFalse(self.has_tab(self.course.tabs, 'syllabus'))

    def test_initialize_default_with_syllabus(self):
        self.course.tabs = []
        self.course.syllabus_present = True
        xmodule_tabs.CourseTabList.initialize_default(self.course)
        self.assertTrue(self.has_tab(self.course.tabs, 'syllabus'))

    def test_initialize_default_with_external_link(self):
        self.course.tabs = []
        self.course.discussion_link = "other_discussion_link"
        xmodule_tabs.CourseTabList.initialize_default(self.course)
        self.assertTrue(self.has_tab(self.course.tabs, 'external_discussion'))
        self.assertFalse(self.has_tab(self.course.tabs, 'discussion'))

    def test_initialize_default_without_external_link(self):
        self.course.tabs = []
        self.course.discussion_link = ""
        xmodule_tabs.CourseTabList.initialize_default(self.course)
        self.assertFalse(self.has_tab(self.course.tabs, 'external_discussion'))
        self.assertTrue(self.has_tab(self.course.tabs, 'discussion'))

    def test_iterate_displayable(self):
        # enable all tab types
        self.settings.FEATURES['ENABLE_TEXTBOOK'] = True
        self.settings.FEATURES['ENABLE_DISCUSSION_SERVICE'] = True
        self.settings.FEATURES['ENABLE_STUDENT_NOTES'] = True
        self.settings.FEATURES['ENABLE_EDXNOTES'] = True
        self.course.hide_progress_tab = False

        # create 1 book per textbook type
        self.set_up_books(1)

        # initialize the course tabs to a list of all valid tabs
        self.course.tabs = self.all_valid_tab_list

        # enumerate the tabs with no user
        for i, tab in enumerate(xmodule_tabs.CourseTabList.iterate_displayable(
                self.course,
                self.settings,
                inline_collections=False
        )):
            self.assertEquals(tab.type, self.course.tabs[i].type)

        # enumerate the tabs with a staff user
        user = UserFactory(is_staff=True)
        CourseEnrollment.enroll(user, self.course.id)
        for i, tab in enumerate(xmodule_tabs.CourseTabList.iterate_displayable(
                self.course,
                self.settings,
                user=user
        )):
            if getattr(tab, 'is_collection_item', False):
                # a collection item was found as a result of a collection tab
                self.assertTrue(getattr(self.course.tabs[i], 'is_collection', False))
            else:
                # all other tabs must match the expected type
                self.assertEquals(tab.type, self.course.tabs[i].type)

        # test including non-empty collections
        self.assertIn(
            {'type': 'html_textbooks'},
            list(xmodule_tabs.CourseTabList.iterate_displayable(self.course, self.settings, inline_collections=False)),
        )

        # test not including empty collections
        self.course.html_textbooks = []
        self.assertNotIn(
            {'type': 'html_textbooks'},
            list(xmodule_tabs.CourseTabList.iterate_displayable(self.course, self.settings, inline_collections=False)),
        )

    def test_get_tab_by_methods(self):
        """Tests the get_tab methods in CourseTabList"""
        self.course.tabs = self.all_valid_tab_list
        for tab in self.course.tabs:

            # get tab by type
            self.assertEquals(xmodule_tabs.CourseTabList.get_tab_by_type(self.course.tabs, tab.type), tab)

            # get tab by id
            self.assertEquals(xmodule_tabs.CourseTabList.get_tab_by_id(self.course.tabs, tab.tab_id), tab)


class DiscussionLinkTestCase(TabTestCase):
    """Test cases for discussion link tab."""

    def setUp(self):
        super(DiscussionLinkTestCase, self).setUp()

        self.tabs_with_discussion = [
            xmodule_tabs.CourseTab.from_json({'type': 'discussion'}),
        ]
        self.tabs_without_discussion = [
        ]

    @staticmethod
    def _reverse(course):
        """Custom reverse function"""
        def reverse_discussion_link(viewname, args):
            """reverse lookup for discussion link"""
            if viewname == "django_comment_client.forum.views.forum_form_discussion" and args == [unicode(course.id)]:
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
        discussion_tab = xmodule_tabs.CourseTabList.get_discussion(self.course)
        user = self.create_mock_user(is_authenticated=True, is_staff=is_staff, is_enrolled=is_enrolled)
        with patch('student.models.CourseEnrollment.is_enrolled') as check_is_enrolled:
            check_is_enrolled.return_value = is_enrolled
            self.assertEquals(
                (
                    discussion_tab is not None and
                    self.is_tab_enabled(discussion_tab, self.course, self.settings, user) and
                    (discussion_tab.link_func(self.course, self._reverse(self.course)) == expected_discussion_link)
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
