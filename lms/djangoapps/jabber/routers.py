class JabberRouter(object):
    """
    A router to control all database operations on models in the
    Jabber application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read Jabber models go to the Jabber DB.
        """
        if model._meta.app_label == 'jabber':
            return 'jabber'
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write Jabber models go to the Jabber DB.
        """
        if model._meta.app_label == 'jabber':
            return 'jabber'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the Jabber app is involved.
        """
        if obj1._meta.app_label == 'jabber' or \
           obj2._meta.app_label == 'jabber':
           return True
        return None

    def allow_syncdb(self, db, model):
        """
        Make sure the Jabber app only appears in the 'jabber'
        database.
        """
        if db == 'jabber':
            return model._meta.app_label == 'jabber'
        elif model._meta.app_label == 'jabber':
            return False
        return None
