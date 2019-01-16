# -*- coding: utf-8 -*-
"""
print_setting
=============

Django command to output a single Django setting.
Useful when paver or a shell script needs such a value.

This handles the one specific use case of the "print_settings" command from
django-extensions that we were actually using.
"""
from __future__ import print_function

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """print_setting command"""

    help = "Print the value of a single Django setting."

    def add_arguments(self, parser):
        parser.add_argument(
            'setting',
            help='Specifies the setting to be printed.'
        )

    def handle(self, *args, **options):
        setting = options.get('setting')

        if not hasattr(settings, setting):
            raise CommandError('%s not found in settings.' % setting)

        print(getattr(settings, setting))
