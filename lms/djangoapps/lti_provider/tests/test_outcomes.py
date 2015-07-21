"""
Tests for the LTI outcome service handlers, both in outcomes.py and in tasks.py
"""

from django.test import TestCase
from lxml import etree
from mock import patch, MagicMock, ANY
from student.tests.factories import UserFactory

from lti_provider.models import GradedAssignment, LtiConsumer, OutcomeService
import lti_provider.outcomes as outcomes
import lti_provider.tasks as tasks
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator


class StoreOutcomeParametersTest(TestCase):
    """
    Tests for the store_outcome_parameters method in outcomes.py
    """

    def setUp(self):
        super(StoreOutcomeParametersTest, self).setUp()
        self.user = UserFactory.create()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )
        self.usage_key = BlockUsageLocator(
            course_key=self.course_key,
            block_type='problem',
            block_id='block_id'
        )
        self.consumer = LtiConsumer(
            consumer_name='consumer',
            consumer_key='consumer_key',
            consumer_secret='secret'
        )
        self.consumer.save()

    def get_valid_request_params(self):
        """
        Returns a dictionary containing a complete set of required LTI
        parameters.
        """
        return {
            'lis_result_sourcedid': 'sourcedid',
            'lis_outcome_service_url': 'http://example.com/service_url',
            'oauth_consumer_key': 'consumer_key',
            'tool_consumer_instance_guid': 'tool_instance_guid',
            'usage_key': self.usage_key,
            'course_key': self.course_key,
        }

    def test_graded_assignment_created(self):
        params = self.get_valid_request_params()
        with self.assertNumQueries(4):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        assignment = GradedAssignment.objects.get(
            lis_result_sourcedid=params['lis_result_sourcedid']
        )
        self.assertEqual(assignment.course_key, self.course_key)
        self.assertEqual(assignment.usage_key, self.usage_key)
        self.assertEqual(assignment.user, self.user)

    def test_outcome_service_created(self):
        params = self.get_valid_request_params()
        with self.assertNumQueries(4):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        outcome = OutcomeService.objects.get(
            lti_consumer=self.consumer
        )
        self.assertEqual(outcome.lti_consumer, self.consumer)

    def test_graded_assignment_references_outcome_service(self):
        params = self.get_valid_request_params()
        with self.assertNumQueries(4):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        outcome = OutcomeService.objects.get(
            lti_consumer=self.consumer
        )
        assignment = GradedAssignment.objects.get(
            lis_result_sourcedid=params['lis_result_sourcedid']
        )
        self.assertEqual(assignment.outcome_service, outcome)

    def test_no_duplicate_graded_assignments(self):
        params = self.get_valid_request_params()
        with self.assertNumQueries(4):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        with self.assertNumQueries(2):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        assignments = GradedAssignment.objects.filter(
            lis_result_sourcedid=params['lis_result_sourcedid']
        )
        self.assertEqual(len(assignments), 1)

    def test_no_duplicate_outcome_services(self):
        params = self.get_valid_request_params()
        with self.assertNumQueries(4):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        with self.assertNumQueries(2):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        outcome_services = OutcomeService.objects.filter(
            lti_consumer=self.consumer
        )
        self.assertEqual(len(outcome_services), 1)

    def test_no_db_update_for_ungraded_assignment(self):
        params = self.get_valid_request_params()
        del params['lis_result_sourcedid']
        with self.assertNumQueries(0):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)

    def test_no_db_update_for_bad_request(self):
        params = self.get_valid_request_params()
        del params['lis_outcome_service_url']
        with self.assertNumQueries(0):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)

    def test_db_record_created_without_consumer_id(self):
        params = self.get_valid_request_params()
        del params['tool_consumer_instance_guid']
        with self.assertNumQueries(4):
            outcomes.store_outcome_parameters(params, self.user, self.consumer)
        self.assertEqual(GradedAssignment.objects.count(), 1)
        self.assertEqual(OutcomeService.objects.count(), 1)


