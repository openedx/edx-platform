# -*- coding: utf-8 -*-
"""Test for LTI Xmodule functional logic."""
from mock import Mock
import textwrap
from xmodule.lti_module import LTIModuleDescriptor
from . import LogicTest


class LTIModuleTest(LogicTest):
    """Logic tests for LTI module."""
    descriptor_class = LTIModuleDescriptor

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

    def test_custom_handler(self):
        self.system.get_real_user = Mock()
        self.system.publish = Mock()

        dispatch = 'replaceresult'
        
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
                            <textString>{score}</textString>
                          </resultScore>
                        </result>
                      </resultRecord>
                    </replaceResultRequest>
                  </imsx_POXBody>
                </imsx_POXEnvelopeRequest>
        """)
        
        
        mock_request = Mock()
        good_values = {'score': '0.5'}
        mock_request.body = xml_template.format(**good_values)

        result = self.xmodule.custom_handler(mock_request, dispatch)
        self.assertTrue(result.status_code == 200)


