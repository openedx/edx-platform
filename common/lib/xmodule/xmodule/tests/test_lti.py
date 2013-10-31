# -*- coding: utf-8 -*-
"""Test for LTI Xmodule functional logic."""
from xmodule.lti_module import LTIModuleDescriptor
from . import LogicTest


class LTIModuleTest(LogicTest):
    """Logic tests for Poll Xmodule."""
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
