"""Signal receivers for appsembler_eventtracking app."""


from tahoeusermetadata import tahoe_userprofile_metadata_cache


def invalidate_user_metadata_cache_entry(sender, **kwargs):
    """Invalidate cache entry for modified or deleted UserProfile in UserProrifle Metadata cache."""
    instance = kwargs['instance']
    tahoe_userprofile_metadata_cache.invalidate(instance)
