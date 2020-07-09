"""Unit tests for the Paver server tasks."""


import os
from unittest import TestCase
from uuid import uuid4

from paver import tasks
from paver.easy import BuildFailure


class PaverTestCase(TestCase):
    """
    Base class for Paver test cases.
    """
    def setUp(self):
        super().setUp()

        # Show full length diffs upon test failure
        self.maxDiff = None  # pylint: disable=invalid-name

        # Create a mock Paver environment
        tasks.environment = MockEnvironment()

        # Don't run pre-reqs
        os.environ['NO_PREREQ_INSTALL'] = 'true'

    def tearDown(self):
        super().tearDown()
        tasks.environment = tasks.Environment()
        del os.environ['NO_PREREQ_INSTALL']

    @property
    def task_messages(self):
        """Returns the messages output by the Paver task."""
        return tasks.environment.messages

    @property
    def platform_root(self):
        """Returns the current platform's root directory."""
        return os.getcwd()

    def reset_task_messages(self):
        """Clear the recorded message"""
        tasks.environment.messages = []


class MockEnvironment(tasks.Environment):
    """
    Mock environment that collects information about Paver commands.
    """
    def __init__(self):
        super().__init__()
        self.dry_run = True
        self.messages = []

    def info(self, message, *args):
        """Capture any messages that have been recorded"""
        if args:
            output = message % args
        else:
            output = message
        if not output.startswith("--->"):
            self.messages.append(str(output))


def fail_on_eslint(*args, **kwargs):
    """
    For our tests, we need the call for diff-quality running eslint reports
    to fail, since that is what is going to fail when we pass in a
    percentage ("p") requirement.
    """
    if "eslint" in args[0]:
        raise BuildFailure('Subprocess return code: 1')
    else:
        if kwargs.get('capture', False):
            return uuid4().hex
        else:
            return


def fail_on_npm_install():
    """
    Used to simulate an error when executing "npm install"
    """
    return 1


def unexpected_fail_on_npm_install(*args, **kwargs):  # pylint: disable=unused-argument
    """
    For our tests, we need the call for diff-quality running pycodestyle reports to fail, since that is what
    is going to fail when we pass in a percentage ("p") requirement.
    """
    if ["npm", "install", "--verbose"] == args[0]:
        raise BuildFailure('Subprocess return code: 50')
    else:
        return
