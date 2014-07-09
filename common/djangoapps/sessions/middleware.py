"""
Session Middlewares.
"""

import logging
import types

from django.contrib.sessions.middleware import SessionMiddleware as DjangoSessionMiddleware
from django.conf import settings

AUDIT_LOG = logging.getLogger(__name__)


def patch_session_object(session):
    """Patch session object to do some additional logging."""

    original_create = session.create
    original_delete = session.delete

    def create(self):
        """Logs and then calls original create method."""
        original_create()
        AUDIT_LOG.info("SessionEngine:Created SessionKey:{0} SessionExpiry:{1}".format(
            self.session_key, self.get_expiry_date())
        )

    def delete(self, session_key=None):
        """Logs and then calls original delete method."""
        original_delete(session_key)

        if session_key is None:
            session_key = self.session_key
        AUDIT_LOG.info("SessionEngine:Deleted SessionKey:{0} SessionExpiry:{1}".format(
            self.session_key, self.get_expiry_date())
        )

    session.create = types.MethodType(create, session)
    session.delete = types.MethodType(delete, session)


class SessionMiddleware(DjangoSessionMiddleware):
    """
    A middleware which inherits from django.contrib.sessions.middleware.SessionMiddleware.
    Currently it adds additional logging to session creation and deletion.
    """

    def process_request(self, request):
        """
        Call Django's SessionMiddleware.process_request() and then patch the request.session object to do some logging.
        """
        super(SessionMiddleware, self).process_request(request)

        if settings.FEATURES.get("ENABLE_VERBOSE_LOGGING_FOR_SESSIONS", False):
            patch_session_object(request.session)
