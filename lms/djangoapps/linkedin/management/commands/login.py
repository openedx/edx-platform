"""
Log into LinkedIn API.
"""
import json
import urllib2
import urlparse
import uuid

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...models import LinkedInTokens


class Command(BaseCommand):
    """
    Can take a sysadmin through steps to log into LinkedIn API so that the
    findusers script can work.
    """
    args = ''
    help = ('Takes a user through the steps to log in to LinkedIn as a user '
            'with API access in order to gain an access token for use by the '
            'findusers script.')

    def handle(self, *args, **options):
        """
        """
        api = getattr(settings, "LINKEDIN_API", None)
        if not api:
            raise CommandError("LINKEDIN_API is not configured")

        state = str(uuid.uuid4())
        url= ("https://www.linkedin.com/uas/oauth2/authorization"
              "?response_type=code"
              "&client_id=%s&state=%s&redirect_uri=%s" % (
              api['CLIENT_ID'], state, api['REDIRECT_URI']))

        print "Let's log into your LinkedIn account."
        print "Start by visiting this url:"
        print url
        print
        print "Within 30 seconds of logging in, enter the full URL of the "
        print "webpage you were redirected to: "
        redirect = raw_input()
        query = urlparse.parse_qs(urlparse.urlparse(redirect).query)
        assert query['state'][0] == state, (query['state'][0], state)
        code = query['code'][0]

        url = ("https://www.linkedin.com/uas/oauth2/accessToken"
               "?grant_type=authorization_code"
               "&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (
                   code, api['REDIRECT_URI'], api['CLIENT_ID'],
                   api['CLIENT_SECRET']))

        try:
            response = urllib2.urlopen(url).read()
        except urllib2.HTTPError, e:
            print "!!ERROR!!"
            print e
            print e.read()
            raise CommandError("Unable to retrieve access token")

        access_token =  json.loads(response)['access_token']
        try:
            tokens = LinkedInTokens.objects.get()
            tokens.access_token = access_token
            tokens.authorization_code = code
        except LinkedInTokens.DoesNotExist:
            tokens = LinkedInTokens(
                access_token=access_token,
                authorization_code=code)
        tokens.save()
