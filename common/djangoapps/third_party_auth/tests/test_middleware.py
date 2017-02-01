"""
Test the session-flushing middleware
"""
import unittest

from django.conf import settings
from django.test import Client


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestSessionFlushMiddleware(unittest.TestCase):
    """
    Ensure that if the pipeline is exited when it's been quarantined,
    the entire session is flushed.
    """
    def test_session_flush(self):
        """
        Test that a quarantined session is flushed when navigating elsewhere
        """
        client = Client()
        session = client.session
        session['fancy_variable'] = 13025
        session['partial_pipeline'] = 'pipeline_running'
        session['third_party_auth_quarantined_modules'] = ('fake_quarantined_module',)
        session.save()
        client.get('/')
        self.assertEqual(client.session.get('fancy_variable', None), None)

    def test_session_no_running_pipeline(self):
        """
        Test that a quarantined session without a running pipeline is not flushed
        """
        client = Client()
        session = client.session
        session['fancy_variable'] = 13025
        session['third_party_auth_quarantined_modules'] = ('fake_quarantined_module',)
        session.save()
        client.get('/')
        self.assertEqual(client.session.get('fancy_variable', None), 13025)

    def test_session_no_quarantine(self):
        """
        Test that a session with a running pipeline but no quarantine is not flushed
        """
        client = Client()
        session = client.session
        session['fancy_variable'] = 13025
        session['partial_pipeline'] = 'pipeline_running'
        session.save()
        client.get('/')
        self.assertEqual(client.session.get('fancy_variable', None), 13025)
