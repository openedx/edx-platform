"""Signal receivers for appsembler_eventtracking app."""


from .tahoeusermetadata import userprofile_metadata_cache


def invalidate_user_metadata_cache_entry(sender, instance, **kwargs):
    """Invalidate cache entry for modified or deleted UserProfile in UserProrifle Metadata cache."""
    userprofile_metadata_cache.invalidate(instance)
