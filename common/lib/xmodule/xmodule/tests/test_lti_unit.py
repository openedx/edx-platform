# -*- coding: utf-8 -*-
"""Test for LTI Xmodule functional logic."""

from mock import Mock, patch, PropertyMock
import textwrap
from lxml import etree
from webob.request import Request
from copy import copy
import urllib


from xmodule.lti_module import LTIDescriptor
from xmodule.lti_2_util import LTIError

from . import LogicTest


class LTIModuleTest(LogicTest):
    """Logic tests for LTI module."""
    descriptor_class = LTIDescriptor

    def setUp(self):
        super(LTIModuleTest, self).setUp()
        self.environ = {'wsgi.url_scheme': 'http', 'REQUEST_METHOD': 'POST'}
        self.request_body_xml_template = textwrap.dedent("""
            <?xml version = "1.0" encoding = "UTF-8"?>
                <imsx_POXEnvelopeRequest xmlns = "{namespace}">
                  <imsx_POXHeader>
                    <imsx_POXRequestHeaderInfo>
                      <imsx_version>V1.0</imsx_version>
                      <imsx_messageIdentifier>{messageIdentifier}</imsx_messageIdentifier>
                    </imsx_POXRequestHeaderInfo>
                  </imsx_POXHeader>
                  <imsx_POXBody>
                    <{action}>
                      <resultRecord>
                        <sourcedGUID>
                          <sourcedId>{sourcedId}</sourcedId>
                        </sourcedGUID>
                        <result>
                          <resultScore>
                            <language>en-us</language>
                            <textString>{grade}</textString>
                          </resultScore>
                        </result>
                      </resultRecord>
                    </{action}>
                  </imsx_POXBody>
                </imsx_POXEnvelopeRequest>
            """)
        self.system.get_real_user = Mock()
        self.system.publish = Mock()
        self.system.rebind_noauth_module_to_user = Mock()

        self.user_id = self.xmodule.runtime.anonymous_student_id
        self.lti_id = self.xmodule.lti_id
        self.unquoted_resource_link_id = u'{}-i4x-2-3-lti-31de800015cf4afb973356dbe81496df'.format(self.xmodule.runtime.hostname)

        sourced_id = u':'.join(urllib.quote(i) for i in (self.lti_id, self.unquoted_resource_link_id, self.user_id))

        self.defaults = {
            'namespace': "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0",
            'sourcedId': sourced_id,
            'action': 'replaceResultRequest',
            'grade': 0.5,
            'messageIdentifier': '528243ba5241b',
        }

    def get_request_body(self, params=None):
        """Fetches the body of a request specified by params"""
        if params is None:
            params = {}
        data = copy(self.defaults)

        data.update(params)
        return self.request_body_xml_template.format(**data)

    def get_response_values(self, response):
        """Gets the values from the given response"""
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(response.body.strip(), parser=parser)
        lti_spec_namespace = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"
        namespaces = {'def': lti_spec_namespace}

        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text
        description = root.xpath("//def:imsx_description", namespaces=namespaces)[0].text
        message_identifier = root.xpath("//def:imsx_messageIdentifier", namespaces=namespaces)[0].text
        imsx_pox_body = root.xpath("//def:imsx_POXBody", namespaces=namespaces)[0]

        try:
            action = imsx_pox_body.getchildren()[0].tag.replace('{' + lti_spec_namespace + '}', '')
        except Exception:  # pylint: disable=broad-except
            action = None

        return {
            'code_major': code_major,
            'description': description,
            'messageIdentifier': message_identifier,
            'action': action
        }

    @patch('xmodule.lti_module.LTIModule.get_client_key_secret', return_value=('test_client_key', u'test_client_secret'))
    def test_authorization_header_not_present(self, _get_key_secret):
        """
        Request has no Authorization header.

        This is an unknown service request, i.e., it is not a part of the original service specification.
        """
        request = Request(self.environ)
        request.body = self.get_request_body()
        response = self.xmodule.grade_handler(request, '')
        real_response = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'OAuth verification error: Malformed authorization header',
            'messageIdentifier': self.defaults['messageIdentifier'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)

    @patch('xmodule.lti_module.LTIModule.get_client_key_secret', return_value=('test_client_key', u'test_client_secret'))
    def test_authorization_header_empty(self, _get_key_secret):
        """
        Request Authorization header has no value.

        This is an unknown service request, i.e., it is not a part of the original service specification.
        """
        request = Request(self.environ)
        request.authorization = "bad authorization header"
        request.body = self.get_request_body()
        response = self.xmodule.grade_handler(request, '')
        real_response = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'OAuth verification error: Malformed authorization header',
            'messageIdentifier': self.defaults['messageIdentifier'],
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)

    def test_real_user_is_none(self):
        """
        If we have no real user, we should send back failure response.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        self.xmodule.has_score = True
        self.system.get_real_user = Mock(return_value=None)
        request = Request(self.environ)
        request.body = self.get_request_body()
        response = self.xmodule.grade_handler(request, '')
        real_response = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'User not found.',
            'messageIdentifier': self.defaults['messageIdentifier'],
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)

    def test_grade_not_in_range(self):
        """
        Grade returned from Tool Provider is outside the range 0.0-1.0.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        request = Request(self.environ)
        request.body = self.get_request_body(params={'grade': '10'})
        response = self.xmodule.grade_handler(request, '')
        real_response = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'Request body XML parsing error: score value outside the permitted range of 0-1.',
            'messageIdentifier': 'unknown',
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)

    def test_bad_grade_decimal(self):
        """
        Grade returned from Tool Provider doesn't use a period as the decimal point.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        request = Request(self.environ)
        request.body = self.get_request_body(params={'grade': '0,5'})
        response = self.xmodule.grade_handler(request, '')
        real_response = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'Request body XML parsing error: invalid literal for float(): 0,5',
            'messageIdentifier': 'unknown',
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)

    def test_unsupported_action(self):
        """
        Action returned from Tool Provider isn't supported.
        `replaceResultRequest` is supported only.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        request = Request(self.environ)
        request.body = self.get_request_body({'action': 'wrongAction'})
        response = self.xmodule.grade_handler(request, '')
        real_response = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'unsupported',
            'description': 'Target does not support the requested operation.',
            'messageIdentifier': self.defaults['messageIdentifier'],
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)

    def test_good_request(self):
        """
        Response from Tool Provider is correct.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        self.xmodule.has_score = True
        request = Request(self.environ)
        request.body = self.get_request_body()
        response = self.xmodule.grade_handler(request, '')
        description_expected = 'Score for {sourcedId} is now {score}'.format(
            sourcedId=self.defaults['sourcedId'],
            score=self.defaults['grade'],
        )
        real_response = self.get_response_values(response)
        expected_response = {
            'action': 'replaceResultResponse',
            'code_major': 'success',
            'description': description_expected,
            'messageIdentifier': self.defaults['messageIdentifier'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_response)
        self.assertEqual(self.xmodule.module_score, float(self.defaults['grade']))

    def test_user_id(self):
        expected_user_id = unicode(urllib.quote(self.xmodule.runtime.anonymous_student_id))
        real_user_id = self.xmodule.get_user_id()
        self.assertEqual(real_user_id, expected_user_id)

    def test_outcome_service_url(self):
        mock_url_prefix = 'https://hostname/'
        test_service_name = "test_service"

        def mock_handler_url(block, handler_name, **kwargs):  # pylint: disable=unused-argument
            """Mock function for returning fully-qualified handler urls"""
            return mock_url_prefix + handler_name

        self.xmodule.runtime.handler_url = Mock(side_effect=mock_handler_url)
        real_outcome_service_url = self.xmodule.get_outcome_service_url(service_name=test_service_name)
        self.assertEqual(real_outcome_service_url, mock_url_prefix + test_service_name)

    def test_resource_link_id(self):
        with patch('xmodule.lti_module.LTIModule.location', new_callable=PropertyMock):
            self.xmodule.location.html_id = lambda: 'i4x-2-3-lti-31de800015cf4afb973356dbe81496df'
            expected_resource_link_id = unicode(urllib.quote(self.unquoted_resource_link_id))
            real_resource_link_id = self.xmodule.get_resource_link_id()
            self.assertEqual(real_resource_link_id, expected_resource_link_id)

    def test_lis_result_sourcedid(self):
        expected_sourced_id = u':'.join(urllib.quote(i) for i in (
            self.system.course_id.to_deprecated_string(),
            self.xmodule.get_resource_link_id(),
            self.user_id
        ))
        real_lis_result_sourcedid = self.xmodule.get_lis_result_sourcedid()
        self.assertEqual(real_lis_result_sourcedid, expected_sourced_id)

    def test_client_key_secret(self):
        """
        LTI module gets client key and secret provided.
        """
        #this adds lti passports to system
        mocked_course = Mock(lti_passports=['lti_id:test_client:test_secret'])
        modulestore = Mock()
        modulestore.get_course.return_value = mocked_course
        runtime = Mock(modulestore=modulestore)
        self.xmodule.descriptor.runtime = runtime
        self.xmodule.lti_id = "lti_id"
        key, secret = self.xmodule.get_client_key_secret()
        expected = ('test_client', 'test_secret')
        self.assertEqual(expected, (key, secret))

    def test_client_key_secret_not_provided(self):
        """
        LTI module attempts to get client key and secret provided in cms.

        There are key and secret but not for specific LTI.
        """

        #this adds lti passports to system
        mocked_course = Mock(lti_passports=['test_id:test_client:test_secret'])
        modulestore = Mock()
        modulestore.get_course.return_value = mocked_course
        runtime = Mock(modulestore=modulestore)
        self.xmodule.descriptor.runtime = runtime
        #set another lti_id
        self.xmodule.lti_id = "another_lti_id"
        key_secret = self.xmodule.get_client_key_secret()
        expected = ('', '')
        self.assertEqual(expected, key_secret)

    def test_bad_client_key_secret(self):
        """
        LTI module attempts to get client key and secret provided in cms.

        There are key and secret provided in wrong format.
        """
        #this adds lti passports to system
        mocked_course = Mock(lti_passports=['test_id_test_client_test_secret'])
        modulestore = Mock()
        modulestore.get_course.return_value = mocked_course
        runtime = Mock(modulestore=modulestore)
        self.xmodule.descriptor.runtime = runtime
        self.xmodule.lti_id = 'lti_id'
        with self.assertRaises(LTIError):
            self.xmodule.get_client_key_secret()

    @patch('xmodule.lti_module.signature.verify_hmac_sha1', Mock(return_value=True))
    @patch('xmodule.lti_module.LTIModule.get_client_key_secret', Mock(return_value=('test_client_key', u'test_client_secret')))
    def test_successful_verify_oauth_body_sign(self):
        """
        Test if OAuth signing was successful.
        """
        try:
            self.xmodule.verify_oauth_body_sign(self.get_signed_grade_mock_request())
        except LTIError as err:
            self.fail("verify_oauth_body_sign() raised LTIError: " + err.message)

    def test_wrong_xml_namespace(self):
        """
        Test wrong XML Namespace.

        Tests that tool provider returned grade back with wrong XML Namespace.
        """
        with self.assertRaises(IndexError):
            mocked_request = self.get_signed_grade_mock_request(namespace_lti_v1p1=False)
            self.xmodule.parse_grade_xml_body(mocked_request.body)

    def test_parse_grade_xml_body(self):
        """
        Test XML request body parsing.

        Tests that xml body was parsed successfully.
        """
        mocked_request = self.get_signed_grade_mock_request()
        message_identifier, sourced_id, grade, action = self.xmodule.parse_grade_xml_body(mocked_request.body)
        self.assertEqual(self.defaults['messageIdentifier'], message_identifier)
        self.assertEqual(self.defaults['sourcedId'], sourced_id)
        self.assertEqual(self.defaults['grade'], grade)
        self.assertEqual(self.defaults['action'], action)

    @patch('xmodule.lti_module.signature.verify_hmac_sha1', Mock(return_value=False))
    @patch('xmodule.lti_module.LTIModule.get_client_key_secret', Mock(return_value=('test_client_key', u'test_client_secret')))
    def test_failed_verify_oauth_body_sign(self):
        """
        Oauth signing verify fail.
        """
        with self.assertRaises(LTIError):
            req = self.get_signed_grade_mock_request()
            self.xmodule.verify_oauth_body_sign(req)

    def get_signed_grade_mock_request(self, namespace_lti_v1p1=True):
        """
        Example of signed request from LTI Provider.

        When `namespace_v1p0` is set to True then the default namespase from
        LTI 1.1 will be used. Otherwise fake namespace will be added to XML.
        """
        mock_request = Mock()
        mock_request.headers = {  # pylint: disable=no-space-before-operator
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': u'OAuth oauth_nonce="135685044251684026041377608307", \
                oauth_timestamp="1234567890", oauth_version="1.0", \
                oauth_signature_method="HMAC-SHA1", \
                oauth_consumer_key="test_client_key", \
                oauth_signature="my_signature%3D", \
                oauth_body_hash="JEpIArlNCeV4ceXxric8gJQCnBw="'
        }
        mock_request.url = u'http://testurl'
        mock_request.http_method = u'POST'

        params = {}
        if not namespace_lti_v1p1:
            params = {
                'namespace': "http://www.fakenamespace.com/fake"
            }
        mock_request.body = self.get_request_body(params)

        return mock_request

    def test_good_custom_params(self):
        """
        Custom parameters are presented in right format.
        """
        self.xmodule.custom_parameters = ['test_custom_params=test_custom_param_value']
        self.xmodule.get_client_key_secret = Mock(return_value=('test_client_key', 'test_client_secret'))
        self.xmodule.oauth_params = Mock()
        self.xmodule.get_input_fields()
        self.xmodule.oauth_params.assert_called_with(
            {u'custom_test_custom_params': u'test_custom_param_value'},
            'test_client_key', 'test_client_secret'
        )

    def test_bad_custom_params(self):
        """
        Custom parameters are presented in wrong format.
        """
        bad_custom_params = ['test_custom_params: test_custom_param_value']
        self.xmodule.custom_parameters = bad_custom_params
        self.xmodule.get_client_key_secret = Mock(return_value=('test_client_key', 'test_client_secret'))
        self.xmodule.oauth_params = Mock()
        with self.assertRaises(LTIError):
            self.xmodule.get_input_fields()

    def test_max_score(self):
        self.xmodule.weight = 100.0

        self.assertFalse(self.xmodule.has_score)
        self.assertEqual(self.xmodule.max_score(), None)

        self.xmodule.has_score = True

        self.assertEqual(self.xmodule.max_score(), 100.0)

    def test_context_id(self):
        """
        Tests that LTI parameter context_id is equal to course_id.
        """
        self.assertEqual(self.system.course_id.to_deprecated_string(), self.xmodule.context_id)
