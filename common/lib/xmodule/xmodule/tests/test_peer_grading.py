import unittest
from xmodule.modulestore import Location
from .import get_test_system
from test_util_open_ended import MockQueryDict, DummyModulestore

import logging

log = logging.getLogger(__name__)

ORG = "edX"
COURSE = "open_ended"


class PeerGradingModuleTest(unittest.TestCase, DummyModulestore):
    """
    Test peer grading xmodule at the unit level.  More detailed tests are difficult, as the module relies on an
    external grading service.
    """
    problem_location = Location(["i4x", "edX", "open_ended", "peergrading",
                                 "PeerGradingSample"])
    calibrated_dict = {'location': "blah"}
    save_dict = MockQueryDict()
    save_dict.update({
        'location': "blah",
        'submission_id': 1,
        'submission_key': "",
        'score': 1,
        'feedback': "",
        'rubric_scores[]': [0, 1],
        'submission_flagged': False,
    })

    def setUp(self):
        """
        Create a peer grading module from a test system
        @return:
        """
        self.test_system = get_test_system()
        self.test_system.open_ended_grading_interface = None
        self.setup_modulestore(COURSE)
        self.peer_grading = self.get_module_from_location(self.problem_location, COURSE)

    def test_module_closed(self):
        """
        Test if peer grading is closed
        @return:
        """
        closed = self.peer_grading.closed()
        self.assertEqual(closed, False)

    def test_get_html(self):
        """
        Test to see if the module can be rendered
        @return:
        """
        html = self.peer_grading.get_html()

    def test_get_data(self):
        """
        Try getting data from the external grading service
        @return:
        """
        success, data = self.peer_grading.query_data_for_location()
        self.assertEqual(success, True)

    def test_get_score(self):
        """
        Test getting the score
        @return:
        """
        score = self.peer_grading.get_score()
        self.assertEquals(score['score'], None)

    def test_get_max_score(self):
        """
        Test getting the max score
        @return:
        """
        max_score = self.peer_grading.max_score()
        self.assertEquals(max_score, None)

    def get_next_submission(self):
        """
        Test to see if we can get the next mock submission
        @return:
        """
        success, next_submission = self.peer_grading.get_next_submission({'location': 'blah'})
        self.assertEqual(success, True)

    def test_save_grade(self):
        """
        Test if we can save the grade
        @return:
        """
        response = self.peer_grading.save_grade(self.save_dict)
        self.assertEqual(response['success'], True)

    def test_is_student_calibrated(self):
        """
        Check to see if the student has calibrated yet
        @return:
        """
        calibrated_dict = {'location': "blah"}
        response = self.peer_grading.is_student_calibrated(self.calibrated_dict)
        self.assertEqual(response['success'], True)

    def test_show_calibration_essay(self):
        """
        Test showing the calibration essay
        @return:
        """
        response = self.peer_grading.show_calibration_essay(self.calibrated_dict)
        self.assertEqual(response['success'], True)

    def test_save_calibration_essay(self):
        """
        Test saving the calibration essay
        @return:
        """
        response = self.peer_grading.save_calibration_essay(self.save_dict)
        self.assertEqual(response['success'], True)

    def test_peer_grading_problem(self):
        """
        See if we can render a single problem
        @return:
        """
        response = self.peer_grading.peer_grading_problem(self.calibrated_dict)
        self.assertEqual(response['success'], True)

    def test_get_instance_state(self):
        """
        Get the instance state dict
        @return:
        """
        self.peer_grading.get_instance_state()

class PeerGradingModuleScoredTest(unittest.TestCase, DummyModulestore):
    """
    Test peer grading xmodule at the unit level.  More detailed tests are difficult, as the module relies on an
    external grading service.
    """
    problem_location = Location(["i4x", "edX", "open_ended", "peergrading",
                                 "PeerGradingScored"])
    def setUp(self):
        """
        Create a peer grading module from a test system
        @return:
        """
        self.test_system = get_test_system()
        self.test_system.open_ended_grading_interface = None
        self.setup_modulestore(COURSE)

    def test_metadata_load(self):
        peer_grading = self.get_module_from_location(self.problem_location, COURSE)
        self.assertEqual(peer_grading.closed(), False)
