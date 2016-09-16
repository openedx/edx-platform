# -*- coding: utf-8 -*-
"""
Test for lms courseware app, module render unit
"""
import ddt
import itertools
import json
from nose.plugins.attrib import attr
from functools import partial

from bson import ObjectId
from django.http import Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.contrib.auth.models import AnonymousUser
from mock import MagicMock, patch, Mock
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from pyquery import PyQuery
from courseware.module_render import hash_resource
from xblock.field_data import FieldData
from xblock.runtime import Runtime
from xblock.fields import ScopeIds
from xblock.core import XBlock
from xblock.fragment import Fragment

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from courseware import module_render as render
from courseware.courses import get_course_with_access, course_image_url, get_course_info_section
from courseware.field_overrides import OverrideFieldData
from courseware.model_data import FieldDataCache
from courseware.module_render import hash_resource, get_module_for_descriptor
from courseware.models import StudentModule
from courseware.tests.factories import StudentModuleFactory, UserFactory, GlobalStaffFactory, StaffFactory, InstructorFactory
from courseware.tests.tests import LoginEnrollmentTestCase
from courseware.tests.test_submitting_problems import TestSubmittingProblems
from lms.djangoapps.lms_xblock.runtime import quote_slashes
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from student.models import anonymous_id_for_user
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MIXED_TOY_MODULESTORE,
    TEST_DATA_XML_MODULESTORE,
)
from xmodule.lti_module import LTIDescriptor
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ItemFactory, CourseFactory, ToyCourseFactory, check_mongo_calls
from xmodule.x_module import XModuleDescriptor, XModule, STUDENT_VIEW, CombinedSystem

from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.credit.api import (
    set_credit_requirements,
    set_credit_requirement_status
)

from edx_proctoring.api import (
    create_exam,
    create_exam_attempt,
    update_attempt_status
)
from edx_proctoring.runtime import set_runtime_service
from edx_proctoring.tests.test_services import MockCreditService

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


@XBlock.needs("field-data")
@XBlock.needs("i18n")
@XBlock.needs("fs")
@XBlock.needs("user")
class PureXBlock(XBlock):
    """
    Pure XBlock to use in tests.
    """
    pass


class EmptyXModule(XModule):  # pylint: disable=abstract-method
    """
    Empty XModule for testing with no dependencies.
    """
    pass


class EmptyXModuleDescriptor(XModuleDescriptor):  # pylint: disable=abstract-method
    """
    Empty XModule for testing with no dependencies.
    """
    module_class = EmptyXModule


class GradedStatelessXBlock(XBlock):
    """
    This XBlock exists to test grade storage for blocks that don't store
    student state in a scoped field.
    """

    @XBlock.json_handler
    def set_score(self, json_data, suffix):  # pylint: disable=unused-argument
        """
        Set the score for this testing XBlock.
        """
        self.runtime.publish(
            self,
            'grade',
            {
                'value': json_data['grade'],
                'max_value': 1
            }
        )


