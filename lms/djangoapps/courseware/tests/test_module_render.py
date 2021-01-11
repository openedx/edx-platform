# -*- coding: utf-8 -*-
"""
Test for lms courseware app, module render unit
"""


import itertools
import json
import textwrap
from datetime import datetime
from functools import partial

import ddt
import pytz
import six
from bson import ObjectId
from capa.tests.response_xml_factory import OptionResponseXMLFactory
from completion import waffle as completion_waffle
from completion.models import BlockCompletion
from common.djangoapps.course_modes.models import CourseMode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import Http404, HttpResponse
from django.middleware.csrf import get_token
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from edx_proctoring.api import create_exam, create_exam_attempt, update_attempt_status
from edx_proctoring.runtime import set_runtime_service
from edx_proctoring.tests.test_services import MockCertificateService, MockCreditService, MockGradesService
from edx_toggles.toggles import WaffleSwitch
from edx_toggles.toggles.testutils import override_waffle_switch
from edx_when.field_data import DateLookupFieldData
from freezegun import freeze_time
from milestones.tests.utils import MilestonesTestCaseMixin
from mock import MagicMock, Mock, patch
from opaque_keys.edx.asides import AsideUsageKeyV2
from opaque_keys.edx.keys import CourseKey, UsageKey
from pyquery import PyQuery
from six import text_type
from six.moves import range
from web_fragments.fragment import Fragment
from xblock.completable import CompletableXBlockMixin
from xblock.core import XBlock, XBlockAside
from xblock.field_data import FieldData
from xblock.fields import ScopeIds
from xblock.runtime import DictKeyValueStore, KvsFieldData, Runtime
from xblock.test.tools import TestRuntime

from capa.tests.response_xml_factory import OptionResponseXMLFactory
from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.courseware import module_render as render
from lms.djangoapps.courseware.access_response import AccessResponse
from lms.djangoapps.courseware.courses import get_course_info_section, get_course_with_access
from lms.djangoapps.courseware.field_overrides import OverrideFieldData
from lms.djangoapps.courseware.masquerade import CourseMasquerade
from lms.djangoapps.courseware.model_data import FieldDataCache
from lms.djangoapps.courseware.models import StudentModule
from lms.djangoapps.courseware.module_render import get_module_for_descriptor, hash_resource
from lms.djangoapps.courseware.tests.factories import (
    GlobalStaffFactory,
    RequestFactoryNoCsrf,
    StudentModuleFactory,
    UserFactory
)
from lms.djangoapps.courseware.tests.test_submitting_problems import TestSubmittingProblems
from lms.djangoapps.courseware.tests.tests import LoginEnrollmentTestCase
from lms.djangoapps.lms_xblock.field_data import LmsFieldData
from openedx.core.djangoapps.credit.api import set_credit_requirement_status, set_credit_requirements
from openedx.core.djangoapps.credit.models import CreditCourse
from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.oauth_dispatch.tests.factories import AccessTokenFactory, ApplicationFactory
from openedx.core.lib.courses import course_image_url
from openedx.core.lib.gating import api as gating_api
from openedx.core.lib.url_utils import quote_slashes
from common.djangoapps.student.models import CourseEnrollment, anonymous_id_for_user
from lms.djangoapps.verify_student.tests.factories import SoftwareSecurePhotoVerificationFactory
from common.djangoapps.xblock_django.models import XBlockConfiguration
from xmodule.capa_module import ProblemBlock
from xmodule.html_module import AboutBlock, CourseInfoBlock, HtmlBlock, StaticTabBlock
from xmodule.lti_module import LTIDescriptor
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_MIXED_MODULESTORE,
    ModuleStoreTestCase,
    SharedModuleStoreTestCase
)
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, ToyCourseFactory, check_mongo_calls
from xmodule.modulestore.tests.test_asides import AsideTestType
from xmodule.video_module import VideoBlock
from xmodule.x_module import STUDENT_VIEW, CombinedSystem, XModule, XModuleDescriptor


TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT

# pylint: disable=feature-toggle-needs-doc
ENABLE_COMPLETION_TRACKING_SWITCH = WaffleSwitch(
    completion_waffle.waffle(), completion_waffle.ENABLE_COMPLETION_TRACKING, __name__
)


@XBlock.needs("field-data")
@XBlock.needs("i18n")
@XBlock.needs("fs")
@XBlock.needs("user")
@XBlock.needs("bookmarks")
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


class StubCompletableXBlock(CompletableXBlockMixin):
    """
    This XBlock exists to test completion storage.
    """

    @XBlock.json_handler
    def complete(self, json_data, suffix):  # pylint: disable=unused-argument
        """
        Mark the block's completion value using the completion API.
        """
        return self.runtime.publish(
            self,
            'completion',
            {'completion': json_data['completion']},
        )

    @XBlock.json_handler
    def progress(self, json_data, suffix):  # pylint: disable=unused-argument
        """
        Mark the block as complete using the deprecated progress interface.

        New code should use the completion event instead.
        """
        return self.runtime.publish(self, 'progress', {})


class XBlockWithoutCompletionAPI(XBlock):
    """
    This XBlock exists to test completion storage for xblocks
    that don't support completion API but do emit progress signal.
    """

    @XBlock.json_handler
    def progress(self, json_data, suffix):  # pylint: disable=unused-argument
        """
        Mark the block as complete using the deprecated progress interface.

        New code should use the completion event instead.
        """
        return self.runtime.publish(self, 'progress', {})


