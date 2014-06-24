"""
Middleware class handling sneakpeek in cms, which should never be allowed
"""
from student.models import UserProfile
from django.contrib.auth import logout
from django.shortcuts import redirect

class SneakPeekLogoutMiddleware(object):
    """
    Middleware that logs out all sneakpeek users and then retries (redirects) the same URL
    """
    def process_request(self, request):
        """
        logs out all sneakpeek users and then retries (redirects) the same URL
        """
        #Do nothing with AnonymousUser
        if request.user.is_anonymous():
            return None

        #Do nothing with non-sneakpeek user
        if UserProfile.has_registered(request.user):
            return None

        logout(request)
        return redirect(request.get_full_path())

