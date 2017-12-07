"""
Tests for adaptive learning utilities.
"""

import json
import unittest

import ddt
import httpretty
from mock import DEFAULT, Mock, patch, call

from ..util.adaptive_learning import (
    AdaptiveLearningConfiguration, AdaptiveLearningAPIClient, AdaptiveLearningAPIMixin
)


ADAPTIVE_LEARNING_CONFIGURATION = {
    'url': 'https://dummy.com',
    'api_version': 'v42',
    'instance_id': 23,
    'access_token': 'this-is-not-a-test',
}

URLS = {
    'adaptive_learning_url': 'https://dummy.com/v42',
    'instance_url': 'https://dummy.com/v42/instances/23',
    'students_url': 'https://dummy.com/v42/instances/23/students',
    'events_url': 'https://dummy.com/v42/instances/23/events',
    'knowledge_node_students_url': 'https://dummy.com/v42/instances/23/knowledge_node_students',
    'pending_reviews_url': 'https://dummy.com/v42/instances/23/review_utils/fetch_pending_reviews_questions'
}


def make_mock_course():
    """
    Return mock course with attributes and methods that are relevant for testing adaptive learning features.
    """
    course = Mock()
    course.id.to_deprecated_string.return_value = 'abc'
    course.adaptive_learning_configuration = ADAPTIVE_LEARNING_CONFIGURATION
    return course


@ddt.ddt
class TestAdaptiveLearningConfiguration(unittest.TestCase):
    """
    Tests for class that stores configuration for interacting with external services
    that provide adaptive learning features.
    """

    def setUp(self):
        super(TestAdaptiveLearningConfiguration, self).setUp()
        self.attributes = {
            'foo': None,
            'bar': 42,
            'baz': 'This is not a test.',
        }
        self.adaptive_learning_configuration = AdaptiveLearningConfiguration(**self.attributes)

    def test_init(self):
        """
        Test that constructor correctly sets attributes.
        """
        self.assertEqual(self.adaptive_learning_configuration._configuration, self.attributes)  # pylint: disable=protected-access
        for attribute, value in self.attributes.items():
            self.assertTrue(hasattr(self.adaptive_learning_configuration, attribute))
            self.assertEqual(getattr(self.adaptive_learning_configuration, attribute), value)

    def test_str(self):
        """
        Test string representation of AdaptiveLearningConfiguration object.
        """
        self.assertEqual(
            str(self.adaptive_learning_configuration),
            str(self.adaptive_learning_configuration._configuration)  # pylint: disable=protected-access
        )

    @ddt.data(
        # Empty configuration
        ({}, False),
        # Configuration with *no* meaningful values
        (
            {
                'a': '',
                'b': '',
                'c': -1
            },
            False
        ),
        # Configuration with *some* meaningful values
        (
            {
                'a': 'meaningful-value',
                'b': '',
                'c': -1
            },
            False
        ),
        # Configuration with *all* meaningful values
        (
            {
                'a': 'meaningful-value',
                'b': 'another-meaningful-value',
                'c': 42
            },
            True
        ),
    )
    @ddt.unpack
    def test_is_meaningful(self, configuration, expected_result):
        """
        Test that `is_meaningful` returns appropriate results for configurations
        that are (not) meaningful.
        """
        self.assertEqual(AdaptiveLearningConfiguration.is_meaningful(configuration), expected_result)


class DummyClient(AdaptiveLearningAPIMixin):
    """
    Helper class for testing functionality provided by AdaptiveLearningAPIMixin.
    """

    def __init__(self):
        self._course = make_mock_course()


