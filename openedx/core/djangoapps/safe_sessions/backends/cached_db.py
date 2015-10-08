from django.contrib.sessions.backends.cached_db import SessionStore
from .base import SafeSessionMixin

class SessionStore(SafeSessionMixin, SessionStore):
    pass
