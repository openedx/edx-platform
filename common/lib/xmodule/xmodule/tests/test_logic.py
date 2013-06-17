# -*- coding: utf-8 -*-
"""Test for Xmodule functional logic."""

import json
import unittest

from lxml import etree

from xmodule.poll_module import PollDescriptor
from xmodule.conditional_module import ConditionalDescriptor
from xmodule.word_cloud_module import WordCloudDescriptor
from xmodule.videoalpha_module import VideoAlphaDescriptor

class PostData:
    """Class which emulate postdata."""
    def __init__(self, dict_data):
        self.dict_data = dict_data

    def getlist(self, key):
        return self.dict_data.get(key)


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    descriptor_class = None
    raw_model_data = {}

    def setUp(self):
        class EmptyClass:
            pass

        self.system = None
        self.descriptor = EmptyClass()

        self.xmodule_class = self.descriptor_class.module_class
        self.xmodule = self.xmodule_class(
            self.system,
            self.descriptor,
            self.raw_model_data
        )

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


class WordCloudModuleTest(LogicTest):
    descriptor_class = WordCloudDescriptor
    raw_model_data = {
        'all_words': {'cat': 10, 'dog': 5, 'mom': 1, 'dad': 2},
        'top_words': {'cat': 10, 'dog': 5, 'dad': 2},
        'submitted': False
    }

    def test_bad_ajax_request(self):

        # TODO: move top global test. Formalize all our Xmodule errors.
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

        self.assertEqual(100.0, sum(i['percent'] for i in response['top_words']) )


class VideoAlphaModuleTest(LogicTest):
    descriptor_class = VideoAlphaDescriptor

    raw_model_data = {
        'data': '<videoalpha />'
    }

    def test_get_timeframe_no_parameters(self):
        xmltree = etree.fromstring('<videoalpha>test</videoalpha>')
        output = self.xmodule._get_timeframe(xmltree)
        self.assertEqual(output, ('', ''))

    def test_get_timeframe_with_one_parameter(self):
        xmltree = etree.fromstring(
            '<videoalpha start_time="00:04:07">test</videoalpha>'
        )
        output = self.xmodule._get_timeframe(xmltree)
        self.assertEqual(output, (247, ''))

    def test_get_timeframe_with_two_parameters(self):
        xmltree = etree.fromstring(
            '''<videoalpha
                    start_time="00:04:07"
                    end_time="13:04:39"
                >test</videoalpha>'''
        )
        output = self.xmodule._get_timeframe(xmltree)
        self.assertEqual(output, (247, 47079))
