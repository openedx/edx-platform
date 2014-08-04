"""
Test for lms courseware app, module render unit
"""
import ddt
from functools import partial
from mock import MagicMock, patch, Mock
import json

from django.http import Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from xblock.field_data import FieldData
from xblock.runtime import Runtime
from xblock.fields import ScopeIds
from xmodule.lti_module import LTIDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory, check_mongo_calls
from xmodule.x_module import XModuleDescriptor, STUDENT_VIEW
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware import module_render as render
from courseware.courses import get_course_with_access, course_image_url, get_course_info_section
from courseware.model_data import FieldDataCache
from courseware.models import StudentModule
from courseware.tests.factories import StudentModuleFactory, UserFactory, GlobalStaffFactory
from courseware.tests.tests import LoginEnrollmentTestCase

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from courseware.tests.modulestore_config import TEST_DATA_MONGO_MODULESTORE
from courseware.tests.modulestore_config import TEST_DATA_XML_MODULESTORE
from courseware.tests.test_submitting_problems import TestSubmittingProblems

from student.models import anonymous_id_for_user
from lms.lib.xblock.runtime import quote_slashes
from xmodule.modulestore import ModuleStoreEnum


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class ModuleRenderTestCase(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests of courseware.module_render
    """
    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.location = self.course_key.make_usage_key('chapter', 'Overview')
        self.toy_course = modulestore().get_course(self.course_key)
        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactory()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Construct a 'standard' xqueue_callback url
        self.callback_url = reverse('xqueue_callback', kwargs=dict(course_id=self.course_key.to_deprecated_string(),
                                                                   userid=str(self.mock_user.id),
                                                                   mod_id=self.mock_module.id,
                                                                   dispatch=self.dispatch))

    def test_get_module(self):
        self.assertEqual(
            None,
            render.get_module('dummyuser', None, 'invalid location', None)
        )

    def test_module_render_with_jump_to_id(self):
        """
        This test validates that the /jump_to_id/<id> shorthand for intracourse linking works assertIn
        expected. Note there's a HTML element in the 'toy' course with the url_name 'toyjumpto' which
        defines this linkage
        """
        mock_request = MagicMock()
        mock_request.user = self.mock_user

        course = get_course_with_access(self.mock_user, 'load', self.course_key)

        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course_key, self.mock_user, course, depth=2)

        module = render.get_module(
            self.mock_user,
            mock_request,
            self.course_key.make_usage_key('html', 'toyjumpto'),
            field_data_cache,
        )

        # get the rendered HTML output which should have the rewritten link
        html = module.render(STUDENT_VIEW).content

        # See if the url got rewritten to the target link
        # note if the URL mapping changes then this assertion will break
        self.assertIn('/courses/' + self.course_key.to_deprecated_string() + '/jump_to_id/vertical_test', html)

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
            render.xqueue_callback(request, self.course_key, self.mock_user.id, self.mock_module.id, self.dispatch)

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
                render.xqueue_callback(request, self.course_key, self.mock_user.id, self.mock_module.id, self.dispatch)

            # Test with missing xqueue_header
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, data)
                render.xqueue_callback(request, self.course_key, self.mock_user.id, self.mock_module.id, self.dispatch)

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
                self.course_key.to_deprecated_string(),
                quote_slashes(self.course_key.make_usage_key('videosequence', 'Toy_Videos').to_deprecated_string()),
                'xmodule_handler',
                'goto_position'
            ]
        )
        response = self.client.post(dispatch_url, {'position': 2})
        self.assertEquals(403, response.status_code)
        self.assertEquals('Unauthenticated', response.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestHandleXBlockCallback(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test the handle_xblock_callback function
    """

    def setUp(self):
        self.course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        self.location = self.course_key.make_usage_key('chapter', 'Overview')
        self.toy_course = modulestore().get_course(self.course_key)
        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactory()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Construct a 'standard' xqueue_callback url
        self.callback_url = reverse(
            'xqueue_callback', kwargs={
                'course_id': self.course_key.to_deprecated_string(),
                'userid': str(self.mock_user.id),
                'mod_id': self.mock_module.id,
                'dispatch': self.dispatch
            }
        )

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
                self.course_key.to_deprecated_string(),
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
                self.course_key.to_deprecated_string(),
                quote_slashes(self.location.to_deprecated_string()),
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
                self.course_key.to_deprecated_string(),
                quote_slashes(self.location.to_deprecated_string()),
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
            self.course_key.to_deprecated_string(),
            quote_slashes(self.location.to_deprecated_string()),
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
                quote_slashes(self.location.to_deprecated_string()),
                'xmodule_handler',
                'goto_position',
            )

    def test_bad_location(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                self.course_key.to_deprecated_string(),
                quote_slashes(self.course_key.make_usage_key('chapter', 'bad_location').to_deprecated_string()),
                'xmodule_handler',
                'goto_position',
            )

    def test_bad_xmodule_dispatch(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                self.course_key.to_deprecated_string(),
                quote_slashes(self.location.to_deprecated_string()),
                'xmodule_handler',
                'bad_dispatch',
            )

    def test_missing_handler(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                self.course_key.to_deprecated_string(),
                quote_slashes(self.location.to_deprecated_string()),
                'bad_handler',
                'bad_dispatch',
            )