@attr('shard_1')
@ddt.ddt
class ModuleRenderTestCase(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests of courseware.module_render
    """
    # TODO: this test relies on the specific setup of the toy course.
    # It should be rewritten to build the course it needs and then test that.
    def setUp(self):
        """
        Set up the course and user context
        """
        super(ModuleRenderTestCase, self).setUp()

        self.course_key = ToyCourseFactory.create().id
        self.toy_course = modulestore().get_course(self.course_key)
        self.mock_user = UserFactory()
        self.request_factory = RequestFactory()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Construct a 'standard' xqueue_callback url
        self.callback_url = reverse(
            'xqueue_callback',
            kwargs=dict(
                course_id=self.course_key.to_deprecated_string(),
                userid=str(self.mock_user.id),
                mod_id=self.mock_module.id,
                dispatch=self.dispatch
            )
        )

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

    FEATURES_WITH_EMAIL = settings.FEATURES.copy()
    FEATURES_WITH_EMAIL['SEND_USERS_EMAILADDR_WITH_CODERESPONSE'] = True

    @override_settings(FEATURES=FEATURES_WITH_EMAIL)
    def test_module_populated_with_user_email(self):
        """
        This tests that the module's system knows about the user's email when the appropriate flag is
        set in LMS settings
        """
        mock_request = MagicMock()
        mock_request.user = self.mock_user
        course = get_course_with_access(self.mock_user, 'load', self.course_key)

        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.toy_course.id, self.mock_user, course, depth=2)

        module = render.get_module(
            self.mock_user,
            mock_request,
            self.course_key.make_usage_key('chapter', 'Overview'),
            field_data_cache,
        )
        self.assertTrue(module.xmodule_runtime.send_users_emailaddr_with_coderesponse)
        self.assertEqual(module.xmodule_runtime.deanonymized_user_email, self.mock_user.email)

    def test_module_not_populated_with_user_email(self):
        """
        This tests that the module's system DOES NOT know about the user's email when the appropriate flag is NOT
        set in LMS settings, which is the default
        """
        mock_request = MagicMock()
        mock_request.user = self.mock_user
        course = get_course_with_access(self.mock_user, 'load', self.course_key)

        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.toy_course.id, self.mock_user, course, depth=2)

        module = render.get_module(
            self.mock_user,
            mock_request,
            self.course_key.make_usage_key('chapter', 'Overview'),
            field_data_cache,
        )
        self.assertFalse(hasattr(module.xmodule_runtime, 'send_users_emailaddr_with_coderesponse'))
        self.assertFalse(hasattr(module.xmodule_runtime, 'deanonymized_user_email'))

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
        with patch('courseware.module_render.load_single_xblock', return_value=self.mock_module):
            # call xqueue_callback with our mocked information
            request = self.request_factory.post(self.callback_url, data)
            render.xqueue_callback(
                request,
                unicode(self.course_key),
                self.mock_user.id,
                self.mock_module.id,
                self.dispatch
            )

        # Verify that handle ajax is called with the correct data
        request.POST['queuekey'] = fake_key
        self.mock_module.handle_ajax.assert_called_once_with(self.dispatch, request.POST)

    def test_xqueue_callback_missing_header_info(self):
        data = {
            'xqueue_header': '{}',
            'xqueue_body': 'hello world',
        }

        with patch('courseware.module_render.load_single_xblock', return_value=self.mock_module):
            # Test with missing xqueue data
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, {})
                render.xqueue_callback(
                    request,
                    unicode(self.course_key),
                    self.mock_user.id,
                    self.mock_module.id,
                    self.dispatch
                )

            # Test with missing xqueue_header
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, data)
                render.xqueue_callback(
                    request,
                    unicode(self.course_key),
                    self.mock_user.id,
                    self.mock_module.id,
                    self.dispatch
                )

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

    def test_missing_position_handler(self):
        """
        Test that sending POST request without or invalid position argument don't raise server error
        """
        self.client.login(username=self.mock_user.username, password="test")
        dispatch_url = reverse(
            'xblock_handler',
            args=[
                self.course_key.to_deprecated_string(),
                quote_slashes(self.course_key.make_usage_key('videosequence', 'Toy_Videos').to_deprecated_string()),
                'xmodule_handler',
                'goto_position'
            ]
        )
        response = self.client.post(dispatch_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content), {'success': True})

        response = self.client.post(dispatch_url, {'position': ''})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content), {'success': True})

        response = self.client.post(dispatch_url, {'position': '-1'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content), {'success': True})

        response = self.client.post(dispatch_url, {'position': "string"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content), {'success': True})

        response = self.client.post(dispatch_url, {'position': u"Φυσικά"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content), {'success': True})

        response = self.client.post(dispatch_url, {'position': None})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content), {'success': True})

    @ddt.data('pure', 'vertical')
    @XBlock.register_temp_plugin(PureXBlock, identifier='pure')
    def test_rebinding_same_user(self, block_type):
        request = self.request_factory.get('')
        request.user = self.mock_user
        course = CourseFactory()
        descriptor = ItemFactory(category=block_type, parent=course)
        field_data_cache = FieldDataCache([self.toy_course, descriptor], self.toy_course.id, self.mock_user)
        # This is verifying that caching doesn't cause an error during get_module_for_descriptor, which
        # is why it calls the method twice identically.
        render.get_module_for_descriptor(
            self.mock_user,
            request,
            descriptor,
            field_data_cache,
            self.toy_course.id,
            course=self.toy_course
        )
        render.get_module_for_descriptor(
            self.mock_user,
            request,
            descriptor,
            field_data_cache,
            self.toy_course.id,
            course=self.toy_course
        )

    @override_settings(FIELD_OVERRIDE_PROVIDERS=(
        'ccx.overrides.CustomCoursesForEdxOverrideProvider',
    ))
    def test_rebind_different_users_ccx(self):
        """
        This tests the rebinding a descriptor to a student does not result
        in overly nested _field_data when CCX is enabled.
        """
        request = self.request_factory.get('')
        request.user = self.mock_user
        course = CourseFactory.create(enable_ccx=True)

        descriptor = ItemFactory(category='html', parent=course)
        field_data_cache = FieldDataCache(
            [course, descriptor], course.id, self.mock_user
        )

        # grab what _field_data was originally set to
        original_field_data = descriptor._field_data  # pylint: disable=protected-access, no-member

        render.get_module_for_descriptor(
            self.mock_user, request, descriptor, field_data_cache, course.id, course=course
        )

        # check that _unwrapped_field_data is the same as the original
        # _field_data, but now _field_data as been reset.
        # pylint: disable=protected-access, no-member
        self.assertIs(descriptor._unwrapped_field_data, original_field_data)
        self.assertIsNot(descriptor._unwrapped_field_data, descriptor._field_data)

        # now bind this module to a few other students
        for user in [UserFactory(), UserFactory(), UserFactory()]:
            render.get_module_for_descriptor(
                user,
                request,
                descriptor,
                field_data_cache,
                course.id,
                course=course
            )

        # _field_data should now be wrapped by LmsFieldData
        # pylint: disable=protected-access, no-member
        self.assertIsInstance(descriptor._field_data, LmsFieldData)

        # the LmsFieldData should now wrap OverrideFieldData
        self.assertIsInstance(
            # pylint: disable=protected-access, no-member
            descriptor._field_data._authored_data._source,
            OverrideFieldData
        )

        # the OverrideFieldData should point to the original unwrapped field_data
        self.assertIs(
            # pylint: disable=protected-access, no-member
            descriptor._field_data._authored_data._source.fallback,
            descriptor._unwrapped_field_data
        )

    def test_hash_resource(self):
        """
        Ensure that the resource hasher works and does not fail on unicode,
        decoded or otherwise.
        """
        resources = ['ASCII text', u'❄ I am a special snowflake.', "❄ So am I, but I didn't tell you."]
        self.assertEqual(hash_resource(resources), 'a76e27c8e80ca3efd7ce743093aa59e0')


@attr('shard_1')
class TestHandleXBlockCallback(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test the handle_xblock_callback function
    """

    def setUp(self):
        super(TestHandleXBlockCallback, self).setUp()

        self.course_key = ToyCourseFactory.create().id
        self.location = self.course_key.make_usage_key('chapter', 'Overview')
        self.toy_course = modulestore().get_course(self.course_key)
        self.mock_user = UserFactory.create()
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
            }, indent=2)
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
            }, indent=2)
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

    @XBlock.register_temp_plugin(GradedStatelessXBlock, identifier='stateless_scorer')
    def test_score_without_student_state(self):
        course = CourseFactory.create()
        block = ItemFactory.create(category='stateless_scorer', parent=course)

        request = self.request_factory.post(
            'dummy_url',
            data=json.dumps({"grade": 0.75}),
            content_type='application/json'
        )
        request.user = self.mock_user

        response = render.handle_xblock_callback(
            request,
            unicode(course.id),
            quote_slashes(unicode(block.scope_ids.usage_id)),
            'set_score',
            '',
        )
        self.assertEquals(response.status_code, 200)
        student_module = StudentModule.objects.get(
            student=self.mock_user,
            module_state_key=block.scope_ids.usage_id,
        )
        self.assertEquals(student_module.grade, 0.75)
        self.assertEquals(student_module.max_grade, 1)

    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_XBLOCK_VIEW_ENDPOINT': True})
    def test_xblock_view_handler(self):
        args = [
            'edX/toy/2012_Fall',
            quote_slashes('i4x://edX/toy/videosequence/Toy_Videos'),
            'student_view'
        ]
        xblock_view_url = reverse(
            'xblock_view',
            args=args
        )

        request = self.request_factory.get(xblock_view_url)
        request.user = self.mock_user
        response = render.xblock_view(request, *args)
        self.assertEquals(200, response.status_code)

        expected = ['csrf_token', 'html', 'resources']
        content = json.loads(response.content)
        for section in expected:
            self.assertIn(section, content)
        doc = PyQuery(content['html'])
        self.assertEquals(len(doc('div.xblock-student_view-videosequence')), 1)