class SignAndSendReplaceResultTest(TestCase):
    """
    Tests for the sign_and_send_replace_result method in outcomes.py
    """

    def setUp(self):
        super(SignAndSendReplaceResultTest, self).setUp()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )
        self.usage_key = BlockUsageLocator(
            course_key=self.course_key,
            block_type='problem',
            block_id='block_id'
        )
        self.user = UserFactory.create()
        consumer = LtiConsumer(
            consumer_name='consumer',
            consumer_key='consumer_key',
            consumer_secret='secret'
        )
        consumer.save()
        outcome = OutcomeService(
            lis_outcome_service_url='http://example.com/service_url',
            lti_consumer=consumer,
        )
        outcome.save()
        self.assignment = GradedAssignment(
            user=self.user,
            course_key=self.course_key,
            usage_key=self.usage_key,
            outcome_service=outcome,
            lis_result_sourcedid='sourcedid',
        )
        self.assignment.save()

    @patch('requests.post', return_value='response')
    def test_sign_and_send_replace_result(self, post_mock):
        response = outcomes.sign_and_send_replace_result(self.assignment, 'xml')
        post_mock.assert_called_with(
            'http://example.com/service_url',
            data='xml',
            auth=ANY,
            headers={'content-type': 'application/xml'}
        )
        self.assertEqual(response, 'response')


class SendOutcomeTest(TestCase):
    """
    Tests for the send_outcome method in tasks.py
    """

    def setUp(self):
        super(SendOutcomeTest, self).setUp()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )
        self.usage_key = BlockUsageLocator(
            course_key=self.course_key,
            block_type='problem',
            block_id='block_id'
        )
        self.descriptor = MagicMock()
        self.descriptor.location = self.usage_key
        self.descriptor.get_parent = MagicMock(return_value=None)
        self.user = UserFactory.create()
        self.points_possible = 10.0
        self.points_earned = 3.0
        self.generate_xml_mock = self.setup_patch(
            'lti_provider.outcomes.generate_replace_result_xml',
            'replace result XML'
        )
        self.replace_result_mock = self.setup_patch(
            'lti_provider.outcomes.sign_and_send_replace_result',
            'replace result response'
        )
        self.check_result_mock = self.setup_patch(
            'lti_provider.outcomes.check_replace_result_response',
            True
        )
        self.module_store = MagicMock()
        self.module_store.get_item = MagicMock(return_value=self.descriptor)
        self.check_result_mock = self.setup_patch(
            'lti_provider.tasks.modulestore',
            self.module_store
        )
        consumer = LtiConsumer(
            consumer_name='Lti Consumer Name',
            consumer_key='consumer_key',
            consumer_secret='consumer_secret',
            instance_guid='tool_instance_guid'
        )
        consumer.save()
        outcome = OutcomeService(
            lis_outcome_service_url='http://example.com/service_url',
            lti_consumer=consumer
        )
        outcome.save()
        self.assignment = GradedAssignment(
            user=self.user,
            course_key=self.course_key,
            usage_key=self.usage_key,
            outcome_service=outcome,
            lis_result_sourcedid='sourcedid',
        )
        self.assignment.save()

    def setup_patch(self, function_name, return_value):
        """
        Patch a method with a given return value, and return the mock
        """
        mock = MagicMock(return_value=return_value)
        new_patch = patch(function_name, new=mock)
        new_patch.start()
        self.addCleanup(new_patch.stop)
        return mock

    @patch('lti_provider.outcomes.get_scores_for_locations')
    def test_with_one_assignment(self, score_mock):
        tasks.send_outcome(
            self.points_possible,
            self.points_earned,
            self.user.id,
            unicode(self.course_key),
            unicode(self.usage_key)
        )
        self.assertFalse(score_mock.called)

    @patch('lti_provider.outcomes.get_scores_for_locations')
    def test_with_composite_assignment(self, score_mock):
        leaf_key = BlockUsageLocator(
            course_key=self.course_key,
            block_type='problem',
            block_id='leaf_problem'
        )
        leaf_descriptor = MagicMock()
        leaf_descriptor.location = leaf_key
        leaf_descriptor.get_parent = MagicMock(return_value=self.descriptor)
        self.module_store.get_item = MagicMock(return_value=leaf_descriptor)
        tasks.send_outcome(
            self.points_possible,
            self.points_earned,
            self.user.id,
            unicode(self.course_key),
            unicode(leaf_key)
        )
        self.assertTrue(score_mock.called)

    def test_score(self):
        tasks.send_outcome(
            self.points_possible,
            self.points_earned,
            self.user.id,
            unicode(self.course_key),
            unicode(self.usage_key)
        )
        self.generate_xml_mock.assert_called_once_with('sourcedid', 0.3)

    def test_integer_score(self):
        tasks.send_outcome(
            10,
            1,
            self.user.id,
            unicode(self.course_key),
            unicode(self.usage_key)
        )
        self.generate_xml_mock.assert_called_once_with('sourcedid', 0.1)

    def test_scores_sent_for_multiple_assignments(self):
        assignment2 = GradedAssignment(
            user=self.user,
            course_key=self.course_key,
            usage_key=self.usage_key,
            outcome_service=self.assignment.outcome_service,
            lis_result_sourcedid='sourcedid2',
        )
        assignment2.save()
        tasks.send_outcome(
            self.points_possible,
            self.points_earned,
            self.user.id,
            unicode(self.course_key),
            unicode(self.usage_key)
        )
        self.assertEqual(self.generate_xml_mock.call_count, 2)


