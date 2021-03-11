"""
Database Routers for use with the coursewarehistoryextended django app.
"""


class StudentModuleHistoryExtendedRouter:
    """
    A Database Router that separates StudentModuleHistoryExtended into its own database.
    """

    DATABASE_NAME = 'student_module_history'

    def _is_csm(self, model):
        """
        Return True if ``model`` is courseware.models.StudentModule.
        """
        return (
            model._meta.app_label == 'courseware' and
            type(model).__name__ == 'StudentModule'
        )

    def _is_csm_h(self, model):
        """
        Return True if ``model`` is coursewarehistoryextended.models.StudentModuleHistoryExtended.
        """
        return (
            model._meta.app_label == 'coursewarehistoryextended' and
            (
                type(model).__name__ == 'StudentModuleHistoryExtended' or
                getattr(model, '__name__', '') == 'StudentModuleHistoryExtended'
            )
        )

    def db_for_read(self, model, **hints):  # pylint: disable=unused-argument
        """
        Use the StudentModuleHistoryExtendedRouter.DATABASE_NAME if the model is StudentModuleHistoryExtended.
        """
        if self._is_csm_h(model):
            return self.DATABASE_NAME
        else:
            return None

    def db_for_write(self, model, **hints):  # pylint: disable=unused-argument
        """
        Use the StudentModuleHistoryExtendedRouter.DATABASE_NAME if the model is StudentModuleHistoryExtended.
        """
        if self._is_csm_h(model):
            return self.DATABASE_NAME
        else:
            return None

    def allow_relation(self, obj1, obj2, **hints):  # pylint: disable=unused-argument
        """
        Manage relations if the model is StudentModuleHistoryExtended.
        """
        # Allow relation between CSM and CSMH (this cross-database relationship is declared with db_constraint=False
        # so while cross-model relationship is allowed via Django it is not stored as such within the database).
        # Note: The order of obj1 and obj2 are based on the parent-child relationship as explained in
        #   https://github.com/django/django/blob/stable/2.2.x/django/db/models/fields/related_descriptors.py
        if self._is_csm(obj1) and self._is_csm_h(obj2):
            return True

        # Prevent any other relations with CSMH since CSMH is in its own different database.
        elif self._is_csm_h(obj1) or self._is_csm_h(obj2):
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # pylint: disable=unused-argument
        """
        Only sync StudentModuleHistoryExtended to StudentModuleHistoryExtendedRouter.DATABASE_Name
        """
        if model_name is not None:
            model = hints.get('model')
            if model is not None and self._is_csm_h(model):
                return db == self.DATABASE_NAME
        if db == self.DATABASE_NAME:
            return False

        return None
