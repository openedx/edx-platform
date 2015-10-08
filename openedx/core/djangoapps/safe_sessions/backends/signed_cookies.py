from django.contrib.sessions.backends.signed_cookies import SessionStore
from .base import SafeSessionMixin

class SessionStore(SafeSessionMixin, SessionStore):
    pass
