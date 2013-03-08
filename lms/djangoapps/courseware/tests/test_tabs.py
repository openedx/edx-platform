from django.test import TestCase
from mock import MagicMock

import courseware.tabs as tabs

from django.test.utils import override_settings
from django.core.urlresolvers import reverse


class ProgressTestCase(TestCase):

   def setUp(self):

       self.mockuser1 = MagicMock()
       self.mockuser0 = MagicMock()
       self.course = MagicMock()
       self.mockuser1.is_authenticated.return_value = True
       self.mockuser0.is_authenticated.return_value = False
       self.course.id = 'edX/full/6.002_Spring_2012'
       self.tab = {'name': 'same'}
       self.active_page1 = 'progress'
       self.active_page0 = 'stagnation'

   def test_progress(self):

        self.assertEqual(tabs._progress(self.tab, self.mockuser0, self.course,
                                        self.active_page0), [])

        self.assertEqual(tabs._progress(self.tab, self.mockuser1, self.course,
                                        self.active_page1)[0].name, 'same')

        self.assertEqual(tabs._progress(self.tab, self.mockuser1, self.course,
                                       self.active_page1)[0].link,
                         reverse('progress', args = [self.course.id]))

        self.assertEqual(tabs._progress(self.tab, self.mockuser1, self.course,
                                        self.active_page0)[0].is_active, False)

        self.assertEqual(tabs._progress(self.tab, self.mockuser1, self.course,
                                        self.active_page1)[0].is_active, True)


class WikiTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.course = MagicMock()
        self.course.id = 'edX/full/6.002_Spring_2012'
        self.tab = {'name': 'same'}
        self.active_page1 = 'wiki'
        self.active_page0 = 'miki'

    @override_settings(WIKI_ENABLED=True)
    def test_wiki_enabled(self):

        self.assertEqual(tabs._wiki(self.tab, self.user,
                                    self.course, self.active_page1)[0].name,
                         'same')

        self.assertEqual(tabs._wiki(self.tab, self.user,
                    				self.course, self.active_page1)[0].link,
                         reverse('course_wiki', args=[self.course.id]))

        self.assertEqual(tabs._wiki(self.tab, self.user,
        			                self.course, self.active_page1)[0].is_active,
                         True)

        self.assertEqual(tabs._wiki(self.tab, self.user,
        			                self.course, self.active_page0)[0].is_active,
                         False)

    @override_settings(WIKI_ENABLED=False)
    def test_wiki_enabled_false(self):

        self.assertEqual(tabs._wiki(self.tab, self.user,
                                    self.course, self.active_page1), [])


class ExternalLinkTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.course = MagicMock()
        self.tabby = {'name': 'same', 'link': 'blink'}
        self.active_page0 = None
        self.active_page00 = True

    def test_external_link(self):

        self.assertEqual(tabs._external_link(self.tabby, self.user,
                                             self.course, self.active_page0)[0].name,
                         'same')

        self.assertEqual(tabs._external_link(self.tabby, self.user,
                                             self.course, self.active_page0)[0].link,
                         'blink')

        self.assertEqual(tabs._external_link(self.tabby, self.user,
                                             self.course, self.active_page0)[0].is_active,
                         False)

        self.assertEqual(tabs._external_link(self.tabby, self.user,
                                             self.course, self.active_page00)[0].is_active,
                         False)


class StaticTabTestCase(TestCase):

    def setUp(self):

        self.user = MagicMock()
        self.course = MagicMock()
        self.tabby = {'name': 'same', 'url_slug': 'schmug'}
        self.course.id = 'edX/full/6.002_Spring_2012'
        self.active_page1 = 'static_tab_schmug'
        self.active_page0 = 'static_tab_schlug'

    def test_static_tab(self):

        self.assertEqual(tabs._static_tab(self.tabby, self.user,
                                          self.course, self.active_page1)[0].name,
                         'same')

        self.assertEqual(tabs._static_tab(self.tabby, self.user,
                                          self.course, self.active_page1)[0].link,
                         reverse('static_tab', args = [self.course.id,
                                                       self.tabby['url_slug']]))

        self.assertEqual(tabs._static_tab(self.tabby, self.user,
                                          self.course, self.active_page1)[0].is_active,
                         True)


        self.assertEqual(tabs._static_tab(self.tabby, self.user,
                                          self.course, self.active_page0)[0].is_active,
                         False)


