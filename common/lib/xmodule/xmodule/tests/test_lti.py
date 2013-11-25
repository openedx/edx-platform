# -*- coding: utf-8 -*-
"""Test for LTI Xmodule functional logic."""
from mock import Mock
import textwrap
from lxml import etree
import unittest
from xmodule.lti_module import LTIModuleDescriptor
from . import LogicTest


class LTIModuleTest(LogicTest):
    """Logic tests for LTI module."""
    descriptor_class = LTIModuleDescriptor

    xml_template = textwrap.dedent("""
            <?xml version = "1.0" encoding = "UTF-8"?>
                <imsx_POXEnvelopeRequest xmlns = "some_link (may be not required)">
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

    def test_handle_ajax(self):
        # Make sure that ajax request works correctly.

        good_requests = {'set': {'score': 5}, 'read': {}, 'delete': {}}
        bad_requests = {'set': {}, 'unknown_dispatch': {}}

        for dispatch, data in bad_requests.items():
            response = self.ajax_request(dispatch, data)
            if dispatch == 'set':
                self.assertEqual(response['status_code'], 400)
            else:
                self.assertEqual(response['status_code'], 404)

        for dispatch, data in good_requests.items():
            response = self.ajax_request(dispatch, data)
            self.assertEqual(response['status_code'], 200)
            if dispatch == 'read':
                self.assertDictEqual(response['content']['value'], {'score': 0.5, 'total': 1.0})

    def test_valid_xml(self):
        """
        Valid XML returned from Tool Provider.
        """
        self.system.get_real_user = Mock()
        self.system.publish = Mock()

        dispatch = 'replaceresult'
               
        mock_request = Mock()
        
        good_value = {'grade': '0.5'}
        mock_request.body = self.xml_template.format(**good_value)
        result = self.xmodule.custom_handler(mock_request, dispatch)

        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(result.body.strip(), parser=parser)
        namespaces = {'def': root.nsmap.values()[0]}

        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text

        self.assertEqual(code_major, 'success', code_major)


    def test_bad_grade_range(self):
        """
        Grade returned from Tool Provider is outside the range 0.0-1.0.
        """
        self.system.get_real_user = Mock()
        self.system.publish = Mock()

        dispatch = 'replaceresult'
               
        mock_request = Mock()
        
        bad_value = {'grade': '100'}
        mock_request.body = self.xml_template.format(**bad_value)
        result = self.xmodule.custom_handler(mock_request, dispatch)

        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(result.body.strip(), parser=parser)
        namespaces = {'def': root.nsmap.values()[0]}
        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text

        self.assertEqual(code_major, 'failure', code_major)

    def test_bad_grade_decimal(self):
        """
        Grade returned from Tool Provider doesn't use a period as the decimal point.
        """
        self.system.get_real_user = Mock()
        self.system.publish = Mock()

        dispatch = 'replaceresult'
       
        mock_request = Mock()
        bad_value = {'grade': '0,5'}
        mock_request.body = self.xml_template.format(**bad_value)
        result = self.xmodule.custom_handler(mock_request, dispatch)

        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(result.body.strip(), parser=parser)
        namespaces = {'def': root.nsmap.values()[0]}
        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text

        self.assertEqual(code_major, 'failure', code_major)

    def test_incomplete_response_body(self):
        """
        Response body from Tool Provider doesn't contain messageIdentifier and sourcedId and textString.
        """
        self.system.get_real_user = Mock()
        self.system.publish = Mock()

        dispatch = 'replaceresult'

        xml_template = textwrap.dedent("""
            <?xml version = "1.0" encoding = "UTF-8"?>
                <imsx_POXEnvelopeRequest xmlns = "some_link (may be not required)">
                  <imsx_POXHeader>
                    <imsx_POXRequestHeaderInfo>
                      <imsx_version>V1.0</imsx_version>
                      "here must be messageIdentifier"
                    </imsx_POXRequestHeaderInfo>
                  </imsx_POXHeader>
                  <imsx_POXBody>
                    <replaceResultRequest>
                      <resultRecord>
                        <sourcedGUID>
                          "here must be sourcedId"
                        </sourcedGUID>
                        <result>
                          <resultScore>
                            <language>en-us</language>
                            "here must be textString"
                          </resultScore>
                        </result>
                      </resultRecord>
                    </replaceResultRequest>
                  </imsx_POXBody>
                </imsx_POXEnvelopeRequest>
        """)

        mock_request = Mock()
        mock_request.body = xml_template
        result = self.xmodule.custom_handler(mock_request, dispatch)

        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        root = etree.fromstring(result.body.strip(), parser=parser)
        namespaces = {'def': root.nsmap.values()[0]}
        code_major = root.xpath("//def:imsx_codeMajor", namespaces=namespaces)[0].text

        self.assertEqual(code_major, 'unsupported', code_major)

    @unittest.skip("skipped because not completed")
    def test_authorization_header_not_present(self):
        """
        Authorization header not provided in request.
        """
        mock_request = Mock()
        mock_request.META = None

        mock_course = Mock()
        import ipdb; ipdb.set_trace()
        descriptor = LTIModuleDescriptor()

        result = descriptor.authenticate(mock_request, mock_course)