class AdaptiveLearningServiceMixin(object):
    """
    Mixin that provides utility methods for mocking an external adaptive learning service.
    """
    def _mock_request(self, method, url, status, body):
        """
        Register a mock response with HTTP status `status` and response body `body`
        for a request to `url` that uses `method`.
        """
        httpretty.register_uri(method, url, status=status, body=json.dumps(body))

    def _mock_get_request(self, url, body, status=200):
        """
        Register a mock response for a GET request.
        """
        self._mock_request(httpretty.GET, url, status, body)

    def _mock_post_request(self, url, body, status=200):
        """
        Register a mock response for a POST request.
        """
        self._mock_request(httpretty.POST, url, status, body)

    def register_student(self, url, student=None):
        """
        Register a mock response listing `student` if specified.
        """
        if student is None:
            body = []
        else:
            body = [student]
        self._mock_get_request(url, body)

    def register_knowledge_node_students(self, knowledge_node_students):
        """
        Register a mock response listing students that external service knows about.
        """
        self._mock_get_request(URLS['knowledge_node_students_url'], knowledge_node_students)


class AdaptiveLearningAPITestMixin(unittest.TestCase, AdaptiveLearningServiceMixin):
    """
    Base class for testing interactions with external adaptive learning service.
    """

    KNOWLEDGE_NODE_STUDENTS = [
        {
            'id': n,
            'knowledge_node_id': n,
            'knowledge_node_uid': 'knowledge-node-{n}'.format(n=n),
            'student_id': n,
            'student_uid': 'student-{n}'.format(n=n)
        } for n in range(5)
    ]