class TextbooksTestCase(TestCase):

    def setUp(self):

        self.mockuser1 = MagicMock()
        self.mockuser0 = MagicMock()
        self.course = MagicMock()
        self.tab = MagicMock()
        A = MagicMock()
        T = MagicMock()
        self.mockuser1.is_authenticated.return_value = True
        self.mockuser0.is_authenticated.return_value = False
        self.course.id = 'edX/full/6.002_Spring_2012'
        self.active_page0 = 'textbook/0'
        self.active_page1 = 'textbook/1'
        self.active_pageX = 'you_shouldnt_be_seein_this'
        A.title = 'Algebra'
        T.title = 'Topology'
        self.course.textbooks = [A, T]

    @override_settings(MITX_FEATURES={'ENABLE_TEXTBOOK': True})
    def test_textbooks1(self):

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_page0)[0].name,
                         'Algebra')

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_page0)[0].link,
                         reverse('book', args=[self.course.id, 0]))

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_page0)[0].is_active,
                         True)

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_pageX)[0].is_active,
                         False)

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_page1)[1].name,
                        'Topology')

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_page1)[1].link,
                         reverse('book', args=[self.course.id, 1]))

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_page1)[1].is_active,
                         True)

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_pageX)[1].is_active,
                         False)

    @override_settings(MITX_FEATURES={'ENABLE_TEXTBOOK': False})
    def test_textbooks0(self):

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser1,
                                         self.course, self.active_pageX), [])

        self.assertEqual(tabs._textbooks(self.tab, self.mockuser0,
                                         self.course, self.active_pageX), [])

class KeyCheckerTestCase(TestCase):

    def setUp(self):

        self.expected_keys1 = ['a', 'b']
        self.expected_keys0 = ['a', 'v', 'g']
        self.dictio = {'a': 1, 'b': 2, 'c': 3}

    def test_key_checker(self):

        self.assertIsNone(tabs.key_checker(self.expected_keys1)(self.dictio))
        self.assertRaises(tabs.InvalidTabsException,
                          tabs.key_checker(self.expected_keys0), self.dictio)


class NullValidatorTestCase(TestCase):

   def setUp(self):

      self.d = {}

      def test_null_validator(self):

         self.assertIsNone(tabs.null_validator(self.d))


class ValidateTabsTestCase(TestCase):

    def setUp(self):

        self.courses = [MagicMock() for i in range(0,5)]

        self.courses[0].tabs = None

        self.courses[1].tabs = [{'type':'courseware'}, {'type': 'fax'}]

        self.courses[2].tabs = [{'type':'shadow'}, {'type': 'course_info'}]

        self.courses[3].tabs = [{'type':'courseware'},{'type':'course_info', 'name': 'alice'},
                             {'type': 'wiki', 'name':'alice'}, {'type':'discussion', 'name': 'alice'},
                             {'type':'external_link', 'name': 'alice', 'link':'blink'},
                             {'type':'textbooks'}, {'type':'progress', 'name': 'alice'},
                             {'type':'static_tab', 'name':'alice', 'url_slug':'schlug'},
                             {'type': 'staff_grading'}]

        self.courses[4].tabs = [{'type':'courseware'},{'type': 'course_info'}, {'type': 'flying'}]


    def test_validate_tabs(self):

        self.assertIsNone(tabs.validate_tabs(self.courses[0]))
        self.assertRaises(tabs.InvalidTabsException, tabs.validate_tabs, self.courses[1])
        self.assertRaises(tabs.InvalidTabsException, tabs.validate_tabs, self.courses[2])
        self.assertIsNone(tabs.validate_tabs(self.courses[3]))
        self.assertRaises(tabs.InvalidTabsException, tabs.validate_tabs, self.courses[4])
