# -*- coding: utf-8 -*-
"""Test for LTI Xmodule functional logic."""

from mock import Mock
import textwrap
from lxml import etree
import unittest
from webob.request import Request

from xmodule.lti_module import LTIModuleDescriptor

from . import LogicTest


class LTIModuleTest(LogicTest):
    """Logic tests for LTI module."""
    descriptor_class = LTIModuleDescriptor

    def setUp(self):
         super(TestAssetIndex, self).setUp()
         self.environ = {'wsgi.url_scheme': 'http', 'REQUEST_METHOD': 'POST'}
         self.requet_body_xml_template = textwrap.dedent("""
            <?xml version = "1.0" encoding = "UTF-8"?>
                <imsx_POXEnvelopeRequest xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
                  <imsx_POXHeader>
                    <imsx_POXRequestHeaderInfo>
                      <imsx_version>V1.0</imsx_version>
                      <imsx_messageIdentifier>528243ba5241b</imsx_messageIdentifier>
                    </imsx_POXRequestHeaderInfo>
                  </imsx_POXHeader>
                  <imsx_POXBody>
                    <replaceResultRequest>
                      <resultRecord>
                        <sourcedGUID>
                          <sourcedId>feb-123-456-2929::28883</sourcedId>
                        </sourcedGUID>
                        <result>
                          <resultScore>
                            <language>en-us</language>
                            <textString>{grade}</textString>
                          </resultScore>
                        </result>
                      </resultRecord>
                    </replaceResultRequest>
                  </imsx_POXBody>
                </imsx_POXEnvelopeRequest>
        """)
        self.system.get_real_user = Mock()
        self.xmodule.get_client_key_secret = Mock(return_value=('key', 'secret'))
        self.system.publish = Mock()

    def get_code_major(self, response):
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(response.body.strip(), parser=parser)
        namespaces = {'def': root.nsmap.values()[0]}
        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text
        return code_major

    def test_authorization_header_not_present(self):
        """
        Request has no Authorization header.
        This is an unknown service request, i.e., it is not a part of the original service specification.
        """
        incorrect_request = Request(self.environ)
        good_value = {'grade': '0.5'}
        incorrect_request.body = self.requet_body_xml_template.format(**good_value)
        response = self.xmodule.grade_handler(incorrect_request, '')
        code_major = self.get_code_major(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(code_major, 'unsupported', code_major)

    def test_authorization_header_empty(self):
        """
        Request Authorization header has no value.
        This is an unknown service request, i.e., it is not a part of the original service specification.
        """
        incorrect_request = Request(self.environ)
        incorrect_request.authorization = "bad authorization header"
        good_value = {'grade': '0.5'}
        incorrect_request.body = self.requet_body_xml_template.format(**good_value)
        response = self.xmodule.grade_handler(incorrect_request, '')
        code_major = self.get_code_major(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(code_major, 'unsupported', code_major)

    def test_grade_not_in_range(self):
        """
        Grade returned from Tool Provider is outside the range 0.0-1.0.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        incorrect_request = Request(self.environ)
        bad_value = {'grade': '10'}  #grade not in range
        incorrect_request.body = self.xml_template.format(**bad_value)
        response = self.xmodule.grade_handler(incorrect_request, '')
        self.assertEqual(response.status_code, 200)
        code_major = self.get_code_major(response)
        self.assertEqual(code_major, 'failure', code_major)

    def test_bad_grade_decimal(self):
        """
        Grade returned from Tool Provider doesn't use a period as the decimal point.
        """
        self.xmodule.verify_oauth_body_sign = Mock()
        incorrect_request = Request(self.environ)
        bad_value = {'grade': '0,5'}
        incorrect_request.body = self.requet_body_xml_template.format(**bad_value)
        response = self.xmodule.grade_handler(incorrect_request, '')
        code_major = self.get_code_major(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(code_major, 'failure', code_major)

    @unittest.skip("not implemented")
    def test_good_request(self):
        self.system.get_real_user = Mock()
        incorrect_request = Request(self.environ)
        incorrect_request.authorization = "bad authorization header"
        good_value = {'grade': '0.5'}
        incorrect_request.body = self.requet_body_xml_template.format(**good_value)
        response = self.xmodule.grade_handler(incorrect_request, '')
        code_major = self.get_code_major(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(code_major, 'unsupported', code_major)



