"""
Test for lms courseware app, module render unit
"""
from ddt import ddt, data
from mock import MagicMock, patch, Mock
import json

from django.http import Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from xblock.field_data import FieldData
from xblock.runtime import Runtime
from xblock.fields import ScopeIds
from xmodule.lti_module import LTIDescriptor
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory
from xmodule.x_module import XModuleDescriptor

from courseware import module_render as render
from courseware.courses import get_course_with_access, course_image_url, get_course_info_section
from courseware.model_data import FieldDataCache
from courseware.tests.factories import StudentModuleFactory, UserFactory
from courseware.tests.tests import LoginEnrollmentTestCase
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE

from lms.lib.xblock.runtime import quote_slashes


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class ModuleRenderTestCase(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests of courseware.module_render
    """
    def setUp(self):
        self.location = Location('i4x', 'edX', 'toy', 'chapter', 'Overview')
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
            Location('i4x', 'edX', 'toy', 'html', 'toyjumpto'),
            field_data_cache,
            self.course_id
        )

        # get the rendered HTML output which should have the rewritten link
        html = module.render('student_view').content

        # See if the url got rewritten to the target link
        # note if the URL mapping changes then this assertion will break
        self.assertIn('/courses/' + self.course_id + '/jump_to_id/vertical_test', html)


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

    def test_anonymous_handle_xblock_callback(self):
        dispatch_url = reverse(
            'xblock_handler',
            args=[
                'edX/toy/2012_Fall',
                quote_slashes('i4x://edX/toy/videosequence/Toy_Videos'),
                'xmodule_handler',
                'goto_position'
            ]
        )
        response = self.client.post(dispatch_url, {'position': 2})
        self.assertEquals(403, response.status_code)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestHandleXBlockCallback(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test the handle_xblock_callback function
    """

    def setUp(self):
        self.location = Location('i4x', 'edX', 'toy', 'chapter', 'Overview')
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

    def _mock_file(self, name='file', size=10):
        """Create a mock file object for testing uploads"""
        mock_file = MagicMock(
            size=size,
            read=lambda: 'x' * size
        )
        # We can't use `name` as a kwarg to Mock to set the name attribute
        # because mock uses `name` to name the mock itself
        mock_file.name = name
        return mock_file

    def test_invalid_location(self):
        request = self.request_factory.post('dummy_url', data={'position': 1})
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                'dummy/course/id',
                'invalid Location',
                'dummy_handler'
                'dummy_dispatch'
            )

    def test_too_many_files(self):
        request = self.request_factory.post(
            'dummy_url',
            data={'file_id': (self._mock_file(), ) * (settings.MAX_FILEUPLOADS_PER_INPUT + 1)}
        )
        request.user = self.mock_user
        self.assertEquals(
            render.handle_xblock_callback(
                request,
                'dummy/course/id',
                quote_slashes(str(self.location)),
                'dummy_handler'
            ).content,
            json.dumps({
                'success': 'Submission aborted! Maximum %d files may be submitted at once' %
                           settings.MAX_FILEUPLOADS_PER_INPUT
            })
        )

    def test_too_large_file(self):
        inputfile = self._mock_file(size=1 + settings.STUDENT_FILEUPLOAD_MAX_SIZE)
        request = self.request_factory.post(
            'dummy_url',
            data={'file_id': inputfile}
        )
        request.user = self.mock_user
        self.assertEquals(
            render.handle_xblock_callback(
                request,
                'dummy/course/id',
                quote_slashes(str(self.location)),
                'dummy_handler'
            ).content,
            json.dumps({
                'success': 'Submission aborted! Your file "%s" is too large (max size: %d MB)' %
                           (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))
            })
        )

    def test_xmodule_dispatch(self):
        request = self.request_factory.post('dummy_url', data={'position': 1})
        request.user = self.mock_user
        response = render.handle_xblock_callback(
            request,
            self.course_id,
            quote_slashes(str(self.location)),
            'xmodule_handler',
            'goto_position',
        )
        self.assertIsInstance(response, HttpResponse)

    def test_bad_course_id(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                'bad_course_id',
                quote_slashes(str(self.location)),
                'xmodule_handler',
                'goto_position',
            )

    def test_bad_location(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                self.course_id,
                quote_slashes(str(Location('i4x', 'edX', 'toy', 'chapter', 'bad_location'))),
                'xmodule_handler',
                'goto_position',
            )

    def test_bad_xmodule_dispatch(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                self.course_id,
                quote_slashes(str(self.location)),
                'xmodule_handler',
                'bad_dispatch',
            )

    def test_missing_handler(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                self.course_id,
                quote_slashes(str(self.location)),
                'bad_handler',
                'bad_dispatch',
            )


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

        self.assertIn('div class="xblock xblock-student_view xmodule_display xmodule_HtmlModule"', result_fragment.content)

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

        self.assertNotIn('div class="xblock xblock-student_view xmodule_display xmodule_HtmlModule"', result_fragment.content)

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


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@patch.dict('django.conf.settings.FEATURES', {'DISPLAY_DEBUG_INFO_TO_STAFF': True, 'DISPLAY_HISTOGRAMS_TO_STAFF': True})
@patch('courseware.module_render.has_access', Mock(return_value=True))
class TestStaffDebugInfo(ModuleStoreTestCase):
    """Tests to verify that Staff Debug Info panel and histograms are displayed to staff."""

    def setUp(self):
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = {}
        self.course = CourseFactory.create()

        problem_xml = OptionResponseXMLFactory().build_xml(
            question_text='The correct answer is Correct',
            num_inputs=2,
            weight=2,
            options=['Correct', 'Incorrect'],
            correct_option='Correct'
        )
        self.descriptor = ItemFactory.create(
            category='problem',
            data=problem_xml,
            display_name='Option Response Problem'
        )

        self.location = self.descriptor.location
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            self.descriptor
        )

    @patch.dict('django.conf.settings.FEATURES', {'DISPLAY_DEBUG_INFO_TO_STAFF': False})
    def test_staff_debug_info_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')
        self.assertNotIn('Staff Debug', result_fragment.content)

    def test_staff_debug_info_enabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')
        self.assertIn('Staff Debug', result_fragment.content)

    @patch.dict('django.conf.settings.FEATURES', {'DISPLAY_HISTOGRAMS_TO_STAFF': False})
    def test_histogram_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            self.course.id,
        )
        result_fragment = module.render('student_view')
        self.assertNotIn('histrogram', result_fragment.content)

    def test_histogram_enabled_for_unscored_xmodules(self):
        """Histograms should not display for xmodules which are not scored."""

        html_descriptor = ItemFactory.create(
            category='html',
            data='Here are some course details.'
        )
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            self.descriptor
        )
        with patch('xmodule_modifiers.grade_histogram') as mock_grade_histogram:
            mock_grade_histogram.return_value = []
            module = render.get_module(
                self.user,
                self.request,
                html_descriptor.location,
                field_data_cache,
                self.course.id,
            )
            module.render('student_view')
            self.assertFalse(mock_grade_histogram.called)

    def test_histogram_enabled_for_scored_xmodules(self):
        """Histograms should display for xmodules which are scored."""

        StudentModuleFactory.create(
            course_id=self.course.id,
            module_state_key=self.location,
            student=UserFactory(),
            grade=1,
            max_grade=1,
            state="{}",
        )
        with patch('xmodule_modifiers.grade_histogram') as mock_grade_histogram:
            mock_grade_histogram.return_value = []
            module = render.get_module(
                self.user,
                self.request,
                self.location,
                self.field_data_cache,
                self.course.id,
            )
            module.render('student_view')
            self.assertTrue(mock_grade_histogram.called)