@ddt.ddt
@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestTOC(ModuleStoreTestCase):
    """Check the Table of Contents for a course"""
    def setup_modulestore(self, default_ms, num_finds, num_sends):
        self.course_key = self.create_toy_course()
        self.chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_key, self.chapter)
        factory = RequestFactory()
        self.request = factory.get(chapter_url)
        self.request.user = UserFactory()
        self.modulestore = self.store._get_modulestore_for_courseid(self.course_key)
        with check_mongo_calls(self.modulestore, num_finds, num_sends):
            self.toy_course = self.store.get_course(self.toy_loc, depth=2)
            self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                self.toy_loc, self.request.user, self.toy_course, depth=2)


    @ddt.data((ModuleStoreEnum.Type.mongo, 3, 0), (ModuleStoreEnum.Type.split, 7, 0))
    @ddt.unpack
    def test_toc_toy_from_chapter(self, default_ms, num_finds, num_sends):
        with self.store.default_store(default_ms):
            self.setup_modulestore(default_ms, num_finds, num_sends)
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

            with check_mongo_calls(self.modulestore, 0, 0):
                actual = render.toc_for_course(
                    self.request.user, self.request, self.toy_course, self.chapter, None, self.field_data_cache
                )
        for toc_section in expected:
            self.assertIn(toc_section, actual)

    @ddt.data((ModuleStoreEnum.Type.mongo, 3, 0), (ModuleStoreEnum.Type.split, 7, 0))
    @ddt.unpack
    def test_toc_toy_from_section(self, default_ms, num_finds, num_sends):
        with self.store.default_store(default_ms):
            self.setup_modulestore(default_ms, num_finds, num_sends)
            section = 'Welcome'
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

            actual = render.toc_for_course(self.request.user, self.request, self.toy_course, self.chapter, section, self.field_data_cache)
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
            wrap_xmodule_display=True,
        )
        result_fragment = module.render(STUDENT_VIEW)

        self.assertIn('div class="xblock xblock-student_view xmodule_display xmodule_HtmlModule"', result_fragment.content)

    def test_xmodule_display_wrapper_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            wrap_xmodule_display=False,
        )
        result_fragment = module.render(STUDENT_VIEW)

        self.assertNotIn('div class="xblock xblock-student_view xmodule_display xmodule_HtmlModule"', result_fragment.content)

    def test_static_link_rewrite(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)

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
        )
        result_fragment = module.render(STUDENT_VIEW)

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
            static_asset_path="toy_course_dir",
        )
        result_fragment = module.render(STUDENT_VIEW)
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
        )
        result_fragment = module.render(STUDENT_VIEW)

        self.assertIn(
            '/courses/{course_id}/bar/content'.format(
                course_id=self.course.id.to_deprecated_string()
            ),
            result_fragment.content
        )


