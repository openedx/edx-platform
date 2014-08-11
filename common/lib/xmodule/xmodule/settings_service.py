"""
XBlock service to allow to access the server settings
"""

from django.conf import settings

class SettingsService(object):
    def get(self, setting_name):
        return getattr(settings, setting_name)
