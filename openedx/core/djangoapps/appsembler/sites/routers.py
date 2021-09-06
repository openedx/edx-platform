"""
Database routers for Tiers app.
"""


class TiersDbRouter(object):
    """
    A router to control all database operations on models in the
    tiers application.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read tiers models go to tiers db.
        """
        if model._meta.app_label == 'tiers':
            return 'tiers'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write tiers models go to tiers db.
        """
        if model._meta.app_label == 'tiers':
            return 'tiers'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the tiers app is involved.
        """
        if obj1._meta.app_label == 'tiers' or obj2._meta.app_label == 'tiers':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the tiers app only appears in the 'tiers'
        database.
        """
        if app_label == 'tiers':
            return db == 'tiers'
        return None
