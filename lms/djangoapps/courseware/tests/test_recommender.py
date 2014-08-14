"""
This test file will run through some XBlock test scenarios regarding the
recommender system
"""
import json
import itertools
import StringIO
from ddt import ddt, data
from copy import deepcopy

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, mixed_store_config

from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tests.factories import GlobalStaffFactory

from lms.djangoapps.lms_xblock.runtime import quote_slashes

MODULESTORE_CONFIG = mixed_store_config(settings.COMMON_TEST_DATA_ROOT, {}, include_xml=False)


@override_settings(MODULESTORE=MODULESTORE_CONFIG)
class TestRecommender(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Check that Recommender state is saved properly
    """
    STUDENTS = [
        {'email': 'view@test.com', 'password': 'foo'},
        {'email': 'view2@test.com', 'password': 'foo'}
    ]
    XBLOCK_NAMES = ['recommender', 'recommender_second']

    def setUp(self):
        self.course = CourseFactory.create(
            display_name='Recommender_Test_Course'
        )
        self.chapter = ItemFactory.create(
            parent=self.course, display_name='Overview'
        )
        self.section = ItemFactory.create(
            parent=self.chapter, display_name='Welcome'
        )
        self.unit = ItemFactory.create(
            parent=self.section, display_name='New Unit'
        )
        self.xblock = ItemFactory.create(
            parent=self.unit,
            category='recommender',
            display_name='recommender'
        )
        self.xblock2 = ItemFactory.create(
            parent=self.unit,
            category='recommender',
            display_name='recommender_second'
        )

        self.course_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course.id.to_deprecated_string(),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )

        self.resource_urls = [
            (
                "https://courses.edx.org/courses/MITx/3.091X/"
                "2013_Fall/courseware/SP13_Week_4/"
                "SP13_Periodic_Trends_and_Bonding/"
            ),
            (
                "https://courses.edx.org/courses/MITx/3.091X/"
                "2013_Fall/courseware/SP13_Week_4/SP13_Covalent_Bonding/"
            )
        ]

        self.test_recommendations = {
            self.resource_urls[0]: {
                "title": "Covalent bonding and periodic trends",
                "url": self.resource_urls[0],
                "description": (
                    "http://people.csail.mit.edu/swli/edx/"
                    "recommendation/img/videopage1.png"
                ),
                "descriptionText": (
                    "short description for Covalent bonding "
                    "and periodic trends"
                )
            },
            self.resource_urls[1]: {
                "title": "Polar covalent bonds and electronegativity",
                "url": self.resource_urls[1],
                "description": (
                    "http://people.csail.mit.edu/swli/edx/"
                    "recommendation/img/videopage2.png"
                ),
                "descriptionText": (
                    "short description for Polar covalent "
                    "bonds and electronegativity"
                )
            }
        }

        for idx, student in enumerate(self.STUDENTS):
            username = "u{}".format(idx)
            self.create_account(username, student['email'], student['password'])
            self.activate_user(student['email'])

        self.staff_user = GlobalStaffFactory()

    def get_handler_url(self, handler, xblock_name=None):
        """
        Get url for the specified xblock handler
        """
        if xblock_name is None:
            xblock_name = TestRecommender.XBLOCK_NAMES[0]
        return reverse('xblock_handler', kwargs={
            'course_id': self.course.id.to_deprecated_string(),
            'usage_id': quote_slashes(self.course.id.make_usage_key('recommender', xblock_name).to_deprecated_string()),
            'handler': handler,
            'suffix': ''
        })

    def enroll_student(self, email, password):
        """
        Student login and enroll for the course
        """
        self.login(email, password)
        self.enroll(self.course, verify=True)

    def enroll_staff(self, staff):
        """
        Staff login and enroll for the course
        """
        email = staff.email
        password = 'test'
        self.login(email, password)
        self.enroll(self.course, verify=True)

    def initialize_database_by_id(self, handler, resource_id, times, xblock_name=None):
        """
        Call a ajax event (vote, delete, endorse) on a resource by its id
        several times
        """
        if xblock_name is None:
            xblock_name = TestRecommender.XBLOCK_NAMES[0]
        url = self.get_handler_url(handler, xblock_name)
        for _ in range(0, times):
            self.client.post(url, json.dumps({'id': resource_id}), '')

    def call_event(self, handler, resource, xblock_name=None):
        """
        Call a ajax event (add, edit, flag, etc.) by specifying the resource
        it takes
        """
        if xblock_name is None:
            xblock_name = TestRecommender.XBLOCK_NAMES[0]
        url = self.get_handler_url(handler, xblock_name)
        resp = self.client.post(url, json.dumps(resource), '')
        return json.loads(resp.content)

    def check_event_response_by_element(self, handler, resource, resp_key, resp_val, xblock_name=None):
        """
        Call the event specified by the handler with the resource, and check
        whether the element (resp_key) in response is as expected (resp_val)
        """
        if xblock_name is None:
            xblock_name = TestRecommender.XBLOCK_NAMES[0]
        resp = self.call_event(handler, resource, xblock_name)
        self.assertEqual(resp[resp_key], resp_val)
        self.assert_request_status_code(200, self.course_url)


class TestRecommenderCreateFromEmpty(TestRecommender):
    """
    Check whether we can add resources to an empty database correctly
    """
    def test_add_resource(self):
        """
        Verify the addition of new resource is handled correctly
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'])
        # Check whether adding new resource is successful
        for resource_id, resource in self.test_recommendations.iteritems():
            for xblock_name in self.XBLOCK_NAMES:
                result = self.call_event('add_resource', resource, xblock_name)

                expected_result = {
                    'Success': True,
                    'upvotes': 0,
                    'downvotes': 0,
                    'id': resource_id
                }
                for field in resource:
                    expected_result[field] = resource[field]

                self.assertDictEqual(result, expected_result)
                self.assert_request_status_code(200, self.course_url)

    def test_import_resources_by_student(self):
        """
        Test the function for importing all resources into the Recommender
        by a student.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'])
        # Preparing imported resources
        initial_configuration = {
            'flagged_accum_resources': {},
            'endorsed_recommendation_reasons': [],
            'endorsed_recommendation_ids': [],
            'deendorsed_recommendations': {},
            'recommendations': self.test_recommendations[self.resource_urls[0]]
        }
        # Importing resources
        f_handler = StringIO.StringIO(json.dumps(initial_configuration, sort_keys=True))
        f_handler.name = 'import_resources'
        url = self.get_handler_url('import_resources')
        resp = self.client.post(url, {'file': f_handler})
        self.assertEqual(resp.content, 'NOT_A_STAFF')
        self.assert_request_status_code(200, self.course_url)

    def test_import_resources(self):
        """
        Test the function for importing all resources into the Recommender.
        """
        self.enroll_staff(self.staff_user)
        # Preparing imported resources
        initial_configuration = {
            'flagged_accum_resources': {},
            'endorsed_recommendation_reasons': [],
            'endorsed_recommendation_ids': [],
            'deendorsed_recommendations': {},
            'recommendations': self.test_recommendations[self.resource_urls[0]]
        }
        # Importing resources
        f_handler = StringIO.StringIO(json.dumps(initial_configuration, sort_keys=True))
        f_handler.name = 'import_resources'
        url = self.get_handler_url('import_resources')
        resp = self.client.post(url, {'file': f_handler})
        self.assertEqual(resp.content, json.dumps(initial_configuration, sort_keys=True))
        self.assert_request_status_code(200, self.course_url)


class TestRecommenderWithResources(TestRecommender):
    """
    Check whether we can add/edit/flag/export resources correctly
    """
    def setUp(self):
        # call the setUp function from the superclass
        super(TestRecommenderWithResources, self).setUp()
        self.resource_id = self.resource_urls[0]
        self.resource_id_second = self.resource_urls[1]
        self.non_existing_resource_id = 'An non-existing id'
        self.set_up_resources()

    def set_up_resources(self):
        """
        Set up resources and enroll staff
        """
        self.logout()
        self.enroll_staff(self.staff_user)
        # Add resources, assume correct here, tested in test_add_resource
        for resource, xblock_name in itertools.product(self.test_recommendations.values(), self.XBLOCK_NAMES):
            self.call_event('add_resource', resource, xblock_name)

    def generate_edit_resource(self, resource_id):
        """
        Based on the given resource (specified by resource_id), this function
        generate a new one for testing 'edit_resource' event
        """
        resource = {"id": resource_id}
        edited_recommendations = {
            key: value + " edited" for key, value in self.test_recommendations[self.resource_id].iteritems()
        }
        resource.update(edited_recommendations)
        return resource

    def test_add_redundant_resource(self):
        """
        Verify the addition of a redundant resource (url) is rejected
        """
        for suffix in ['', '#IAmSuffix', '%23IAmSuffix']:
            resource = deepcopy(self.test_recommendations[self.resource_id])
            resource['url'] += suffix
            result = self.call_event('add_resource', resource)

            expected_result = {
                'Success': False,
                'error': (
                    'The resource you are attempting to '
                    'provide has already existed'
                ),
                'dup_id': self.resource_id
            }
            for field in resource:
                expected_result[field] = resource[field]
                expected_result['dup_' + field] = self.test_recommendations[self.resource_id][field]

            self.assertDictEqual(result, expected_result)
            self.assert_request_status_code(200, self.course_url)

    def test_add_deendorsed_resource(self):
        """
        Verify the addition of a deendorsed resource (url) is rejected
        """
        self.call_event('deendorse_resource', {"id": self.resource_id, 'reason': ''})
        err_msg = 'The resource you are attempting to provide has been de-endorsed by staff, because: .*'
        for suffix in ['', '#IAmSuffix', '%23IAmSuffix']:
            resource = deepcopy(self.test_recommendations[self.resource_id])
            resource['url'] += suffix
            resp = self.call_event('add_resource', resource)
            self.assertRegexpMatches(resp['error'], err_msg)
            self.assert_request_status_code(200, self.course_url)

    def test_edit_resource_non_existing(self):
        """
        Edit a non-existing resource
        """
        resp = self.call_event(
            'edit_resource', self.generate_edit_resource(self.non_existing_resource_id)
        )
        self.assertEqual(resp['error'], 'The selected resource is not existing')
        self.assert_request_status_code(200, self.course_url)

    def test_edit_redundant_resource(self):
        """
        Check whether changing the url to the one of 'another' resource is
        rejected
        """
        for suffix in ['', '#IAmSuffix', '%23IAmSuffix']:
            resource = self.generate_edit_resource(self.resource_id)
            resource['url'] = self.resource_id_second + suffix
            resp = self.call_event('edit_resource', resource)
            self.assertEqual(resp['error'], 'The resource you are attempting to provide has already existed')
            self.assertEqual(resp['dup_id'], self.resource_id_second)
            self.assert_request_status_code(200, self.course_url)

    def test_edit_deendorsed_resource(self):
        """
        Check whether changing the url to the one of a deendorsed resource is
        rejected
        """
        self.call_event('deendorse_resource', {"id": self.resource_id_second, 'reason': ''})
        err_msg = 'The resource you are attempting to provide has been de-endorsed by staff, because: .*'
        for suffix in ['', '#IAmSuffix', '%23IAmSuffix']:
            resource = self.generate_edit_resource(self.resource_id)
            resource['url'] = self.resource_id_second + suffix
            resp = self.call_event('edit_resource', resource)
            self.assertRegexpMatches(resp['error'], err_msg)
            self.assertEqual(resp['dup_id'], self.resource_id_second)
            self.assert_request_status_code(200, self.course_url)

    def test_edit_resource(self):
        """
        Check whether changing the content of resource is successful
        """
        resp = self.call_event(
            'edit_resource', self.generate_edit_resource(self.resource_id)
        )
        self.assertEqual(resp['Success'], True)
        self.assert_request_status_code(200, self.course_url)

    def test_edit_resource_same_url(self):
        """
        Check whether changing the content (except for url) of resource is successful
        """
        resource = self.generate_edit_resource(self.resource_id)
        for suffix in ['', '#IAmSuffix', '%23IAmSuffix']:
            resource['url'] = self.resource_id + suffix
            resp = self.call_event('edit_resource', resource)
            self.assertEqual(resp['Success'], True)
            self.assert_request_status_code(200, self.course_url)

    def test_edit_then_add_resource(self):
        """
        Check whether we can add back an edited resource
        """
        self.call_event('edit_resource', self.generate_edit_resource(self.resource_id))
        # Test
        resp = self.call_event('add_resource', self.test_recommendations[self.resource_id])
        self.assertEqual(resp['id'], self.resource_id)
        self.assert_request_status_code(200, self.course_url)

    def test_edit_resources_in_different_xblocks(self):
        """
        Check whether changing the content of resource is successful in two
        different xblocks
        """
        resource = self.generate_edit_resource(self.resource_id)
        for xblock_name in self.XBLOCK_NAMES:
            resp = self.call_event('edit_resource', resource, xblock_name)
            self.assertEqual(resp['Success'], True)
            self.assert_request_status_code(200, self.course_url)

    def test_flag_resource_wo_reason(self):
        """
        Flag a resource as problematic, without providing the reason
        """
        resource = {'id': self.resource_id, 'isProblematic': True, 'reason': ''}
        # Test
        self.check_event_response_by_element('flag_resource', resource, 'reason', '')

    def test_flag_resource_w_reason(self):
        """
        Flag a resource as problematic, with providing the reason
        """
        resource = {'id': self.resource_id, 'isProblematic': True, 'reason': 'reason 0'}
        # Test
        self.check_event_response_by_element('flag_resource', resource, 'reason', 'reason 0')

    def test_flag_resource_change_reason(self):
        """
        Flag a resource as problematic twice, with different reasons
        """
        resource = {'id': self.resource_id, 'isProblematic': True, 'reason': 'reason 0'}
        self.call_event('flag_resource', resource)
        # Test
        resource['reason'] = 'reason 1'
        resp = self.call_event('flag_resource', resource)
        self.assertEqual(resp['oldReason'], 'reason 0')
        self.assertEqual(resp['reason'], 'reason 1')
        self.assert_request_status_code(200, self.course_url)

    def test_flag_resources_in_different_xblocks(self):
        """
        Flag resources as problematic in two different xblocks
        """
        resource = {'id': self.resource_id, 'isProblematic': True, 'reason': 'reason 0'}
        # Test
        for xblock_name in self.XBLOCK_NAMES:
            self.check_event_response_by_element('flag_resource', resource, 'reason', 'reason 0', xblock_name)

    def test_flag_resources_by_different_users(self):
        """
        Different users can't see the flag result of each other
        """
        resource = {'id': self.resource_id, 'isProblematic': True, 'reason': 'reason 0'}
        self.call_event('flag_resource', resource)
        self.logout()
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'])
        # Test
        resp = self.call_event('flag_resource', resource)
        # The second user won't see the reason provided by the first user
        self.assertNotIn('oldReason', resp)
        self.assertEqual(resp['reason'], 'reason 0')
        self.assert_request_status_code(200, self.course_url)

    def test_export_resources(self):
        """
        Test the function for exporting all resources from the Recommender.
        """
        self.call_event('deendorse_resource', {"id": self.resource_id, 'reason': ''})
        self.call_event('endorse_resource', {"id": self.resource_id_second, 'reason': ''})
        # Test
        resp = self.call_event('export_resources', {})

        self.assertIn(self.resource_id_second, resp['export']['recommendations'])
        self.assertNotIn(self.resource_id, resp['export']['recommendations'])
        self.assertIn(self.resource_id_second, resp['export']['endorsed_recommendation_ids'])
        self.assertIn(self.resource_id, resp['export']['deendorsed_recommendations'])
        self.assert_request_status_code(200, self.course_url)


@ddt
class TestRecommenderVoteWithResources(TestRecommenderWithResources):
    """
    Check whether we can vote resources correctly
    """
    def setUp(self):
        # call the setUp function from the superclass
        super(TestRecommenderVoteWithResources, self).setUp()

    @data(
        {'event': 'recommender_upvote'},
        {'event': 'recommender_downvote'}
    )
    def test_vote_resource_non_existing(self, test_case):
        """
        Vote a non-existing resource
        """
        resource = {"id": self.non_existing_resource_id, 'event': test_case['event']}
        self.check_event_response_by_element('handle_vote', resource, 'error', 'The selected resource is not existing')

    @data(
        {'event': 'recommender_upvote', 'new_votes': 1},
        {'event': 'recommender_downvote', 'new_votes': -1}
    )
    def test_vote_resource_once(self, test_case):
        """
        Vote a resource
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'])

    @data(
        {'event': 'recommender_upvote', 'new_votes': 0},
        {'event': 'recommender_downvote', 'new_votes': 0}
    )
    def test_vote_resource_twice(self, test_case):
        """
        Vote a resource twice
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        self.call_event('handle_vote', resource)
        # Test
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'])

    @data(
        {'event': 'recommender_upvote', 'new_votes': 1},
        {'event': 'recommender_downvote', 'new_votes': -1}
    )
    def test_vote_resource_thrice(self, test_case):
        """
        Vote a resource thrice
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        for _ in range(0, 2):
            self.call_event('handle_vote', resource)
        # Test
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'])

    @data(
        {'event': 'recommender_upvote', 'event_second': 'recommender_downvote', 'new_votes': -1},
        {'event': 'recommender_downvote', 'event_second': 'recommender_upvote', 'new_votes': 1}
    )
    def test_switch_vote_resource(self, test_case):
        """
        Switch the vote of a resource
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        self.call_event('handle_vote', resource)
        # Test
        resource['event'] = test_case['event_second']
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'])

    @data(
        {'event': 'recommender_upvote', 'new_votes': 1},
        {'event': 'recommender_downvote', 'new_votes': -1}
    )
    def test_vote_different_resources(self, test_case):
        """
        Vote two different resources
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        self.call_event('handle_vote', resource)
        # Test
        resource['id'] = self.resource_id_second
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'])

    @data(
        {'event': 'recommender_upvote', 'new_votes': 1},
        {'event': 'recommender_downvote', 'new_votes': -1}
    )
    def test_vote_resources_in_different_xblocks(self, test_case):
        """
        Vote two resources in two different xblocks
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        self.call_event('handle_vote', resource)
        # Test
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'], self.XBLOCK_NAMES[1])

    @data(
        {'event': 'recommender_upvote', 'new_votes': 2},
        {'event': 'recommender_downvote', 'new_votes': -2}
    )
    def test_vote_resource_by_different_users(self, test_case):
        """
        Vote resource by two different users
        """
        resource = {"id": self.resource_id, 'event': test_case['event']}
        self.call_event('handle_vote', resource)
        self.logout()
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'])
        # Test
        self.check_event_response_by_element('handle_vote', resource, 'newVotes', test_case['new_votes'])


@ddt
class TestRecommenderStaffFeedbackWithResources(TestRecommenderWithResources):
    """
    Check whether we can deendorse/endorse resources correctly
    """
    def setUp(self):
        # call the setUp function from the superclass
        super(TestRecommenderStaffFeedbackWithResources, self).setUp()

    @data('deendorse_resource', 'endorse_resource')
    def test_deendorse_or_endorse_resource_non_existing(self, test_case):
        """
        Deendorse/endorse a non-existing resource
        """
        resource = {"id": self.non_existing_resource_id, 'reason': ''}
        self.check_event_response_by_element(test_case, resource, 'error', 'The selected resource is not existing')

    @data(
        {'handler': 'deendorse_resource', 'key': 'Success', 'val': True},
        {'handler': 'endorse_resource', 'key': 'status', 'val': 'endorsement'}
    )
    def test_deendorse_or_endorse_resource_once(self, test_case):
        """
        Deendorse/endorse a resource
        """
        resource = {"id": self.resource_id, 'reason': ''}
        self.check_event_response_by_element(test_case['handler'], resource, test_case['key'], test_case['val'])

    @data(
        {'handler': 'deendorse_resource', 'key': 'error', 'val': 'The selected resource is not existing'},
        {'handler': 'endorse_resource', 'key': 'status', 'val': 'undo endorsement'}
    )
    def test_deendorse_or_endorse_resource_twice(self, test_case):
        """
        Deendorse/endorse a resource twice
        """
        resource = {"id": self.resource_id, 'reason': ''}
        self.call_event(test_case['handler'], resource)
        # Test
        self.check_event_response_by_element(test_case['handler'], resource, test_case['key'], test_case['val'])

    @data(
        {'handler': 'deendorse_resource', 'key': 'error', 'val': 'The selected resource is not existing'},
        {'handler': 'endorse_resource', 'key': 'status', 'val': 'endorsement'}
    )
    def test_endorse_resource_thrice(self, test_case):
        """
        Deendorse/endorse a resource thrice
        """
        resource = {"id": self.resource_id, 'reason': ''}
        for _ in range(0, 2):
            self.call_event(test_case['handler'], resource)
        # Test
        self.check_event_response_by_element(test_case['handler'], resource, test_case['key'], test_case['val'])

    @data(
        {'handler': 'deendorse_resource', 'key': 'Success', 'val': True},
        {'handler': 'endorse_resource', 'key': 'status', 'val': 'endorsement'}
    )
    def test_deendorse_or_endorse_different_resources(self, test_case):
        """
        Deendorse/endorse two different resources
        """
        self.call_event(test_case['handler'], {"id": self.resource_id, 'reason': ''})
        # Test
        resource = {"id": self.resource_id_second, 'reason': ''}
        self.check_event_response_by_element(test_case['handler'], resource, test_case['key'], test_case['val'])

    @data(
        {'handler': 'deendorse_resource', 'key': 'Success', 'val': True},
        {'handler': 'endorse_resource', 'key': 'status', 'val': 'endorsement'}
    )
    def test_deendorse_or_endorse_resources_in_different_xblocks(self, test_case):
        """
        Deendorse/endorse two resources in two different xblocks
        """
        self.call_event(test_case['handler'], {"id": self.resource_id, 'reason': ''})
        # Test
        resource = {"id": self.resource_id, 'reason': ''}
        self.check_event_response_by_element(test_case['handler'], resource, test_case['key'], test_case['val'], self.XBLOCK_NAMES[1])

    @data(
        {'handler': 'deendorse_resource', 'key': 'error', 'val': 'Deendorse resource without permission'},
        {'handler': 'endorse_resource', 'key': 'error', 'val': 'Endorse resource without permission'}
    )
    def test_deendorse_or_endorse_resource_by_student(self, test_case):
        """
        Deendorse/endorse resource by a student
        """
        self.logout()
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'])
        # Test
        resource = {"id": self.resource_id, 'reason': ''}
        self.check_event_response_by_element(test_case['handler'], resource, test_case['key'], test_case['val'])


@ddt
class TestRecommenderFileUploading(TestRecommender):
    """
    Check whether we can handle file uploading correctly
    """
    def setUp(self):
        # call the setUp function from the superclass
        super(TestRecommenderFileUploading, self).setUp()

    def attempt_upload_file_and_verify_result(self, test_case, xblock_name=None):
        """
        Running on a test case, creating a temp file, uploading it by
        calling the corresponding ajax event, and verifying that upload
        happens or is rejected as expected.
        """
        if xblock_name is None:
            xblock_name = TestRecommender.XBLOCK_NAMES[0]
        f_handler = StringIO.StringIO(test_case['magic_number'].decode('hex'))
        f_handler.content_type = test_case['mimetypes']
        f_handler.name = 'file' + test_case['suffixes']
        url = self.get_handler_url('upload_screenshot', xblock_name)
        resp = self.client.post(url, {'file': f_handler})
        self.assertRegexpMatches(resp.content, test_case['response_regexp'])
        self.assert_request_status_code(200, self.course_url)

    @data(
        {
            'suffixes': '.csv',
            'magic_number': 'ffff',
            'mimetypes': 'text/plain',
            'response_regexp': 'FILE_TYPE_ERROR'
        },  # Upload file with wrong extension name
        {
            'suffixes': '.gif',
            'magic_number': '89504e470d0a1a0a',
            'mimetypes': 'image/gif',
            'response_regexp': 'FILE_TYPE_ERROR'
        },  # Upload file with wrong magic number
        {
            'suffixes': '.jpg',
            'magic_number': '89504e470d0a1a0a',
            'mimetypes': 'image/jpeg',
            'response_regexp': 'FILE_TYPE_ERROR'
        },  # Upload file with wrong magic number
        {
            'suffixes': '.png',
            'magic_number': '474946383761',
            'mimetypes': 'image/png',
            'response_regexp': 'FILE_TYPE_ERROR'
        },  # Upload file with wrong magic number
        {
            'suffixes': '.jpg',
            'magic_number': '474946383761',
            'mimetypes': 'image/jpeg',
            'response_regexp': 'FILE_TYPE_ERROR'
        },  # Upload file with wrong magic number
        {
            'suffixes': '.png',
            'magic_number': 'ffd8ffd9',
            'mimetypes': 'image/png',
            'response_regexp': 'FILE_TYPE_ERROR'
        },  # Upload file with wrong magic number
        {
            'suffixes': '.gif',
            'magic_number': 'ffd8ffd9',
            'mimetypes': 'image/gif',
            'response_regexp': 'FILE_TYPE_ERROR'
        }
    )
    def test_upload_screenshot_wrong_file_type(self, test_case):
        """
        Verify the file uploading fails correctly when file with wrong type
        (extension/magic number) is provided
        """
        self.enroll_staff(self.staff_user)
        # Upload file with wrong extension name or magic number
        self.attempt_upload_file_and_verify_result(test_case)
        self.assert_request_status_code(200, self.course_url)

    @data(
        {
            'suffixes': '.png',
            'magic_number': '89504e470d0a1a0a',
            'mimetypes': 'image/png',
            'response_regexp': 'fs://.*.png'
        },
        {
            'suffixes': '.gif',
            'magic_number': '474946383961',
            'mimetypes': 'image/gif',
            'response_regexp': 'fs://.*.gif'
        },
        {
            'suffixes': '.gif',
            'magic_number': '474946383761',
            'mimetypes': 'image/gif',
            'response_regexp': 'fs://.*.gif'
        },
        {
            'suffixes': '.jpg',
            'magic_number': 'ffd8ffd9',
            'mimetypes': 'image/jpeg',
            'response_regexp': 'fs://.*.jpeg'
        }
    )
    def test_upload_screenshot_correct_file_type(self, test_case):
        """
        Verify the file type checking in the file uploading method is
        successful.
        """
        self.enroll_staff(self.staff_user)
        # Upload file with correct extension name and magic number
        self.attempt_upload_file_and_verify_result(test_case)
        self.assert_request_status_code(200, self.course_url)
