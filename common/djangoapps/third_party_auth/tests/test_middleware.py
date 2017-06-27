"""
Test the session-flushing middleware
"""
import unittest

from django.conf import settings
from django.test import Client
from social_django.models import Partial


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestSessionFlushMiddleware(unittest.TestCase):
    """
    Ensure that if the pipeline is exited when it's been quarantined,
    the entire session is flushed.
    """
    def setUp(self):
        self.client = Client()
        self.fancy_variable = 13025
        self.token = 'pipeline_running'
        self.tpa_quarantined_modules = ('fake_quarantined_module',)

    def tearDown(self):
        Partial.objects.all().delete()

    def test_session_flush(self):
        """
        Test that a quarantined session is flushed when navigating elsewhere
        """
        session = self.client.session
        session['fancy_variable'] = self.fancy_variable
        session['partial_pipeline_token'] = self.token
        session['third_party_auth_quarantined_modules'] = self.tpa_quarantined_modules
        session.save()
        Partial.objects.create(token=session.get('partial_pipeline_token'))
        self.client.get('/')
        self.assertEqual(self.client.session.get('fancy_variable', None), None)

    def test_session_no_running_pipeline(self):
        """
        Test that a quarantined session without a running pipeline is not flushed
        """
        session = self.client.session
        session['fancy_variable'] = self.fancy_variable
        session['third_party_auth_quarantined_modules'] = self.tpa_quarantined_modules
        session.save()
        self.client.get('/')
        self.assertEqual(self.client.session.get('fancy_variable', None), self.fancy_variable)

    def test_session_no_quarantine(self):
        """
        Test that a session with a running pipeline but no quarantine is not flushed
        """
        session = self.client.session
        session['fancy_variable'] = self.fancy_variable
        session['partial_pipeline_token'] = self.token
        session.save()
        Partial.objects.create(token=session.get('partial_pipeline_token'))
        self.client.get('/')
        self.assertEqual(self.client.session.get('fancy_variable', None), self.fancy_variable)
