"""Unit tests for the Paver server tasks."""

import os
from paver import tasks
from unittest import TestCase


class PaverTestCase(TestCase):
    """
    Base class for Paver test cases.
    """
    def setUp(self):
        super(PaverTestCase, self).setUp()

        # Show full length diffs upon test failure
        self.maxDiff = None  # pylint: disable=invalid-name

        # Create a mock Paver environment
        tasks.environment = MockEnvironment()

        # Don't run pre-reqs
        os.environ['NO_PREREQ_INSTALL'] = 'true'

    def tearDown(self):
        super(PaverTestCase, self).tearDown()
        tasks.environment = tasks.Environment()
        del os.environ['NO_PREREQ_INSTALL']

    @property
    def task_messages(self):
        """Returns the messages output by the Paver task."""
        return tasks.environment.messages

    def reset_task_messages(self):
        """Clear the recorded message"""
        tasks.environment.messages = []


class MockEnvironment(tasks.Environment):
    """
    Mock environment that collects information about Paver commands.
    """
    def __init__(self):
        super(MockEnvironment, self).__init__()
        self.dry_run = True
        self.messages = []

    def info(self, message, *args):
        """Capture any messages that have been recorded"""
        if args:
            output = message % args
        else:
            output = message
        if not output.startswith("--->"):
            self.messages.append(output)
