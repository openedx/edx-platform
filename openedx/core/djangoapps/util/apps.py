"""
Configuration for the openedx.core.djangoapps.util Django application
"""


from django.apps import AppConfig


class UtilConfig(AppConfig):
    """
    Configuration class for the openedx.core.djangoapps.util Django application
    """
    label = 'open_edx_util'
    name = 'openedx.core.djangoapps.util'
    verbose_name = 'Open edX Utilities'

    def ready(self):
        """
        Registers signal handlers at startup.
        """
<<<<<<< HEAD
        import openedx.core.djangoapps.util.signals  # lint-amnesty, pylint: disable=unused-import, unused-variable
=======
        import openedx.core.djangoapps.util.signals  # pylint: disable=unused-import, unused-variable
        import openedx.core.djangoapps.util.checks  # pylint: disable=unused-import, unused-variable
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