@httpretty.activate
class TestAdaptiveLearningAPIMixin(AdaptiveLearningAPITestMixin):
    """
    Tests for class that provides low-level methods for interacting with external adaptive learning service.

    Note that example data only lists properties of corresponding entities (students, events, etc.)
    that are relevant in the context of individual tests. The external service that provides
    adaptive learning features may return additional properties for different types of entities.
    """

    STUDENTS = [
        {
            'id': n,
            'uid': 'student-{n}'.format(n=n)
        } for n in range(5)
    ]

    def setUp(self):
        super(TestAdaptiveLearningAPIMixin, self).setUp()
        self.dummy_client = DummyClient()

    def test_adaptive_learning_configuration(self):
        """
        Test `adaptive_learning_configuration` property.
        """
        adaptive_learning_configuration = self.dummy_client.adaptive_learning_configuration
        self.assertIsInstance(adaptive_learning_configuration, AdaptiveLearningConfiguration)
        for attribute, value in ADAPTIVE_LEARNING_CONFIGURATION.items():
            self.assertTrue(hasattr(adaptive_learning_configuration, attribute))
            self.assertEqual(getattr(adaptive_learning_configuration, attribute), value)

    def test_urls(self):
        """
        Test that `*_url` properties return appropriate values.
        """
        for url_property, expected_value in URLS.items():
            self.assertTrue(hasattr(self.dummy_client, url_property))
            self.assertEqual(getattr(self.dummy_client, url_property), expected_value)

    def test_request_headers(self):
        """
        Test that `request_headers` property returns appropriate value.
        """
        expected_headers = {
            'Authorization': 'Token token=this-is-not-a-test'
        }
        self.assertEqual(self.dummy_client.request_headers, expected_headers)

    def test_get_knowledge_node_student_id(self):
        """
        Test the `get_knowledge_node_student_id` returns ID of a given 'knowledge node student' object.
        """
        knowledge_node_uid = 'knowledge-node-23'
        student_uid = 'student-23'
        knowledge_node_student = {
            'id': 42,
            'knowledge_node_id': 23,
            'knowledge_node_uid': knowledge_node_uid,
            'student_id': 23,
            'student_uid': student_uid
        }
        with patch.object(self.dummy_client, 'get_or_create_knowledge_node_student') as patched_get_or_create:
            patched_get_or_create.return_value = knowledge_node_student
            knowledge_node_student_id = self.dummy_client.get_knowledge_node_student_id(knowledge_node_uid, student_uid)
            self.assertEqual(knowledge_node_student_id, 42)
            patched_get_or_create.assert_called_once_with(knowledge_node_uid, student_uid)

    def test_get_or_create_knowledge_node_student(self):
        """
        Test that `get_or_create_knowledge_node_student` method creates 'knowledge node student' object
        on external service if it doesn't exist, and returns it.
        """
        student = self.STUDENTS[0]
        knowledge_node_uid = 'knowledge-node-42'
        student_uid = student['uid']
        expected_knowledge_node_student = {
            'id': 23,
            'knowledge_node_id': 23,
            'knowledge_node_uid': knowledge_node_uid,
            'student_id': 23,
            'student_uid': student_uid,
        }
        # 'Knowledge node student' object does not exist
        with patch.multiple(
            self.dummy_client,
            get_or_create_student=DEFAULT,
            get_knowledge_node_student=DEFAULT,
            create_knowledge_node_student=DEFAULT
        ) as patched_methods:
            patched_methods['get_or_create_student'].return_value = student
            patched_methods['get_knowledge_node_student'].return_value = None
            patched_methods['create_knowledge_node_student'].return_value = expected_knowledge_node_student
            knowledge_node_student = self.dummy_client.get_or_create_knowledge_node_student(
                knowledge_node_uid, student_uid
            )
            self.assertDictEqual(knowledge_node_student, expected_knowledge_node_student)
            patched_methods['get_or_create_student'].assert_called_once_with(student_uid)
            patched_methods['get_knowledge_node_student'].assert_called_once_with(knowledge_node_uid, student_uid)
            patched_methods['create_knowledge_node_student'].assert_called_once_with(knowledge_node_uid, student_uid)

        # 'Knowledge node student' object exists
        with patch.multiple(
            self.dummy_client,
            get_or_create_student=DEFAULT,
            get_knowledge_node_student=DEFAULT,
            create_knowledge_node_student=DEFAULT
        ) as patched_methods:
            patched_methods['get_or_create_student'].return_value = student
            patched_methods['get_knowledge_node_student'].return_value = expected_knowledge_node_student
            patched_methods['create_knowledge_node_student'].return_value = expected_knowledge_node_student
            knowledge_node_student = self.dummy_client.get_or_create_knowledge_node_student(
                knowledge_node_uid, student_uid
            )
            self.assertDictEqual(knowledge_node_student, expected_knowledge_node_student)
            patched_methods['get_or_create_student'].assert_called_once_with(student_uid)
            patched_methods['get_knowledge_node_student'].assert_called_once_with(knowledge_node_uid, student_uid)
            patched_methods['create_knowledge_node_student'].assert_not_called()

    def test_get_or_create_student(self):
        """
        Test that `get_or_create_student` method creates student on external service if it doesn't exist,
        and returns it.
        """
        student_uid = 'student-42'
        expected_student = {
            'id': 42,
            'uid': student_uid,
        }

        # Student does not exist
        with patch.object(self.dummy_client, 'get_student') as patched_get_student, \
                patch.object(self.dummy_client, 'create_student') as patched_create_student:
            patched_get_student.return_value = None
            patched_create_student.return_value = expected_student
            student = self.dummy_client.get_or_create_student(student_uid)
            self.assertDictEqual(student, expected_student)
            patched_get_student.assert_called_once_with(student_uid)
            patched_create_student.assert_called_once_with(student_uid)

        # Student exists
        with patch.object(self.dummy_client, 'get_student') as patched_get_student, \
                patch.object(self.dummy_client, 'create_student') as patched_create_student:
            patched_get_student.return_value = expected_student
            patched_create_student.return_value = expected_student
            student = self.dummy_client.get_or_create_student(student_uid)
            self.assertDictEqual(student, expected_student)
            patched_get_student.assert_called_once_with(student_uid)
            patched_create_student.assert_not_called()

    def test_get_student(self):
        """
        Test that `_get_student` method returns appropriate information
        if external service knows about a given student,
        and `None` otherwise.
        """
        # Unknown student
        url = self.dummy_client.generate_student_url('student-999')
        self.register_student(url)

        student = self.dummy_client.get_student('student-999')
        self.assertIsNone(student)

        # Known students
        for existing_student in self.STUDENTS:
            student_uid = existing_student['uid']
            url = self.dummy_client.generate_student_url(student_uid)
            self.register_student(url, existing_student)

            student = self.dummy_client.get_student(student_uid)
            self.assertDictEqual(student, existing_student)

    def test_create_student(self):
        """
        Test that `create_student` method creates student on external service, and returns it.
        """
        student_uid = 'student-42'
        expected_student = {
            'id': 42,
            'uid': student_uid,
        }
        response = Mock()
        response.content = json.dumps(expected_student)
        with patch('xmodule.util.adaptive_learning.requests') as patched_requests:
            patched_requests.post.return_value = response
            student = self.dummy_client.create_student(student_uid)
            self.assertDictEqual(student, expected_student)
            patched_requests.post.assert_called_once_with(
                self.dummy_client.students_url,
                headers=self.dummy_client.request_headers,
                data={'uid': student_uid}
            )

    def test_get_knowledge_node_student(self):
        """
        Test that `_get_knowledge_node_student` method returns appropriate information
        if 'knowledge node student' object exists on external service,
        and `None` otherwise.
        """
        self.register_knowledge_node_students(self.KNOWLEDGE_NODE_STUDENTS)

        # Unknown 'knowledge node student' object
        knowledge_node_student = self.dummy_client.get_knowledge_node_student('knowledge-node-999', 'student-999')
        self.assertIsNone(knowledge_node_student)

        # Known 'knowledge node student' object
        for expected_knowledge_node_student in self.KNOWLEDGE_NODE_STUDENTS:
            knowledge_node_student = self.dummy_client.get_knowledge_node_student(
                expected_knowledge_node_student['knowledge_node_uid'],
                expected_knowledge_node_student['student_uid']
            )
            self.assertDictEqual(knowledge_node_student, expected_knowledge_node_student)

    def test_get_knowledge_node_students(self):
        """
        Test that `get_knowledge_node_students` method returns list of all 'knowledge node student' objects
        that reference a specific user.
        """
        for expected_knowledge_node_student in self.KNOWLEDGE_NODE_STUDENTS:
            response = Mock()
            response.content = json.dumps([expected_knowledge_node_student])
            with patch('xmodule.util.adaptive_learning.requests') as patched_requests:
                patched_requests.get.return_value = response
                student_uid = expected_knowledge_node_student['student_uid']
                knowledge_node_students = self.dummy_client.get_knowledge_node_students(student_uid)
                knowledge_node_student = knowledge_node_students.pop(0)
                self.assertDictEqual(knowledge_node_student, expected_knowledge_node_student)
                patched_requests.get.assert_called_once_with(
                    self.dummy_client.knowledge_node_students_url,
                    headers=self.dummy_client.request_headers,
                    data={'student_id': student_uid, 'key_type': 'uid'}
                )

    def test_create_knowledge_node_student(self):
        """
        Test that `create_knowledge_node_student` method creates 'knowledge node student' object
        on external service, and returns it.
        """
        block_id = 'knowledge-node-42'
        student_uid = 'student-42'
        expected_knowledge_node_student = {
            'id': 23,
            'knowledge_node_id': 23,
            'knowledge_node_uid': block_id,
            'student_id': 23,
            'student_uid': student_uid,
        }
        response = Mock()
        response.content = json.dumps(expected_knowledge_node_student)
        with patch('xmodule.util.adaptive_learning.requests') as patched_requests:
            patched_requests.post.return_value = response
            knowledge_node_student = self.dummy_client.create_knowledge_node_student(block_id, student_uid)
            self.assertDictEqual(knowledge_node_student, expected_knowledge_node_student)
            patched_requests.post.assert_called_once_with(
                self.dummy_client.knowledge_node_students_url,
                headers=self.dummy_client.request_headers,
                data={'knowledge_node_uid': block_id, 'student_uid': student_uid}
            )

    def test_create_event(self):
        """
        Test that `create_event` method creates event of appropriate type on external service,
        and returns it.
        """
        knowledge_node_student_id = 42
        knowledge_node_uid = 'knowledge-node-42'
        student_uid = 'student-42'
        event_type = 'DummyEventType'
        expected_event = {
            'id': 23,
            'knowledge_node_student_id': knowledge_node_student_id,
            'type': event_type,
            'payload': None,
        }
        response = Mock()
        response.content = json.dumps(expected_event)
        with patch.object(self.dummy_client, 'get_knowledge_node_student_id') as patched_get_id, \
                patch('xmodule.util.adaptive_learning.requests') as patched_requests:
            patched_get_id.return_value = knowledge_node_student_id
            patched_requests.post.return_value = response
            event = self.dummy_client.create_event(knowledge_node_uid, student_uid, event_type)
            self.assertDictEqual(event, expected_event)
            patched_get_id.assert_called_once_with(knowledge_node_uid, student_uid)
            patched_requests.post.assert_called_once_with(
                self.dummy_client.events_url,
                headers=self.dummy_client.request_headers,
                data={'knowledge_node_student_id': knowledge_node_student_id, 'type': event_type}
            )

    def test_generate_student_url(self):
        """
        Test that `generate_student_url` returns appropriate URL.
        """
        student_uid = 'student-23'
        expected_student_url = self.dummy_client.students_url + '/' + student_uid
        student_url = self.dummy_client.generate_student_url(student_uid)
        self.assertEqual(student_url, expected_student_url)

    def test_generate_student_uid(self):
        """
        Test that `generate_student_uid` returns the same ID when called multiple times.
        """
        user_id = 23
        expected_student_uid = self.dummy_client.generate_student_uid(user_id)
        for dummy in range(5):
            student_uid = self.dummy_client.generate_student_uid(user_id)
            self.assertEqual(student_uid, expected_student_uid)


