import json
from django.test.client import Client
from django.test import TestCase
from mock import patch, Mock
from override_settings import override_settings
from django.conf import settings

def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)

class AuthTestCase(TestCase):
    """Check that various permissions-related things work"""

    def test_index(self):
        """Make sure the main page loads."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_signup_load(self):
        """Make sure the signup page loads."""
        resp = self.client.get('/signup')
        self.assertEqual(resp.status_code, 200)


    def test_create_account(self):

        # No post data -- should fail
        resp = self.client.post('/create_account', {})
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], False)
        
        # Should work
        resp = self.client.post('/create_account', {
            'username': 'user',
            'email': 'a@b.com',
            'password': 'xyz',
            'location' : 'home',
            'language' : 'Franglish',
            'name' : 'Fred Weasley',
            'terms_of_service' : 'true',
            'honor_code' : 'true'})
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['success'], True)
        
        
