from django.contrib.sessions.backends.file import SessionStore
from .base import SafeSessionMixin

class SessionStore(SafeSessionMixin, SessionStore):
    pass
