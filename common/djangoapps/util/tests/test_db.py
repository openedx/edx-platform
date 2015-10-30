"""Tests for util.db module."""

import ddt
import threading
import time
import unittest

from django.contrib.auth.models import User
from django.db import connection, IntegrityError
from django.db.transaction import atomic, TransactionManagementError
from django.test import TestCase, TransactionTestCase

from util.db import commit_on_success, generate_int_id, outer_atomic


@ddt.ddt
class TransactionManagersTestCase(TransactionTestCase):
    """
    Tests commit_on_success and outer_atomic.

    Note: This TestCase only works with MySQL.

    To test do: "./manage.py lms --settings=test_with_mysql test util.tests.test_db"
    """

    @ddt.data(
        (outer_atomic(), IntegrityError, None, True),
        (outer_atomic(read_committed=True), type(None), False, True),
        (commit_on_success(), IntegrityError, None, True),
        (commit_on_success(read_committed=True), type(None), False, True),
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

    def test_outer_atomic_nesting(self):
        """
        Test that outer_atomic raises an error if it is nested inside
        another atomic.
        """

        if connection.vendor != 'mysql':
            raise unittest.SkipTest('Only works on MySQL.')

        def do_nothing():
            """Just return."""
            return

        outer_atomic()(do_nothing)()

        with atomic():
            atomic()(do_nothing)()

        with outer_atomic():
            atomic()(do_nothing)()

        with self.assertRaisesRegexp(TransactionManagementError, 'Cannot be inside an atomic block.'):
            with atomic():
                outer_atomic()(do_nothing)()

        with self.assertRaisesRegexp(TransactionManagementError, 'Cannot be inside an atomic block.'):
            with outer_atomic():
                outer_atomic()(do_nothing)()

    def test_commit_on_success_nesting(self):
        """
        Test that commit_on_success raises an error if it is nested inside
        atomic or if the isolation level is changed when it is nested
        inside another commit_on_success.
        """
        # pylint: disable=not-callable

        if connection.vendor != 'mysql':
            raise unittest.SkipTest('Only works on MySQL.')

        def do_nothing():
            """Just return."""
            return

        commit_on_success(read_committed=True)(do_nothing)()

        with self.assertRaisesRegexp(TransactionManagementError, 'Cannot change isolation level when nested.'):
            with commit_on_success():
                commit_on_success(read_committed=True)(do_nothing)()

        with self.assertRaisesRegexp(TransactionManagementError, 'Cannot be inside an atomic block.'):
            with atomic():
                commit_on_success(read_committed=True)(do_nothing)()


@ddt.ddt
class GenerateIntIdTestCase(TestCase):
    """Tests for `generate_int_id`"""
    @ddt.data(10)
    def test_no_used_ids(self, times):
        """
        Verify that we get a random integer within the specified range
        when there are no used ids.
        """
        minimum = 1
        maximum = times
        for i in range(times):
            self.assertIn(generate_int_id(minimum, maximum), range(minimum, maximum + 1))

    @ddt.data(10)
    def test_used_ids(self, times):
        """
        Verify that we get a random integer within the specified range
        but not in a list of used ids.
        """
        minimum = 1
        maximum = times
        used_ids = {2, 4, 6, 8}
        for i in range(times):
            int_id = generate_int_id(minimum, maximum, used_ids)
            self.assertIn(int_id, list(set(range(minimum, maximum + 1)) - used_ids))
