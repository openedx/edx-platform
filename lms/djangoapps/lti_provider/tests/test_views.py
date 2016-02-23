"""
Tests for the LTI provider views
"""

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import RequestFactory
from mock import patch, MagicMock, ANY

from courseware.testutils import RenderXBlockTestMixin
from lti_provider import views, models
from lti_provider.signature_validator import SignatureValidator
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.contrib.auth.models import User
from student.models import CourseEnrollment

LTI_DEFAULT_PARAMS = {
    'roles': u'Instructor,urn:lti:instrole:ims/lis/Administrator',
    'context_id': u'lti_launch_context_id',
    'oauth_version': u'1.0',
    'oauth_consumer_key': u'consumer_key',
    'oauth_signature': u'OAuth Signature',
    'oauth_signature_method': u'HMAC-SHA1',
    'oauth_timestamp': u'OAuth Timestamp',
    'oauth_nonce': u'OAuth Nonce',
    'user_id': u'LTI_User',
}

LTI_OPTIONAL_PARAMS = {
    'lis_result_sourcedid': u'result sourcedid',
    'lis_outcome_service_url': u'outcome service URL',
    'lis_person_contact_email_primary': u'rob.smith@example.com',
    'lis_person_name_given': u'Rob',
    'lis_person_name_family': u'Smith',
    'tool_consumer_instance_guid': u'consumer instance guid'
}

COURSE_KEY = CourseLocator(org='some_org', course='some_course', run='some_run')
USAGE_KEY = BlockUsageLocator(course_key=COURSE_KEY, block_type='problem', block_id='block_id')

COURSE_PARAMS = {
    'course_key': COURSE_KEY,
    'usage_key': USAGE_KEY
}


ALL_PARAMS = dict(LTI_DEFAULT_PARAMS.items() + COURSE_PARAMS.items())


def build_launch_request(authenticated=True):
    """
    Helper method to create a new request object for the LTI launch.
    """
    request = RequestFactory().post('/')
    request.user = UserFactory.create()
    request.user.is_authenticated = MagicMock(return_value=authenticated)
    request.session = {}
    request.POST.update(LTI_DEFAULT_PARAMS)
    return request


class LtiTestMixin(object):
    """
    Mixin for LTI tests
    """
    @patch.dict('django.conf.settings.FEATURES', {'ENABLE_LTI_PROVIDER': True})
    def setUp(self):
        super(LtiTestMixin, self).setUp()
        # Always accept the OAuth signature
        SignatureValidator.verify = MagicMock(return_value=True)
        self.consumer = models.LtiConsumer(
            consumer_name='consumer',
            consumer_key=LTI_DEFAULT_PARAMS['oauth_consumer_key'],
            consumer_secret='secret'
        )
        self.consumer.save()


