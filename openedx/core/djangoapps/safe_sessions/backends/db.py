from django.contrib.sessions.backends.db import SessionStore
from .base import SafeSessionMixin

class SessionStore(SafeSessionMixin, SessionStore):
    pass
