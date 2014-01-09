"""
Class for accessing LinkedIn's API.
"""
import json
import urllib2
import urlparse
import uuid

from django.conf import settings
from django.core.management.base import CommandError
import requests

from ...models import LinkedInToken

class LinkedInError(Exception):
    pass

class LinkedInAPI(object):
    """
    Encapsulates the LinkedIn API.
    """
    def __init__(self, command):
        config = getattr(settings, "LINKEDIN_API", None)
        if not config:
            raise CommandError("LINKEDIN_API is not configured")
        self.config = config

        try:
            self.token = LinkedInToken.objects.get()
        except LinkedInToken.DoesNotExist:
            self.token = None

        self.command = command
        self.state = str(uuid.uuid4())

    def http_error(self, error, message):
        """
        Handle an unexpected HTTP response.
        """
        stderr = self.command.stderr
        stderr.write("!!ERROR!!")
        stderr.write(error)
        stderr.write(error.read())
        raise CommandError(message)

    def authorization_url(self):
        """
        Synthesize a URL for beginning the authorization flow.
        """
        config = self.config
        return ("https://www.linkedin.com/uas/oauth2/authorization"
                "?response_type=code"
                "&client_id=%s&state=%s&redirect_uri=%s" % (
                config['CLIENT_ID'], self.state, config['REDIRECT_URI']))

    def get_authorization_code(self, redirect):
        """
        Extract the authorization code from the redirect URL at the end of
        the authorization flow.
        """
        query = urlparse.parse_qs(urlparse.urlparse(redirect).query)
        assert query['state'][0] == self.state, (query['state'][0], self.state)
        return query['code'][0]

    def access_token_url(self, code):
        """
        Construct URL for retreiving access token, given authorization code.
        """
        config = self.config
        return ("https://www.linkedin.com/uas/oauth2/accessToken"
                "?grant_type=authorization_code"
                "&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (
                    code, config['REDIRECT_URI'], config['CLIENT_ID'],
                    config['CLIENT_SECRET']))

    def call_json_api(self, url):
        """
        Make an HTTP call to the LinkedIn JSON API.
        """
        if settings.LINKEDIN_API.get('TEST_MODE'):
            raise LinkedInError(
                "Attempting to make real API call while in test mode - "
                "Mock LinkedInAPI.call_json_api instead."
            )
        try:
            request = urllib2.Request(url, headers={'x-li-format': 'json'})
            response = urllib2.urlopen(request, timeout=5).read()
            return json.loads(response)
        except urllib2.HTTPError, error:
            self.http_error(error, "Error calling LinkedIn API")

    def get_access_token(self, code):
        """
        Given an authorization code, get an access token.
        """
        response = self.call_json_api(self.access_token_url(code))
        access_token = response['access_token']
        try:
            token = LinkedInToken.objects.get()
            token.access_token = access_token
        except LinkedInToken.DoesNotExist:
            token = LinkedInToken(access_token=access_token)
        token.save()
        self.token = token

        return access_token

    def require_token(self):
        """
        Raise CommandError if user has not yet obtained an access token.
        """
        if self.token is None:
            raise CommandError(
                "You must log in to LinkedIn in order to use this script. "
                "Please use the 'login' command to log in to LinkedIn.")

    def batch_url(self, emails):
        """
        Construct URL for querying a batch of email addresses.
        """
        self.require_token()
        queries = ','.join(("email=" + email for email in emails))
        url = "https://api.linkedin.com/v1/people::(%s):(id)" % queries
        url += "?oauth2_access_token=%s" % self.token.access_token
        return url

    def batch(self, emails):
        """
        Get the LinkedIn status for a batch of emails.
        """
        emails = list(emails)  # realize generator since we traverse twice
        response = self.call_json_api(self.batch_url(emails))
        accounts = set(value['_key'][6:] for value in response['values'])
        return (email in accounts for email in emails)