class XmlHandlingTest(TestCase):
    """
    Tests for the generate_replace_result_xml and check_replace_result_response
    methods in outcomes.py
    """

    response_xml = """
        <imsx_POXEnvelopeResponse xmlns = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
          <imsx_POXHeader>
            <imsx_POXResponseHeaderInfo>
              <imsx_version>V1.0</imsx_version>
              <imsx_messageIdentifier>4560</imsx_messageIdentifier>
              <imsx_statusInfo>
                {major_code}
                <imsx_severity>status</imsx_severity>
                <imsx_description>Score for result_id is now 0.25</imsx_description>
                <imsx_messageRefIdentifier>999999123</imsx_messageRefIdentifier>
                <imsx_operationRefIdentifier>replaceResult</imsx_operationRefIdentifier>
              </imsx_statusInfo>
            </imsx_POXResponseHeaderInfo>
          </imsx_POXHeader>
          <imsx_POXBody>
            <replaceResultResponse/>
          </imsx_POXBody>
        </imsx_POXEnvelopeResponse>
    """

    result_id = 'result_id'
    score = 0.25

    @patch('uuid.uuid4', return_value='random_uuid')
    def test_replace_result_message_uuid(self, _uuid_mock):
        # Pylint doesn't recognize members in the LXML module
        # pylint: disable=no-member
        xml = outcomes.generate_replace_result_xml(self.result_id, self.score)
        tree = etree.fromstring(xml)
        message_id = tree.xpath(
            '//ns:imsx_messageIdentifier',
            namespaces={'ns': 'http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0'}
        )
        self.assertEqual(len(message_id), 1)
        self.assertEqual(message_id[0].text, 'random_uuid')

    def test_replace_result_sourced_id(self):
        # pylint: disable=no-member
        xml = outcomes.generate_replace_result_xml(self.result_id, self.score)
        tree = etree.fromstring(xml)
        sourced_id = tree.xpath(
            '/ns:imsx_POXEnvelopeRequest/ns:imsx_POXBody/ns:replaceResultRequest/'
            'ns:resultRecord/ns:sourcedGUID/ns:sourcedId',
            namespaces={'ns': 'http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0'}
        )
        self.assertEqual(len(sourced_id), 1)
        self.assertEqual(sourced_id[0].text, 'result_id')

    def test_replace_result_score(self):
        # pylint: disable=no-member
        xml = outcomes.generate_replace_result_xml(self.result_id, self.score)
        tree = etree.fromstring(xml)
        xml_score = tree.xpath(
            '/ns:imsx_POXEnvelopeRequest/ns:imsx_POXBody/ns:replaceResultRequest/'
            'ns:resultRecord/ns:result/ns:resultScore/ns:textString',
            namespaces={'ns': 'http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0'}
        )
        self.assertEqual(len(xml_score), 1)
        self.assertEqual(xml_score[0].text, '0.25')

    def create_response_object(
            self, status, xml,
            major_code='<imsx_codeMajor>success</imsx_codeMajor>'
    ):
        """
        Returns an XML document containing a successful replace_result response.
        """
        response = MagicMock()
        response.status_code = status
        response.content = xml.format(major_code=major_code).encode('ascii', 'ignore')
        return response

    def test_response_with_correct_xml(self):
        xml = self.response_xml
        response = self.create_response_object(200, xml)
        self.assertTrue(outcomes.check_replace_result_response(response))

    def test_response_with_bad_status_code(self):
        response = self.create_response_object(500, '')
        self.assertFalse(outcomes.check_replace_result_response(response))

    def test_response_with_invalid_xml(self):
        xml = '<badly>formatted</xml>'
        response = self.create_response_object(200, xml)
        self.assertFalse(outcomes.check_replace_result_response(response))

    def test_response_with_multiple_status_fields(self):
        response = self.create_response_object(
            200, self.response_xml,
            major_code='<imsx_codeMajor>success</imsx_codeMajor>'
                       '<imsx_codeMajor>failure</imsx_codeMajor>'
        )
        self.assertFalse(outcomes.check_replace_result_response(response))

    def test_response_with_no_status_field(self):
        response = self.create_response_object(
            200, self.response_xml,
            major_code=''
        )
        self.assertFalse(outcomes.check_replace_result_response(response))

    def test_response_with_failing_status_field(self):
        response = self.create_response_object(
            200, self.response_xml,
            major_code='<imsx_codeMajor>failure</imsx_codeMajor>'
        )
        self.assertFalse(outcomes.check_replace_result_response(response))


