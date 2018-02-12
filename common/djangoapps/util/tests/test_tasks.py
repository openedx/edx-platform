"""
Tests for tasks.py
"""

from django.contrib.sessions.backends.db import SessionStore as DatabaseSession
from django.contrib.sessions.models import Session
from django.test import TestCase, override_settings
from util.tasks import run_clearsessions


class ClearSessionsTaskTest(TestCase):
    """
    Tests for the run_clearsessions task.
    """

    @override_settings(SESSION_ENGINE='django.contrib.sessions.backends.db')
    def test_run_clearsessions(self):
        """
        Test the task that clears expired sessions (using Django's clearsession command).
        """
        # Create not expired session
        self.client.get('/')
        session = self.client.session
        session.save()

        self.assertEqual(1, Session.objects.count())

        # Call the task. Session won't be cleared because it's not expired
        run_clearsessions.apply_async()
        self.assertEqual(1, Session.objects.count())

        # Create expired session
        other_session = DatabaseSession()
        other_session.set_expiry(-3600)
        other_session.save()

        self.assertEqual(2, Session.objects.count())

        # This time, the expired session will be deleted
        run_clearsessions.apply_async()
        self.assertEqual(1, Session.objects.count())

        return
