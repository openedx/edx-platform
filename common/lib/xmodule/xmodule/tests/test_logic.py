# -*- coding: utf-8 -*-

import json
import unittest

from xmodule.poll_module import PollDescriptor
from xmodule.conditional_module import ConditionalDescriptor


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    descriptor_class = None
    raw_model_data = {}

    def setUp(self):
        class EmptyClass: pass

        self.system = None
        self.location = None
        self.descriptor = EmptyClass()

        self.xmodule_class = self.descriptor_class.module_class
        self.xmodule = self.xmodule_class(self.system, self.location,
            self.descriptor, self.raw_model_data)

    def ajax_request(self, dispatch, get):
        return json.loads(self.xmodule.handle_ajax(dispatch, get))


class PollModuleTest(LogicTest):
    descriptor_class = PollDescriptor
    raw_model_data = {
        'poll_answers': {'Yes': 1, 'Dont_know': 0, 'No': 0},
        'voted': False,
        'poll_answer': ''
    }

    def test_bad_ajax_request(self):
        response = self.ajax_request('bad_answer', {})
        self.assertDictEqual(response, {'error': 'Unknown Command!'})

    def test_good_ajax_request(self):
        response = self.ajax_request('No', {})

        poll_answers = response['poll_answers']
        total = response['total']
        callback = response['callback']

        self.assertDictEqual(poll_answers, {'Yes': 1, 'Dont_know': 0, 'No': 1})
        self.assertEqual(total, 2)
        self.assertDictEqual(callback, {'objectName': 'Conditional'})
        self.assertEqual(self.xmodule.poll_answer, 'No')


class ConditionalModuleTest(LogicTest):
    descriptor_class = ConditionalDescriptor

    def test_ajax_request(self):
        # Mock is_condition_satisfied
        self.xmodule.is_condition_satisfied = lambda: True
        setattr(self.xmodule.descriptor, 'get_children', lambda: [])

        response = self.ajax_request('No', {})
        html = response['html']

        self.assertEqual(html, [])
