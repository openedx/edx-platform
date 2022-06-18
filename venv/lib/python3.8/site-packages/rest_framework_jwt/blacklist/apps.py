# -*- coding: utf-8 -*-

from django.apps import AppConfig


class BlacklistedTokenConfig(AppConfig):
    name = 'rest_framework_jwt.blacklist'

    def ready(self):
        import rest_framework_jwt.blacklist.signals  # noqa
