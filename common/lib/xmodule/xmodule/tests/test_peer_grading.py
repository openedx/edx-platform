import unittest
from xmodule.modulestore import Location
import json
from lxml import etree
from mock import Mock
from . import test_system
from dummy_system import DummySystem, DummySystemUser, MockQueryDict

from xmodule.peer_grading_module import PeerGradingModule, PeerGradingDescriptor
from xmodule.open_ended_grading_classes.grading_service_module import GradingServiceError

ORG = "edX"
COURSE="open_ended"


class PeerGradingModuleTest(unittest.TestCase, DummySystemUser):
    problem_location = Location(["i4x", "edX", "open_ended", "peergrading",
                         "PeerGradingSample"])
    calibrated_dict = {'location' : "blah"}
    save_dict = MockQueryDict()
    save_dict.update({
        'location' : "blah",
        'submission_id' : 1,
        'submission_key' : "",
        'score': 1,
        'feedback' : "",
        'rubric_scores[]' : [0,1],
        'submission_flagged': False,
        })

    def setUp(self):
        self.test_system = test_system()
        self.test_system.open_ended_grading_interface = None
        self.peer_grading = self.get_module_from_location(self.problem_location, COURSE)

    def test_module_closed(self):
        closed = self.peer_grading.closed()
        self.assertEqual(closed, False)

    def test_get_html(self):
        html = self.peer_grading.get_html()

    def test_get_data(self):
        try:
            success, data = self.peer_grading.query_data_for_location()
        except GradingServiceError:
            pass

    def test_get_score(self):
        score = self.peer_grading.get_score()

    def test_get_max_score(self):
        max_score = self.peer_grading.max_score()

    def get_next_submission(self):
        success, next_submission = self.peer_grading.get_next_submission({'location' : 'blah'})

    def test_save_grade(self):
        self.peer_grading.save_grade(self.save_dict)

    def test_is_student_calibrated(self):
        calibrated_dict = {'location' : "blah"}
        self.peer_grading.is_student_calibrated(self.calibrated_dict)

    def test_show_calibration_essay(self):

        self.peer_grading.show_calibration_essay(self.calibrated_dict)

    def test_save_calibration_essay(self):
        self.peer_grading.save_calibration_essay(self.save_dict)

    def test_peer_grading_closed(self):
        self.peer_grading.peer_grading_closed()

    def test_peer_grading_problem(self):
        self.peer_grading.peer_grading_problem(self.calibrated_dict)

    def test_get_instance_state(self):
        self.peer_grading.get_instance_state()