"""
Database Routers for use with the coursewarehistoryextended django app.
"""


class StudentModuleHistoryExtendedRouter(object):
    """
    A Database Router that separates StudentModuleHistoryExtended into its own database.
    """

    DATABASE_NAME = 'student_module_history'

    def _is_csmh(self, model):
        """
        Return True if ``model`` is courseware.StudentModuleHistoryExtended.
        """
        return (
            model._meta.app_label == 'coursewarehistoryextended' and
            model.__name__ == 'StudentModuleHistoryExtended'
        )

    def db_for_read(self, model, **hints):  # pylint: disable=unused-argument
        """
        Use the StudentModuleHistoryExtendedRouter.DATABASE_NAME if the model is StudentModuleHistoryExtended.
        """
        if self._is_csmh(model):
            return self.DATABASE_NAME
        else:
            return None

    def db_for_write(self, model, **hints):  # pylint: disable=unused-argument
        """
        Use the StudentModuleHistoryExtendedRouter.DATABASE_NAME if the model is StudentModuleHistoryExtended.
        """
        if self._is_csmh(model):
            return self.DATABASE_NAME
        else:
            return None

    def allow_relation(self, obj1, obj2, **hints):  # pylint: disable=unused-argument
        """
        Disable relations if the model is StudentModuleHistoryExtended.
        """
        if self._is_csmh(obj1) or self._is_csmh(obj2):
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # pylint: disable=unused-argument
        """
        Only sync StudentModuleHistoryExtended to StudentModuleHistoryExtendedRouter.DATABASE_Name
        """
        if model_name is not None:
            model = hints.get('model')
            if model is not None and self._is_csmh(model):
                return db == self.DATABASE_NAME
        if db == self.DATABASE_NAME:
            return False

        return None
