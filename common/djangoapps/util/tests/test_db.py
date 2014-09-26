"""Tests for util.db module."""

import ddt
import threading
import time
import unittest

from django.contrib.auth.models import User
from django.db import connection, IntegrityError
from django.db.transaction import commit_on_success
from django.test import TransactionTestCase

from util.db import commit_on_success_with_read_committed


@ddt.ddt
class TransactionIsolationLevelsTestCase(TransactionTestCase):
    """
    Tests the effects of changing transaction isolation level to READ COMMITTED instead of REPEATABLE READ.

    Note: This TestCase only works with MySQL.

    To run it on devstack:
    1. Add TEST_RUNNER = 'django_nose.NoseTestSuiteRunner' to envs/devstack.py
    2. Run "./manage.py lms --settings=devstack test util.tests.test_db"
    """

    @ddt.data(
        (commit_on_success, IntegrityError, None, True),
        (commit_on_success_with_read_committed, type(None), False, True),
    )
    @ddt.unpack
    def test_concurrent_requests(self, transaction_decorator, exception_class, created_in_1, created_in_2):
        """
        Test that when isolation level is set to READ COMMITTED get_or_create()
        for the same row in concurrent requests does not raise an IntegrityError.
        """

        if connection.vendor != 'mysql':
            raise unittest.SkipTest('Only works on MySQL.')

        class RequestThread(threading.Thread):
            """ A thread which runs a dummy view."""
            def __init__(self, delay, **kwargs):
                super(RequestThread, self).__init__(**kwargs)
                self.delay = delay
                self.status = {}

            @transaction_decorator
            def run(self):
                """A dummy view."""
                try:
                    try:
                        User.objects.get(username='student', email='student@edx.org')
                    except User.DoesNotExist:
                        pass
                    else:
                        raise AssertionError('Did not raise User.DoesNotExist.')

                    if self.delay > 0:
                        time.sleep(self.delay)

                    __, created = User.objects.get_or_create(username='student', email='student@edx.org')
                except Exception as exception:  # pylint: disable=broad-except
                    self.status['exception'] = exception
                else:
                    self.status['created'] = created

        thread1 = RequestThread(delay=1)
        thread2 = RequestThread(delay=0)

        thread1.start()
        thread2.start()
        thread2.join()
        thread1.join()

        self.assertIsInstance(thread1.status.get('exception'), exception_class)
        self.assertEqual(thread1.status.get('created'), created_in_1)

        self.assertIsNone(thread2.status.get('exception'))
        self.assertEqual(thread2.status.get('created'), created_in_2)
