"""
Middleware that checks user standing for the purpose of keeping users with
disabled accounts from accessing the site.
"""
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.conf import settings
from student.models import UserStanding

# Generate UserStanding cache on startup
UserStanding.generate_cache()

class UserStandingMiddleware(object):
    """
    Checks a user's standing on request. Returns a 403 if the user's
    status is 'disabled'.
    """
    def process_request(self, request):
        user = request.user
        if user.id in cache.get('disabled_account_ids', []):
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
            return HttpResponseForbidden(msg)
