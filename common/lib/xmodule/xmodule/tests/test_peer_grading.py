import unittest
import json
import logging
from mock import Mock, patch
from webob.multidict import MultiDict

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey
from xmodule.tests import get_test_system, get_test_descriptor_system
from xmodule.tests.test_util_open_ended import DummyModulestore
from xmodule.open_ended_grading_classes.peer_grading_service import MockPeerGradingService
from xmodule.peer_grading_module import PeerGradingModule, PeerGradingDescriptor, MAX_ALLOWED_FEEDBACK_LENGTH
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem
from xmodule.validation import StudioValidationMessage

log = logging.getLogger(__name__)


class PeerGradingModuleTest(unittest.TestCase, DummyModulestore):
    """
    Test peer grading xmodule at the unit level.  More detailed tests are difficult, as the module relies on an
    external grading service.
    """
    course_id = SlashSeparatedCourseKey('edX', 'open_ended', '2012_Fall')
    problem_location = course_id.make_usage_key("peergrading", "PeerGradingSample")
    coe_location = course_id.make_usage_key("combinedopenended", "SampleQuestion")
    calibrated_dict = {'location': "blah"}
    coe_dict = {'location': coe_location.to_deprecated_string()}
    save_dict = MultiDict({
        'location': "blah",
        'submission_id': 1,
        'submission_key': "",
        'score': 1,
        'feedback': "",
        'submission_flagged': False,
        'answer_unknown': False,
    })
    save_dict.extend(('rubric_scores[]', val) for val in (0, 1))

    def get_module_system(self, descriptor):
        test_system = get_test_system(self.course_id)
        test_system.open_ended_grading_interface = None
        return test_system

    def setUp(self):
        """
        Create a peer grading module from a test system
        @return:
        """
        super(PeerGradingModuleTest, self).setUp()
        self.setup_modulestore(self.course_id.course)
        self.peer_grading = self.get_module_from_location(self.problem_location)
        self.coe = self.get_module_from_location(self.coe_location)

    def test_module_closed(self):
        """
        Test if peer grading is closed
        @return:
        """
        closed = self.peer_grading.closed()
        self.assertFalse(closed)

    def test_get_html(self):
        """
        Test to see if the module can be rendered
        @return:
        """
        _html = self.peer_grading.get_html()

    def test_get_data(self):
        """
        Try getting data from the external grading service
        @return:
        """
        success, _data = self.peer_grading.query_data_for_location(self.problem_location)
        self.assertTrue(success)

    def test_get_score_none(self):
        """
        Test getting the score.
        """
        score = self.peer_grading.get_score()

        # Score should be None.
        self.assertIsNone(score['score'])

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
        success, _next_submission = self.peer_grading.get_next_submission({'location': 'blah'})
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
        response = self.peer_grading.is_student_calibrated(self.calibrated_dict)
        self.assertTrue(response['success'])

    def test_show_calibration_essay(self):
        """
        Test showing the calibration essay
        @return:
        """
        response = self.peer_grading.show_calibration_essay(self.calibrated_dict)
        self.assertTrue(response['success'])

    def test_save_calibration_essay(self):
        """
        Test saving the calibration essay
        @return:
        """
        response = self.peer_grading.save_calibration_essay(self.save_dict)
        self.assertTrue(response['success'])

    def test_peer_grading_problem(self):
        """
        See if we can render a single problem
        @return:
        """
        response = self.peer_grading.peer_grading_problem(self.coe_dict)
        self.assertTrue(response['success'])

    def test___find_corresponding_module_for_location_exceptions(self):
        """
        Unit test for the exception cases of __find_corresponding_module_for_location
        Mainly for diff coverage
        @return:
        """
        # pylint: disable=protected-access
        with self.assertRaises(ItemNotFoundError):
            self.peer_grading._find_corresponding_module_for_location(
                Location('org', 'course', 'run', 'category', 'name', 'revision')
            )

    def test_get_instance_state(self):
        """
        Get the instance state dict
        @return:
        """
        self.peer_grading.get_instance_state()

    def test_save_grade_with_long_feedback(self):
        """
        Test if feedback is too long save_grade() should return error message.
        """

        feedback_fragment = "This is very long feedback."
        self.save_dict["feedback"] = feedback_fragment * (
            (MAX_ALLOWED_FEEDBACK_LENGTH / len(feedback_fragment) + 1)
        )

        response = self.peer_grading.save_grade(self.save_dict)

        # Should not succeed.
        self.assertEqual(response['success'], False)
        self.assertEqual(
            response['error'],
            "Feedback is too long, Max length is {0} characters.".format(
                MAX_ALLOWED_FEEDBACK_LENGTH
            )
        )

    def test_get_score_success_fails(self):
        """
        Test if query_data_for_location not succeed, their score is None.
        """
        score_dict = self.get_score(False, 0, 0)

        # Score dict should be None.
        self.assertIsNone(score_dict)

    def test_get_score(self):
        """
        Test if the student has graded equal to required submissions,
        their score is 1.0.
        """

        score_dict = self.get_score(True, 3, 3)

        # Score should be 1.0.
        self.assertEqual(score_dict["score"], 1.0)

        # Testing score after data is stored in student_data_for_location in xmodule.
        _score_dict = self.peer_grading.get_score()

        # Score should be 1.0.
        self.assertEqual(_score_dict["score"], 1.0)

    def test_get_score_zero(self):
        """
        Test if the student has graded not equal to required submissions,
        their score is 0.0.
        """
        score_dict = self.get_score(True, 2, 3)

        # Score should be 0.0.
        self.assertEqual(score_dict["score"], 0.0)

    def get_score(self, success, count_graded, count_required):
        self.peer_grading.use_for_single_location_local = True
        self.peer_grading.graded = True

        # Patch for external grading service.
        with patch('xmodule.peer_grading_module.PeerGradingModule.query_data_for_location') as mock_query_data_for_location:
            mock_query_data_for_location.return_value = (
                success,
                {"count_graded": count_graded, "count_required": count_required}
            )

            # Returning score dict.
            return self.peer_grading.get_score()

    def test_deprecation_message(self):
        """
        Test the validation message produced for deprecation.
        """
        peer_grading_module = self.peer_grading

        validation = peer_grading_module.validate()
        self.assertEqual(len(validation.messages), 0)

        self.assertEqual(
            validation.summary.text,
            "ORA1 is no longer supported. To use this assessment, replace this ORA1 component with an ORA2 component."
        )
        self.assertEqual(validation.summary.type, StudioValidationMessage.ERROR)