def create_descriptor_mock(parent, course_key, block_id):
    """
    Build a mock object for a content descriptor. This method assumes that
    parent descriptors are created before child descriptors in order to properly
    wire up the parent and child accessors.
    """
    desc = MagicMock()
    desc.location = BlockUsageLocator(
        course_key=course_key,
        block_type='problem',
        block_id=block_id,
    )
    desc.children = []
    desc.get_children = MagicMock(return_value=desc.children)
    desc.get_parent = MagicMock(return_value=parent)
    if parent:
        parent.children.append(desc)
    return desc


class TestAssignmentsForProblem(TestCase):
    """
    Test cases for the assignments_for_problem method in outcomes.py
    """
    def setUp(self):
        super(TestAssignmentsForProblem, self).setUp()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )
        self.course_desc = create_descriptor_mock(None, self.course_key, 'course')
        self.chapter_desc = create_descriptor_mock(self.course_desc, self.course_key, 'chapter')
        self.section_desc = create_descriptor_mock(self.course_desc, self.course_key, 'section')
        self.vertical_desc = create_descriptor_mock(self.section_desc, self.course_key, 'vertical')
        self.unit_desc = create_descriptor_mock(self.vertical_desc, self.course_key, 'unit')
        self.user = UserFactory.create()
        self.user_id = self.user.id
        self.outcome_service = self.create_outcome_service('outcomes')

    def create_outcome_service(self, id_suffix):
        """
        Create and save a new OutcomeService model in the test database. The
        OutcomeService model requires an LtiConsumer model, so we create one of
        those as well. The method takes an ID string that is used to ensure that
        unique fields do not conflict.
        """
        lti_consumer = LtiConsumer(
            consumer_name='lti_consumer_name' + id_suffix,
            consumer_key='lti_consumer_key' + id_suffix,
            consumer_secret='lti_consumer_secret' + id_suffix,
            instance_guid='lti_instance_guid' + id_suffix
        )
        lti_consumer.save()
        outcome_service = OutcomeService(
            lis_outcome_service_url='https://example.com/outcomes/' + id_suffix,
            lti_consumer=lti_consumer
        )
        outcome_service.save()
        return outcome_service

    def create_graded_assignment(self, desc, result_id, outcome_service):
        """
        Create and save a new GradedAssignment model in the test database.
        """
        assignment = GradedAssignment(
            user=self.user,
            course_key=self.course_key,
            usage_key=desc.location,
            outcome_service=outcome_service,
            lis_result_sourcedid=result_id
        )
        assignment.save()
        return assignment

    def test_with_no_graded_assignments(self):
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, self.user_id, self.course_key
        )
        self.assertEqual(len(assignments), 0)

    def test_with_graded_unit(self):
        self.create_graded_assignment(self.unit_desc, 'graded_unit', self.outcome_service)
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, self.user_id, self.course_key
        )
        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(assignments[self.unit_desc]), 1)
        self.assertEqual(
            assignments[self.unit_desc][0].lis_result_sourcedid,
            'graded_unit'
        )

    def test_with_graded_vertical(self):
        self.create_graded_assignment(self.vertical_desc, 'graded_vertical', self.outcome_service)
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, self.user_id, self.course_key
        )
        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(assignments[self.vertical_desc]), 1)
        self.assertEqual(
            assignments[self.vertical_desc][0].lis_result_sourcedid,
            'graded_vertical'
        )

    def test_with_graded_unit_and_vertical(self):
        self.create_graded_assignment(self.unit_desc, 'graded_unit', self.outcome_service)
        self.create_graded_assignment(self.vertical_desc, 'graded_vertical', self.outcome_service)
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, self.user_id, self.course_key
        )
        self.assertEqual(len(assignments), 2)
        self.assertEqual(len(assignments[self.unit_desc]), 1)
        self.assertEqual(len(assignments[self.vertical_desc]), 1)
        self.assertEqual(
            assignments[self.unit_desc][0].lis_result_sourcedid,
            'graded_unit'
        )
        self.assertEqual(
            assignments[self.vertical_desc][0].lis_result_sourcedid,
            'graded_vertical'
        )

    def test_with_unit_used_twice(self):
        self.create_graded_assignment(self.unit_desc, 'graded_unit', self.outcome_service)
        self.create_graded_assignment(self.unit_desc, 'graded_unit2', self.outcome_service)
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, self.user_id, self.course_key
        )
        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(assignments[self.unit_desc]), 2)
        self.assertEqual(
            assignments[self.unit_desc][0].lis_result_sourcedid,
            'graded_unit'
        )
        self.assertEqual(
            assignments[self.unit_desc][1].lis_result_sourcedid,
            'graded_unit2'
        )

    def test_with_unit_graded_for_different_user(self):
        self.create_graded_assignment(self.unit_desc, 'graded_unit', self.outcome_service)
        other_user = UserFactory.create()
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, other_user.id, self.course_key
        )
        self.assertEqual(len(assignments), 0)

    def test_with_unit_graded_for_multiple_consumers(self):
        other_outcome_service = self.create_outcome_service('second_consumer')
        self.create_graded_assignment(self.unit_desc, 'graded_unit', self.outcome_service)
        self.create_graded_assignment(self.unit_desc, 'graded_unit2', other_outcome_service)
        assignments = outcomes.get_assignments_for_problem(
            self.unit_desc, self.user_id, self.course_key
        )
        self.assertEqual(len(assignments), 1)
        self.assertEqual(len(assignments[self.unit_desc]), 2)
        self.assertEqual(
            assignments[self.unit_desc][0].lis_result_sourcedid,
            'graded_unit'
        )
        self.assertEqual(
            assignments[self.unit_desc][1].lis_result_sourcedid,
            'graded_unit2'
        )
        self.assertEqual(
            assignments[self.unit_desc][0].outcome_service,
            self.outcome_service
        )
        self.assertEqual(
            assignments[self.unit_desc][1].outcome_service,
            other_outcome_service
        )


