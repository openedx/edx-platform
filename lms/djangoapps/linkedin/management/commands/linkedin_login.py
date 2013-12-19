"""
Log into LinkedIn API.
"""
from django.core.management.base import BaseCommand

from . import LinkedinAPI


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
        api = LinkedinAPI()
        print "Let's log into your LinkedIn account."
        print "Start by visiting this url:"
        print api.authorization_url()
        print
        print "Within 30 seconds of logging in, enter the full URL of the "
        print "webpage you were redirected to: "
        redirect = raw_input()
        code = api.get_authorization_code(redirect)
        api.get_access_token(code)