@ddt.ddt
@httpretty.activate
class TestAdaptiveLearningAPIClient(AdaptiveLearningAPITestMixin):
    """
    Tests for class that handles communication with external adaptive learning service.

    Note that example data only lists properties of corresponding entities (students, events, etc.)
    that are relevant in the context of individual tests. The external service that provides
    adaptive learning features may return additional properties for different types of entities.
    """

    PENDING_REVIEWS = [
        {
            'id': n,
            'student_uid': 'student-{n}'.format(n=n)
        } for n in range(5)
    ]

    def setUp(self):
        super(TestAdaptiveLearningAPIClient, self).setUp()
        mock_course = make_mock_course()
        self.api_client = AdaptiveLearningAPIClient(mock_course)

    def test_create_read_event(self):
        """
        Test that `create_read_event` method creates an event of type `EventRead` on external service,
        and returns it.
        """
        knowledge_node_uid = 'knowledge-node-42'
        user_id = 42
        student_uid = 'student-42'
        expected_event = {
            'id': 23,
            'knowledge_node_student_id': 42,
            'type': 'EventRead',
            'payload': None,
        }
        with patch.multiple(
            'xmodule.util.adaptive_learning.AdaptiveLearningAPIMixin',
            generate_student_uid=DEFAULT,
            create_event=DEFAULT
        ) as patched_methods:
            patched_methods['generate_student_uid'].return_value = student_uid
            patched_methods['create_event'].return_value = expected_event
            event = self.api_client.create_read_event(knowledge_node_uid, user_id)
            self.assertDictEqual(event, expected_event)
            patched_methods['generate_student_uid'].assert_called_once_with(user_id)
            patched_methods['create_event'].assert_called_once_with(knowledge_node_uid, student_uid, 'EventRead')

    @ddt.data('100', '0')
    def test_create_result_event(self, success):
        """
        Test that `create_result_event` method creates an event of type `EventResult` on external service,
        and returns it.
        """
        knowledge_node_uid = 'knowledge-node-42'
        user_id = 42
        student_uid = 'student-42'
        expected_event = {
            'id': 23,
            'knowledge_node_student_id': 42,
            'type': 'EventResult',
            'payload': success,
        }
        with patch.multiple(
            'xmodule.util.adaptive_learning.AdaptiveLearningAPIMixin',
            generate_student_uid=DEFAULT,
            create_event=DEFAULT
        ) as patched_methods:
            patched_methods['generate_student_uid'].return_value = student_uid
            patched_methods['create_event'].return_value = expected_event
            event = self.api_client.create_result_event(knowledge_node_uid, user_id, success)
            self.assertDictEqual(event, expected_event)
            patched_methods['generate_student_uid'].assert_called_once_with(user_id)
            patched_methods['create_event'].assert_called_once_with(
                knowledge_node_uid, student_uid, 'EventResult', payload=success
            )

    def test_create_knowledge_node_students(self):
        """
        Test that `create_knowledge_node_students` method creates 'knowledge node student' objects
        on external service, and returns them.
        """
        block_ids = [
            knowledge_node_student['knowledge_node_uid'] for knowledge_node_student in self.KNOWLEDGE_NODE_STUDENTS
        ]
        user_id = 42
        student_uid = 'student-42'
        with patch.multiple(
            'xmodule.util.adaptive_learning.AdaptiveLearningAPIMixin',
            generate_student_uid=DEFAULT,
            get_or_create_knowledge_node_student=DEFAULT
        ) as patched_methods:
            patched_methods['generate_student_uid'].return_value = student_uid
            patched_methods['get_or_create_knowledge_node_student'].side_effect = self.KNOWLEDGE_NODE_STUDENTS
            knowledge_node_students = self.api_client.create_knowledge_node_students(block_ids, user_id)
            self.assertEqual(knowledge_node_students, self.KNOWLEDGE_NODE_STUDENTS)
            patched_methods['generate_student_uid'].assert_called_once_with(user_id)
            patched_methods['get_or_create_knowledge_node_student'].assert_has_calls(
                [call(block_id, student_uid) for block_id in block_ids]
            )

    def test_get_pending_reviews(self):
        """
        Test that `get_pending_reviews` method fetches list of pending reviews
        for a given user from external service, and returns them.
        """
        user_id = 23
        student_uid = 'student-23'
        expected_pending_reviews = self.PENDING_REVIEWS[:1]
        response = Mock()
        response.content = json.dumps(expected_pending_reviews)
        with patch(
            'xmodule.util.adaptive_learning.AdaptiveLearningAPIMixin.generate_student_uid'
        ) as patched_generate_student_uid, \
                patch('xmodule.util.adaptive_learning.requests') as patched_requests:
            patched_generate_student_uid.return_value = student_uid
            patched_requests.get.return_value = response
            pending_reviews = self.api_client.get_pending_reviews(user_id)
            self.assertEqual(pending_reviews, expected_pending_reviews)
            patched_generate_student_uid.assert_called_once_with(user_id)
            patched_requests.get.assert_called_once_with(
                self.api_client.pending_reviews_url,
                headers=self.api_client.request_headers,
                data={'student_uid': student_uid, 'nested': True}
            )

    def test_get_pending_reviews_unknown_user(self):
        """
        Test that `get_pending_reviews` method returns empty list if external service
        does not know about current user.
        """
        user_id = 23
        student_uid = 'student-23'
        response = Mock()
        response.content = 'No Student Found'
        with patch(
            'xmodule.util.adaptive_learning.AdaptiveLearningAPIMixin.generate_student_uid'
        ) as patched_generate_student_uid, \
                patch('xmodule.util.adaptive_learning.requests') as patched_requests:
            patched_generate_student_uid.return_value = student_uid
            patched_requests.get.return_value = response
            pending_reviews = self.api_client.get_pending_reviews(user_id)
            self.assertEqual(pending_reviews, [])
            patched_generate_student_uid.assert_called_once_with(user_id)
            patched_requests.get.assert_called_once_with(
                self.api_client.pending_reviews_url,
                headers=self.api_client.request_headers,
                data={'student_uid': student_uid, 'nested': True}
            )
