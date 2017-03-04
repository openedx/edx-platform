"""
User Tag Service implementation.
"""
from itertools import chain
from .provider_registry import UserTagProviderRegistry


class UserTagService(object):
    """
    User Tag Service.
    """
    # TODO (future) Add optional 'feature' parameter to support feature-specific list of tags.
    # TODO group by type
    @classmethod
    def tags(cls, context=None, **kwargs):
        """
        Returns a list of tags that are supported in the system
        for the given context.

        Arguments:
            context(UserTagContext) - Optional
        Returns:
            set(UserTag) - Empty set if None.
        """
        return set(chain(*[
            provider.tags(context, **kwargs)
            for provider in UserTagProviderRegistry.get_registered_providers()
        ]))

    @classmethod
    def get_users_for_tag(cls, tag, context=None, **kwargs):
        """
        Returns an iterator of users that are associated with the
        given tag and context across the system.

        Arguments:
            tag(UserTag)
            context(UserTagContext) - Optional
        Returns:
            set(User) - Empty set if None.
        """
        return set(chain(*[
            provider.get_users_for_tag(tag, context, **kwargs)
            for provider in UserTagProviderRegistry.get_registered_providers()
        ]))

    @classmethod
    def get_tags_for_user(cls, user, context=None, **kwargs):
        """
        Returns a list of tags that are associated with the
        give user within the given context across the system.

        Arguments:
            user(User)
            context(UserTagContext) - Optional
        Returns:
            list(UserTag) - Empty list if None.
        """
        return set(chain(*[
            provider.get_tags_for_user(user, context, **kwargs)
            for provider in UserTagProviderRegistry.get_registered_providers()
        ]))