class ViewInStudioTest(ModuleStoreTestCase):
    """Tests for the 'View in Studio' link visiblity."""

    def setUp(self):
        """ Set up the user and request that will be used. """
        self.staff_user = GlobalStaffFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.staff_user
        self.request.session = {}
        self.module = None

    def _get_module(self, course_id, descriptor, location):
        """
        Get the module from the course from which to pattern match (or not) the 'View in Studio' buttons
        """
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course_id,
            self.staff_user,
            descriptor
        )

        return render.get_module(
            self.staff_user,
            self.request,
            location,
            field_data_cache,
        )

    def setup_mongo_course(self, course_edit_method='Studio'):
        """ Create a mongo backed course. """
        course = CourseFactory.create(
            course_edit_method=course_edit_method
        )

        descriptor = ItemFactory.create(
            category='vertical',
        )

        child_descriptor = ItemFactory.create(
            category='vertical',
            parent_location=descriptor.location
        )

        self.module = self._get_module(course.id, descriptor, descriptor.location)

        # pylint: disable=W0201
        self.child_module = self._get_module(course.id, child_descriptor, child_descriptor.location)

    def setup_xml_course(self):
        """
        Define the XML backed course to use.
        Toy courses are already loaded in XML and mixed modulestores.
        """
        course_key = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        location = course_key.make_usage_key('chapter', 'Overview')
        descriptor = modulestore().get_item(location)

        self.module = self._get_module(course_key, descriptor, location)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class MongoViewInStudioTest(ViewInStudioTest):
    """Test the 'View in Studio' link visibility in a mongo backed course."""

    def setUp(self):
        super(MongoViewInStudioTest, self).setUp()

    def test_view_in_studio_link_studio_course(self):
        """Regular Studio courses should see 'View in Studio' links."""
        self.setup_mongo_course()
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertIn('View Unit in Studio', result_fragment.content)

    def test_view_in_studio_link_only_in_top_level_vertical(self):
        """Regular Studio courses should not see 'View in Studio' for child verticals of verticals."""
        self.setup_mongo_course()
        # Render the parent vertical, then check that there is only a single "View Unit in Studio" link.
        result_fragment = self.module.render(STUDENT_VIEW)
        # The single "View Unit in Studio" link should appear before the first xmodule vertical definition.
        parts = result_fragment.content.split('xmodule_VerticalModule')
        self.assertEqual(3, len(parts), "Did not find two vertical modules")
        self.assertIn('View Unit in Studio', parts[0])
        self.assertNotIn('View Unit in Studio', parts[1])
        self.assertNotIn('View Unit in Studio', parts[2])

    def test_view_in_studio_link_xml_authored(self):
        """Courses that change 'course_edit_method' setting can hide 'View in Studio' links."""
        self.setup_mongo_course(course_edit_method='XML')
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertNotIn('View Unit in Studio', result_fragment.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class MixedViewInStudioTest(ViewInStudioTest):
    """Test the 'View in Studio' link visibility in a mixed mongo backed course."""

    def setUp(self):
        super(MixedViewInStudioTest, self).setUp()

    def test_view_in_studio_link_mongo_backed(self):
        """Mixed mongo courses that are mongo backed should see 'View in Studio' links."""
        self.setup_mongo_course()
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertIn('View Unit in Studio', result_fragment.content)

    def test_view_in_studio_link_xml_authored(self):
        """Courses that change 'course_edit_method' setting can hide 'View in Studio' links."""
        self.setup_mongo_course(course_edit_method='XML')
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertNotIn('View Unit in Studio', result_fragment.content)

    def test_view_in_studio_link_xml_backed(self):
        """Course in XML only modulestore should not see 'View in Studio' links."""
        self.setup_xml_course()
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertNotIn('View Unit in Studio', result_fragment.content)


@override_settings(MODULESTORE=TEST_DATA_XML_MODULESTORE)
class XmlViewInStudioTest(ViewInStudioTest):
    """Test the 'View in Studio' link visibility in an xml backed course."""

    def setUp(self):
        super(XmlViewInStudioTest, self).setUp()

    def test_view_in_studio_link_xml_backed(self):
        """Course in XML only modulestore should not see 'View in Studio' links."""
        self.setup_xml_course()
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertNotIn('View Unit in Studio', result_fragment.content)


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
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertNotIn('Staff Debug', result_fragment.content)

    def test_staff_debug_info_enabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertIn('Staff Debug', result_fragment.content)

    @patch.dict('django.conf.settings.FEATURES', {'DISPLAY_HISTOGRAMS_TO_STAFF': False})
    def test_histogram_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
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
            )
            module.render(STUDENT_VIEW)
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
            )
            module.render(STUDENT_VIEW)
            self.assertTrue(mock_grade_histogram.called)


