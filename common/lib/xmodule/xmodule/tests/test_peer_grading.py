import unittest
from xmodule.modulestore import Location
from .import get_test_system
from test_util_open_ended import MockQueryDict, DummyModulestore
from xmodule.open_ended_grading_classes.peer_grading_service import MockPeerGradingService
from mock import Mock
from xmodule.peer_grading_module import PeerGradingModule, InvalidLinkLocation
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
import json

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
    coe_location = Location(["i4x", "edX", "open_ended", "combinedopenended", "SampleQuestion"])
    calibrated_dict = {'location': "blah"}
    coe_dict = {'location': coe_location.url()}
    save_dict = MockQueryDict()
    save_dict.update({
        'location': "blah",
        'submission_id': 1,
        'submission_key': "",
        'score': 1,
        'feedback': "",
        'rubric_scores[]': [0, 1],
        'submission_flagged': False,
        'answer_unknown' : False,
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
        self.coe = self.get_module_from_location(self.coe_location, COURSE)

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
        success, data = self.peer_grading.query_data_for_location(self.problem_location.url())
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
        response = self.peer_grading.peer_grading_problem(self.coe_dict)
        self.assertEqual(response['success'], True)

    def test___find_corresponding_module_for_location_exceptions(self):
        """
        Unit test for the exception cases of __find_corresponding_module_for_location
        Mainly for diff coverage
        @return:
        """
        with self.assertRaises(ItemNotFoundError):
            self.peer_grading._find_corresponding_module_for_location(Location('i4x','a','b','c','d'))

    def test_get_instance_state(self):
        """
        Get the instance state dict
        @return:
        """
        self.peer_grading.get_instance_state()

class MockPeerGradingServiceProblemList(MockPeerGradingService):
    def get_problem_list(self, course_id, grader_id):
        return {'success': True,
                'problem_list': [
                    {"num_graded": 3, "num_pending": 681, "num_required": 3, "location": "i4x://edX/open_ended/combinedopenended/SampleQuestion", "problem_name": "Peer-Graded Essay"},
                ]}

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

    def test_problem_list(self):
        """
        Test to see if a peer grading problem list can be correctly initialized.
        """

        # Initialize peer grading module.
        peer_grading = self.get_module_from_location(self.problem_location, COURSE)

        # Ensure that it cannot find any peer grading.
        html = peer_grading.peer_grading()
        self.assertNotIn("Peer-Graded", html)

        # Swap for our mock class, which will find peer grading.
        peer_grading.peer_gs = MockPeerGradingServiceProblemList()
        html = peer_grading.peer_grading()
        self.assertIn("Peer-Graded", html)

class PeerGradingModuleLinkedTest(unittest.TestCase, DummyModulestore):
    """
    Test peer grading that is linked to an open ended module.
    """
    problem_location = Location(["i4x", "edX", "open_ended", "peergrading",
                                 "PeerGradingLinked"])
    coe_location = Location(["i4x", "edX", "open_ended", "combinedopenended",
                             "SampleQuestion"])

    def setUp(self):
        """
        Create a peer grading module from a test system.
        """
        self.test_system = get_test_system()
        self.test_system.open_ended_grading_interface = None
        self.setup_modulestore(COURSE)

    def _create_peer_grading_with_linked_problem(self, location, valid_linked_descriptor=True):
        """
        Create a peer grading problem with a linked location.
        """

        # Mock the linked problem descriptor.
        linked_descriptor = Mock()
        linked_descriptor.location = location

        # Mock the peer grading descriptor.
        pg_descriptor = Mock()
        pg_descriptor.location = self.problem_location

        if valid_linked_descriptor:
            pg_descriptor.get_required_module_descriptors = lambda: [linked_descriptor, ]
        else:
            pg_descriptor.get_required_module_descriptors = lambda: []

        # Setup the proper field data for the peer grading module.
        field_data = DictFieldData({
            'data': '<peergrading/>',
            'location': self.problem_location,
            'use_for_single_location': True,
            'link_to_location': self.coe_location.url(),
            'graded': True,
        })

        # Initialize the peer grading module.
        peer_grading = PeerGradingModule(
            pg_descriptor,
            self.test_system,
            field_data,
            ScopeIds(None, None, self.problem_location, self.problem_location)
        )

        return peer_grading

    def test_invalid_link(self):
        """
        Ensure that a peer grading problem with no linked locations raises an error.
        """

        # Setup the peer grading module with no linked locations.
        with self.assertRaises(InvalidLinkLocation):
            self._create_peer_grading_with_linked_problem(self.coe_location, valid_linked_descriptor=False)


    def test_linked_problem(self):
        """
        Ensure that a peer grading problem with a linked location loads properly.
        """

        # Setup the peer grading module with the proper linked location.
        peer_grading = self._create_peer_grading_with_linked_problem(self.coe_location)

        # Ensure that it is properly setup.
        self.assertTrue(peer_grading.use_for_single_location)

    def test_linked_ajax(self):
        """
        Ensure that a peer grading problem with a linked location responds to ajax calls.
        """

        # Setup the peer grading module with the proper linked location.
        peer_grading = self._create_peer_grading_with_linked_problem(self.coe_location)

        # If we specify a location, it will render the problem for that location.
        data = peer_grading.handle_ajax('problem', {'location' : self.coe_location})
        self.assertTrue(json.loads(data)['success'])

        # If we don't specify a location, it should use the linked location.
        data = peer_grading.handle_ajax('problem', {})
        self.assertTrue(json.loads(data)['success'])

    def test_linked_score(self):
        """
        Ensure that a peer grading problem with a linked location is properly scored.
        """

        # Setup the peer grading module with the proper linked location.
        peer_grading = self._create_peer_grading_with_linked_problem(self.coe_location)

        score_dict = peer_grading.get_score()

        self.assertEqual(score_dict['score'], 1)
        self.assertEqual(score_dict['total'], 1)

    def test_get_next_submission(self):
        """
        Ensure that a peer grading problem with a linked location can get a submission to score.
        """

        # Setup the peer grading module with the proper linked location.
        peer_grading = self._create_peer_grading_with_linked_problem(self.coe_location)

        data = peer_grading.handle_ajax('get_next_submission', {'location': self.coe_location})
        self.assertEqual(json.loads(data)['submission_id'], 1)


class PeerGradingModuleTrackChangesTest(unittest.TestCase, DummyModulestore):
    """
    Test peer grading with the track changes modification
    """
    class MockedTrackChangesProblem(object):
        track_changes = True

    mock_track_changes_problem = Mock(side_effect=[MockedTrackChangesProblem()])
    pgm_location = Location(["i4x", "edX", "open_ended", "peergrading", "PeerGradingSample"])

    def setUp(self):
        """
        Create a peer grading module from a test system
        @return:
        """
        self.test_system = get_test_system()
        self.test_system.open_ended_grading_interface = None
        self.setup_modulestore(COURSE)
        self.peer_grading = self.get_module_from_location(self.pgm_location, COURSE)

    def test_tracking_peer_eval_problem(self):
        """
        Tests rendering of peer eval problem with track changes set.  With the test_system render_template
        this test becomes a bit tautological, but oh well.
        @return:
        """
        self.peer_grading._find_corresponding_module_for_location = self.mock_track_changes_problem
        response = self.peer_grading.peer_grading_problem({'location': 'mocked'})
        self.assertEqual(response['success'], True)
        self.assertIn("'track_changes': True", response['html'])
