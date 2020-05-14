"""
Edly Organization Access Middleware.
"""
from logging import getLogger
from django.http import Http404

from openedx.features.edly.utils import user_has_edly_organization_access

logger = getLogger(__name__)


class EdlyOrganizationAccessMiddleware(object):
    """
    Django middleware to validate edly user organization access based on request.
    """

    def process_request(self, request):
        """
        Validate logged in user's access based on request site and its linked edly sub organization.
        """

        user_is_authenticated = request.user.is_authenticated
        user_is_superuser = request.user.is_superuser
        if user_is_authenticated and not user_is_superuser and not user_has_edly_organization_access(request):
            logger.exception('Edly user %s has no access for site %s.' % (request.user.email, request.site))
            raise Http404()
