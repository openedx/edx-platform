"""
Caching model instances
-----------------------

``cache_model`` adds utility methods to a model to obtain ``ForeignKey``
instances via the cache.

Usage
~~~~~

::

    from django.db import models
    from django.contrib.auth.models import User

    class Foo(models.Model):
        name = models.CharField(length=20)

    cache_model(Foo)

::

    >>> a = Foo.objects.create(name='a')
    >>> a
    <Foo: >
    >>> Foo.get_cached(a.pk) # Cache miss
    <Foo: >
    >>> a = Foo.get_cached(a.pk) # Cache hit
    >>> a.name
    u'a'

Instances returned from ``get_cached`` are real model instances::

    >>> a = Foo.get_cached(a.pk) # Cache hit
    >>> type(a)
    <class '__main__.models.A'>
    >>> a.pk
    1L

Invalidation
~~~~~~~~~~~~

Invalidation is performed automatically upon saving or deleting a ``Foo``
instance::

    >>> a = Foo.objects.create(name='a')
    >>> a.name = 'b'
    >>> a.save()
    >>> a = Foo.get_cached(a.pk)
    >>> a.name
    u'b'
    >>> a.delete()
    >>> a = Foo.get_cached(a.pk)
    ... Foo.DoesNotExist
"""


from django.db.models.signals import post_delete, post_save

from .core import delete_instance, get_instance


def cache_model(model, timeout=None):
    """
    Adds utility methods to the given model to obtain
    ``ForeignKey`` instances via the cache.
    """
    if hasattr(model, 'get_cached'):
        # Already patched
        return

    def clear_cache(sender, instance, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Clears the cache for the given instance.
        """
        delete_instance(sender, instance)

    post_save.connect(clear_cache, sender=model, weak=False)
    post_delete.connect(clear_cache, sender=model, weak=False)

    @classmethod
    def get(cls, pk, using=None):  # pylint: disable=invalid-name
        """
        Returns the model for the given primary key (pk).
        """
        if pk is None:
            return None
        return get_instance(cls, pk, timeout, using)

    model.get_cached = get