class MockPeerGradingServiceProblemList(MockPeerGradingService):
    def get_problem_list(self, course_id, grader_id):
        return {'success': True,
                'problem_list': [
                    {
                        "num_graded": 3,
                        "num_pending": 681,
                        "num_required": 3,
                        "location": course_id.make_usage_key('combinedopenended', 'SampleQuestion'),
                        "problem_name": "Peer-Graded Essay"
                    },
                ]}


class PeerGradingModuleScoredTest(unittest.TestCase, DummyModulestore):
    """
    Test peer grading xmodule at the unit level.  More detailed tests are difficult, as the module relies on an
    external grading service.
    """

    course_id = SlashSeparatedCourseKey('edX', 'open_ended', '2012_Fall')
    problem_location = course_id.make_usage_key("peergrading", "PeerGradingScored")

    def get_module_system(self, descriptor):
        test_system = get_test_system(self.course_id)
        test_system.open_ended_grading_interface = None
        return test_system

    def setUp(self):
        """
        Create a peer grading module from a test system
        @return:
        """
        super(PeerGradingModuleScoredTest, self).setUp()
        self.setup_modulestore(self.course_id.course)

    def test_metadata_load(self):
        peer_grading = self.get_module_from_location(self.problem_location)
        self.assertFalse(peer_grading.closed())

    def test_problem_list(self):
        """
        Test to see if a peer grading problem list can be correctly initialized.
        """

        # Initialize peer grading module.
        peer_grading = self.get_module_from_location(self.problem_location)

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
    course_id = SlashSeparatedCourseKey('edX', 'open_ended', '2012_Fall')
    problem_location = course_id.make_usage_key("peergrading", "PeerGradingLinked")
    coe_location = course_id.make_usage_key("combinedopenended", "SampleQuestion")

    def get_module_system(self, descriptor):
        test_system = get_test_system(self.course_id)
        test_system.open_ended_grading_interface = None
        return test_system

    def setUp(self):
        """
        Create a peer grading module from a test system.
        """
        super(PeerGradingModuleLinkedTest, self).setUp()
        self.setup_modulestore(self.course_id.course)

    @property
    def field_data(self):
        """
        Setup the proper field data for a peer grading module.
        """

        return DictFieldData({
            'data': '<peergrading/>',
            'location': self.problem_location,
            'use_for_single_location': True,
            'link_to_location': self.coe_location.to_deprecated_string(),
            'graded': True,
        })

    @property
    def scope_ids(self):
        """
        Return the proper scope ids for the peer grading module.
        """
        return ScopeIds(None, None, self.problem_location, self.problem_location)

    def _create_peer_grading_descriptor_with_linked_problem(self):
        # Initialize the peer grading module.
        system = get_test_descriptor_system()

        return system.construct_xblock_from_class(
            PeerGradingDescriptor,
            field_data=self.field_data,
            scope_ids=self.scope_ids
        )

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

        test_system = self.get_module_system(pg_descriptor)

        # Initialize the peer grading module.
        peer_grading = PeerGradingModule(
            pg_descriptor,
            test_system,
            self.field_data,
            self.scope_ids,
        )

        return peer_grading

    def _get_descriptor_with_invalid_link(self, exception_to_raise):
        """
        Ensure that a peer grading descriptor with an invalid link will return an empty list.
        """

        # Create a descriptor, and make loading an item throw an error.
        descriptor = self._create_peer_grading_descriptor_with_linked_problem()
        descriptor.system.load_item = Mock(side_effect=exception_to_raise)

        # Ensure that modules is a list of length 0.
        modules = descriptor.get_required_module_descriptors()
        self.assertIsInstance(modules, list)
        self.assertEqual(len(modules), 0)

    def test_descriptor_with_nopath(self):
        """
        Test to see if a descriptor with a NoPathToItem error when trying to get
        its linked module behaves properly.
        """

        self._get_descriptor_with_invalid_link(NoPathToItem)

    def test_descriptor_with_item_not_found(self):
        """
        Test to see if a descriptor with an ItemNotFound error when trying to get
        its linked module behaves properly.
        """

        self._get_descriptor_with_invalid_link(ItemNotFoundError)

    def test_invalid_link(self):
        """
        Ensure that a peer grading problem with no linked locations stays in panel mode.
        """

        # Setup the peer grading module with no linked locations.
        peer_grading = self._create_peer_grading_with_linked_problem(self.coe_location, valid_linked_descriptor=False)

        self.assertFalse(peer_grading.use_for_single_location_local)
        self.assertTrue(peer_grading.use_for_single_location)

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
        data = peer_grading.handle_ajax('problem', {'location': self.coe_location.to_deprecated_string()})
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
