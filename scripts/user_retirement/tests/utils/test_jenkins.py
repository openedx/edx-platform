"""
Tests for triggering a Jenkins job.
"""

import json
import re
import unittest
from itertools import islice
<<<<<<< HEAD
=======
from unittest.mock import Mock, call, mock_open, patch
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

import backoff
import ddt
import requests_mock
<<<<<<< HEAD
from mock import Mock, call, mock_open, patch
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

import scripts.user_retirement.utils.jenkins as jenkins
from scripts.user_retirement.utils.exception import BackendError

BASE_URL = u'https://test-jenkins'
USER_ID = u'foo'
USER_TOKEN = u'12345678901234567890123456789012'
JOB = u'test-job'
TOKEN = u'asdf'
BUILD_NUM = 456
JOBS_URL = u'{}/job/{}/'.format(BASE_URL, JOB)
JOB_URL = u'{}{}'.format(JOBS_URL, BUILD_NUM)
MOCK_BUILD = {u'number': BUILD_NUM, u'url': JOB_URL}
MOCK_JENKINS_DATA = {'jobs': [{'name': JOB, 'url': JOBS_URL, 'color': 'blue'}]}
MOCK_BUILDS_DATA = {
    'actions': [
        {'parameterDefinitions': [
            {'defaultParameterValue': {'value': '0'}, 'name': 'EXIT_CODE', 'type': 'StringParameterDefinition'}
        ]}
    ],
    'builds': [MOCK_BUILD],
    'lastBuild': MOCK_BUILD
}
MOCK_QUEUE_DATA = {
    'id': 123,
    'task': {'name': JOB, 'url': JOBS_URL},
    'executable': {'number': BUILD_NUM, 'url': JOB_URL}
}
MOCK_BUILD_DATA = {
    'actions': [{}],
    'fullDisplayName': 'foo',
    'number': BUILD_NUM,
    'result': 'SUCCESS',
    'url': JOB_URL,
}
MOCK_CRUMB_DATA = {
    'crumbRequestField': 'Jenkins-Crumb',
    'crumb': '1234567890'
}


class TestProperties(unittest.TestCase):
    """
    Test the Jenkins property-creating methods.
    """

    def test_properties_files(self):
        learners = [
            {
                'original_username': 'learnerA'
            },
            {
                'original_username': 'learnerB'
            },
        ]
        open_mocker = mock_open()
        with patch('scripts.user_retirement.utils.jenkins.open', open_mocker, create=True):
            jenkins._recreate_directory = Mock()  # pylint: disable=protected-access
            jenkins.export_learner_job_properties(learners, "tmpdir")
        jenkins._recreate_directory.assert_called_once()  # pylint: disable=protected-access
        self.assertIn(call('tmpdir/learner_retire_learnera', 'w'), open_mocker.call_args_list)
        self.assertIn(call('tmpdir/learner_retire_learnerb', 'w'), open_mocker.call_args_list)
        handle = open_mocker()
        self.assertIn(call('RETIREMENT_USERNAME=learnerA\n'), handle.write.call_args_list)
        self.assertIn(call('RETIREMENT_USERNAME=learnerB\n'), handle.write.call_args_list)


@ddt.ddt
class TestBackoff(unittest.TestCase):
    u"""
    Test of custom backoff code (wait time generator and max_tries)
    """

    @ddt.data(
        (2, 1, 1, 2, [1]),
        (2, 1, 2, 3, [1, 1]),
        (2, 1, 3, 3, [1, 2]),
        (2, 100, 90, 2, [90]),
        (2, 1, 90, 8, [1, 2, 4, 8, 16, 32, 27]),
        (3, 5, 1000, 7, [5, 15, 45, 135, 405, 395]),
        (2, 1, 3600, 13, [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 1553]),
    )
    @ddt.unpack
    def test_max_timeout(self, base, factor, timeout, expected_max_tries, expected_waits):
        # pylint: disable=protected-access
        wait_gen, max_tries = jenkins._backoff_timeout(timeout, base, factor)
        self.assertEqual(expected_max_tries, max_tries)

        # Use max_tries-1, because we only wait that many times
        waits = list(islice(wait_gen(), max_tries - 1))
        self.assertEqual(expected_waits, waits)

        self.assertEqual(timeout, sum(waits))

    def test_backoff_call(self):
        # pylint: disable=protected-access
        wait_gen, max_tries = jenkins._backoff_timeout(timeout=.36, base=2, factor=.0001)
        always_false = Mock(return_value=False)

        count_retries = backoff.on_predicate(
            wait_gen,
            max_tries=max_tries,
            on_backoff=print,
            jitter=None,
        )(always_false.__call__)

        count_retries()

        self.assertEqual(always_false.call_count, 13)


@ddt.ddt
class TestJenkinsAPI(unittest.TestCase):
    """
    Tests for interacting with the Jenkins API
    """

    @requests_mock.Mocker()
    def test_failure(self, mock):
        """
        Test the failure condition when triggering a jenkins job
        """
        # Mock all network interactions
        mock.get(
            re.compile(".*"),
            status_code=404,
        )
        with self.assertRaises(BackendError):
            jenkins.trigger_build(BASE_URL, USER_ID, USER_TOKEN, JOB, TOKEN, None, ())

    @ddt.data(
        (None, ()),
        ('my cause', ()),
        (None, ((u'FOO', u'bar'),)),
        (None, ((u'FOO', u'bar'), (u'BAZ', u'biz'))),
        ('my cause', ((u'FOO', u'bar'),)),
    )
    @ddt.unpack
    @requests_mock.Mocker()
    def test_success(self, cause, param, mock):
        u"""
        Test triggering a jenkins job
        """

        def text_callback(request, context):
            u""" What to return from the mock. """
            # This is the initial call that jenkinsapi uses to
            # establish connectivity to Jenkins
            # https://test-jenkins/api/python?tree=jobs[name,color,url]
            context.status_code = 200
            if request.url.startswith(u'https://test-jenkins/api/python'):
                return json.dumps(MOCK_JENKINS_DATA)
            elif request.url.startswith(u'https://test-jenkins/job/test-job/456'):
                return json.dumps(MOCK_BUILD_DATA)
            elif request.url.startswith(u'https://test-jenkins/job/test-job'):
                return json.dumps(MOCK_BUILDS_DATA)
            elif request.url.startswith(u'https://test-jenkins/queue/item/123/api/python'):
                return json.dumps(MOCK_QUEUE_DATA)
            elif request.url.startswith(u'https://test-jenkins/crumbIssuer/api/python'):
                return json.dumps(MOCK_CRUMB_DATA)
            else:
                # We should never get here, unless the jenkinsapi implementation changes.
                # This response will catch that condition.
                context.status_code = 500
                return None

        # Mock all network interactions
        mock.get(
            re.compile('.*'),
            text=text_callback
        )
        mock.post(
            '{}/job/test-job/buildWithParameters'.format(BASE_URL),
            status_code=201,  # Jenkins responds with a 201 Created on success
            headers={'location': '{}/queue/item/123'.format(BASE_URL)}
        )

        # Make the call to the Jenkins API
        result = jenkins.trigger_build(BASE_URL, USER_ID, USER_TOKEN, JOB, TOKEN, cause, param)
        self.assertEqual(result, 'SUCCESS')
