"""
Test for lms courseware app, module render unit
"""
from mock import MagicMock, patch, Mock
import json

from django.http import Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
import courseware.module_render as render
from courseware.tests.tests import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.model_data import FieldDataCache

from courseware.courses import get_course_with_access, course_image_url, get_course_info_section

from .factories import UserFactory


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class ModuleRenderTestCase(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests of courseware.module_render
    """
    def setUp(self):
        self.location = ['i4x', 'edX', 'toy', 'chapter', 'Overview']
        self.course_id = 'edX/toy/2012_Fall'
        self.toy_course = modulestore().get_course(self.course_id)
        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactory()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Construct a 'standard' xqueue_callback url
        self.callback_url = reverse('xqueue_callback', kwargs=dict(course_id=self.course_id,
                                                                   userid=str(self.mock_user.id),
                                                                   mod_id=self.mock_module.id,
                                                                   dispatch=self.dispatch))

    def test_get_module(self):
        self.assertEqual(
            None,
            render.get_module('dummyuser', None, 'invalid location', None, None)
        )

    def test_module_render_with_jump_to_id(self):
        """
        This test validates that the /jump_to_id/<id> shorthand for intracourse linking works assertIn
        expected. Note there's a HTML element in the 'toy' course with the url_name 'toyjumpto' which
        defines this linkage
        """
        mock_request = MagicMock()
        mock_request.user = self.mock_user

        course = get_course_with_access(self.mock_user, self.course_id, 'load')

        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course_id, self.mock_user, course, depth=2)

        module = render.get_module(
            self.mock_user,
            mock_request,
            ['i4x', 'edX', 'toy', 'html', 'toyjumpto'],
            field_data_cache,
            self.course_id
        )

        # get the rendered HTML output which should have the rewritten link
        html = module.render('student_view').content

        # See if the url got rewritten to the target link
        # note if the URL mapping changes then this assertion will break
        self.assertIn('/courses/' + self.course_id + '/jump_to_id/vertical_test', html)

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
        inputfile = MagicMock()
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
        mock_request_3.user = self.mock_user
        inputfile_2 = MagicMock()
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

    def test_xqueue_callback_success(self):
        """
        Test for happy-path xqueue_callback
        """
        fake_key = 'fake key'
        xqueue_header = json.dumps({'lms_key': fake_key})
        data = {
            'xqueue_header': xqueue_header,
            'xqueue_body': 'hello world',
        }

        # Patch getmodule to return our mock module
        with patch('courseware.module_render.find_target_student_module') as get_fake_module:
            get_fake_module.return_value = self.mock_module
            # call xqueue_callback with our mocked information
            request = self.request_factory.post(self.callback_url, data)
            render.xqueue_callback(request, self.course_id, self.mock_user.id, self.mock_module.id, self.dispatch)

        # Verify that handle ajax is called with the correct data
        request.POST['queuekey'] = fake_key
        self.mock_module.handle_ajax.assert_called_once_with(self.dispatch, request.POST)

    def test_xqueue_callback_missing_header_info(self):
        data = {
            'xqueue_header': '{}',
            'xqueue_body': 'hello world',
        }

        with patch('courseware.module_render.find_target_student_module') as get_fake_module:
            get_fake_module.return_value = self.mock_module
            # Test with missing xqueue data
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, {})
                render.xqueue_callback(request, self.course_id, self.mock_user.id, self.mock_module.id, self.dispatch)

            # Test with missing xqueue_header
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, data)
                render.xqueue_callback(request, self.course_id, self.mock_user.id, self.mock_module.id, self.dispatch)

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


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
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
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.toy_course.id, self.portal_user, self.toy_course, depth=2)

        expected = ([{'active': True, 'sections':
                      [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True,
                        'format': u'Lecture Sequence', 'due': None, 'active': False},
                       {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True,
                        'format': '', 'due': None, 'active': False},
                       {'url_name': 'video_123456789012', 'display_name': 'Test Video', 'graded': True,
                        'format': '', 'due': None, 'active': False},
                       {'url_name': 'video_4f66f493ac8f', 'display_name': 'Video', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'Overview', 'display_name': u'Overview'},
                     {'active': False, 'sections':
                      [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'secret:magic', 'display_name': 'secret:magic'}])

        actual = render.toc_for_course(self.portal_user, request, self.toy_course, chapter, None, field_data_cache)
        for toc_section in expected:
            self.assertIn(toc_section, actual)

    def test_toc_toy_from_section(self):
        chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_name, chapter)
        section = 'Welcome'
        factory = RequestFactory()
        request = factory.get(chapter_url)
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.toy_course.id, self.portal_user, self.toy_course, depth=2)

        expected = ([{'active': True, 'sections':
                      [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True,
                        'format': u'Lecture Sequence', 'due': None, 'active': False},
                       {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True,
                        'format': '', 'due': None, 'active': True},
                       {'url_name': 'video_123456789012', 'display_name': 'Test Video', 'graded': True,
                        'format': '', 'due': None, 'active': False},
                       {'url_name': 'video_4f66f493ac8f', 'display_name': 'Video', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'Overview', 'display_name': u'Overview'},
                     {'active': False, 'sections':
                      [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True,
                        'format': '', 'due': None, 'active': False}],
                      'url_name': 'secret:magic', 'display_name': 'secret:magic'}])

        actual = render.toc_for_course(self.portal_user, request, self.toy_course, chapter, section, field_data_cache)
        for toc_section in expected:
            self.assertIn(toc_section, actual)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestHtmlModifiers(ModuleStoreTestCase):
    """
    Tests to verify that standard modifications to the output of XModule/XBlock
    student_view are taking place
    """
    def setUp(self):
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = {}
        self.course = CourseFactory.create()
        self.content_string = '<p>This is the content<p>'
        self.rewrite_link = '<a href="/static/foo/content">Test rewrite</a>'
        self.rewrite_bad_link = '<img src="/static//file.jpg" />'
        self.course_link = '<a href="/course/bar/content">Test course rewrite</a>'
        self.descriptor = ItemFactory.create(
            category='html',
            data=self.content_string + self.rewrite_link + self.rewrite_bad_link + self.course_link
        )
        self.location = self.descriptor.location
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            self.descriptor
        )

    def test_xmodule_display_wrapper_enabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
            wrap_xmodule_display=True,
        )
        result_fragment = module.render('student_view')

        self.assertIn('section class="xblock xblock-student_view xmodule_display xmodule_HtmlModule"', result_fragment.content)

    def test_xmodule_display_wrapper_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
            wrap_xmodule_display=False,
        )
        result_fragment = module.render('student_view')

        self.assertNotIn('section class="xblock xblock-student_view xmodule_display xmodule_HtmlModule"', result_fragment.content)

    def test_static_link_rewrite(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')

        self.assertIn(
            '/c4x/{org}/{course}/asset/foo_content'.format(
                org=self.course.location.org,
                course=self.course.location.course,
            ),
            result_fragment.content
        )

    def test_static_badlink_rewrite(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')

        self.assertIn(
            '/c4x/{org}/{course}/asset/_file.jpg'.format(
                org=self.course.location.org,
                course=self.course.location.course,
            ),
            result_fragment.content
        )

    def test_static_asset_path_use(self):
        '''
        when a course is loaded with do_import_static=False (see xml_importer.py), then
        static_asset_path is set as an lms kv in course.  That should make static paths
        not be mangled (ie not changed to c4x://).
        '''
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
            static_asset_path="toy_course_dir",
        )
        result_fragment = module.render('student_view')
        self.assertIn('href="/static/toy_course_dir', result_fragment.content)

    def test_course_image(self):
        url = course_image_url(self.course)
        self.assertTrue(url.startswith('/c4x/'))

        self.course.static_asset_path = "toy_course_dir"
        url = course_image_url(self.course)
        self.assertTrue(url.startswith('/static/toy_course_dir/'))
        self.course.static_asset_path = ""

    def test_get_course_info_section(self):
        self.course.static_asset_path = "toy_course_dir"
        get_course_info_section(self.request, self.course, "handouts")
        # NOTE: check handouts output...right now test course seems to have no such content
        # at least this makes sure get_course_info_section returns without exception

    def test_course_link_rewrite(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')

        self.assertIn(
            '/courses/{course_id}/bar/content'.format(
                course_id=self.course.id
            ),
            result_fragment.content
        )

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    def test_histogram(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')

        self.assertIn(
            'Staff Debug',
            result_fragment.content
        )
