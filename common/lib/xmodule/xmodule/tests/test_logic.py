# -*- coding: utf-8 -*-

import json
import unittest

from xmodule.poll_module import PollModule
from xmodule.conditional_module import ConditionalModule


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    xmodule_class = None
    raw_model_data = {}

    def setUp(self):
        self.system = None
        self.location = None
        self.descriptor = None

        self.xmodule = self.xmodule_class(self.system, self.location,
            self.descriptor, self.raw_model_data)

    def ajax_request(self, dispatch, get):
        return json.loads(self.xmodule.handle_ajax(dispatch, get))


class PollModuleTest(LogicTest):
    xmodule_class = PollModule
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
    xmodule_class = ConditionalModule
    raw_model_data = {
        'contents': 'Some content'
    }

    def test_ajax_request(self):
        # Mock is_condition_satisfied
        self.xmodule.is_condition_satisfied = lambda: True

        response = self.ajax_request('No', {})
        html = response['html']

        self.assertEqual(html, 'Some content')
