from mock import MagicMock
import json

from django.http import Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from xmodule.modulestore.django import modulestore
import courseware.module_render as render
from courseware.tests.tests import LoginEnrollmentTestCase
from courseware.model_data import ModelDataCache

from .factories import UserFactory


class Stub:
    def __init__(self):
        pass


def xml_store_config(data_dir):
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class ModuleRenderTestCase(LoginEnrollmentTestCase):
    def setUp(self):
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self.course_id = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_id)

    def test_get_module(self):
        self.assertIsNone(render.get_module('dummyuser', None,
                                            'invalid location', None, None))

    def test_modx_dispatch(self):
        self.assertRaises(Http404, render.modx_dispatch, 'dummy', 'dummy',
                          'invalid Location', 'dummy')
        mock_request = MagicMock()
        mock_request.FILES.keys.return_value = ['file_id']
        mock_request.FILES.getlist.return_value = ['file'] * (settings.MAX_FILEUPLOADS_PER_INPUT + 1)
        self.assertEquals(render.modx_dispatch(mock_request, 'dummy', self.location, 'dummy').content,
                          json.dumps({'success': 'Submission aborted! Maximum %d files may be submitted at once' %
                                      settings.MAX_FILEUPLOADS_PER_INPUT}))
        mock_request_2 = MagicMock()
        mock_request_2.FILES.keys.return_value = ['file_id']
        inputfile = Stub()
        inputfile.size = 1 + settings.STUDENT_FILEUPLOAD_MAX_SIZE
        inputfile.name = 'name'
        filelist = [inputfile]
        mock_request_2.FILES.getlist.return_value = filelist
        self.assertEquals(render.modx_dispatch(mock_request_2, 'dummy', self.location,
                                               'dummy').content,
                          json.dumps({'success': 'Submission aborted! Your file "%s" is too large (max size: %d MB)' %
                                      (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))}))
        mock_request_3 = MagicMock()
        mock_request_3.POST.copy.return_value = {'position': 1}
        mock_request_3.FILES = False
        mock_request_3.user = UserFactory()
        inputfile_2 = Stub()
        inputfile_2.size = 1
        inputfile_2.name = 'name'
        self.assertIsInstance(render.modx_dispatch(mock_request_3, 'goto_position',
                                                   self.location, self.course_id), HttpResponse)
        self.assertRaises(
            Http404,
            render.modx_dispatch,
            mock_request_3,
            'goto_position',
            self.location,
            'bad_course_id'
        )
        self.assertRaises(
            Http404,
            render.modx_dispatch,
            mock_request_3,
            'goto_position',
            ['i4x', 'edX', 'toy', 'chapter', 'bad_location'],
            self.course_id
        )
        self.assertRaises(
            Http404,
            render.modx_dispatch,
            mock_request_3,
            'bad_dispatch',
            self.location,
            self.course_id
        )

    def test_get_score_bucket(self):
        self.assertEquals(render.get_score_bucket(0, 10), 'incorrect')
        self.assertEquals(render.get_score_bucket(1, 10), 'partial')
        self.assertEquals(render.get_score_bucket(10, 10), 'correct')
        # get_score_bucket calls error cases 'incorrect'
        self.assertEquals(render.get_score_bucket(11, 10), 'incorrect')
        self.assertEquals(render.get_score_bucket(-1, 10), 'incorrect')

    def test_anonymous_modx_dispatch(self):
        dispatch_url = reverse(
            'modx_dispatch',
            args=[
                'edX/toy/2012_Fall',
                'i4x://edX/toy/videosequence/Toy_Videos',
                'goto_position'
            ]
        )
        response = self.client.post(dispatch_url, {'position': 2})
        self.assertEquals(403, response.status_code)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class TestTOC(TestCase):
    """Check the Table of Contents for a course"""
    def setUp(self):

        # Toy courses should be loaded
        self.course_name = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_name)
        self.portal_user = UserFactory()

    def test_toc_toy_from_chapter(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_name, chapter)
        factory = RequestFactory()
        request = factory.get(chapter_url)
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.toy_course.id, self.portal_user, self.toy_course, depth=2)

        expected = ([{'active': True, 'sections':
                      [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True,
                        'format': u'Lecture Sequence', 'due': None, 'active': False},
                       {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True,
                        'format': '', 'due': None, 'active': False},
                       {'url_name': 'video_123456789012', 'display_name': 'video 123456789012', 'graded': True,
                        'format': '', 'due': None, 'active': False},
                       {'url_name': 'video_4f66f493ac8f', 'display_name': 'video 4f66f493ac8f', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'Overview', 'display_name': u'Overview'},
                     {'active': False, 'sections':
                      [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'secret:magic', 'display_name': 'secret:magic'}])

        actual = render.toc_for_course(self.portal_user, request, self.toy_course, chapter, None, model_data_cache)
        self.assertEqual(expected, actual)

    def test_toc_toy_from_section(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_name, chapter)
        section = 'Welcome'
        factory = RequestFactory()
        request = factory.get(chapter_url)
        model_data_cache = ModelDataCache.cache_for_descriptor_descendents(
            self.toy_course.id, self.portal_user, self.toy_course, depth=2)

        expected = ([{'active': True, 'sections':
                      [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True,
                        'format': u'Lecture Sequence', 'due': None, 'active': False},
                       {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True,
                        'format': '', 'due': None, 'active': True},
                       {'url_name': 'video_123456789012', 'display_name': 'video 123456789012', 'graded': True,
                        'format': '', 'due': None, 'active': False},
                       {'url_name': 'video_4f66f493ac8f', 'display_name': 'video 4f66f493ac8f', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'Overview', 'display_name': u'Overview'},
                     {'active': False, 'sections':
                      [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'secret:magic', 'display_name': 'secret:magic'}])

        actual = render.toc_for_course(self.portal_user, request, self.toy_course, chapter, section, model_data_cache)
        self.assertEqual(expected, actual)
