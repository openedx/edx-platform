from django import test
from django.core import cache


class TestCase(test.TransactionTestCase):

    def _pre_setup(self):
        cache.cache.clear()
        super(TestCase, self)._pre_setup()


class ReplicationRouter(object):
    """Router for simulating an environment with DB replication

    This router directs all DB reads to a completely different database than
    writes. This can be useful for simulating an environment where DB
    replication is delayed to identify potential race conditions.

    """
    def db_for_read(self, model, **hints):
        return 'readonly'

    def db_for_write(self, model, **hints):
        return 'default'