PER_COURSE_ANONYMIZED_DESCRIPTORS = (LTIDescriptor, )

# The "set" here is to work around the bug that load_classes returns duplicates for multiply-delcared classes.
PER_STUDENT_ANONYMIZED_DESCRIPTORS = set(
    class_ for (name, class_) in XModuleDescriptor.load_classes()
    if not issubclass(class_, PER_COURSE_ANONYMIZED_DESCRIPTORS)
)


@ddt.ddt
@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestAnonymousStudentId(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test that anonymous_student_id is set correctly across a variety of XBlock types
    """

    def setUp(self):
        self.user = UserFactory()

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    def _get_anonymous_id(self, course_id, xblock_class):
        location = course_id.make_usage_key('dummy_category', 'dummy_name')
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
        # Use the xblock_class's bind_for_student method
        descriptor.bind_for_student = partial(xblock_class.bind_for_student, descriptor)

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

    @ddt.data(*PER_STUDENT_ANONYMIZED_DESCRIPTORS)
    def test_per_student_anonymized_id(self, descriptor_class):
        for course_id in ('MITx/6.00x/2012_Fall', 'MITx/6.00x/2013_Spring'):
            self.assertEquals(
                # This value is set by observation, so that later changes to the student
                # id computation don't break old data
                '5afe5d9bb03796557ee2614f5c9611fb',
                self._get_anonymous_id(SlashSeparatedCourseKey.from_deprecated_string(course_id), descriptor_class)
            )

    @ddt.data(*PER_COURSE_ANONYMIZED_DESCRIPTORS)
    def test_per_course_anonymized_id(self, descriptor_class):
        self.assertEquals(
            # This value is set by observation, so that later changes to the student
            # id computation don't break old data
            'e3b0b940318df9c14be59acb08e78af5',
            self._get_anonymous_id(SlashSeparatedCourseKey('MITx', '6.00x', '2012_Fall'), descriptor_class)
        )

        self.assertEquals(
            # This value is set by observation, so that later changes to the student
            # id computation don't break old data
            'f82b5416c9f54b5ce33989511bb5ef2e',
            self._get_anonymous_id(SlashSeparatedCourseKey('MITx', '6.00x', '2013_Spring'), descriptor_class)
        )


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@patch('track.views.tracker')
class TestModuleTrackingContext(ModuleStoreTestCase):
    """
    Ensure correct tracking information is included in events emitted during XBlock callback handling.
    """

    def setUp(self):
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = {}
        self.course = CourseFactory.create()

        self.problem_xml = OptionResponseXMLFactory().build_xml(
            question_text='The correct answer is Correct',
            num_inputs=2,
            weight=2,
            options=['Correct', 'Incorrect'],
            correct_option='Correct'
        )

    def test_context_contains_display_name(self, mock_tracker):
        problem_display_name = u'Option Response Problem'
        actual_display_name = self.handle_callback_and_get_display_name_from_event(mock_tracker, problem_display_name)
        self.assertEquals(problem_display_name, actual_display_name)

    def handle_callback_and_get_display_name_from_event(self, mock_tracker, problem_display_name=None):
        """
        Creates a fake module, invokes the callback and extracts the display name from the emitted problem_check event.
        """
        descriptor_kwargs = {
            'category': 'problem',
            'data': self.problem_xml
        }
        if problem_display_name:
            descriptor_kwargs['display_name'] = problem_display_name

        descriptor = ItemFactory.create(**descriptor_kwargs)

        render.handle_xblock_callback(
            self.request,
            self.course.id.to_deprecated_string(),
            quote_slashes(descriptor.location.to_deprecated_string()),
            'xmodule_handler',
            'problem_check',
        )

        self.assertEquals(len(mock_tracker.send.mock_calls), 1)
        mock_call = mock_tracker.send.mock_calls[0]
        event = mock_call[1][0]

        self.assertEquals(event['event_type'], 'problem_check')
        return event['context']['module']['display_name']

    def test_missing_display_name(self, mock_tracker):
        actual_display_name = self.handle_callback_and_get_display_name_from_event(mock_tracker)
        self.assertTrue(actual_display_name.startswith('problem'))


class TestXmoduleRuntimeEvent(TestSubmittingProblems):
    """
    Inherit from TestSubmittingProblems to get functionality that set up a course and problems structure
    """

    def setUp(self):
        super(TestXmoduleRuntimeEvent, self).setUp()
        self.homework = self.add_graded_section_to_course('homework')
        self.problem = self.add_dropdown_to_section(self.homework.location, 'p1', 1)
        self.grade_dict = {'value': 0.18, 'max_value': 32, 'user_id': self.student_user.id}
        self.delete_dict = {'value': None, 'max_value': None, 'user_id': self.student_user.id}

    def get_module_for_user(self, user):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, user, self.course, depth=2)

        return render.get_module(  # pylint: disable=protected-access
            user,
            mock_request,
            self.problem.location,
            field_data_cache,
        )._xmodule

    def set_module_grade_using_publish(self, grade_dict):
        """Publish the user's grade, takes grade_dict as input"""
        module = self.get_module_for_user(self.student_user)
        module.system.publish(module, 'grade', grade_dict)
        return module

    def test_xmodule_runtime_publish(self):
        """Tests the publish mechanism"""
        self.set_module_grade_using_publish(self.grade_dict)
        student_module = StudentModule.objects.get(student=self.student_user, module_state_key=self.problem.location)
        self.assertEqual(student_module.grade, self.grade_dict['value'])
        self.assertEqual(student_module.max_grade, self.grade_dict['max_value'])

    def test_xmodule_runtime_publish_delete(self):
        """Test deleting the grade using the publish mechanism"""
        module = self.set_module_grade_using_publish(self.grade_dict)
        module.system.publish(module, 'grade', self.delete_dict)
        student_module = StudentModule.objects.get(student=self.student_user, module_state_key=self.problem.location)
        self.assertIsNone(student_module.grade)
        self.assertIsNone(student_module.max_grade)


class TestRebindModule(TestSubmittingProblems):
    """
    Tests to verify the functionality of rebinding a module.
    Inherit from TestSubmittingProblems to get functionality that set up a course structure
    """
    def setUp(self):
        super(TestRebindModule, self).setUp()
        self.homework = self.add_graded_section_to_course('homework')
        self.lti = ItemFactory.create(category='lti', parent=self.homework)
        self.user = UserFactory.create()
        self.anon_user = AnonymousUser()

    def get_module_for_user(self, user):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, user, self.course, depth=2)

        return render.get_module(  # pylint: disable=protected-access
            user,
            mock_request,
            self.lti.location,
            field_data_cache,
        )._xmodule

    def test_rebind_noauth_module_to_user_not_anonymous(self):
        """
        Tests that an exception is thrown when rebind_noauth_module_to_user is run from a
        module bound to a real user
        """
        module = self.get_module_for_user(self.user)
        user2 = UserFactory()
        user2.id = 2
        with self.assertRaisesRegexp(
            render.LmsModuleRenderError,
            "rebind_noauth_module_to_user can only be called from a module bound to an anonymous user"
        ):
            self.assertTrue(module.system.rebind_noauth_module_to_user(module, user2))

    def test_rebind_noauth_module_to_user_anonymous(self):
        """
        Tests that get_user_module_for_noauth succeeds when rebind_noauth_module_to_user is run from a
        module bound to AnonymousUser
        """
        module = self.get_module_for_user(self.anon_user)
        user2 = UserFactory()
        user2.id = 2
        module.system.rebind_noauth_module_to_user(module, user2)
        self.assertTrue(module)
        self.assertEqual(module.system.anonymous_student_id, anonymous_id_for_user(user2, self.course.id))
        self.assertEqual(module.scope_ids.user_id, user2.id)
        self.assertEqual(module.descriptor.scope_ids.user_id, user2.id)

    @patch('courseware.module_render.make_psychometrics_data_update_handler')
    @patch.dict(settings.FEATURES, {'ENABLE_PSYCHOMETRICS': True})
    def test_psychometrics_anonymous(self, psycho_handler):
        """
        Make sure that noauth modules with anonymous users don't have
        the psychometrics callback bound.
        """
        module = self.get_module_for_user(self.anon_user)
        module.system.rebind_noauth_module_to_user(module, self.anon_user)
        self.assertFalse(psycho_handler.called)
