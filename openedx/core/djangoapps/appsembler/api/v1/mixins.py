"""
Mixins for API views
"""

from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from openedx.core.djangoapps.appsembler.api.permissions import IsSiteAdminUser


class TahoeAuthMixin(object):
    """Provides a common authorization base for the Tahoe multi-site aware API views
    """
    authentication_classes = (
        SessionAuthentication,
        TokenAuthentication,
    )
    permission_classes = (
        IsAuthenticated,
        IsSiteAdminUser,
    )
