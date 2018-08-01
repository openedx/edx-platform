from django.apps import AppConfig


class UserSyncServiceConfig(AppConfig):
    name = u'user_sync_service'

    def ready(self):
        """
        Import Tasks
        """
        pass