@attr('shard_1')
@ddt.ddt
class TestTOC(ModuleStoreTestCase):
    """Check the Table of Contents for a course"""
    def setup_request_and_course(self, num_finds, num_sends):
        """
        Sets up the toy course in the modulestore and the request object.
        """
        self.course_key = ToyCourseFactory.create().id  # pylint: disable=attribute-defined-outside-init
        self.chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_key, self.chapter)
        factory = RequestFactory()
        self.request = factory.get(chapter_url)
        self.request.user = UserFactory()
        self.modulestore = self.store._get_modulestore_for_courselike(self.course_key)  # pylint: disable=protected-access, attribute-defined-outside-init
        with self.modulestore.bulk_operations(self.course_key):
            with check_mongo_calls(num_finds, num_sends):
                self.toy_course = self.store.get_course(self.course_key, depth=2)  # pylint: disable=attribute-defined-outside-init
                self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                    self.course_key, self.request.user, self.toy_course, depth=2
                )

    # Mongo makes 3 queries to load the course to depth 2:
    #     - 1 for the course
    #     - 1 for its children
    #     - 1 for its grandchildren
    # Split makes 6 queries to load the course to depth 2:
    #     - load the structure
    #     - load 5 definitions
    # Split makes 5 queries to render the toc:
    #     - it loads the active version at the start of the bulk operation
    #     - it loads 4 definitions, because it instantiates 4 VideoModules
    #       each of which access a Scope.content field in __init__
    @ddt.data((ModuleStoreEnum.Type.mongo, 3, 0, 0), (ModuleStoreEnum.Type.split, 6, 0, 5))
    @ddt.unpack
    def test_toc_toy_from_chapter(self, default_ms, setup_finds, setup_sends, toc_finds):
        with self.store.default_store(default_ms):
            self.setup_request_and_course(setup_finds, setup_sends)

            expected = ([{'active': True, 'sections':
                          [{'url_name': 'Toy_Videos', 'display_name': u'Toy Videos', 'graded': True,
                            'format': u'Lecture Sequence', 'due': None, 'active': False},
                           {'url_name': 'Welcome', 'display_name': u'Welcome', 'graded': True,
                            'format': '', 'due': None, 'active': False},
                           {'url_name': 'video_123456789012', 'display_name': 'Test Video', 'graded': True,
                            'format': '', 'due': None, 'active': False},
                           {'url_name': 'video_4f66f493ac8f', 'display_name': 'Video', 'graded': True,
                            'format': '', 'due': None, 'active': False}],
                          'url_name': 'Overview', 'display_name': u'Overview', 'display_id': u'overview'},
                         {'active': False, 'sections':
                          [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True,
                            'format': '', 'due': None, 'active': False}],
                          'url_name': 'secret:magic', 'display_name': 'secret:magic', 'display_id': 'secretmagic'}])

            course = self.store.get_course(self.toy_course.id, depth=2)
            with check_mongo_calls(toc_finds):
                actual = render.toc_for_course(
                    self.request.user, self.request, course, self.chapter, None, self.field_data_cache
                )
        for toc_section in expected:
            self.assertIn(toc_section, actual)

    # Mongo makes 3 queries to load the course to depth 2:
    #     - 1 for the course
    #     - 1 for its children
    #     - 1 for its grandchildren
    # Split makes 6 queries to load the course to depth 2:
    #     - load the structure
    #     - load 5 definitions
    # Split makes 5 queries to render the toc:
    #     - it loads the active version at the start of the bulk operation
    #     - it loads 4 definitions, because it instantiates 4 VideoModules
    #       each of which access a Scope.content field in __init__
    @ddt.data((ModuleStoreEnum.Type.mongo, 3, 0, 0), (ModuleStoreEnum.Type.split, 6, 0, 5))
    @ddt.unpack
    def test_toc_toy_from_section(self, default_ms, setup_finds, setup_sends, toc_finds):
        with self.store.default_store(default_ms):
            self.setup_request_and_course(setup_finds, setup_sends)
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
                          'url_name': 'Overview', 'display_name': u'Overview', 'display_id': u'overview'},
                         {'active': False, 'sections':
                          [{'url_name': 'toyvideo', 'display_name': 'toyvideo', 'graded': True,
                            'format': '', 'due': None, 'active': False}],
                          'url_name': 'secret:magic', 'display_name': 'secret:magic', 'display_id': 'secretmagic'}])

            with check_mongo_calls(toc_finds):
                actual = render.toc_for_course(
                    self.request.user, self.request, self.toy_course, self.chapter, section, self.field_data_cache
                )
            for toc_section in expected:
                self.assertIn(toc_section, actual)


