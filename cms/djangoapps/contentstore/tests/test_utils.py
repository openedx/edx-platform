"""Tests for utils."""
import mock
import unittest
import collections
import copy
import json
from uuid import uuid4

from django.test import TestCase

from contentstore import utils
from django.test.utils import override_settings
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError


class LMSLinksTestCase(TestCase):
    """ Tests for LMS links. """
    def about_page_test(self):
        """ Get URL for about page, no marketing site """
        # default for ENABLE_MKTG_SITE is False.
        self.assertEquals(self.get_about_page_link(), "//localhost:8000/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def about_page_marketing_site_test(self):
        """ Get URL for about page, marketing root present. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), "//dummy-root/courses/mitX/101/test/about")
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': False}):
            self.assertEquals(self.get_about_page_link(), "//localhost:8000/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={'ROOT': 'http://www.dummy'})
    def about_page_marketing_site_remove_http_test(self):
        """ Get URL for about page, marketing root present, remove http://. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), "//www.dummy/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={'ROOT': 'https://www.dummy'})
    def about_page_marketing_site_remove_https_test(self):
        """ Get URL for about page, marketing root present, remove https://. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), "//www.dummy/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={'ROOT': 'www.dummyhttps://x'})
    def about_page_marketing_site_https__edge_test(self):
        """ Get URL for about page, only remove https:// at the beginning of the string. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), "//www.dummyhttps://x/courses/mitX/101/test/about")

    @override_settings(MKTG_URLS={})
    def about_page_marketing_urls_not_set_test(self):
        """ Error case. ENABLE_MKTG_SITE is True, but there is either no MKTG_URLS, or no MKTG_URLS Root property. """
        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': True}):
            self.assertEquals(self.get_about_page_link(), None)

    @override_settings(LMS_BASE=None)
    def about_page_no_lms_base_test(self):
        """ No LMS_BASE, nor is ENABLE_MKTG_SITE True """
        self.assertEquals(self.get_about_page_link(), None)

    def get_about_page_link(self):
        """ create mock course and return the about page link """
        location = 'i4x', 'mitX', '101', 'course', 'test'
        utils.get_course_id = mock.Mock(return_value="mitX/101/test")
        return utils.get_lms_link_for_about_page(location)

    def lms_link_test(self):
        """ Tests get_lms_link_for_item. """
        location = 'i4x', 'mitX', '101', 'vertical', 'contacting_us'
        utils.get_course_id = mock.Mock(return_value="mitX/101/test")
        link = utils.get_lms_link_for_item(location, False)
        self.assertEquals(link, "//localhost:8000/courses/mitX/101/test/jump_to/i4x://mitX/101/vertical/contacting_us")
        link = utils.get_lms_link_for_item(location, True)
        self.assertEquals(
            link,
            "//preview/courses/mitX/101/test/jump_to/i4x://mitX/101/vertical/contacting_us"
        )


class UrlReverseTestCase(ModuleStoreTestCase):
    """ Tests for get_url_reverse """
    def test_course_page_names(self):
        """ Test the defined course pages. """
        course = CourseFactory.create(org='mitX', number='666', display_name='URL Reverse Course')

        self.assertEquals(
            '/manage_users/i4x://mitX/666/course/URL_Reverse_Course',
            utils.get_url_reverse('ManageUsers', course)
        )

        self.assertEquals(
            '/mitX/666/settings-details/URL_Reverse_Course',
            utils.get_url_reverse('SettingsDetails', course)
        )

        self.assertEquals(
            '/mitX/666/settings-grading/URL_Reverse_Course',
            utils.get_url_reverse('SettingsGrading', course)
        )

        self.assertEquals(
            '/mitX/666/course/URL_Reverse_Course',
            utils.get_url_reverse('CourseOutline', course)
        )

        self.assertEquals(
            '/mitX/666/checklists/URL_Reverse_Course',
            utils.get_url_reverse('Checklists', course)
        )

    def test_unknown_passes_through(self):
        """ Test that unknown values pass through. """
        course = CourseFactory.create(org='mitX', number='666', display_name='URL Reverse Course')
        self.assertEquals(
            'foobar',
            utils.get_url_reverse('foobar', course)
        )
        self.assertEquals(
            'https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/about',
            utils.get_url_reverse('https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/about', course)
        )


class ExtraPanelTabTestCase(TestCase):
    """ Tests adding and removing extra course tabs. """

    def get_tab_type_dicts(self, tab_types):
        """ Returns an array of tab dictionaries. """
        if tab_types:
            return [{'tab_type': tab_type} for tab_type in tab_types.split(',')]
        else:
            return []

    def get_course_with_tabs(self, tabs=[]):
        """ Returns a mock course object with a tabs attribute. """
        course = collections.namedtuple('MockCourse', ['tabs'])
        if isinstance(tabs, basestring):
            course.tabs = self.get_tab_type_dicts(tabs)
        else:
            course.tabs = tabs
        return course

    def test_add_extra_panel_tab(self):
        """ Tests if a tab can be added to a course tab list. """
        for tab_type in utils.EXTRA_TAB_PANELS.keys():
            tab = utils.EXTRA_TAB_PANELS.get(tab_type)

            # test adding with changed = True
            for tab_setup in ['', 'x', 'x,y,z']:
                course = self.get_course_with_tabs(tab_setup)
                expected_tabs = copy.copy(course.tabs)
                expected_tabs.append(tab)
                changed, actual_tabs = utils.add_extra_panel_tab(tab_type, course)
                self.assertTrue(changed)
                self.assertEqual(actual_tabs, expected_tabs)

            # test adding with changed = False
            tab_test_setup = [
                [tab],
                [tab, self.get_tab_type_dicts('x,y,z')],
                [self.get_tab_type_dicts('x,y'), tab, self.get_tab_type_dicts('z')],
                [self.get_tab_type_dicts('x,y,z'), tab]]

            for tab_setup in tab_test_setup:
                course = self.get_course_with_tabs(tab_setup)
                expected_tabs = copy.copy(course.tabs)
                changed, actual_tabs = utils.add_extra_panel_tab(tab_type, course)
                self.assertFalse(changed)
                self.assertEqual(actual_tabs, expected_tabs)

    def test_remove_extra_panel_tab(self):
        """ Tests if a tab can be removed from a course tab list. """
        for tab_type in utils.EXTRA_TAB_PANELS.keys():
            tab = utils.EXTRA_TAB_PANELS.get(tab_type)

            # test removing with changed = True
            tab_test_setup = [
                [tab],
                [tab, self.get_tab_type_dicts('x,y,z')],
                [self.get_tab_type_dicts('x,y'), tab, self.get_tab_type_dicts('z')],
                [self.get_tab_type_dicts('x,y,z'), tab]]

            for tab_setup in tab_test_setup:
                course = self.get_course_with_tabs(tab_setup)
                expected_tabs = [t for t in course.tabs if t != utils.EXTRA_TAB_PANELS.get(tab_type)]
                changed, actual_tabs = utils.remove_extra_panel_tab(tab_type, course)
                self.assertTrue(changed)
                self.assertEqual(actual_tabs, expected_tabs)

            # test removing with changed = False
            for tab_setup in ['', 'x', 'x,y,z']:
                course = self.get_course_with_tabs(tab_setup)
                expected_tabs = copy.copy(course.tabs)
                changed, actual_tabs = utils.remove_extra_panel_tab(tab_type, course)
                self.assertFalse(changed)
                self.assertEqual(actual_tabs, expected_tabs)


class TestReturnAjaxStatus(unittest.TestCase):
    """Tests for `return_ajax_status` decorator."""
    def setUp(self):
        self.true_view_func = lambda *args, **kwargs: True
        self.true_extra_view_func = lambda *args, **kwargs: (True, {'msg': 'some message'})
        self.false_view_func = lambda *args, **kwargs: False

    def test_success_response(self):
        request = None
        response = utils.return_ajax_status(self.true_view_func)(request)
        status = json.loads(response.content).get('success')
        self.assertTrue(status)

    def test_fail_response(self):
        request = None
        response = utils.return_ajax_status(self.false_view_func)(request)
        status = json.loads(response.content).get('success')
        self.assertFalse(status)

    def test_extra_response_data(self):
        request = None
        response = utils.return_ajax_status(self.true_extra_view_func)(request)
        resp = json.loads(response.content)

        self.assertTrue(resp.get('success'))
        self.assertEqual(resp.get('msg'), 'some message')


class TestGenerateSubs(unittest.TestCase):
    """Tests for `generate_subs` function."""
    def setUp(self):
        self.source_subs = {
            'start': [100, 200, 240, 390, 1000],
            'end': [200, 240, 380, 1000, 1500],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }

    def test_generate_subs_increase_speed(self):
        subs = utils.generate_subs(2, 1, self.source_subs)
        self.assertDictEqual(
            subs,
            {
                'start': [200, 400, 480, 780, 2000],
                'end': [400, 480, 760, 2000, 3000],
                'text': ['subs #1', 'subs #2', 'subs #3', 'subs #4', 'subs #5']
            }
        )

    def test_generate_subs_decrease_speed_1(self):
        subs = utils.generate_subs(0.5, 1, self.source_subs)
        self.assertDictEqual(
            subs,
            {
                'start': [50, 100, 120, 195, 500],
                'end': [100, 120, 190, 500, 750],
                'text': ['subs #1', 'subs #2', 'subs #3', 'subs #4', 'subs #5']
            }
        )

    def test_generate_subs_decrease_speed_2(self):
        """Test for correct devision during `generate_subs` process."""
        subs = utils.generate_subs(1, 2, self.source_subs)
        self.assertDictEqual(
            subs,
            {
                'start': [50, 100, 120, 195, 500],
                'end': [100, 120, 190, 500, 750],
                'text': ['subs #1', 'subs #2', 'subs #3', 'subs #4', 'subs #5']
            }
        )


class TestSaveSubsToStore(ModuleStoreTestCase):
    """Tests for `save_subs_to_store` function."""

    org = 'MITx'
    number = '999'
    display_name = 'Test course'

    def clear_subs_content(self):
        """Remove, if subtitles content exists."""
        try:
            content = contentstore().find(self.content_location)
            contentstore().delete(content.get_id())
        except NotFoundError:
            pass

    def setUp(self):
        self.subs = {
            'start': [100, 200, 240, 390, 1000],
            'end': [200, 240, 380, 1000, 1500],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }

        self.subs_id = str(uuid4())
        filename = 'subs_{0}.srt.sjson'.format(self.subs_id)
        self.course = CourseFactory.create(
            org=self.org, number=self.number, display_name=self.display_name)
        self.content_location = StaticContent.compute_location(
            self.org, self.number, filename)

        self.clear_subs_content()

    def test_save_subs_to_store(self):
        self.assertRaises(
            NotFoundError,
            contentstore().find,
            self.content_location
        )

        result_location = utils.save_subs_to_store(
            self.subs,
            self.subs_id,
            self.course)

        self.assertTrue(contentstore().find(self.content_location))
        self.assertEqual(result_location, self.content_location)

    def tearDown(self):
        self.clear_subs_content()


class TestDownloadYoutubeSubs(ModuleStoreTestCase):
    """Tests for `download_youtube_subs` function."""

    org = 'MITx'
    number = '999'
    display_name = 'Test course'

    def clear_subs_content(self, youtube_subs):
        """Remove, if subtitles content exists."""
        for subs_id in youtube_subs.values():
            filename = 'subs_{0}.srt.sjson'.format(subs_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            try:
                content = contentstore().find(content_location)
                contentstore().delete(content.get_id())
            except NotFoundError:
                pass

    def setUp(self):
        self.course = CourseFactory.create(
            org=self.org, number=self.number, display_name=self.display_name)

    def test_success_downloading_subs(self):
        good_youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }
        self.clear_subs_content(good_youtube_subs)

        status = utils.download_youtube_subs(good_youtube_subs, self.course)
        self.assertTrue(status)

        # Check assets status after importing subtitles.
        for subs_id in good_youtube_subs.values():
            filename = 'subs_{0}.srt.sjson'.format(subs_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            self.assertTrue(contentstore().find(content_location))

        self.clear_subs_content(good_youtube_subs)

    def test_fail_downloading_subs(self):
        bad_youtube_subs = {
            0.5: 'BAD_YOUTUBE_ID1',
            1.0: 'BAD_YOUTUBE_ID2',
            2.0: 'BAD_YOUTUBE_ID3'
        }
        self.clear_subs_content(bad_youtube_subs)

        status = utils.download_youtube_subs(bad_youtube_subs, self.course)
        self.assertFalse(status)

        # Check assets status after importing subtitles.
        for subs_id in bad_youtube_subs.values():
            filename = 'subs_{0}.srt.sjson'.format(subs_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            self.assertRaises(
                NotFoundError, contentstore().find, content_location)

        self.clear_subs_content(bad_youtube_subs)


class TestGenerateSubsFromSource(TestDownloadYoutubeSubs):
    """Tests for `generate_subs_from_source` function."""

    def test_success_generating_subs(self):
        youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }
        srt_filedata = """
1
00:00:10,500 --> 00:00:13,000
Elephant's Dream

2
00:00:15,000 --> 00:00:18,000
At the left we can see...
        """
        self.clear_subs_content(youtube_subs)

        status = utils.generate_subs_from_source(
            youtube_subs,
            'srt',
            srt_filedata,
            self.course)
        self.assertTrue(status)

        # Check assets status after importing subtitles.
        for subs_id in youtube_subs.values():
            filename = 'subs_{0}.srt.sjson'.format(subs_id)
            content_location = StaticContent.compute_location(
                self.org, self.number, filename)
            self.assertTrue(contentstore().find(content_location))

        self.clear_subs_content(youtube_subs)

    def test_fail_bad_subs_type(self):
        youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }

        srt_filedata = """
1
00:00:10,500 --> 00:00:13,000
Elephant's Dream

2
00:00:15,000 --> 00:00:18,000
At the left we can see...
        """

        status = utils.generate_subs_from_source(
            youtube_subs,
            'BAD_FORMAT',
            srt_filedata,
            self.course)
        self.assertFalse(status)

    def test_fail_bad_subs_filedata(self):
        youtube_subs = {
            0.5: 'JMD_ifUUfsU',
            1.0: 'hI10vDNYz4M',
            2.0: 'AKqURZnYqpk'
        }

        srt_filedata = """BAD_DATA"""

        status = utils.generate_subs_from_source(
            youtube_subs,
            'srt',
            srt_filedata,
            self.course)
        self.assertFalse(status)


class TestGenerateSrtFromSjson(TestDownloadYoutubeSubs):
    """Tests for `generate_srt_from_sjson` function."""

    def test_success_generating_subs(self):
        sjson_subs = {
            'start': [100, 200, 240, 390, 54000],
            'end': [200, 240, 380, 1000, 78400],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        srt_subs = utils.generate_srt_from_sjson(sjson_subs, 1)
        self.assertIsNotNone(srt_subs)
        self.assertIn(
            '00:00:00,100 --> 00:00:00,200\nsubs #1',
            srt_subs)
        self.assertIn(
            '00:00:00,200 --> 00:00:00,240\nsubs #2',
            srt_subs)
        self.assertIn(
            '00:00:00,240 --> 00:00:00,380\nsubs #3',
            srt_subs)
        self.assertIn(
            '00:00:00,390 --> 00:00:01,000\nsubs #4',
            srt_subs)
        self.assertIn(
            '00:00:54,000 --> 00:01:18,400\nsubs #5',
            srt_subs)

    def test_success_generating_subs_speed_up(self):
        sjson_subs = {
            'start': [100, 200, 240, 390, 54000],
            'end': [200, 240, 380, 1000, 78400],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        srt_subs = utils.generate_srt_from_sjson(sjson_subs, 0.5)
        self.assertIsNotNone(srt_subs)
        self.assertIn(
            '00:00:00,050 --> 00:00:00,100\nsubs #1',
            srt_subs)
        self.assertIn(
            '00:00:00,100 --> 00:00:00,120\nsubs #2',
            srt_subs)
        self.assertIn(
            '00:00:00,120 --> 00:00:00,190\nsubs #3',
            srt_subs)
        self.assertIn(
            '00:00:00,195 --> 00:00:00,500\nsubs #4',
            srt_subs)
        self.assertIn(
            '00:00:27,000 --> 00:00:39,200\nsubs #5',
            srt_subs)

    def test_success_generating_subs_speed_down(self):
        sjson_subs = {
            'start': [100, 200, 240, 390, 54000],
            'end': [200, 240, 380, 1000, 78400],
            'text': [
                'subs #1',
                'subs #2',
                'subs #3',
                'subs #4',
                'subs #5'
            ]
        }
        srt_subs = utils.generate_srt_from_sjson(sjson_subs, 2)
        self.assertIsNotNone(srt_subs)
        self.assertIn(
            '00:00:00,200 --> 00:00:00,400\nsubs #1',
            srt_subs)
        self.assertIn(
            '00:00:00,400 --> 00:00:00,480\nsubs #2',
            srt_subs)
        self.assertIn(
            '00:00:00,480 --> 00:00:00,760\nsubs #3',
            srt_subs)
        self.assertIn(
            '00:00:00,780 --> 00:00:02,000\nsubs #4',
            srt_subs)
        self.assertIn(
            '00:01:48,000 --> 00:02:36,800\nsubs #5',
            srt_subs)

    def test_fail_generating_subs(self):
        sjson_subs = {
            'start': [100, 200],
            'end': [100],
            'text': [
                'subs #1',
                'subs #2'
            ]
        }
        srt_subs = utils.generate_srt_from_sjson(sjson_subs, 1)
        self.assertIsNone(srt_subs)
