"""
Django Model baseclass for database-backed configuration.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.cache import get_cache, InvalidCacheBackendError

try:
    cache = get_cache('configuration')  # pylint: disable=invalid-name
except InvalidCacheBackendError:
    from django.core.cache import cache


class ConfigurationModel(models.Model):
    """
    Abstract base class for model-based configuration

    Properties:
        cache_timeout (int): The number of seconds that this configuration
            should be cached
    """

    class Meta(object):  # pylint: disable=missing-docstring
        abstract = True

    # The number of seconds
    cache_timeout = 600

    change_date = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, editable=False, null=True, on_delete=models.PROTECT)
    enabled = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Clear the cached value when saving a new configuration entry
        """
        super(ConfigurationModel, self).save(*args, **kwargs)
        cache.delete(self.cache_key_name())

    @classmethod
    def cache_key_name(cls):
        """Return the name of the key to use to cache the current configuration"""
        return 'configuration/{}/current'.format(cls.__name__)

    @classmethod
    def current(cls):
        """
        Return the active configuration entry, either from cache,
        from the database, or by creating a new empty entry (which is not
        persisted).
        """
        cached = cache.get(cls.cache_key_name())
        if cached is not None:
            return cached

        try:
            current = cls.objects.order_by('-change_date')[0]
        except IndexError:
            current = cls()

        cache.set(cls.cache_key_name(), current, cls.cache_timeout)
        return current
