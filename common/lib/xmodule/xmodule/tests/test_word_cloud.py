# -*- coding: utf-8 -*-
"""Test for Word cloud Xmodule functional logic."""

from xmodule.word_cloud_module import WordCloudDescriptor
from . import PostData, LogicTest


class WordCloudModuleTest(LogicTest):
    descriptor_class = WordCloudDescriptor
    raw_model_data = {
        'all_words': {'cat': 10, 'dog': 5, 'mom': 1, 'dad': 2},
        'top_words': {'cat': 10, 'dog': 5, 'dad': 2},
        'submitted': False
    }

    def test_bad_ajax_request(self):
        "Make sure that answer for incorrect request is error json"
        # TODO: move top global test. Formalize all our Xmodule errors.
        response = self.ajax_request('bad_dispatch', {})
        self.assertDictEqual(response, {
            'status': 'fail',
            'error': 'Unknown Command!'
        })

    def test_good_ajax_request(self):
        "Make shure that ajax request works correctly"
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