@attr('shard_1')
@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True})
class TestProctoringRendering(ModuleStoreTestCase):
    """Check the Table of Contents for a course"""
    def setUp(self):
        """
        Set up the initial mongo datastores
        """
        super(TestProctoringRendering, self).setUp()
        self.course_key = ToyCourseFactory.create().id
        self.chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_key, self.chapter)
        factory = RequestFactory()
        self.request = factory.get(chapter_url)
        self.request.user = UserFactory()
        self.modulestore = self.store._get_modulestore_for_courselike(self.course_key)  # pylint: disable=protected-access
        with self.modulestore.bulk_operations(self.course_key):
            self.toy_course = self.store.get_course(self.course_key, depth=2)
            self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                self.course_key, self.request.user, self.toy_course, depth=2
            )

    @ddt.data(
        ('honor', False, None, None),
        (
            'honor',
            True,
            'eligible',
            {
                'status': 'eligible',
                'short_description': 'Ungraded Practice Exam',
                'suggested_icon': '',
                'in_completed_state': False
            }
        ),
        (
            'honor',
            True,
            'submitted',
            {
                'status': 'submitted',
                'short_description': 'Practice Exam Completed',
                'suggested_icon': 'fa-check',
                'in_completed_state': True
            }
        ),
        (
            'honor',
            True,
            'error',
            {
                'status': 'error',
                'short_description': 'Practice Exam Failed',
                'suggested_icon': 'fa-exclamation-triangle',
                'in_completed_state': True
            }
        ),
        (
            'verified',
            False,
            None,
            {
                'status': 'eligible',
                'short_description': 'Proctored Option Available',
                'suggested_icon': 'fa-pencil-square-o',
                'in_completed_state': False
            }
        ),
        (
            'verified',
            False,
            'declined',
            {
                'status': 'declined',
                'short_description': 'Taking As Open Exam',
                'suggested_icon': 'fa-pencil-square-o',
                'in_completed_state': False
            }
        ),
        (
            'verified',
            False,
            'submitted',
            {
                'status': 'submitted',
                'short_description': 'Pending Session Review',
                'suggested_icon': 'fa-spinner fa-spin',
                'in_completed_state': True
            }
        ),
        (
            'verified',
            False,
            'verified',
            {
                'status': 'verified',
                'short_description': 'Passed Proctoring',
                'suggested_icon': 'fa-check',
                'in_completed_state': True
            }
        ),
        (
            'verified',
            False,
            'rejected',
            {
                'status': 'rejected',
                'short_description': 'Failed Proctoring',
                'suggested_icon': 'fa-exclamation-triangle',
                'in_completed_state': True
            }
        ),
        (
            'verified',
            False,
            'error',
            {
                'status': 'error',
                'short_description': 'Failed Proctoring',
                'suggested_icon': 'fa-exclamation-triangle',
                'in_completed_state': True
            }
        ),
    )
    @ddt.unpack
    def test_proctored_exam_toc(self, enrollment_mode, is_practice_exam,
                                attempt_status, expected):
        """
        Generate TOC for a course with a single chapter/sequence which contains proctored exam
        """
        self._setup_test_data(enrollment_mode, is_practice_exam, attempt_status)

        actual = render.toc_for_course(
            self.request.user,
            self.request,
            self.toy_course,
            self.chapter,
            'Toy_Videos',
            self.field_data_cache
        )
        section_actual = self._find_section(actual, 'Overview', 'Toy_Videos')

        if expected:
            self.assertIn(expected, [section_actual['proctoring']])
        else:
            # we expect there not to be a 'proctoring' key in the dict
            self.assertNotIn('proctoring', section_actual)

    @ddt.data(
        (
            'honor',
            True,
            None,
            'Try a proctored exam',
            True
        ),
        (
            'honor',
            True,
            'submitted',
            'You have submitted this practice proctored exam',
            False
        ),
        (
            'honor',
            True,
            'error',
            'There was a problem with your practice proctoring session',
            True
        ),
        (
            'verified',
            False,
            None,
            'This exam is proctored',
            False
        ),
        (
            'verified',
            False,
            'submitted',
            'You have submitted this proctored exam for review',
            True
        ),
        (
            'verified',
            False,
            'verified',
            'Your proctoring session was reviewed and passed all requirements',
            False
        ),
        (
            'verified',
            False,
            'rejected',
            'Your proctoring session was reviewed and did not pass requirements',
            True
        ),
        (
            'verified',
            False,
            'error',
            'There was a problem with your proctoring session',
            False
        ),
    )
    @ddt.unpack
    def test_render_proctored_exam(self, enrollment_mode, is_practice_exam,
                                   attempt_status, expected, with_credit_context):
        """
        Verifies gated content from the student view rendering of a sequence
        this is labeled as a proctored exam
        """

        usage_key = self._setup_test_data(enrollment_mode, is_practice_exam, attempt_status)

        # initialize some credit requirements, if so then specify
        if with_credit_context:
            credit_course = CreditCourse(course_key=self.course_key, enabled=True)
            credit_course.save()
            set_credit_requirements(
                self.course_key,
                [
                    {
                        'namespace': 'reverification',
                        'name': 'reverification-1',
                        'display_name': 'ICRV1',
                        'criteria': {},
                    },
                    {
                        'namespace': 'proctored-exam',
                        'name': 'Exam1',
                        'display_name': 'A Proctored Exam',
                        'criteria': {}
                    }
                ]
            )

            set_credit_requirement_status(
                self.request.user.username,
                self.course_key,
                'reverification',
                'ICRV1'
            )

        module = render.get_module(
            self.request.user,
            self.request,
            usage_key,
            self.field_data_cache,
            wrap_xmodule_display=True,
        )
        content = module.render(STUDENT_VIEW).content

        self.assertIn(expected, content)

    def _setup_test_data(self, enrollment_mode, is_practice_exam, attempt_status):
        """
        Helper method to consolidate some courseware/proctoring/credit
        test harness data
        """
        usage_key = self.course_key.make_usage_key('videosequence', 'Toy_Videos')
        sequence = self.modulestore.get_item(usage_key)

        sequence.is_time_limited = True
        sequence.is_proctored_exam = True
        sequence.is_practice_exam = is_practice_exam

        self.modulestore.update_item(sequence, self.user.id)

        self.toy_course = self.modulestore.get_course(self.course_key)

        # refresh cache after update
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course_key, self.request.user, self.toy_course, depth=2
        )

        set_runtime_service(
            'credit',
            MockCreditService(enrollment_mode=enrollment_mode)
        )

        exam_id = create_exam(
            course_id=unicode(self.course_key),
            content_id=unicode(sequence.location),
            exam_name='foo',
            time_limit_mins=10,
            is_proctored=True,
            is_practice_exam=is_practice_exam
        )

        if attempt_status:
            create_exam_attempt(exam_id, self.request.user.id, taking_as_proctored=True)
            update_attempt_status(exam_id, self.request.user.id, attempt_status)

        return usage_key

    def _find_url_name(self, toc, url_name):
        """
        Helper to return the dict TOC section associated with a Chapter of url_name
        """

        for entry in toc:
            if entry['url_name'] == url_name:
                return entry

        return None

    def _find_section(self, toc, chapter_url_name, section_url_name):
        """
        Helper to return the dict TOC section associated with a section of url_name
        """

        chapter = self._find_url_name(toc, chapter_url_name)
        if chapter:
            return self._find_url_name(chapter['sections'], section_url_name)

        return None


