"""
Caching instances via ``related_name``
--------------------------------------

``cache_relation`` adds utility methods to a model to obtain ``related_name``
instances via the cache.

Usage
~~~~~

::

    from django.db import models
    from django.contrib.auth.models import User

    class Foo(models.Model):
        user = models.OneToOneField(
            User,
            primary_key=True,
            related_name='foo',
        )

        name = models.CharField(max_length=20)

    cache_relation(User.foo)

::

    >>> user = User.objects.get(pk=1)
    >>> user.foo_cache # Cache miss - hits the database
    <Foo: >
    >>> user = User.objects.get(pk=1)
    >>> user.foo_cache # Cache hit - no database access
    <Foo: >
    >>> user = User.objects.get(pk=2)
    >>> user.foo # Regular lookup - hits the database
    <Foo: >
    >>> user.foo_cache # Special-case: Will not hit cache or database.
    <Foo: >

Accessing ``user_instance.foo_cache`` (note the "_cache" suffix) will now
obtain the related ``Foo`` instance via the cache. Accessing the original
``user_instance.foo`` attribute will perform the lookup as normal.

Invalidation
~~~~~~~~~~~~

Upon saving (or deleting) the instance, the cache is cleared. For example::

    >>> user = User.objects.get(pk=1)
    >>> foo = user.foo_cache # (Assume cache hit from previous session)
    >>> foo.name = "New name"
    >>> foo.save() # Cache is cleared on save
    >>> user = User.objects.get(pk=1)
    >>> user.foo_cache # Cache miss.
    <Foo: >

Manual invalidation may also be performed using the following methods::

    >>> user_instance.foo_cache_clear()
    >>> User.foo_cache_clear_fk(user_instance_pk)

Manual invalidation is required if you use ``.update()`` methods which the
``post_save`` and ``post_delete`` hooks cannot intercept.

Support
~~~~~~~

``cache_relation`` currently only works with ``OneToOneField`` fields. Support
for regular ``ForeignKey`` fields is planned.
"""

from django.db.models.signals import post_save, post_delete

from .core import get_instance, delete_instance


def cache_relation(descriptor, timeout=None):
    rel = descriptor.related
    related_name = '%s_cache' % rel.field.related_query_name()

    @property
    def get(self):
        # Always use the cached "real" instance if available
        try:
            return getattr(self, descriptor.cache_name)
        except AttributeError:
            pass

        # Lookup cached instance
        try:
            return getattr(self, '_%s_cache' % related_name)
        except AttributeError:
            pass

#        import logging
#        log = logging.getLogger("tracking")
#        log.info( "DEBUG: "+str(str(rel.model)+"/"+str(self.pk) ))

        instance = get_instance(rel.model, self.pk, timeout)

        setattr(self, '_%s_cache' % related_name, instance)

        return instance
    setattr(rel.parent_model, related_name, get)

    # Clearing cache

    def clear(self):
        delete_instance(rel.model, self)

    @classmethod
    def clear_pk(cls, *instances_or_pk):
        delete_instance(rel.model, *instances_or_pk)

    def clear_cache(sender, instance, *args, **kwargs):
        delete_instance(rel.model, instance)

    setattr(rel.parent_model, '%s_clear' % related_name, clear)
    setattr(rel.parent_model, '%s_clear_pk' % related_name, clear_pk)

    post_save.connect(clear_cache, sender=rel.model, weak=False)
    post_delete.connect(clear_cache, sender=rel.model, weak=False)