PER_COURSE_ANONYMIZED_DESCRIPTORS = (LTIDescriptor, )

PER_STUDENT_ANONYMIZED_DESCRIPTORS = [
    class_ for (name, class_) in XModuleDescriptor.load_classes()
    if not issubclass(class_, PER_COURSE_ANONYMIZED_DESCRIPTORS)
]


@ddt
@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestAnonymousStudentId(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test that anonymous_student_id is set correctly across a variety of XBlock types
    """

    def setUp(self):
        self.user = UserFactory()

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    def _get_anonymous_id(self, course_id, xblock_class):
        location = Location('dummy_org', 'dummy_course', 'dummy_category', 'dummy_name')
        descriptor = Mock(
            spec=xblock_class,
            _field_data=Mock(spec=FieldData),
            location=location,
            static_asset_path=None,
            runtime=Mock(
                spec=Runtime,
                resources_fs=None,
                mixologist=Mock(_mixins=())
            ),
            scope_ids=Mock(spec=ScopeIds),
        )
        if hasattr(xblock_class, 'module_class'):
            descriptor.module_class = xblock_class.module_class

        return render.get_module_for_descriptor_internal(
            self.user,
            descriptor,
            Mock(spec=FieldDataCache),
            course_id,
            Mock(),  # Track Function
            Mock(),  # XQueue Callback Url Prefix
        ).xmodule_runtime.anonymous_student_id

    @data(*PER_STUDENT_ANONYMIZED_DESCRIPTORS)
    def test_per_student_anonymized_id(self, descriptor_class):
        for course_id in ('MITx/6.00x/2012_Fall', 'MITx/6.00x/2013_Spring'):
            self.assertEquals(
                # This value is set by observation, so that later changes to the student
                # id computation don't break old data
                '5afe5d9bb03796557ee2614f5c9611fb',
                self._get_anonymous_id(course_id, descriptor_class)
            )

    @data(*PER_COURSE_ANONYMIZED_DESCRIPTORS)
    def test_per_course_anonymized_id(self, descriptor_class):
        self.assertEquals(
            # This value is set by observation, so that later changes to the student
            # id computation don't break old data
            'e3b0b940318df9c14be59acb08e78af5',
            self._get_anonymous_id('MITx/6.00x/2012_Fall', descriptor_class)
        )

        self.assertEquals(
            # This value is set by observation, so that later changes to the student
            # id computation don't break old data
            'f82b5416c9f54b5ce33989511bb5ef2e',
            self._get_anonymous_id('MITx/6.00x/2013_Spring', descriptor_class)
        )