@attr('shard_1')
@ddt.ddt
class TestHtmlModifiers(ModuleStoreTestCase):
    """
    Tests to verify that standard modifications to the output of XModule/XBlock
    student_view are taking place
    """
    def setUp(self):
        super(TestHtmlModifiers, self).setUp()
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

        self.assertEquals(len(PyQuery(result_fragment.content)('div.xblock.xblock-student_view.xmodule_HtmlModule')), 1)

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

    @override_settings(DEFAULT_COURSE_ABOUT_IMAGE_URL='test.png')
    @override_settings(STATIC_URL='static/')
    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_course_image_for_split_course(self, store):
        """
        for split courses if course_image is empty then course_image_url will be
        the default image url defined in settings
        """
        self.course = CourseFactory.create(default_store=store)
        self.course.course_image = ''

        url = course_image_url(self.course)
        self.assertEqual('static/test.png', url)

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


class XBlockWithJsonInitData(XBlock):
    """
    Pure XBlock to use in tests, with JSON init data.
    """
    the_json_data = None

    def student_view(self, context=None):       # pylint: disable=unused-argument
        """
        A simple view that returns just enough to test.
        """
        frag = Fragment(u"Hello there!")
        frag.add_javascript(u'alert("Hi!");')
        frag.initialize_js('ThumbsBlock', self.the_json_data)
        return frag


@attr('shard_1')
@ddt.ddt
class JsonInitDataTest(ModuleStoreTestCase):
    """Tests for JSON data injected into the JS init function."""

    @ddt.data(
        ({'a': 17}, '''{"a": 17}'''),
        ({'xss': '</script>alert("XSS")'}, r'''{"xss": "<\/script>alert(\"XSS\")"}'''),
    )
    @ddt.unpack
    @XBlock.register_temp_plugin(XBlockWithJsonInitData, identifier='withjson')
    def test_json_init_data(self, json_data, json_output):
        XBlockWithJsonInitData.the_json_data = json_data
        mock_user = UserFactory()
        mock_request = MagicMock()
        mock_request.user = mock_user
        course = CourseFactory()
        descriptor = ItemFactory(category='withjson', parent=course)
        field_data_cache = FieldDataCache([course, descriptor], course.id, mock_user)   # pylint: disable=no-member
        module = render.get_module_for_descriptor(
            mock_user,
            mock_request,
            descriptor,
            field_data_cache,
            course.id,                          # pylint: disable=no-member
            course=course
        )
        html = module.render(STUDENT_VIEW).content
        self.assertIn(json_output, html)
        # No matter what data goes in, there should only be one close-script tag.
        self.assertEqual(html.count("</script>"), 1)


class ViewInStudioTest(ModuleStoreTestCase):
    """Tests for the 'View in Studio' link visiblity."""

    def setUp(self):
        """ Set up the user and request that will be used. """
        super(ViewInStudioTest, self).setUp()
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
            parent_location=course.location,
        )

        child_descriptor = ItemFactory.create(
            category='vertical',
            parent_location=descriptor.location
        )

        self.module = self._get_module(course.id, descriptor, descriptor.location)

        # pylint: disable=attribute-defined-outside-init
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


@attr('shard_1')
class MongoViewInStudioTest(ViewInStudioTest):
    """Test the 'View in Studio' link visibility in a mongo backed course."""

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
        parts = result_fragment.content.split('data-block-type="vertical"')
        self.assertEqual(3, len(parts), "Did not find two vertical blocks")
        self.assertIn('View Unit in Studio', parts[0])
        self.assertNotIn('View Unit in Studio', parts[1])
        self.assertNotIn('View Unit in Studio', parts[2])

    def test_view_in_studio_link_xml_authored(self):
        """Courses that change 'course_edit_method' setting can hide 'View in Studio' links."""
        self.setup_mongo_course(course_edit_method='XML')
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertNotIn('View Unit in Studio', result_fragment.content)


@attr('shard_1')
class MixedViewInStudioTest(ViewInStudioTest):
    """Test the 'View in Studio' link visibility in a mixed mongo backed course."""

    MODULESTORE = TEST_DATA_MIXED_TOY_MODULESTORE

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


@attr('shard_1')
class XmlViewInStudioTest(ViewInStudioTest):
    """Test the 'View in Studio' link visibility in an xml backed course."""
    MODULESTORE = TEST_DATA_XML_MODULESTORE

    def test_view_in_studio_link_xml_backed(self):
        """Course in XML only modulestore should not see 'View in Studio' links."""
        self.setup_xml_course()
        result_fragment = self.module.render(STUDENT_VIEW)
        self.assertNotIn('View Unit in Studio', result_fragment.content)


@attr('shard_1')
@patch.dict('django.conf.settings.FEATURES', {'DISPLAY_DEBUG_INFO_TO_STAFF': True, 'DISPLAY_HISTOGRAMS_TO_STAFF': True})
@patch('courseware.module_render.has_access', Mock(return_value=True))
class TestStaffDebugInfo(ModuleStoreTestCase):
    """Tests to verify that Staff Debug Info panel and histograms are displayed to staff."""

    def setUp(self):
        super(TestStaffDebugInfo, self).setUp()
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
        with patch('openedx.core.lib.xblock_utils.grade_histogram') as mock_grade_histogram:
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
        with patch('openedx.core.lib.xblock_utils.grade_histogram') as mock_grade_histogram:
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


