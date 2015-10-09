from django.contrib.sessions.backends.cache import SessionStore
from .base import SafeSessionMixin

class SessionStore(SafeSessionMixin, SessionStore):
    pass
