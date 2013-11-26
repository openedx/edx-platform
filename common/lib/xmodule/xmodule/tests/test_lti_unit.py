# -*- coding: utf-8 -*-
"""Test for LTI Xmodule functional logic."""

from mock import Mock
import textwrap
from lxml import etree
from webob.request import Request
from copy import copy
import urllib

from xmodule.lti_module import LTIModuleDescriptor

from . import LogicTest


class LTIModuleTest(LogicTest):
    """Logic tests for LTI module."""
    descriptor_class = LTIModuleDescriptor

    def setUp(self):
        super(LTIModuleTest, self).setUp()
        self.environ = {'wsgi.url_scheme': 'http', 'REQUEST_METHOD': 'POST'}
        self.request_body_xml_template = textwrap.dedent("""
            <?xml version = "1.0" encoding = "UTF-8"?>
                <imsx_POXEnvelopeRequest xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
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
        self.xmodule.get_client_key_secret = Mock(return_value=('key', 'secret'))
        self.system.publish = Mock()

        user_id = self.xmodule.runtime.anonymous_student_id
        lti_id = self.xmodule.lti_id
        module_id = '//MITx/999/lti/'

        sourcedId = u':'.join(urllib.quote(i) for i in (lti_id, module_id, user_id))

        self.DEFAULTS = {
            'sourcedId': sourcedId,
            'action': 'replaceResultRequest',
            'grade': '0.5',
            'messageIdentifier': '528243ba5241b',
        }

    def get_request_body(self, params={}):
        data = copy(self.DEFAULTS)

        data.update(params)
        return self.request_body_xml_template.format(**data)

    def get_response_values(self, response):
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(response.body.strip(), parser=parser)
        lti_spec_namespace = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"
        namespaces = {'def': lti_spec_namespace}

        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text
        description = root.xpath("//def:imsx_description", namespaces=namespaces)[0].text
        messageIdentifier = root.xpath("//def:imsx_messageIdentifier", namespaces=namespaces)[0].text
        imsx_POXBody = root.xpath("//def:imsx_POXBody", namespaces=namespaces)[0]

        try:
            action = imsx_POXBody.getchildren()[0].tag.replace('{'+lti_spec_namespace+'}', '')
        except Exception:
            action = None

        return {
            'code_major': code_major,
            'description': description,
            'messageIdentifier': messageIdentifier,
            'action': action
        }

    def test_authorization_header_not_present(self):
        """
        Request has no Authorization header.
        This is an unknown service request, i.e., it is not a part of the original service specification.
        """
        incorrect_request = Request(self.environ)
        incorrect_request.body = self.get_request_body()
        response = self.xmodule.grade_handler(incorrect_request, '')
        real_repsonse = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'The request has failed.',
            'messageIdentifier': self.DEFAULTS['messageIdentifier'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_repsonse)

    def test_authorization_header_empty(self):
        """
        Request Authorization header has no value.
        This is an unknown service request, i.e., it is not a part of the original service specification.
        """
        incorrect_request = Request(self.environ)
        incorrect_request.authorization = "bad authorization header"
        incorrect_request.body = self.get_request_body()
        response = self.xmodule.grade_handler(incorrect_request, '')
        real_repsonse = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'The request has failed.',
            'messageIdentifier': self.DEFAULTS['messageIdentifier'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_repsonse)

    def test_grade_not_in_range(self):
        """
        Grade returned from Tool Provider is outside the range 0.0-1.0.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        incorrect_request = Request(self.environ)
        incorrect_request.body = self.get_request_body(params={'grade': '10'})
        response = self.xmodule.grade_handler(incorrect_request, '')
        real_repsonse = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'The request has failed.',
            'messageIdentifier': 'unknown',
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_repsonse)

    def test_bad_grade_decimal(self):
        """
        Grade returned from Tool Provider doesn't use a period as the decimal point.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        incorrect_request = Request(self.environ)
        incorrect_request.body = self.get_request_body(params={'grade': '0,5'})
        response = self.xmodule.grade_handler(incorrect_request, '')
        real_repsonse = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'failure',
            'description': 'The request has failed.',
            'messageIdentifier': 'unknown',
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_repsonse)

    def test_unsupported_action(self):
        """
        Action returned from Tool Provider isn't supported.
        `replaceResultRequest` is supported only.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        incorrect_request = Request(self.environ)
        incorrect_request.body = self.get_request_body({'action': 'wrongAction'})
        response = self.xmodule.grade_handler(incorrect_request, '')
        real_repsonse = self.get_response_values(response)
        expected_response = {
            'action': None,
            'code_major': 'unsupported',
            'description': 'Target does not support the requested operation.',
            'messageIdentifier': self.DEFAULTS['messageIdentifier'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_repsonse)

    def test_good_request(self):
        """
        Response from Tool Provider is correct.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        incorrect_request = Request(self.environ)
        incorrect_request.body = self.get_request_body()
        response = self.xmodule.grade_handler(incorrect_request, '')
        code_major, description, messageIdentifier, action = self.get_response_values(response)
        description_expected = 'Score for {sourcedId} is now {score}'.format(
                sourcedId=self.DEFAULTS['sourcedId'],
                score=self.DEFAULTS['grade'],
            )
        real_repsonse = self.get_response_values(response)
        expected_response = {
            'action': 'replaceResultResponse',
            'code_major': 'success',
            'description': description_expected,
            'messageIdentifier': self.DEFAULTS['messageIdentifier'],
        }

        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(expected_response, real_repsonse)


