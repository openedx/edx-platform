"""
Abstract base class for all User Tag Providers.
"""


class UserTagProvider(object):
    """
    Abstract base class for all User Tag Providers.
    """
    @classmethod
    def name(cls):
        """
        Unique identifier for the provider's class. It should be unique
        and not conflict with other providers. Consider using the
        same name that is used in the Provider Registry. For example,
        for Stevedore, it is specified in the setup.py file.

        Once the provider is in use, do not modify this name value
        without consideration of backward compatibility.
        """
        raise NotImplementedError

    @classmethod
    def tags(cls, context=None, **kwargs):
        """
        Returns a list of tags that are supported by this provider
        within the given context.

        Note: It is possible for multiple registered providers to
        support the same tags.

        Arguments:
            context(UserTagContext) - Optional
        Returns:
            list(UserTag) - Empty list if None.
        """
        raise NotImplementedError

    @classmethod
    def get_users_for_tag(cls, tag, context=None, **kwargs):
        """
        Returns an iterator of users that are associated with the
        given tag and context.

        Arguments:
            tag(UserTag)
            context(UserTagContext) - Optional
        Returns:
            list(User) - Empty list if None.
        """
        raise NotImplementedError

    @classmethod
    def get_tags_for_user(cls, user, context=None, **kwargs):
        """
        Returns a list of tags that are associated with the
        give user within the given context.

        Arguments:
            user(User)
            context(UserTagContext) - Optional
        Returns:
            list(UserTag) - Empty list if None.
        """
        raise NotImplementedError