@attr('shard_1')
@ddt.ddt
class TestAnonymousStudentId(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test that anonymous_student_id is set correctly across a variety of XBlock types
    """

    def setUp(self):
        super(TestAnonymousStudentId, self).setUp(create_user=False)
        self.user = UserFactory()
        self.course_key = ToyCourseFactory.create().id
        self.course = modulestore().get_course(self.course_key)

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    def _get_anonymous_id(self, course_id, xblock_class):
        location = course_id.make_usage_key('dummy_category', 'dummy_name')
        descriptor = Mock(
            spec=xblock_class,
            _field_data=Mock(spec=FieldData, name='field_data'),
            location=location,
            static_asset_path=None,
            _runtime=Mock(
                spec=Runtime,
                resources_fs=None,
                mixologist=Mock(_mixins=(), name='mixologist'),
                name='runtime',
            ),
            scope_ids=Mock(spec=ScopeIds),
            name='descriptor',
            _field_data_cache={},
            _dirty_fields={},
            fields={},
            days_early_for_beta=None,
        )
        descriptor.runtime = CombinedSystem(descriptor._runtime, None)  # pylint: disable=protected-access
        # Use the xblock_class's bind_for_student method
        descriptor.bind_for_student = partial(xblock_class.bind_for_student, descriptor)

        if hasattr(xblock_class, 'module_class'):
            descriptor.module_class = xblock_class.module_class

        return render.get_module_for_descriptor_internal(
            user=self.user,
            descriptor=descriptor,
            student_data=Mock(spec=FieldData, name='student_data'),
            course_id=course_id,
            track_function=Mock(name='track_function'),  # Track Function
            xqueue_callback_url_prefix=Mock(name='xqueue_callback_url_prefix'),  # XQueue Callback Url Prefix
            request_token='request_token',
            course=self.course,
        ).xmodule_runtime.anonymous_student_id

    @ddt.data(*PER_STUDENT_ANONYMIZED_DESCRIPTORS)
    def test_per_student_anonymized_id(self, descriptor_class):
        for course_id in ('MITx/6.00x/2012_Fall', 'MITx/6.00x/2013_Spring'):
            self.assertEquals(
                # This value is set by observation, so that later changes to the student
                # id computation don't break old data
                '5afe5d9bb03796557ee2614f5c9611fb',
                self._get_anonymous_id(CourseKey.from_string(course_id), descriptor_class)
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


@attr('shard_1')
@patch('track.views.tracker')
class TestModuleTrackingContext(ModuleStoreTestCase):
    """
    Ensure correct tracking information is included in events emitted during XBlock callback handling.
    """

    def setUp(self):
        super(TestModuleTrackingContext, self).setUp()

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
        module_info = self.handle_callback_and_get_module_info(mock_tracker, problem_display_name)
        self.assertEquals(problem_display_name, module_info['display_name'])

    def handle_callback_and_get_module_info(self, mock_tracker, problem_display_name=None):
        """
        Creates a fake module, invokes the callback and extracts the 'module'
        metadata from the emitted problem_check event.
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
        return event['context']['module']

    def test_missing_display_name(self, mock_tracker):
        actual_display_name = self.handle_callback_and_get_module_info(mock_tracker)['display_name']
        self.assertTrue(actual_display_name.startswith('problem'))

    def test_library_source_information(self, mock_tracker):
        """
        Check that XBlocks that are inherited from a library include the
        information about their library block source in events.
        We patch the modulestore to avoid having to create a library.
        """
        original_usage_key = UsageKey.from_string(u'block-v1:A+B+C+type@problem+block@abcd1234')
        original_usage_version = ObjectId()
        mock_get_original_usage = lambda _, key: (original_usage_key, original_usage_version)
        with patch('xmodule.modulestore.mixed.MixedModuleStore.get_block_original_usage', mock_get_original_usage):
            module_info = self.handle_callback_and_get_module_info(mock_tracker)
            self.assertIn('original_usage_key', module_info)
            self.assertEqual(module_info['original_usage_key'], unicode(original_usage_key))
            self.assertIn('original_usage_version', module_info)
            self.assertEqual(module_info['original_usage_version'], unicode(original_usage_version))


@attr('shard_1')
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

    @patch('courseware.module_render.SCORE_CHANGED.send')
    def test_score_change_signal(self, send_mock):
        """Test that a Django signal is generated when a score changes"""
        self.set_module_grade_using_publish(self.grade_dict)
        expected_signal_kwargs = {
            'sender': None,
            'points_possible': self.grade_dict['max_value'],
            'points_earned': self.grade_dict['value'],
            'user_id': self.student_user.id,
            'course_id': unicode(self.course.id),
            'usage_id': unicode(self.problem.location)
        }
        send_mock.assert_called_with(**expected_signal_kwargs)


@attr('shard_1')
class TestRebindModule(TestSubmittingProblems):
    """
    Tests to verify the functionality of rebinding a module.
    Inherit from TestSubmittingProblems to get functionality that set up a course structure
    """
    def setUp(self):
        super(TestRebindModule, self).setUp()
        self.homework = self.add_graded_section_to_course('homework')
        self.lti = ItemFactory.create(category='lti', parent=self.homework)
        self.problem = ItemFactory.create(category='problem', parent=self.homework)
        self.user = UserFactory.create()
        self.anon_user = AnonymousUser()

    def get_module_for_user(self, user, item=None):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, user, self.course, depth=2)

        if item is None:
            item = self.lti

        return render.get_module(  # pylint: disable=protected-access
            user,
            mock_request,
            item.location,
            field_data_cache,
        )._xmodule

    def test_rebind_module_to_new_users(self):
        module = self.get_module_for_user(self.user, self.problem)

        # Bind the module to another student, which will remove "correct_map"
        # from the module's _field_data_cache and _dirty_fields.
        user2 = UserFactory.create()
        module.descriptor.bind_for_student(module.system, user2.id)

        # XBlock's save method assumes that if a field is in _dirty_fields,
        # then it's also in _field_data_cache. If this assumption
        # doesn't hold, then we get an error trying to bind this module
        # to a third student, since we've removed "correct_map" from
        # _field_data cache, but not _dirty_fields, when we bound
        # this module to the second student. (TNL-2640)
        user3 = UserFactory.create()
        module.descriptor.bind_for_student(module.system, user3.id)

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


