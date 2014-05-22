# -*- coding: utf-8 -*-
"""Video xmodule tests in mongo."""
from mock import Mock
import json

from . import BaseTestXmodule
from .test_video_xml import SOURCE_XML


class TestVideoScoring(BaseTestXmodule):

    CATEGORY = "video"
    DATA = SOURCE_XML
    METADATA = {}

    def setUp(self):
        self.setup_course()

    def test_maxscore(self):
        self.initialize_module()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance
        self.assertEqual(self.item.max_score(), None)

    def test_update_score(self):
        self.initialize_module()
        self.initialize_module()
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

        with self.assertRaises(NotImplementedError):
            self.item.update_score(0.5)

        self.item.runtime.get_real_user = Mock()
        self.item.runtime.publish = Mock()
        self.item.update_score(0.5)

        self.assertEqual(self.item.module_score, 0.5)

    def test_basic_grader(self):
        """
        Test if no grader selected.

        Basic grader must be enabled.
        """
        metadata = {
            'has_score': True,
            'grade_videos': True,
        }
        self.initialize_module(metadata=metadata)
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

        self.assertEqual(self.item.max_score(), self.item.weight)

        expected_basic_grader = {
            'basic_grader': {
                'graderState': None,
                'saveState': False,
                'isScored': False,
                'graderValue': True,
            }
        }

        self.assertDictEqual(self.item.graders(), expected_basic_grader)

    def test_graders(self):
        metadata = {
            'has_score': True,
            'scored_on_end': True,
            'scored_on_percent': 75,
            'grade_videos': True,
        }
        self.initialize_module(metadata=metadata)
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance
        expected_graders = {
            'scored_on_end': {
                'isScored': False, 'graderValue': True,
                'graderState': None, 'saveState': False,
            },
            'scored_on_percent': {
                'isScored': False, 'graderValue': 75,
                'graderState': None, 'saveState': True,
            },
        }
        self.assertEqual(self.item.max_score(), self.item.weight)
        self.assertDictEqual(self.item.graders(), expected_graders)

    def test_scored_module(self):
        metadata = {
            'has_score': True,
            'grade_videos': True,
        }
        self.initialize_module(metadata=metadata)
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance
        self.item.module_score = 1
        self.assertEqual(self.item.graders(), {})

    def test_cumulative_score_save_action(self):
        metadata = {
            'has_score': True,
            'grade_videos': True,
            'scored_on_end': True,
        }
        self.initialize_module(metadata=metadata)
        self.item_descriptor.render('student_view')
        self.item = self.item_descriptor.xmodule_runtime.xmodule_instance

        expected_grader_before = {
            'scored_on_end': {
                'isScored': False, 'graderValue': True,
                'graderState': None, 'saveState': False,
            },
        }
        self.assertDictEqual(self.item.graders(), expected_grader_before)

        new_grader_state = json.dumps({'scored_on_end': True})
        output = self.item.cumulative_score_save_action(new_grader_state)
        expected_grader_after = {
            'scored_on_end': {
                'isScored': False, 'graderValue': True,
                'graderState': True, 'saveState': False,
            },
        }
        self.assertDictEqual(output, expected_grader_after)
