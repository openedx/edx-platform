"""
Monkey patch implementation of the following _expire_cache performance improvement:

https://github.com/django/django/commit/7628f87e2b1ab4b8a881f06c8973be4c368aaa3d

Remove once we upgrade to a version of django which includes this fix natively!
NOTE: This is on django's master branch but is NOT currently part of any django 1.8 or 1.9 release.
"""

from django.db.models.options import Options


def patch():
    """
    Monkey-patch the Options class.
    """
    def _expire_cache(self, forward=True, reverse=True):
        # pylint: disable=missing-docstring

        # This method is usually called by apps.cache_clear(), when the
        # registry is finalized, or when a new field is added.
        is_abstract = self.abstract
        attrs = self.__dict__
        fwd_prop = self.FORWARD_PROPERTIES
        rev_prop = self.REVERSE_PROPERTIES

        if forward:
            for cache_key in fwd_prop:
                if cache_key in attrs:
                    delattr(self, cache_key)
        if reverse and not is_abstract:
            for cache_key in rev_prop:
                if cache_key in attrs:
                    delattr(self, cache_key)
        self._get_fields_cache = {}  # pylint: disable=protected-access

    # # Patch constants as a set instead of a list.
    # Options.FORWARD_PROPERTIES = {'fields', 'many_to_many', 'concrete_fields',
    #                               'local_concrete_fields', '_forward_fields_map'}

    # Options.REVERSE_PROPERTIES = {'related_objects', 'fields_map', '_relation_tree'}

    # Patch the expire_cache method to utilize constant's new set data structure.
    Options._expire_cache = _expire_cache  # pylint: disable=protected-access
