"""
Middleware that checks user standing for the purpose of keeping users with
disabled accounts from accessing the site.
"""
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from student.models import UserStanding
import student.views

class UserStandingMiddleware(object):
    """
    Checks a user's standing on request. Returns an error page if the user's
    status is 'disabled'.
    """
    def process_request(self, request):
        user = request.user
        try:
            user_account = UserStanding.objects.get(user=user.id)
            # because user is a unique field in UserStanding, there will either be
            # one or zero user_accounts associated with a UserStanding
        except UserStanding.DoesNotExist:
            pass
        else:
            if user_account.account_status == UserStanding.ACCOUNT_DISABLED:
                # logout
                student.views.logout_user(request)
                return redirect(reverse('disabled_account'))