class LtiLaunchTest(LtiTestMixin, TestCase):
    """
    Tests for the lti_launch view
    """
    @patch('lti_provider.views.render_courseware')
    @patch('lti_provider.views.authenticate_lti_user')
    @patch('lti_provider.views.enroll_user_to_course')
    def test_valid_launch(self, enroll_mock, _authenticate, render):
        """
        Verifies that the LTI launch succeeds when passed a valid request.
        """
        request = build_launch_request()
        views.lti_launch(request, unicode(COURSE_KEY), unicode(USAGE_KEY))
        render.assert_called_with(request, USAGE_KEY)
        enroll_mock.assert_called_with(request.user, COURSE_KEY)

    @patch('lti_provider.views.render_courseware')
    @patch('lti_provider.views.store_outcome_parameters')
    @patch('lti_provider.views.authenticate_lti_user')
    def test_outcome_service_registered(self, _authenticate, store_params, _render):
        """
        Verifies that the LTI launch succeeds when passed a valid request.
        """
        request = build_launch_request()
        views.lti_launch(
            request,
            unicode(COURSE_PARAMS['course_key']),
            unicode(COURSE_PARAMS['usage_key'])
        )
        store_params.assert_called_with(ALL_PARAMS, request.user, self.consumer)

    def launch_with_missing_parameter(self, missing_param):
        """
        Helper method to remove a parameter from the LTI launch and call the view
        """
        request = build_launch_request()
        del request.POST[missing_param]
        return views.lti_launch(request, None, None)

    def test_launch_with_missing_parameters(self):
        """
        Runs through all required LTI parameters and verifies that the lti_launch
        view returns Bad Request if any of them are missing.
        """
        for missing_param in views.REQUIRED_PARAMETERS:
            response = self.launch_with_missing_parameter(missing_param)
            self.assertEqual(
                response.status_code, 400,
                'Launch should fail when parameter ' + missing_param + ' is missing'
            )

    def test_launch_with_disabled_feature_flag(self):
        """
        Verifies that the LTI launch will fail if the ENABLE_LTI_PROVIDER flag
        is not set
        """
        with patch.dict('django.conf.settings.FEATURES', {'ENABLE_LTI_PROVIDER': False}):
            request = build_launch_request()
            response = views.lti_launch(request, None, None)
            self.assertEqual(response.status_code, 403)

    def test_forbidden_if_signature_fails(self):
        """
        Verifies that the view returns Forbidden if the LTI OAuth signature is
        incorrect.
        """
        SignatureValidator.verify = MagicMock(return_value=False)
        request = build_launch_request()
        response = views.lti_launch(request, None, None)
        self.assertEqual(response.status_code, 403)

    @patch('lti_provider.views.render_courseware')
    def test_lti_consumer_record_supplemented_with_guid(self, _render):
        SignatureValidator.verify = MagicMock(return_value=False)
        request = build_launch_request()
        request.POST.update(LTI_OPTIONAL_PARAMS)
        with self.assertNumQueries(3):
            views.lti_launch(request, None, None)
        consumer = models.LtiConsumer.objects.get(
            consumer_key=LTI_DEFAULT_PARAMS['oauth_consumer_key']
        )
        self.assertEqual(consumer.instance_guid, u'consumer instance guid')

    @patch('lti_provider.views.render_courseware')
    @patch('lti_provider.views.authenticate_lti_user')
    def test_lti_optional_param_email_is_used(self, _authenticate, _render):
        request = build_launch_request()
        if not hasattr(request, 'POST'):
            request.POST = {}
        request.POST.update(LTI_OPTIONAL_PARAMS)
        views.lti_launch(request, unicode(COURSE_KEY), unicode(USAGE_KEY))
        lti_params = {'email': 'rob.smith@example.com', 'first_name': 'Rob', 'last_name': 'Smith'}
        _authenticate.assert_called_with(ANY, ANY, ANY, lti_params)

    def test_enroll_user_to_course(self):
        email = 'rob.smith@example.com'
        user = User.objects.create_user(
            username=email,
            password='password',
            email=email,
        )
        views.enroll_user_to_course(user, COURSE_KEY)
        self.assertTrue(CourseEnrollment.is_enrolled(user, COURSE_KEY))
        with self.assertNumQueries(1):
            #don't enroll 2d time
            views.enroll_user_to_course(user, COURSE_KEY)


class LtiLaunchTestRender(LtiTestMixin, RenderXBlockTestMixin, ModuleStoreTestCase):
    """
    Tests for the rendering returned by lti_launch view.
    This class overrides the get_response method, which is used by
    the tests defined in RenderXBlockTestMixin.
    """

    def get_response(self, url_encoded_params=None):
        """
        Overridable method to get the response from the endpoint that is being tested.
        """
        lti_launch_url = reverse(
            'lti_provider_launch',
            kwargs={
                'course_id': unicode(self.course.id),
                'usage_id': unicode(self.html_block.location)
            }
        )
        if url_encoded_params:
            lti_launch_url += '?' + url_encoded_params
        SignatureValidator.verify = MagicMock(return_value=True)
        return self.client.post(lti_launch_url, data=LTI_DEFAULT_PARAMS)

    # The following test methods override the base tests for verifying access
    # by unenrolled and unauthenticated students, since there is a discrepancy
    # of access rules between the 2 endpoints (LTI and xBlock_render).
    # TODO fix this access discrepancy to the same underlying data.

    def test_unenrolled_student(self):
        """
        Override since LTI allows access to unenrolled students.
        """
        self.setup_course()
        self.setup_user(admin=False, enroll=False, login=True)
        self.verify_response()

    def test_unauthenticated(self):
        """
        Override since LTI allows access to unauthenticated users.
        """
        self.setup_course()
        self.setup_user(admin=False, enroll=True, login=False)
        self.verify_response()
