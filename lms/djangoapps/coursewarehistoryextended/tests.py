"""
Tests for coursewarehistoryextended
Many aspects of this app are covered by the courseware tests,
but these are specific to the new storage model with multiple
backend tables.
"""

import json
from mock import patch
from django.test import TestCase
from django.conf import settings
from unittest import skipUnless
from nose.plugins.attrib import attr

from courseware.models import BaseStudentModuleHistory, StudentModuleHistory, StudentModule

from courseware.tests.factories import StudentModuleFactory, location, course_id


@attr('shard_1')
@skipUnless(settings.FEATURES["ENABLE_CSMH_EXTENDED"], "CSMH Extended needs to be enabled")
class TestStudentModuleHistoryBackends(TestCase):
    """ Tests of data in CSMH and CSMHE """
    # Tell Django to clean out all databases, not just default
    multi_db = True

    def setUp(self):
        super(TestStudentModuleHistoryBackends, self).setUp()
        for record in (1, 2, 3):
            # This will store into CSMHE via the post_save signal
            csm = StudentModuleFactory.create(module_state_key=location('usage_id'),
                                              course_id=course_id,
                                              state=json.dumps({'type': 'csmhe', 'order': record}))
            # This manually gets us a CSMH record to compare
            csmh = StudentModuleHistory(student_module=csm,
                                        version=None,
                                        created=csm.modified,
                                        state=json.dumps({'type': 'csmh', 'order': record}),
                                        grade=csm.grade,
                                        max_grade=csm.max_grade)
            csmh.save()

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": True})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": True})
    def test_get_history_true_true(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 6)
        self.assertEquals({'type': 'csmhe', 'order': 3}, json.loads(history[0].state))
        self.assertEquals({'type': 'csmhe', 'order': 2}, json.loads(history[1].state))
        self.assertEquals({'type': 'csmhe', 'order': 1}, json.loads(history[2].state))
        self.assertEquals({'type': 'csmh', 'order': 3}, json.loads(history[3].state))
        self.assertEquals({'type': 'csmh', 'order': 2}, json.loads(history[4].state))
        self.assertEquals({'type': 'csmh', 'order': 1}, json.loads(history[5].state))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": True})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": False})
    def test_get_history_true_false(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 3)
        self.assertEquals({'type': 'csmhe', 'order': 3}, json.loads(history[0].state))
        self.assertEquals({'type': 'csmhe', 'order': 2}, json.loads(history[1].state))
        self.assertEquals({'type': 'csmhe', 'order': 1}, json.loads(history[2].state))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": False})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": True})
    def test_get_history_false_true(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 3)
        self.assertEquals({'type': 'csmh', 'order': 3}, json.loads(history[0].state))
        self.assertEquals({'type': 'csmh', 'order': 2}, json.loads(history[1].state))
        self.assertEquals({'type': 'csmh', 'order': 1}, json.loads(history[2].state))

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_CSMH_EXTENDED": False})
    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": False})
    def test_get_history_false_false(self):
        student_module = StudentModule.objects.all()
        history = BaseStudentModuleHistory.get_history(student_module)
        self.assertEquals(len(history), 0)
