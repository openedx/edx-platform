"""
Middleware that checks user standing for the purpose of keeping users with
disabled accounts from accessing the site.
"""
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.conf import settings
from edxmako.shortcuts import render_to_response
from student.models import UserStanding
import student.views

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
                            '{link_start}{support_email}{link_end}'
                        ).format(
                            support_email=settings.DEFAULT_FEEDBACK_EMAIL,
                            link_start=u'<a href="mailto:{address}?subject={subject_line}">'.format(
                                address=settings.DEFAULT_FEEDBACK_EMAIL,
                                subject_line=_('Disabled Account'),
                            ),
                            link_end=u'</a>'
                        )
                # logout
                student.views.logout_user(request)
                context = {'message': msg}
                return render_to_response('disabled_account.html', context)
