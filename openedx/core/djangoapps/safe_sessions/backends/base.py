from django.contrib.auth import SESSION_KEY

class SessionUserChanged(Exception):
    def __init__(self, key, new, stored):
        self.key = key
        self.new = new
        self.stored = stored
        super(SessionUserChanged, self).__init__(
            "Cannot change session {} from user {} to user {}".format(
                self.key,
                self.stored,
                self.new,
            )
        )

class SafeSessionMixin(object):
    """
    Mixin to prevent a session from being changed from one userid to another.
    """
    def __init__(self, *args, **kwargs):
        self.__stored_user = None
        super(SafeSessionMixin, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        if (
            key == SESSION_KEY and
            self.__stored_user is not None and
            value != self.__stored_user
        ):
            raise SessionUserChanged(self.session_key, value, self.__stored_user)

        return super(SafeSessionMixin, self).__setitem__(key, value)

    def pop(self, key, *args):
        if key == SESSION_KEY and self.__stored_user is None:
            self.__stored_user = self._session.get(SESSION_KEY)

        return super(SafeSessionMixin, self).pop(key, *args)

    def setdefault(self, key, value):
        if (
            key == SESSION_KEY and
            self.__stored_user is not None and
            value != self.__stored_user
        ):
            raise SessionUserChanged(self.session_key, value, self.__stored_user)

        return super(SafeSessionMixin, self).setdefault(key, value)

    def update(self, dict_):
        if (
            SESSION_KEY in dict_ and
            self.__stored_user is not None and
            dict_[SESSION_KEY] != self.__stored_user
        ):
            raise SessionUserChanged(self.session_key, dict_[SESSION_KEY], self.__stored_user)

        return super(SafeSessionMixin, self).save(must_create=must_create)

    def clear(self):
        super(SafeSessionMixin, self).clear()
        self.__stored_user = None

    def save(self, must_create=False):
        """
        Saves the session data. If 'must_create' is True, a new session object
        is created (otherwise a CreateError exception is raised). Otherwise,
        save() can update an existing object with the same key.
        """
        if (
            SESSION_KEY in self._session and
            self.__stored_user is not None and
            self._session[SESSION_KEY] != self.__stored_user
        ):
            raise SessionUserChanged(self.session_key, self._session[SESSION_KEY], self.__stored_user)

        return super(SafeSessionMixin, self).save(must_create=must_create)

    def load(self):
        """
        Loads the session data and returns a dictionary.
        """
        session_data = super(SafeSessionMixin, self).load()
        self.__stored_user = session_data.get(SESSION_KEY)
        return session_data