class TestCalculateScore(TestCase):
    """
    Test the method that calculates the score for a given block based on the
    cumulative scores of its children. This test class uses a hard-coded block
    hierarchy with scores as follows:
                                                a
                                       +--------+--------+
                                       b                 c
                        +--------------+-----------+     |
                        d              e           f     g
                     +-----+     +-----+-----+     |     |
                     h     i     j     k     l     m     n
                   (2/5) (3/5) (0/1)   -   (1/3)   -   (3/10)

    """
    def setUp(self):
        super(TestCalculateScore, self).setUp()
        self.course_key = CourseLocator(
            org='some_org',
            course='some_course',
            run='some_run'
        )
        self.desc_a = create_descriptor_mock(None, self.course_key, 'a')
        self.desc_b = create_descriptor_mock(self.desc_a, self.course_key, 'b')
        self.desc_c = create_descriptor_mock(self.desc_a, self.course_key, 'c')
        self.desc_d = create_descriptor_mock(self.desc_b, self.course_key, 'd')
        self.desc_e = create_descriptor_mock(self.desc_b, self.course_key, 'e')
        self.desc_f = create_descriptor_mock(self.desc_b, self.course_key, 'f')
        self.desc_g = create_descriptor_mock(self.desc_c, self.course_key, 'g')
        self.desc_h = create_descriptor_mock(self.desc_d, self.course_key, 'h')
        self.desc_i = create_descriptor_mock(self.desc_d, self.course_key, 'i')
        self.desc_j = create_descriptor_mock(self.desc_e, self.course_key, 'j')
        self.desc_k = create_descriptor_mock(self.desc_e, self.course_key, 'k')
        self.desc_l = create_descriptor_mock(self.desc_e, self.course_key, 'l')
        self.desc_m = create_descriptor_mock(self.desc_f, self.course_key, 'm')
        self.desc_n = create_descriptor_mock(self.desc_g, self.course_key, 'n')

        self.location_to_score = {
            self.desc_h.location: self.create_score(2, 5),
            self.desc_i.location: self.create_score(3, 5),
            self.desc_j.location: self.create_score(0, 1),
            self.desc_l.location: self.create_score(1, 3),
            self.desc_n.location: self.create_score(3, 10),
        }

    def create_score(self, earned, possible):
        """
        Build a mock for the Score model. We are only concerned with the earned
        and possible score fields for these tests.
        """
        score = MagicMock()
        score.possible = possible
        score.earned = earned
        return score

    def test_score_chapter(self):
        earned, possible = outcomes.calculate_score(self.desc_a, self.location_to_score)
        self.assertEqual(earned, 9)
        self.assertEqual(possible, 24)

    def test_score_section_many_leaves(self):
        earned, possible = outcomes.calculate_score(self.desc_b, self.location_to_score)
        self.assertEqual(earned, 6)
        self.assertEqual(possible, 14)

    def test_score_section_one_leaf(self):
        earned, possible = outcomes.calculate_score(self.desc_c, self.location_to_score)
        self.assertEqual(earned, 3)
        self.assertEqual(possible, 10)

    def test_score_vertical_two_leaves(self):
        earned, possible = outcomes.calculate_score(self.desc_d, self.location_to_score)
        self.assertEqual(earned, 5)
        self.assertEqual(possible, 10)

    def test_score_vertical_two_leaves_one_unscored(self):
        earned, possible = outcomes.calculate_score(self.desc_e, self.location_to_score)
        self.assertEqual(earned, 1)
        self.assertEqual(possible, 4)

    def test_score_vertical_no_score(self):
        earned, possible = outcomes.calculate_score(self.desc_f, self.location_to_score)
        self.assertEqual(earned, 0)
        self.assertEqual(possible, 0)

    def test_score_vertical_one_leaf(self):
        earned, possible = outcomes.calculate_score(self.desc_g, self.location_to_score)
        self.assertEqual(earned, 3)
        self.assertEqual(possible, 10)

    def test_score_leaf(self):
        earned, possible = outcomes.calculate_score(self.desc_h, self.location_to_score)
        self.assertEqual(earned, 2)
        self.assertEqual(possible, 5)

    def test_score_leaf_no_score(self):
        earned, possible = outcomes.calculate_score(self.desc_m, self.location_to_score)
        self.assertEqual(earned, 0)
        self.assertEqual(possible, 0)
