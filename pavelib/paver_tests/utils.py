"""Unit tests for the Paver server tasks."""

import os
from unittest import TestCase

import paver.easy
from paver import tasks
from paver.easy import BuildFailure


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
            self.messages.append(unicode(output))


def fail_on_eslint(*args):
    """
    For our tests, we need the call for diff-quality running eslint reports
    to fail, since that is what is going to fail when we pass in a
    percentage ("p") requirement.
    """
    if "eslint" in args[0]:
        # Essentially mock diff-quality exiting with 1
        paver.easy.sh("exit 1")
    else:
        return


def fail_on_pylint(*args):
    """
    For our tests, we need the call for diff-quality running pylint reports
    to fail, since that is what is going to fail when we pass in a
    percentage ("p") requirement.
    """
    if "pylint" in args[0]:
        # Essentially mock diff-quality exiting with 1
        paver.easy.sh("exit 1")
    else:
        return


def fail_on_npm_install(*args, **kwargs):  # pylint: disable=unused-argument
    """
    For our tests, we need the call for diff-quality running pycodestyle reports to fail, since that is what
    is going to fail when we pass in a percentage ("p") requirement.
    """
    if ["npm", "install", "--verbose"] == args[0]:
        raise BuildFailure('Subprocess return code: 1')
    else:
        return


def unexpected_fail_on_npm_install(*args, **kwargs):  # pylint: disable=unused-argument
    """
    For our tests, we need the call for diff-quality running pycodestyle reports to fail, since that is what
    is going to fail when we pass in a percentage ("p") requirement.
    """
    if ["npm", "install", "--verbose"] == args[0]:
        raise BuildFailure('Subprocess return code: 50')
    else:
        return
