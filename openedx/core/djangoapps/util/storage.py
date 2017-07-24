"""
Django storage utilities.
"""
from django.core.files.storage import get_storage_class
from django.utils.lru_cache import lru_cache


@lru_cache()
def get_storage(storage_class=None, **kwargs):
    """
    Returns a storage instance with the given class name and kwargs. If the
    class name is not given, an instance of the default storage is returned.
    Instances are cached so that if this function is called multiple times
    with the same arguments, the same instance is returned. This is useful if
    the storage implementation makes http requests when instantiated, for
    example.
    """
    return get_storage_class(storage_class)(**kwargs)
