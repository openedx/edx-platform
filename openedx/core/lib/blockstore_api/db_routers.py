"""
Blockstore database router.

Blockstore started life as an IDA, but is now a Django app plugin within edx-platform.
This router exists to smooth blockstore's transition into edxapp.
"""
from django.conf import settings


class BlockstoreRouter:
    """
    A Database Router that uses the ``blockstore`` database, if it's configured in settings.
    """
    ROUTE_APP_LABELS = {'bundles'}
    DATABASE_NAME = 'blockstore'

    def _use_blockstore(self, model):
        """
        Return True if the given model should use the blockstore database.

        Ensures that a ``blockstore`` database is configured, and checks the ``model``'s app label.
        """
        return (self.DATABASE_NAME in settings.DATABASES) and (model._meta.app_label in self.ROUTE_APP_LABELS)

    def db_for_read(self, model, **hints):  # pylint: disable=unused-argument
        """
        Use the BlockstoreRouter.DATABASE_NAME when reading blockstore app tables.
        """
        if self._use_blockstore(model):
            return self.DATABASE_NAME
        return None

    def db_for_write(self, model, **hints):  # pylint: disable=unused-argument
        """
        Use the BlockstoreRouter.DATABASE_NAME when writing to blockstore app tables.
        """
        if self._use_blockstore(model):
            return self.DATABASE_NAME
        return None

    def allow_relation(self, obj1, obj2, **hints):  # pylint: disable=unused-argument
        """
        Allow relations if both objects are blockstore app models.
        """
        if self._use_blockstore(obj1) and self._use_blockstore(obj2):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # pylint: disable=unused-argument
        """
        Ensure the blockstore tables only appear in the blockstore database.
        """
        if model_name is not None:
            model = hints.get('model')
            if model is not None and self._use_blockstore(model):
                return db == self.DATABASE_NAME
        if db == self.DATABASE_NAME:
            return False

        return None