@attr('shard_1')
@ddt.ddt
class TestEventPublishing(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests of event publishing for both XModules and XBlocks.
    """

    def setUp(self):
        """
        Set up the course and user context
        """
        super(TestEventPublishing, self).setUp()

        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactory()

    @ddt.data('xblock', 'xmodule')
    @XBlock.register_temp_plugin(PureXBlock, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptor, identifier='xmodule')
    @patch.object(render, 'make_track_function')
    @patch('student.models.UserProfile.has_registered', Mock(return_value=True))
    def test_event_publishing(self, block_type, mock_track_function):
        request = self.request_factory.get('')
        request.user = self.mock_user
        course = CourseFactory()
        descriptor = ItemFactory(category=block_type, parent=course)
        field_data_cache = FieldDataCache([course, descriptor], course.id, self.mock_user)  # pylint: disable=no-member
        block = render.get_module(self.mock_user, request, descriptor.location, field_data_cache)

        event_type = 'event_type'
        event = {'event': 'data'}

        block.runtime.publish(block, event_type, event)

        mock_track_function.assert_called_once_with(request)

        mock_track_function.return_value.assert_called_once_with(event_type, event)


@attr('shard_1')
@ddt.ddt
class LMSXBlockServiceBindingTest(ModuleStoreTestCase):
    """
    Tests that the LMS Module System (XBlock Runtime) provides an expected set of services.
    """
    def setUp(self):
        """
        Set up the user and other fields that will be used to instantiate the runtime.
        """
        super(LMSXBlockServiceBindingTest, self).setUp()
        self.user = UserFactory()
        self.student_data = Mock()
        self.course = CourseFactory.create()
        self.track_function = Mock()
        self.xqueue_callback_url_prefix = Mock()
        self.request_token = Mock()

    @XBlock.register_temp_plugin(PureXBlock, identifier='pure')
    @ddt.data("user", "i18n", "fs", "field-data")
    def test_expected_services_exist(self, expected_service):
        """
        Tests that the 'user', 'i18n', and 'fs' services are provided by the LMS runtime.
        """
        descriptor = ItemFactory(category="pure", parent=self.course)
        runtime, _ = render.get_module_system_for_user(
            self.user,
            self.student_data,
            descriptor,
            self.course.id,
            self.track_function,
            self.xqueue_callback_url_prefix,
            self.request_token,
            course=self.course
        )
        service = runtime.service(descriptor, expected_service)
        self.assertIsNotNone(service)

    def test_beta_tester_fields_added(self):
        """
        Tests that the beta tester fields are set on LMS runtime.
        """
        descriptor = ItemFactory(category="pure", parent=self.course)
        descriptor.days_early_for_beta = 5
        runtime, _ = render.get_module_system_for_user(
            self.user,
            self.student_data,
            descriptor,
            self.course.id,
            self.track_function,
            self.xqueue_callback_url_prefix,
            self.request_token,
            course=self.course
        )

        # pylint: disable=no-member
        self.assertFalse(runtime.user_is_beta_tester)
        self.assertEqual(runtime.days_early_for_beta, 5)


class PureXBlockWithChildren(PureXBlock):
    """
    Pure XBlock with children to use in tests.
    """
    has_children = True


class EmptyXModuleWithChildren(EmptyXModule):  # pylint: disable=abstract-method
    """
    Empty XModule for testing with no dependencies.
    """
    has_children = True


class EmptyXModuleDescriptorWithChildren(EmptyXModuleDescriptor):  # pylint: disable=abstract-method
    """
    Empty XModule for testing with no dependencies.
    """
    module_class = EmptyXModuleWithChildren
    has_children = True


BLOCK_TYPES = ['xblock', 'xmodule']
USER_NUMBERS = range(2)


@attr('shard_1')
@ddt.ddt
class TestFilteredChildren(ModuleStoreTestCase):
    """
    Tests that verify access to XBlock/XModule children work correctly
    even when those children are filtered by the runtime when loaded.
    """
    # pylint: disable=attribute-defined-outside-init, no-member
    def setUp(self):
        super(TestFilteredChildren, self).setUp()
        self.users = {number: UserFactory() for number in USER_NUMBERS}
        self.course = CourseFactory()

        self._old_has_access = render.has_access
        patcher = patch('courseware.module_render.has_access', self._has_access)
        patcher.start()
        self.addCleanup(patcher.stop)

    @ddt.data(*BLOCK_TYPES)
    @XBlock.register_temp_plugin(PureXBlockWithChildren, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptorWithChildren, identifier='xmodule')
    def test_unbound(self, block_type):
        block = self._load_block(block_type)
        self.assertUnboundChildren(block)

    @ddt.data(*itertools.product(BLOCK_TYPES, USER_NUMBERS))
    @ddt.unpack
    @XBlock.register_temp_plugin(PureXBlockWithChildren, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptorWithChildren, identifier='xmodule')
    def test_unbound_then_bound_as_descriptor(self, block_type, user_number):
        user = self.users[user_number]
        block = self._load_block(block_type)
        self.assertUnboundChildren(block)
        self._bind_block(block, user)
        self.assertBoundChildren(block, user)

    @ddt.data(*itertools.product(BLOCK_TYPES, USER_NUMBERS))
    @ddt.unpack
    @XBlock.register_temp_plugin(PureXBlockWithChildren, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptorWithChildren, identifier='xmodule')
    def test_unbound_then_bound_as_xmodule(self, block_type, user_number):
        user = self.users[user_number]
        block = self._load_block(block_type)
        self.assertUnboundChildren(block)
        self._bind_block(block, user)

        # Validate direct XModule access as well
        if isinstance(block, XModuleDescriptor):
            self.assertBoundChildren(block._xmodule, user)  # pylint: disable=protected-access
        else:
            self.assertBoundChildren(block, user)

    @ddt.data(*itertools.product(BLOCK_TYPES, USER_NUMBERS))
    @ddt.unpack
    @XBlock.register_temp_plugin(PureXBlockWithChildren, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptorWithChildren, identifier='xmodule')
    def test_bound_only_as_descriptor(self, block_type, user_number):
        user = self.users[user_number]
        block = self._load_block(block_type)
        self._bind_block(block, user)
        self.assertBoundChildren(block, user)

    @ddt.data(*itertools.product(BLOCK_TYPES, USER_NUMBERS))
    @ddt.unpack
    @XBlock.register_temp_plugin(PureXBlockWithChildren, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptorWithChildren, identifier='xmodule')
    def test_bound_only_as_xmodule(self, block_type, user_number):
        user = self.users[user_number]
        block = self._load_block(block_type)
        self._bind_block(block, user)

        # Validate direct XModule access as well
        if isinstance(block, XModuleDescriptor):
            self.assertBoundChildren(block._xmodule, user)  # pylint: disable=protected-access
        else:
            self.assertBoundChildren(block, user)

    def _load_block(self, block_type):
        """
        Instantiate an XBlock of `block_type` with the appropriate set of children.
        """
        self.parent = ItemFactory(category=block_type, parent=self.course)

        # Create a child of each block type for each user
        self.children_for_user = {
            user: [
                ItemFactory(category=child_type, parent=self.parent).scope_ids.usage_id
                for child_type in BLOCK_TYPES
            ]
            for user in self.users.itervalues()
        }

        self.all_children = sum(self.children_for_user.values(), [])

        return modulestore().get_item(self.parent.scope_ids.usage_id)

    def _bind_block(self, block, user):
        """
        Bind `block` to the supplied `user`.
        """
        course_id = self.course.id
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course_id,
            user,
            block,
        )
        return get_module_for_descriptor(
            user,
            Mock(name='request', user=user),
            block,
            field_data_cache,
            course_id,
            course=self.course
        )

    def _has_access(self, user, action, obj, course_key=None):
        """
        Mock implementation of `has_access` used to control which blocks
        have access to which children during tests.
        """
        if action != 'load':
            return self._old_has_access(user, action, obj, course_key)

        if isinstance(obj, XBlock):
            key = obj.scope_ids.usage_id
        elif isinstance(obj, UsageKey):
            key = obj

        if key == self.parent.scope_ids.usage_id:
            return True
        return key in self.children_for_user[user]

    def assertBoundChildren(self, block, user):
        """
        Ensure the bound children are indeed children.
        """
        self.assertChildren(block, self.children_for_user[user])

    def assertUnboundChildren(self, block):
        """
        Ensure unbound children are indeed children.
        """
        self.assertChildren(block, self.all_children)

    def assertChildren(self, block, child_usage_ids):
        """
        Used to assert that sets of children are equivalent.
        """
        self.assertEquals(set(child_usage_ids), set(child.scope_ids.usage_id for child in block.get_children()))


@attr('shard_1')
@ddt.ddt
class TestDisabledXBlockTypes(ModuleStoreTestCase):
    """
    Tests that verify disabled XBlock types are not loaded.
    """
    # pylint: disable=no-member
    def setUp(self):
        super(TestDisabledXBlockTypes, self).setUp()

        for store in self.store.modulestores:
            store.disabled_xblock_types = ('combinedopenended', 'peergrading', 'video')

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_get_item(self, default_ms):
        with self.store.default_store(default_ms):
            course = CourseFactory()
            for block_type in ('peergrading', 'combinedopenended', 'video'):
                item = ItemFactory(category=block_type, parent=course)
                item = self.store.get_item(item.scope_ids.usage_id)
                self.assertEqual(item.__class__.__name__, 'RawDescriptorWithMixins')


@override_settings(ANALYTICS_DATA_URL='dummy_url')
class TestInlineAnalytics(ModuleStoreTestCase):
    """Tests to verify that Inline Analytics fragment is generated correctly"""

    def setUp(self):
        super(TestInlineAnalytics, self).setUp()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = {}
        self.course = CourseFactory.create(
            org="A",
            number="B",
            display_name="C",
        )
        self.staff = StaffFactory(course_key=self.course.id)
        self.instructor = InstructorFactory(course_key=self.course.id)

        self.problem_xml = OptionResponseXMLFactory().build_xml(
            question_text='The correct answer is Correct',
            num_inputs=2,
            weight=2,
            options=['Correct', 'Incorrect'],
            correct_option='Correct',
        )
        self.descriptor = ItemFactory.create(
            category='problem',
            data=self.problem_xml,
            display_name='Option Response Problem',
            rerandomize='never',
        )

        self.location = self.descriptor.location
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            self.descriptor,
        )
        self.field_data_cache_staff = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.staff,
            self.descriptor,
        )
        self.field_data_cache_instructor = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.instructor,
            self.descriptor,
        )

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    def test_inline_analytics_enabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertIn('Staff Analytics Info', result_fragment.content)

    @override_settings(ANALYTICS_DATA_URL=None)
    def test_inline_analytics_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertNotIn('Staff Analytics Info', result_fragment.content)

    def test_inline_analytics_no_access(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertNotIn('Staff Analytics Info', result_fragment.content)

    def test_inline_analytics_staff_access(self):
        module = render.get_module(
            self.staff,
            self.request,
            self.location,
            self.field_data_cache_staff,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertIn('Staff Analytics Info', result_fragment.content)

    def test_inline_analytics_instructor_access(self):
        module = render.get_module(
            self.instructor,
            self.request,
            self.location,
            self.field_data_cache_instructor,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertIn('Staff Analytics Info', result_fragment.content)

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    @override_settings(INLINE_ANALYTICS_SUPPORTED_TYPES={'ChoiceResponse': 'checkbox'})
    def test_unsupported_response_type(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertIn('Staff Analytics Info', result_fragment.content)
        self.assertIn('The analytics cannot be displayed for this type of question.', result_fragment.content)

    @patch('courseware.module_render.has_access', Mock(return_value=True))
    def test_rerandomization_set(self):
        descriptor = ItemFactory.create(
            category='problem',
            data=self.problem_xml,
            display_name='Option Response Problem2',
            rerandomize='always',
        )

        location = descriptor.location
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            descriptor
        )

        module = render.get_module(
            self.user,
            self.request,
            location,
            field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertIn('Staff Analytics Info', result_fragment.content)
        self.assertIn('The analytics cannot be displayed for this question as it uses randomization.',
                      result_fragment.content)

    def test_no_problems(self):

        descriptor = ItemFactory.create(
            category='html',
            display_name='HTML Component',
        )

        location = descriptor.location
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            descriptor
        )

        module = render.get_module(
            self.user,
            self.request,
            location,
            field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertNotIn('Staff Analytics Info', result_fragment.content)
