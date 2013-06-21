# -*- coding: utf-8 -*-
# pylint: disable=W0232
"""Test for Xmodule functional logic."""

import json
import unittest

from xmodule.poll_module import PollDescriptor
from xmodule.conditional_module import ConditionalDescriptor
from xmodule.word_cloud_module import WordCloudDescriptor
from xmodule.tests import get_test_system

class PostData:
    """Class which emulate postdata."""
    def __init__(self, dict_data):
        self.dict_data = dict_data

    def getlist(self, key):
        """Get data by key from `self.dict_data`."""
        return self.dict_data.get(key)


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    descriptor_class = None
    raw_model_data = {}

    def setUp(self):
        class EmptyClass:
            """Empty object."""
            pass

        self.system = get_test_system()
        self.descriptor = EmptyClass()

        self.xmodule_class = self.descriptor_class.module_class
        self.xmodule = self.xmodule_class(
            self.system,
            self.descriptor,
            self.raw_model_data
        )

    def ajax_request(self, dispatch, get):
        """Call Xmodule.handle_ajax."""
        return json.loads(self.xmodule.handle_ajax(dispatch, get))


class PollModuleTest(LogicTest):
    """Logic tests for Poll Xmodule."""
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
    """Logic tests for Conditional Xmodule."""
    descriptor_class = ConditionalDescriptor

    def test_ajax_request(self):
        # Mock is_condition_satisfied
        self.xmodule.is_condition_satisfied = lambda: True
        setattr(self.xmodule.descriptor, 'get_children', lambda: [])

        response = self.ajax_request('No', {})
        html = response['html']

        self.assertEqual(html, [])


class WordCloudModuleTest(LogicTest):
    """Logic tests for Word Cloud Xmodule."""
    descriptor_class = WordCloudDescriptor
    raw_model_data = {
        'all_words': {'cat': 10, 'dog': 5, 'mom': 1, 'dad': 2},
        'top_words': {'cat': 10, 'dog': 5, 'dad': 2},
        'submitted': False
    }

    def test_bad_ajax_request(self):
        response = self.ajax_request('bad_dispatch', {})
        self.assertDictEqual(response, {
            'status': 'fail',
            'error': 'Unknown Command!'
        })

    def test_good_ajax_request(self):
        post_data = PostData({'student_words[]': ['cat', 'cat', 'dog', 'sun']})
        response = self.ajax_request('submit', post_data)
        self.assertEqual(response['status'], 'success')
        self.assertEqual(response['submitted'], True)
        self.assertEqual(response['total_count'], 22)
        self.assertDictEqual(
            response['student_words'],
            {'sun': 1, 'dog': 6, 'cat': 12}
        )
        self.assertListEqual(
            response['top_words'],
            [{'text': 'dad', 'size': 2, 'percent': 9.0},
             {'text': 'sun', 'size': 1, 'percent': 5.0},
             {'text': 'dog', 'size': 6, 'percent': 27.0},
             {'text': 'mom', 'size': 1, 'percent': 5.0},
             {'text': 'cat', 'size': 12, 'percent': 54.0}]
        )

        self.assertEqual(
            100.0,
            sum(i['percent'] for i in response['top_words']))
