import hashlib
import json
import urllib2
import urlparse
import uuid

from django.conf import settings
from django.core.management.base import CommandError

from ...models import LinkedInToken

class LinkedinAPI(object):
    """
    Encapsulates the LinkedIn API.
    """
    def __init__(self):
        config = getattr(settings, "LINKEDIN_API", None)
        if not config:
            raise CommandError("LINKEDIN_API is not configured")
        self.config = config

        try:
            self.tokens = LinkedInToken.objects.get()
        except LinkedInToken.DoesNotExist:
            self.tokens = None

        self.state = str(uuid.uuid4())

    def http_error(error, message):
        print "!!ERROR!!"
        print error
        print error.read()
        raise CommandError(message)

    def authorization_url(self):
        config = self.config
        return ("https://www.linkedin.com/uas/oauth2/authorization"
                "?response_type=code"
                "&client_id=%s&state=%s&redirect_uri=%s" % (
                config['CLIENT_ID'], self.state, config['REDIRECT_URI']))

    def get_authorization_code(self, redirect):
        query = urlparse.parse_qs(urlparse.urlparse(redirect).query)
        assert query['state'][0] == self.state, (query['state'][0], self.state)
        return query['code'][0]

    def get_access_token(self, code):
        config = self.config
        url = ("https://www.linkedin.com/uas/oauth2/accessToken"
               "?grant_type=authorization_code"
               "&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (
                   code, config['REDIRECT_URI'], config['CLIENT_ID'],
                   config['CLIENT_SECRET']))

        try:
            response = urllib2.urlopen(url).read()
        except urllib2.HTTPError, error:
            self.http_error(error, "Unable to retrieve access token")

        access_token = json.loads(response)['access_token']
        try:
            tokens = LinkedInToken.objects.get()
            tokens.access_token = access_token
            tokens.authorization_code = code
        except LinkedInToken.DoesNotExist:
            tokens = LinkedInToken(access_token=access_token)
        tokens.save()
        self.tokens = tokens

        return access_token

    def batch(self, emails):
        """
        Get the LinkedIn status for a batch of emails.
        """
        if self.tokens is None:
            raise CommandError(
                "You must log in to LinkedIn in order to use this script. "
                "Please use the 'login' command to log in to LinkedIn.")

        def md5(email):
            "Compute md5 hash for an email address."
            hash = hashlib.md5()
            hash.update(email)
            return hash.hexdigest()

        hashes = ','.join(("email-hash=" + md5(email) for email in emails))
        url = "https://api.linkedin.com/v1/people::(%s):(id)" % hashes
        url += "?oauth2_access_token=%s" % self.tokens.access_token
        try:
            response = urllib2.urlopen(url).read()
        except urllib2.HTTPError, error:
            print "!!ERROR!!"
            print error
            print error.read()

            raise CommandError("Unable to access People API")

        return (True for email in emails)