@ddt.ddt
class ModuleRenderTestCase(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests of courseware.module_render
    """

    @classmethod
    def setUpClass(cls):
        super(ModuleRenderTestCase, cls).setUpClass()
        cls.course_key = ToyCourseFactory.create().id
        cls.toy_course = modulestore().get_course(cls.course_key)

    # TODO: this test relies on the specific setup of the toy course.
    # It should be rewritten to build the course it needs and then test that.
    def setUp(self):
        """
        Set up the course and user context
        """
        super(ModuleRenderTestCase, self).setUp()
        OverrideFieldData.provider_classes = None

        self.mock_user = UserFactory()
        self.mock_user.id = 1
        self.request_factory = RequestFactoryNoCsrf()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Construct a 'standard' xqueue_callback url
        self.callback_url = reverse(
            'xqueue_callback',
            kwargs=dict(
                course_id=text_type(self.course_key),
                userid=str(self.mock_user.id),
                mod_id=self.mock_module.id,
                dispatch=self.dispatch
            )
        )

    def tearDown(self):
        OverrideFieldData.provider_classes = None
        super(ModuleRenderTestCase, self).tearDown()

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
        self.assertIn('/courses/' + text_type(self.course_key) + '/jump_to_id/vertical_test', html)

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
        with patch('lms.djangoapps.courseware.module_render.load_single_xblock', return_value=self.mock_module):
            # call xqueue_callback with our mocked information
            request = self.request_factory.post(self.callback_url, data)
            render.xqueue_callback(
                request,
                text_type(self.course_key),
                self.mock_user.id,
                self.mock_module.id,
                self.dispatch
            )

        # Verify that handle ajax is called with the correct data
        request.POST._mutable = True
        request.POST['queuekey'] = fake_key
        self.mock_module.handle_ajax.assert_called_once_with(self.dispatch, request.POST)

    def test_xqueue_callback_missing_header_info(self):
        data = {
            'xqueue_header': '{}',
            'xqueue_body': 'hello world',
        }

        with patch('lms.djangoapps.courseware.module_render.load_single_xblock', return_value=self.mock_module):
            # Test with missing xqueue data
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, {})
                render.xqueue_callback(
                    request,
                    text_type(self.course_key),
                    self.mock_user.id,
                    self.mock_module.id,
                    self.dispatch
                )

            # Test with missing xqueue_header
            with self.assertRaises(Http404):
                request = self.request_factory.post(self.callback_url, data)
                render.xqueue_callback(
                    request,
                    text_type(self.course_key),
                    self.mock_user.id,
                    self.mock_module.id,
                    self.dispatch
                )

    def _get_dispatch_url(self):
        """Helper to get dispatch URL for testing xblock callback."""
        return reverse(
            'xblock_handler',
            args=[
                text_type(self.course_key),
                quote_slashes(text_type(self.course_key.make_usage_key('videosequence', 'Toy_Videos'))),
                'xmodule_handler',
                'goto_position'
            ]
        )

    def test_anonymous_get_xblock_callback(self):
        """Test that anonymous GET is allowed."""
        dispatch_url = self._get_dispatch_url()
        response = self.client.get(dispatch_url)
        self.assertEqual(200, response.status_code)

    def test_anonymous_post_xblock_callback(self):
        """Test that anonymous POST is not allowed."""
        dispatch_url = self._get_dispatch_url()
        response = self.client.post(dispatch_url, {'position': 2})

        # https://openedx.atlassian.net/browse/LEARNER-7131
        self.assertEqual('Unauthenticated', response.content.decode('utf-8'))
        self.assertEqual(403, response.status_code)

    def test_session_authentication(self):
        """ Test that the xblock endpoint supports session authentication."""
        self.client.login(username=self.mock_user.username, password="test")
        dispatch_url = self._get_dispatch_url()
        response = self.client.post(dispatch_url)
        self.assertEqual(200, response.status_code)

    def test_oauth_authentication(self):
        """ Test that the xblock endpoint supports OAuth authentication."""
        dispatch_url = self._get_dispatch_url()
        access_token = AccessTokenFactory(user=self.mock_user, application=ApplicationFactory()).token
        headers = {'HTTP_AUTHORIZATION': 'Bearer ' + access_token}
        response = self.client.post(dispatch_url, {}, **headers)
        self.assertEqual(200, response.status_code)

    def test_jwt_authentication(self):
        """ Test that the xblock endpoint supports JWT authentication."""
        dispatch_url = self._get_dispatch_url()
        token = create_jwt_for_user(self.mock_user)
        headers = {'HTTP_AUTHORIZATION': 'JWT ' + token}
        response = self.client.post(dispatch_url, {}, **headers)
        self.assertEqual(200, response.status_code)

    def test_missing_position_handler(self):
        """
        Test that sending POST request without or invalid position argument don't raise server error
        """
        self.client.login(username=self.mock_user.username, password="test")
        dispatch_url = self._get_dispatch_url()
        response = self.client.post(dispatch_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

        response = self.client.post(dispatch_url, {'position': ''})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

        response = self.client.post(dispatch_url, {'position': '-1'})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

        response = self.client.post(dispatch_url, {'position': "string"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

        response = self.client.post(dispatch_url, {'position': u"Φυσικά"})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

        response = self.client.post(dispatch_url, {'position': ''})
        self.assertEqual(200, response.status_code)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

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
        'lms.djangoapps.courseware.student_field_overrides.IndividualStudentOverrideProvider',
    ))
    @patch('xmodule.modulestore.xml.ImportSystem.applicable_aside_types', lambda self, block: ['test_aside'])
    @patch('xmodule.modulestore.split_mongo.caching_descriptor_system.CachingDescriptorSystem.applicable_aside_types',
           lambda self, block: ['test_aside'])
    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    @ddt.data('regular', 'test_aside')
    def test_rebind_different_users(self, block_category):
        """
        This tests the rebinding a descriptor to a student does not result
        in overly nested _field_data.
        """
        def create_aside(item, block_type):
            """
            Helper function to create aside
            """
            key_store = DictKeyValueStore()
            field_data = KvsFieldData(key_store)
            runtime = TestRuntime(services={'field-data': field_data})

            def_id = runtime.id_generator.create_definition(block_type)
            usage_id = AsideUsageKeyV2(runtime.id_generator.create_usage(def_id), "aside")
            aside = AsideTestType(scope_ids=ScopeIds('user', block_type, def_id, usage_id), runtime=runtime)
            aside.content = '%s_new_value11' % block_type
            aside.data_field = '%s_new_value12' % block_type
            aside.has_score = False

            modulestore().update_item(item, self.mock_user.id, asides=[aside])
            return item

        request = self.request_factory.get('')
        request.user = self.mock_user
        course = CourseFactory.create()

        descriptor = ItemFactory(category="html", parent=course)
        if block_category == 'test_aside':
            descriptor = create_aside(descriptor, "test_aside")

        field_data_cache = FieldDataCache(
            [course, descriptor], course.id, self.mock_user
        )

        # grab what _field_data was originally set to
        original_field_data = descriptor._field_data  # pylint: disable=protected-access

        render.get_module_for_descriptor(
            self.mock_user, request, descriptor, field_data_cache, course.id, course=course
        )

        # check that _unwrapped_field_data is the same as the original
        # _field_data, but now _field_data as been reset.
        # pylint: disable=protected-access
        self.assertIs(descriptor._unwrapped_field_data, original_field_data)
        self.assertIsNot(descriptor._unwrapped_field_data, descriptor._field_data)

        # now bind this module to a few other students
        for user in [UserFactory(), UserFactory(), self.mock_user]:
            render.get_module_for_descriptor(
                user,
                request,
                descriptor,
                field_data_cache,
                course.id,
                course=course
            )

        # _field_data should now be wrapped by LmsFieldData
        # pylint: disable=protected-access
        self.assertIsInstance(descriptor._field_data, LmsFieldData)

        # the LmsFieldData should now wrap OverrideFieldData
        self.assertIsInstance(
            # pylint: disable=protected-access
            descriptor._field_data._authored_data._source,
            OverrideFieldData
        )

        # the OverrideFieldData should point to the date FieldData
        self.assertIsInstance(
            # pylint: disable=protected-access
            descriptor._field_data._authored_data._source.fallback,
            DateLookupFieldData
        )
        self.assertIs(
            descriptor._field_data._authored_data._source.fallback._defaults,
            descriptor._unwrapped_field_data
        )

    def test_hash_resource(self):
        """
        Ensure that the resource hasher works and does not fail on unicode,
        decoded or otherwise.
        """
        resources = ['ASCII text', u'❄ I am a special snowflake.', "❄ So am I, but I didn't tell you."]
        self.assertEqual(hash_resource(resources), '50c2ae79fbce9980e0803848914b0a09')


@ddt.ddt
class TestHandleXBlockCallback(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test the handle_xblock_callback function
    """
    @classmethod
    def setUpClass(cls):
        super(TestHandleXBlockCallback, cls).setUpClass()
        cls.course_key = ToyCourseFactory.create().id
        cls.toy_course = modulestore().get_course(cls.course_key)

    def setUp(self):
        super(TestHandleXBlockCallback, self).setUp()

        self.location = self.course_key.make_usage_key('chapter', 'Overview')
        self.mock_user = UserFactory.create()
        self.request_factory = RequestFactoryNoCsrf()

        # Construct a mock module for the modulestore to return
        self.mock_module = MagicMock()
        self.mock_module.id = 1
        self.dispatch = 'score_update'

        # Construct a 'standard' xqueue_callback url
        self.callback_url = reverse(
            'xqueue_callback', kwargs={
                'course_id': text_type(self.course_key),
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

    def make_xblock_callback_response(self, request_data, course, block, handler):
        """
        Prepares an xblock callback request and returns response to it.
        """
        request = self.request_factory.post(
            '/',
            data=json.dumps(request_data),
            content_type='application/json',
        )
        request.user = self.mock_user
        response = render.handle_xblock_callback(
            request,
            text_type(course.id),
            quote_slashes(text_type(block.scope_ids.usage_id)),
            handler,
            '',
        )

        return response

    def test_invalid_csrf_token(self):
        """
        Verify that invalid CSRF token is rejected.
        """
        request = RequestFactory().post('dummy_url', data={'position': 1})
        csrf_token = get_token(request)
        request._post = {'csrfmiddlewaretoken': '{}-dummy'.format(csrf_token)}  # pylint: disable=protected-access
        request.user = self.mock_user
        response = render.handle_xblock_callback(
            request,
            text_type(self.course_key),
            quote_slashes(text_type(self.location)),
            'xmodule_handler',
            'goto_position',
        )
        self.assertEqual(403, response.status_code)

    def test_valid_csrf_token(self):
        """
        Verify that valid CSRF token is accepted.
        """
        request = RequestFactory().post('dummy_url', data={'position': 1})
        csrf_token = get_token(request)
        request._post = {'csrfmiddlewaretoken': csrf_token}  # pylint: disable=protected-access
        request.user = self.mock_user
        response = render.handle_xblock_callback(
            request,
            text_type(self.course_key),
            quote_slashes(text_type(self.location)),
            'xmodule_handler',
            'goto_position',
        )
        self.assertEqual(200, response.status_code)

    def test_invalid_location(self):
        request = self.request_factory.post('dummy_url', data={'position': 1})
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                text_type(self.course_key),
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
        self.assertEqual(
            render.handle_xblock_callback(
                request,
                text_type(self.course_key),
                quote_slashes(text_type(self.location)),
                'dummy_handler'
            ).content.decode('utf-8'),
            json.dumps({
                'success': u'Submission aborted! Maximum %d files may be submitted at once' %
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
        self.assertEqual(
            render.handle_xblock_callback(
                request,
                text_type(self.course_key),
                quote_slashes(text_type(self.location)),
                'dummy_handler'
            ).content.decode('utf-8'),
            json.dumps({
                'success': u'Submission aborted! Your file "%s" is too large (max size: %d MB)' %
                           (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))
            }, indent=2)
        )

    def test_xmodule_dispatch(self):
        request = self.request_factory.post('dummy_url', data={'position': 1})
        request.user = self.mock_user
        response = render.handle_xblock_callback(
            request,
            text_type(self.course_key),
            quote_slashes(text_type(self.location)),
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
                quote_slashes(text_type(self.location)),
                'xmodule_handler',
                'goto_position',
            )

    def test_bad_location(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                text_type(self.course_key),
                quote_slashes(text_type(self.course_key.make_usage_key('chapter', 'bad_location'))),
                'xmodule_handler',
                'goto_position',
            )

    def test_bad_xmodule_dispatch(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                text_type(self.course_key),
                quote_slashes(text_type(self.location)),
                'xmodule_handler',
                'bad_dispatch',
            )

    def test_missing_handler(self):
        request = self.request_factory.post('dummy_url')
        request.user = self.mock_user
        with self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                text_type(self.course_key),
                quote_slashes(text_type(self.location)),
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
            text_type(course.id),
            quote_slashes(text_type(block.scope_ids.usage_id)),
            'set_score',
            '',
        )
        self.assertEqual(response.status_code, 200)
        student_module = StudentModule.objects.get(
            student=self.mock_user,
            module_state_key=block.scope_ids.usage_id,
        )
        self.assertEqual(student_module.grade, 0.75)
        self.assertEqual(student_module.max_grade, 1)

    @ddt.data(
        ('complete', {'completion': 0.625}),
        ('progress', {}),
    )
    @ddt.unpack
    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_completion_events_with_completion_disabled(self, signal, data):
        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, False):
            course = CourseFactory.create()
            block = ItemFactory.create(category='comp', parent=course)
            request = self.request_factory.post(
                '/',
                data=json.dumps(data),
                content_type='application/json',
            )
            request.user = self.mock_user
            with patch('completion.models.BlockCompletionManager.submit_completion') as mock_complete:
                render.handle_xblock_callback(
                    request,
                    text_type(course.id),
                    quote_slashes(text_type(block.scope_ids.usage_id)),
                    signal,
                    '',
                )
                mock_complete.assert_not_called()
            self.assertFalse(BlockCompletion.objects.filter(block_key=block.scope_ids.usage_id).exists())

    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_completion_signal_for_completable_xblock(self):
        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            course = CourseFactory.create()
            block = ItemFactory.create(category='comp', parent=course)

            response = self.make_xblock_callback_response(
                {'completion': 0.625}, course, block, 'complete'
            )

            self.assertEqual(response.status_code, 200)
            completion = BlockCompletion.objects.get(block_key=block.scope_ids.usage_id)
            self.assertEqual(completion.completion, 0.625)

    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    @ddt.data((True, True), (False, False),)
    @ddt.unpack
    def test_aside(self, is_xblock_aside, is_get_aside_called):
        """
        test get_aside_from_xblock called
        """
        course = CourseFactory.create()
        block = ItemFactory.create(category='comp', parent=course)
        request = self.request_factory.post(
            '/',
            data=json.dumps({'completion': 0.625}),
            content_type='application/json',
        )
        request.user = self.mock_user

        def get_usage_key():
            """return usage key"""
            return (
                quote_slashes(text_type(AsideUsageKeyV2(block.scope_ids.usage_id, "aside")))
                if is_xblock_aside
                else text_type(block.scope_ids.usage_id)
            )

        with patch(
            'lms.djangoapps.courseware.module_render.is_xblock_aside',
            return_value=is_xblock_aside
        ), patch(
            'lms.djangoapps.courseware.module_render.get_aside_from_xblock'
        ) as mocked_get_aside_from_xblock, patch(
            'lms.djangoapps.courseware.module_render.webob_to_django_response'
        ) as mocked_webob_to_django_response:
            render.handle_xblock_callback(
                request,
                text_type(course.id),
                get_usage_key(),
                'complete',
                '',
            )
            assert mocked_webob_to_django_response.called is True
        assert mocked_get_aside_from_xblock.called is is_get_aside_called

    def test_aside_invalid_usage_id(self):
        """
        test aside work when invalid usage id
        """
        course = CourseFactory.create()
        request = self.request_factory.post(
            '/',
            data=json.dumps({'completion': 0.625}),
            content_type='application/json',
        )
        request.user = self.mock_user

        with patch(
            'lms.djangoapps.courseware.module_render.is_xblock_aside',
            return_value=True
        ), self.assertRaises(Http404):
            render.handle_xblock_callback(
                request,
                text_type(course.id),
                "foo@bar",
                'complete',
                '',
            )

    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_progress_signal_ignored_for_completable_xblock(self):
        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            course = CourseFactory.create()
            block = ItemFactory.create(category='comp', parent=course)

            response = self.make_xblock_callback_response(
                {}, course, block, 'progress'
            )

            self.assertEqual(response.status_code, 200)
            self.assertFalse(BlockCompletion.objects.filter(block_key=block.scope_ids.usage_id).exists())

    @XBlock.register_temp_plugin(XBlockWithoutCompletionAPI, identifier='no_comp')
    def test_progress_signal_processed_for_xblock_without_completion_api(self):
        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            course = CourseFactory.create()
            block = ItemFactory.create(category='no_comp', parent=course)

            response = self.make_xblock_callback_response(
                {}, course, block, 'progress'
            )

            self.assertEqual(response.status_code, 200)
            completion = BlockCompletion.objects.get(block_key=block.scope_ids.usage_id)
            self.assertEqual(completion.completion, 1.0)

    @XBlock.register_temp_plugin(StubCompletableXBlock, identifier='comp')
    def test_skip_handlers_for_masquerading_staff(self):
        with override_waffle_switch(ENABLE_COMPLETION_TRACKING_SWITCH, True):
            course = CourseFactory.create()
            block = ItemFactory.create(category='comp', parent=course)
            request = self.request_factory.post(
                '/',
                data=json.dumps({'completion': 0.8}),
                content_type='application/json',
            )
            request.user = self.mock_user
            request.session = {}
            request.user.real_user = GlobalStaffFactory.create()
            request.user.real_user.masquerade_settings = CourseMasquerade(course.id, user_name="jem")
            with patch('lms.djangoapps.courseware.module_render.is_masquerading_as_specific_student') as mock_masq:
                mock_masq.return_value = True
                response = render.handle_xblock_callback(
                    request,
                    text_type(course.id),
                    quote_slashes(text_type(block.scope_ids.usage_id)),
                    'complete',
                    '',
                )
            mock_masq.assert_called()
        self.assertEqual(response.status_code, 200)
        with self.assertRaises(BlockCompletion.DoesNotExist):
            BlockCompletion.objects.get(block_key=block.scope_ids.usage_id)

    @XBlock.register_temp_plugin(GradedStatelessXBlock, identifier='stateless_scorer')
    @patch('lms.djangoapps.courseware.module_render.grades_signals.SCORE_PUBLISHED.send')
    def test_anonymous_user_not_be_graded(self, mock_score_signal):
        course = CourseFactory.create()
        descriptor_kwargs = {
            'category': 'problem',
        }
        request = self.request_factory.get('/')
        request.user = AnonymousUser()
        descriptor = ItemFactory.create(**descriptor_kwargs)

        render.handle_xblock_callback(
            request,
            text_type(course.id),
            quote_slashes(text_type(descriptor.location)),
            'xmodule_handler',
            'problem_check',
        )
        self.assertFalse(mock_score_signal.called)


@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_XBLOCK_VIEW_ENDPOINT': True})
class TestXBlockView(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test the handle_xblock_callback function
    """
    @classmethod
    def setUpClass(cls):
        super(TestXBlockView, cls).setUpClass()
        cls.course_key = ToyCourseFactory.create().id
        cls.toy_course = modulestore().get_course(cls.course_key)

    def setUp(self):
        super(TestXBlockView, self).setUp()

        self.location = text_type(self.course_key.make_usage_key('html', 'toyhtml'))
        self.request_factory = RequestFactory()

        self.view_args = [text_type(self.course_key), quote_slashes(self.location), 'student_view']
        self.xblock_view_url = reverse('xblock_view', args=self.view_args)

    def test_xblock_view_handler(self):
        request = self.request_factory.get(self.xblock_view_url)
        request.user = UserFactory.create()
        response = render.xblock_view(request, *self.view_args)
        self.assertEqual(200, response.status_code)

        expected = ['csrf_token', 'html', 'resources']
        content = json.loads(response.content.decode('utf-8'))
        for section in expected:
            self.assertIn(section, content)
        doc = PyQuery(content['html'])
        self.assertEqual(len(doc('div.xblock-student_view-html')), 1)

    @ddt.data(True, False)
    def test_hide_staff_markup(self, hide):
        """
        When xblock_view gets 'hide_staff_markup' in its context, the staff markup
        should not be included. See 'add_staff_markup' in xblock_utils/__init__.py
        """
        request = self.request_factory.get(self.xblock_view_url)
        request.user = GlobalStaffFactory.create()
        request.session = {}
        if hide:
            request.GET = {'hide_staff_markup': 'true'}
        response = render.xblock_view(request, *self.view_args)
        self.assertEqual(200, response.status_code)

        html = json.loads(response.content.decode('utf-8'))['html']
        self.assertEqual('Staff Debug Info' in html, not hide)

    def test_xblock_view_handler_not_authenticated(self):
        request = self.request_factory.get(self.xblock_view_url)
        request.user = AnonymousUser()
        response = render.xblock_view(request, *self.view_args)
        self.assertEqual(401, response.status_code)


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
        factory = RequestFactoryNoCsrf()
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
    # Split makes 2 queries to load the course to depth 2:
    #     - 1 for the structure
    #     - 1 for 5 definitions
    # Split makes 1 query to render the toc:
    #     - 1 for the active version at the start of the bulk operation
    @ddt.data((ModuleStoreEnum.Type.mongo, 3, 0, 0), (ModuleStoreEnum.Type.split, 2, 0, 1))
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
            self.assertIn(toc_section, actual['chapters'])
        self.assertIsNone(actual['previous_of_active_section'])
        self.assertIsNone(actual['next_of_active_section'])

    # Mongo makes 3 queries to load the course to depth 2:
    #     - 1 for the course
    #     - 1 for its children
    #     - 1 for its grandchildren
    # Split makes 2 queries to load the course to depth 2:
    #     - 1 for the structure
    #     - 1 for 5 definitions
    # Split makes 1 query to render the toc:
    #     - 1 for the active version at the start of the bulk operation
    @ddt.data((ModuleStoreEnum.Type.mongo, 3, 0, 0), (ModuleStoreEnum.Type.split, 2, 0, 1))
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
                self.assertIn(toc_section, actual['chapters'])
            self.assertEqual(actual['previous_of_active_section']['url_name'], 'Toy_Videos')
            self.assertEqual(actual['next_of_active_section']['url_name'], 'video_123456789012')


@ddt.ddt
@patch.dict('django.conf.settings.FEATURES', {'ENABLE_SPECIAL_EXAMS': True})
class TestProctoringRendering(SharedModuleStoreTestCase):
    """Check the Table of Contents for a course"""
    @classmethod
    def setUpClass(cls):
        super(TestProctoringRendering, cls).setUpClass()
        cls.course_key = ToyCourseFactory.create().id

    def setUp(self):
        """
        Set up the initial mongo datastores
        """
        super(TestProctoringRendering, self).setUp()
        self.chapter = 'Overview'
        chapter_url = '%s/%s/%s' % ('/courses', self.course_key, self.chapter)
        factory = RequestFactoryNoCsrf()
        self.request = factory.get(chapter_url)
        self.request.user = UserFactory.create()
        self.user = UserFactory.create()
        SoftwareSecurePhotoVerificationFactory.create(user=self.request.user)
        self.modulestore = self.store._get_modulestore_for_courselike(self.course_key)  # pylint: disable=protected-access
        with self.modulestore.bulk_operations(self.course_key):
            self.toy_course = self.store.get_course(self.course_key, depth=2)
            self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
                self.course_key, self.request.user, self.toy_course, depth=2
            )

    @ddt.data(
        (CourseMode.DEFAULT_MODE_SLUG, False, None, None),
        (
            CourseMode.DEFAULT_MODE_SLUG,
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
            CourseMode.DEFAULT_MODE_SLUG,
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
            CourseMode.DEFAULT_MODE_SLUG,
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
            CourseMode.VERIFIED,
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
            CourseMode.VERIFIED,
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
            CourseMode.VERIFIED,
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
            CourseMode.VERIFIED,
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
            CourseMode.VERIFIED,
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
            CourseMode.VERIFIED,
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
        section_actual = self._find_section(actual['chapters'], 'Overview', 'Toy_Videos')

        if expected:
            self.assertIn(expected, [section_actual['proctoring']])
        else:
            # we expect there not to be a 'proctoring' key in the dict
            self.assertNotIn('proctoring', section_actual)
        self.assertIsNone(actual['previous_of_active_section'])
        self.assertEqual(actual['next_of_active_section']['url_name'], u"Welcome")

    @ddt.data(
        (
            CourseMode.DEFAULT_MODE_SLUG,
            True,
            None,
            'Try a proctored exam',
            True
        ),
        (
            CourseMode.DEFAULT_MODE_SLUG,
            True,
            'submitted',
            'You have submitted this practice proctored exam',
            False
        ),
        (
            CourseMode.DEFAULT_MODE_SLUG,
            True,
            'error',
            'There was a problem with your practice proctoring session',
            True
        ),
        (
            CourseMode.VERIFIED,
            False,
            None,
            'This exam is proctored',
            False
        ),
        (
            CourseMode.VERIFIED,
            False,
            'submitted',
            'You have submitted this proctored exam for review',
            True
        ),
        (
            CourseMode.VERIFIED,
            False,
            'verified',
            'Your proctoring session was reviewed successfully',
            False
        ),
        (
            CourseMode.VERIFIED,
            False,
            'rejected',
            'Your proctoring session was reviewed, but did not pass all requirements',
            True
        ),
        (
            CourseMode.VERIFIED,
            False,
            'error',
            'A technical error has occurred with your proctored exam',
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
                self.request.user,
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
        CourseEnrollment.enroll(self.request.user, self.course_key, mode=enrollment_mode)

        set_runtime_service(
            'grades',
            MockGradesService()
        )

        set_runtime_service(
            'certificates',
            MockCertificateService()
        )

        exam_id = create_exam(
            course_id=text_type(self.course_key),
            content_id=text_type(sequence.location),
            exam_name='foo',
            time_limit_mins=10,
            is_proctored=True,
            is_practice_exam=is_practice_exam
        )

        if attempt_status:
            create_exam_attempt(six.text_type(exam_id).encode('utf-8'), self.request.user.id, taking_as_proctored=True)
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


class TestGatedSubsectionRendering(SharedModuleStoreTestCase, MilestonesTestCaseMixin):
    """
    Test the toc for a course is rendered correctly when there is gated content
    """

    @classmethod
    def setUpClass(cls):
        super(TestGatedSubsectionRendering, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course.enable_subsection_gating = True
        cls.course.save()
        cls.store.update_item(cls.course, 0)

    def setUp(self):
        """
        Set up the initial test data
        """
        super(TestGatedSubsectionRendering, self).setUp()

        self.chapter = ItemFactory.create(
            parent=self.course,
            category="chapter",
            display_name="Chapter"
        )
        self.open_seq = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name="Open Sequential"
        )
        self.gated_seq = ItemFactory.create(
            parent=self.chapter,
            category='sequential',
            display_name="Gated Sequential"
        )
        self.request = RequestFactoryNoCsrf().get('%s/%s/%s' % ('/courses', self.course.id, self.chapter.display_name))
        self.request.user = UserFactory()
        self.field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, self.request.user, self.course, depth=2
        )
        gating_api.add_prerequisite(self.course.id, self.open_seq.location)
        gating_api.set_required_content(self.course.id, self.gated_seq.location, self.open_seq.location, 100)

    def _find_url_name(self, toc, url_name):
        """
        Helper to return the TOC section associated with url_name
        """

        for entry in toc:
            if entry['url_name'] == url_name:
                return entry

        return None

    def _find_sequential(self, toc, chapter_url_name, sequential_url_name):
        """
        Helper to return the sequential associated with sequential_url_name
        """

        chapter = self._find_url_name(toc, chapter_url_name)
        if chapter:
            return self._find_url_name(chapter['sections'], sequential_url_name)

        return None

    def test_toc_with_gated_sequential(self):
        """
        Test generation of TOC for a course with a gated subsection
        """
        actual = render.toc_for_course(
            self.request.user,
            self.request,
            self.course,
            self.chapter.display_name,
            self.open_seq.display_name,
            self.field_data_cache
        )
        self.assertIsNotNone(self._find_sequential(actual['chapters'], 'Chapter', 'Open_Sequential'))
        self.assertIsNotNone(self._find_sequential(actual['chapters'], 'Chapter', 'Gated_Sequential'))
        self.assertIsNone(self._find_sequential(actual['chapters'], 'Non-existent_Chapter', 'Non-existent_Sequential'))
        self.assertIsNone(actual['previous_of_active_section'])
        self.assertIsNone(actual['next_of_active_section'])


@ddt.ddt
class TestHtmlModifiers(ModuleStoreTestCase):
    """
    Tests to verify that standard modifications to the output of XModule/XBlock
    student_view are taking place
    """

    def setUp(self):
        super(TestHtmlModifiers, self).setUp()
        self.course = CourseFactory.create()
        self.request = RequestFactoryNoCsrf().get('/')
        self.request.user = self.user
        self.request.session = {}
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

        self.assertEqual(len(PyQuery(result_fragment.content)('div.xblock.xblock-student_view.xmodule_HtmlBlock')), 1)

    def test_xmodule_display_wrapper_disabled(self):
        module = render.get_module(
            self.user,
            self.request,
            self.location,
            self.field_data_cache,
            wrap_xmodule_display=False,
        )
        result_fragment = module.render(STUDENT_VIEW)

        self.assertNotIn('div class="xblock xblock-student_view xmodule_display xmodule_HtmlBlock"',
                         result_fragment.content)

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
            '/c4x/{org}/{course}/asset/file.jpg'.format(
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
        get_course_info_section(self.request, self.request.user, self.course, "handouts")
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
                course_id=text_type(self.course.id)
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


@ddt.ddt
class JsonInitDataTest(ModuleStoreTestCase):
    """Tests for JSON data injected into the JS init function."""

    @ddt.data(
        ({'a': 17}, '''{"a": 17}'''),
        ({'xss': '</script>alert("XSS")'}, r'''{"xss": "\u003c/script\u003ealert(\"XSS\")"}'''),
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
        field_data_cache = FieldDataCache([course, descriptor], course.id, mock_user)
        module = render.get_module_for_descriptor(
            mock_user,
            mock_request,
            descriptor,
            field_data_cache,
            course.id,
            course=course
        )
        html = module.render(STUDENT_VIEW).content
        self.assertIn(json_output, html)
        # No matter what data goes in, there should only be one close-script tag.
        self.assertEqual(html.count("</script>"), 1)


@XBlock.tag("detached")
class DetachedXBlock(XBlock):
    """
    XBlock marked with the 'detached' flag.
    """

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        A simple view that returns just enough to test.
        """
        frag = Fragment(u"Hello there!")
        return frag


@patch.dict('django.conf.settings.FEATURES', {'DISPLAY_DEBUG_INFO_TO_STAFF': True, 'DISPLAY_HISTOGRAMS_TO_STAFF': True})
@patch('lms.djangoapps.courseware.module_render.has_access', Mock(return_value=True, autospec=True))
class TestStaffDebugInfo(SharedModuleStoreTestCase):
    """Tests to verify that Staff Debug Info panel and histograms are displayed to staff."""

    @classmethod
    def setUpClass(cls):
        super(TestStaffDebugInfo, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestStaffDebugInfo, self).setUp()
        self.user = UserFactory.create()
        self.request = RequestFactoryNoCsrf().get('/')
        self.request.user = self.user
        self.request.session = {}

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

    def test_staff_debug_info_score_for_invalid_dropdown(self):
        """
        Verifies that for an invalid drop down problem, the max score is set
        to zero in the html.
        """
        problem_xml = """
        <problem>
            <optionresponse>
              <p>You can use this template as a guide to the simple editor markdown and OLX markup to use for dropdown problems. Edit this component to replace this template with your own assessment.</p>
            <label>Add the question text, or prompt, here. This text is required.</label>
            <description>You can add an optional tip or note related to the prompt like this. </description>
            <optioninput>
                <option correct="False">an incorrect answer</option>
                <option correct="True">the correct answer</option>
                <option correct="True">an incorrect answer</option>
              </optioninput>
            </optionresponse>
        </problem>
        """
        problem_descriptor = ItemFactory.create(
            category='problem',
            data=problem_xml
        )
        module = render.get_module(
            self.user,
            self.request,
            problem_descriptor.location,
            self.field_data_cache
        )
        html_fragment = module.render(STUDENT_VIEW)
        expected_score_override_html = textwrap.dedent("""<div>
        <label for="sd_fs_{block_id}">Score (for override only):</label>
        <input type="text" tabindex="0" id="sd_fs_{block_id}" placeholder="0"/>
        <label for="sd_fs_{block_id}"> / 0</label>
      </div>""")

        self.assertIn(
            expected_score_override_html.format(block_id=problem_descriptor.location.block_id),
            html_fragment.content
        )

    @XBlock.register_temp_plugin(DetachedXBlock, identifier='detached-block')
    def test_staff_debug_info_disabled_for_detached_blocks(self):
        """Staff markup should not be present on detached blocks."""

        descriptor = ItemFactory.create(
            category='detached-block',
            display_name='Detached Block'
        )
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id,
            self.user,
            descriptor
        )
        module = render.get_module(
            self.user,
            self.request,
            descriptor.location,
            field_data_cache,
        )
        result_fragment = module.render(STUDENT_VIEW)
        self.assertNotIn('Staff Debug', result_fragment.content)

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
PER_STUDENT_ANONYMIZED_XBLOCKS = [
    AboutBlock,
    CourseInfoBlock,
    HtmlBlock,
    ProblemBlock,
    StaticTabBlock,
    VideoBlock,
]

# The "set" here is to work around the bug that load_classes returns duplicates for multiply-declared classes.
PER_STUDENT_ANONYMIZED_DESCRIPTORS = sorted(set([
    class_ for (name, class_) in XModuleDescriptor.load_classes()
    if not issubclass(class_, PER_COURSE_ANONYMIZED_DESCRIPTORS)
] + PER_STUDENT_ANONYMIZED_XBLOCKS), key=str)


@ddt.ddt
class TestAnonymousStudentId(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Test that anonymous_student_id is set correctly across a variety of XBlock types
    """

    @classmethod
    def setUpClass(cls):
        super(TestAnonymousStudentId, cls).setUpClass()
        cls.course_key = ToyCourseFactory.create().id
        cls.course = modulestore().get_course(cls.course_key)

    def setUp(self):
        super(TestAnonymousStudentId, self).setUp()
        self.user = UserFactory()

    @patch('lms.djangoapps.courseware.module_render.has_access', Mock(return_value=True, autospec=True))
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
            self.assertEqual(
                # This value is set by observation, so that later changes to the student
                # id computation don't break old data
                '5afe5d9bb03796557ee2614f5c9611fb',
                self._get_anonymous_id(CourseKey.from_string(course_id), descriptor_class)
            )

    @ddt.data(*PER_COURSE_ANONYMIZED_DESCRIPTORS)
    def test_per_course_anonymized_id(self, descriptor_class):
        self.assertEqual(
            # This value is set by observation, so that later changes to the student
            # id computation don't break old data
            'e3b0b940318df9c14be59acb08e78af5',
            self._get_anonymous_id(CourseKey.from_string('MITx/6.00x/2012_Fall'), descriptor_class)
        )

        self.assertEqual(
            # This value is set by observation, so that later changes to the student
            # id computation don't break old data
            'f82b5416c9f54b5ce33989511bb5ef2e',
            self._get_anonymous_id(CourseKey.from_string('MITx/6.00x/2013_Spring'), descriptor_class)
        )


@patch('common.djangoapps.track.views.eventtracker', autospec=True)
class TestModuleTrackingContext(SharedModuleStoreTestCase):
    """
    Ensure correct tracking information is included in events emitted during XBlock callback handling.
    """

    @classmethod
    def setUpClass(cls):
        super(TestModuleTrackingContext, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestModuleTrackingContext, self).setUp()

        self.user = UserFactory.create()
        self.request = RequestFactoryNoCsrf().get('/')
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
        self.assertEqual(problem_display_name, module_info['display_name'])

    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    @patch('xmodule.modulestore.mongo.base.CachingDescriptorSystem.applicable_aside_types',
           lambda self, block: ['test_aside'])
    @patch('lms.djangoapps.lms_xblock.runtime.LmsModuleSystem.applicable_aside_types',
           lambda self, block: ['test_aside'])
    def test_context_contains_aside_info(self, mock_tracker):
        """
        Check that related xblock asides populate information in the 'problem_check' event in case
        the 'get_event_context' method is exist
        """
        problem_display_name = u'Test Problem'

        def get_event_context(self, event_type, event):  # pylint: disable=unused-argument
            """
            This method return data that should be associated with the "check_problem" event
            """
            return {'content': 'test1', 'data_field': 'test2'}

        AsideTestType.get_event_context = get_event_context

        # for different operations, there are different number of context calls.
        # We are sending this `call_idx` to get the mock call that we are interested in.
        context_info = self.handle_callback_and_get_context_info(mock_tracker, problem_display_name, call_idx=4)

        self.assertIn('asides', context_info)
        self.assertIn('test_aside', context_info['asides'])
        self.assertIn('content', context_info['asides']['test_aside'])
        self.assertEqual(context_info['asides']['test_aside']['content'], 'test1')
        self.assertIn('data_field', context_info['asides']['test_aside'])
        self.assertEqual(context_info['asides']['test_aside']['data_field'], 'test2')

    def handle_callback_and_get_context_info(self,
                                             mock_tracker,
                                             problem_display_name=None,
                                             call_idx=0):
        """
        Creates a fake module, invokes the callback and extracts the 'context'
        metadata from the emitted problem_check event.
        """

        descriptor_kwargs = {
            'category': 'problem',
            'data': self.problem_xml
        }
        if problem_display_name:
            descriptor_kwargs['display_name'] = problem_display_name

        descriptor = ItemFactory.create(**descriptor_kwargs)
        with patch('lms.djangoapps.courseware.module_render.tracker') as mock_tracker_for_context:
            render.handle_xblock_callback(
                self.request,
                text_type(self.course.id),
                quote_slashes(text_type(descriptor.location)),
                'xmodule_handler',
                'problem_check',
            )

            self.assertEquals(len(mock_tracker.emit.mock_calls), 1)
            mock_call = mock_tracker.emit.mock_calls[0]
            event = mock_call[2]

            self.assertEquals(event['name'], 'problem_check')

            # for different operations, there are different number of context calls.
            # We are sending this `call_idx` to get the mock call that we are interested in.
            context = mock_tracker_for_context.get_tracker.mock_calls[call_idx][1][1]

            return context

    def handle_callback_and_get_module_info(self, mock_tracker, problem_display_name=None):
        """
        Creates a fake module, invokes the callback and extracts the 'module'
        metadata from the emitted problem_check event.
        """
        event = self.handle_callback_and_get_context_info(
            mock_tracker, problem_display_name, call_idx=1
        )
        return event['module']

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
            self.assertEqual(module_info['original_usage_key'], text_type(original_usage_key))
            self.assertIn('original_usage_version', module_info)
            self.assertEqual(module_info['original_usage_version'], text_type(original_usage_version))


class TestXmoduleRuntimeEvent(TestSubmittingProblems):
    """
    Inherit from TestSubmittingProblems to get functionality that set up a course and problems structure
    """

    def setUp(self):
        super(TestXmoduleRuntimeEvent, self).setUp()
        self.homework = self.add_graded_section_to_course('homework')
        self.problem = self.add_dropdown_to_section(self.homework.location, 'p1', 1)
        self.grade_dict = {'value': 0.18, 'max_value': 32}
        self.delete_dict = {'value': None, 'max_value': None}

    def get_module_for_user(self, user):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course.id, user, self.course, depth=2)

        return render.get_module(
            user,
            mock_request,
            self.problem.location,
            field_data_cache,
        )

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

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_RAW_SCORE_CHANGED.send')
    def test_score_change_signal(self, send_mock):
        """Test that a Django signal is generated when a score changes"""
        with freeze_time(datetime.now().replace(tzinfo=pytz.UTC)):
            self.set_module_grade_using_publish(self.grade_dict)
            expected_signal_kwargs = {
                'sender': None,
                'raw_possible': self.grade_dict['max_value'],
                'raw_earned': self.grade_dict['value'],
                'weight': None,
                'user_id': self.student_user.id,
                'course_id': text_type(self.course.id),
                'usage_id': text_type(self.problem.location),
                'only_if_higher': None,
                'modified': datetime.now().replace(tzinfo=pytz.UTC),
                'score_db_table': 'csm',
                'score_deleted': None,
                'grader_response': None
            }
            send_mock.assert_called_with(**expected_signal_kwargs)


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

        return render.get_module(
            user,
            mock_request,
            item.location,
            field_data_cache,
        )

    def test_rebind_module_to_new_users(self):
        module = self.get_module_for_user(self.user, self.problem)

        # Bind the module to another student, which will remove "correct_map"
        # from the module's _field_data_cache and _dirty_fields.
        user2 = UserFactory.create()
        module.bind_for_student(module.system, user2.id)

        # XBlock's save method assumes that if a field is in _dirty_fields,
        # then it's also in _field_data_cache. If this assumption
        # doesn't hold, then we get an error trying to bind this module
        # to a third student, since we've removed "correct_map" from
        # _field_data cache, but not _dirty_fields, when we bound
        # this module to the second student. (TNL-2640)
        user3 = UserFactory.create()
        module.bind_for_student(module.system, user3.id)

    def test_rebind_noauth_module_to_user_not_anonymous(self):
        """
        Tests that an exception is thrown when rebind_noauth_module_to_user is run from a
        module bound to a real user
        """
        module = self.get_module_for_user(self.user)
        user2 = UserFactory()
        user2.id = 2
        with self.assertRaisesRegex(
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
        module.system.rebind_noauth_module_to_user(module._xmodule, user2)  # pylint: disable=protected-access
        self.assertTrue(module)
        self.assertEqual(module.system.anonymous_student_id, anonymous_id_for_user(user2, self.course.id))
        self.assertEqual(module.scope_ids.user_id, user2.id)
        self.assertEqual(module._xmodule.scope_ids.user_id, user2.id)  # pylint: disable=protected-access


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
        self.request_factory = RequestFactoryNoCsrf()

    @ddt.data('xblock', 'xmodule')
    @XBlock.register_temp_plugin(PureXBlock, identifier='xblock')
    @XBlock.register_temp_plugin(EmptyXModuleDescriptor, identifier='xmodule')
    @patch.object(render, 'make_track_function')
    def test_event_publishing(self, block_type, mock_track_function):
        request = self.request_factory.get('')
        request.user = self.mock_user
        course = CourseFactory()
        descriptor = ItemFactory(category=block_type, parent=course)
        field_data_cache = FieldDataCache([course, descriptor], course.id, self.mock_user)
        block = render.get_module(self.mock_user, request, descriptor.location, field_data_cache)

        event_type = 'event_type'
        event = {'event': 'data'}

        block.runtime.publish(block, event_type, event)

        mock_track_function.assert_called_once_with(request)

        mock_track_function.return_value.assert_called_once_with(event_type, event)


@ddt.ddt
class LMSXBlockServiceBindingTest(SharedModuleStoreTestCase):
    """
    Tests that the LMS Module System (XBlock Runtime) provides an expected set of services.
    """

    @classmethod
    def setUpClass(cls):
        super(LMSXBlockServiceBindingTest, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        """
        Set up the user and other fields that will be used to instantiate the runtime.
        """
        super(LMSXBlockServiceBindingTest, self).setUp()
        self.user = UserFactory()
        self.student_data = Mock()
        self.track_function = Mock()
        self.xqueue_callback_url_prefix = Mock()
        self.request_token = Mock()

    @XBlock.register_temp_plugin(PureXBlock, identifier='pure')
    @ddt.data("user", "i18n", "fs", "field-data", "bookmarks")
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
USER_NUMBERS = list(range(2))


@ddt.ddt
class TestFilteredChildren(SharedModuleStoreTestCase):
    """
    Tests that verify access to XBlock/XModule children work correctly
    even when those children are filtered by the runtime when loaded.
    """

    @classmethod
    def setUpClass(cls):
        super(TestFilteredChildren, cls).setUpClass()
        cls.course = CourseFactory.create()

    # pylint: disable=attribute-defined-outside-init
    def setUp(self):
        super(TestFilteredChildren, self).setUp()
        self.users = {number: UserFactory() for number in USER_NUMBERS}

        self._old_has_access = render.has_access
        patcher = patch('lms.djangoapps.courseware.module_render.has_access', self._has_access)
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
            for user in six.itervalues(self.users)
        }

        self.all_children = sum(list(self.children_for_user.values()), [])

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
            return AccessResponse(True)
        return AccessResponse(key in self.children_for_user[user])

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
        self.assertEqual(set(child_usage_ids), set(child.scope_ids.usage_id for child in block.get_children()))


@ddt.ddt
class TestDisabledXBlockTypes(ModuleStoreTestCase):
    """
    Tests that verify disabled XBlock types are not loaded.
    """

    def setUp(self):
        super(TestDisabledXBlockTypes, self).setUp()
        XBlockConfiguration(name='video', enabled=False).save()

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_get_item(self, default_ms):
        with self.store.default_store(default_ms):
            course = CourseFactory()
            self._verify_descriptor('video', course, 'RawDescriptorWithMixins')

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_dynamic_updates(self, default_ms):
        """Tests that the list of disabled xblocks can dynamically update."""
        with self.store.default_store(default_ms):
            course = CourseFactory()
            item_usage_id = self._verify_descriptor('problem', course, 'ProblemBlockWithMixins')
            XBlockConfiguration(name='problem', enabled=False).save()

            # First verify that the cached value is used until there is a new request cache.
            self._verify_descriptor('problem', course, 'ProblemBlockWithMixins', item_usage_id)

            # Now simulate a new request cache.
            self.store.request_cache.data.clear()
            self._verify_descriptor('problem', course, 'RawDescriptorWithMixins', item_usage_id)

    def _verify_descriptor(self, category, course, descriptor, item_id=None):
        """
        Helper method that gets an item with the specified category from the
        modulestore and verifies that it has the expected descriptor name.

        Returns the item's usage_id.
        """
        if not item_id:
            item = ItemFactory(category=category, parent=course)
            item_id = item.scope_ids.usage_id

        item = self.store.get_item(item_id)
        self.assertEqual(item.__class__.__name__, descriptor)
        return item_id
