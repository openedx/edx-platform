"""
Middleware that checks user standing for the purpose of keeping users with
disabled accounts from accessing the site.
"""
import jwt

from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _

from student.models import UserStanding


class UserSessionSharingMiddleware(object):
    """
    Middleware to set jwt login token on sign in
    Used for session sharing with NodeBB community
    """
    def process_response(self, request, response):
        try:
            if request.user.is_authenticated():
                encoded_jwt = jwt.encode(
                    {
                        'id': request.user.id,
                        'username': request.user.username,
                        'email': request.user.email
                    },
                    'secret', algorithm='HS256'
                )
                response.set_cookie('token', encoded_jwt, domain=".philanthropyu.org")
            else:
                response.delete_cookie('token', domain=".philanthropyu.org")
        except AttributeError:
            pass
        return response


class UserStandingMiddleware(object):
    """
    Checks a user's standing on request. Returns a 403 if the user's
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
                msg = _(
                    'Your account has been disabled. If you believe '
                    'this was done in error, please contact us at '
                    '{support_email}'
                ).format(
                    support_email=u'<a href="mailto:{address}?subject={subject_line}">{address}</a>'.format(
                        address=settings.DEFAULT_FEEDBACK_EMAIL,
                        subject_line=_('Disabled Account'),
                    ),
                )
                return HttpResponseForbidden(msg)
