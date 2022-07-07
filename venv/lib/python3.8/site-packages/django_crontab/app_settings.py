from __future__ import print_function

import os
import re
import sys

from importlib import import_module


class Settings():
    def __init__(self, settings):
        self.CRONJOBS = getattr(settings, 'CRONJOBS', [])

        self.CRONTAB_EXECUTABLE = getattr(settings, 'CRONTAB_EXECUTABLE', '/usr/bin/crontab')

        self.CRONTAB_LINE_REGEXP = re.compile(r'^\s*(([^#\s]+\s+){5})([^#\n]*)\s*(#\s*([^\n]*)|$)')

        self.CRONTAB_LINE_PATTERN = '%(time)s %(command)s # %(comment)s\n'

        self.DJANGO_PROJECT_NAME = getattr(settings, 'CRONTAB_DJANGO_PROJECT_NAME', os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0])

        self.DJANGO_SETTINGS_MODULE = getattr(settings, 'CRONTAB_DJANGO_SETTINGS_MODULE', None)

        if hasattr(settings, 'CRONTAB_DJANGO_MANAGE_PATH'):
            self. DJANGO_MANAGE_PATH = settings.CRONTAB_DJANGO_MANAGE_PATH
            # check if it's really there
            if not os.path.exists(self.DJANGO_MANAGE_PATH):
                print('ERROR: No manage.py file found at "%s". Check settings.CRONTAB_DJANGO_MANAGE_PATH!' % self.DJANGO_MANAGE_PATH)
        else:
            def ext(fpath):
                return os.path.splitext(fpath)[0] + '.py'
            try:  # Django 1.3
                self.DJANGO_MANAGE_PATH = ext(import_module(self.DJANGO_PROJECT_NAME + '.manage').__file__)
            except ImportError:
                try:  # Django 1.4+
                    self.DJANGO_MANAGE_PATH = ext(import_module('manage').__file__)
                except ImportError:
                    print('ERROR: Can\'t find your manage.py - please define settings.CRONTAB_DJANGO_MANAGE_PATH')

        self.PYTHON_EXECUTABLE = getattr(settings, 'CRONTAB_PYTHON_EXECUTABLE', sys.executable)

        self.CRONTAB_COMMENT = getattr(settings, 'CRONTAB_COMMENT', 'django-cronjobs for %s' % self.DJANGO_PROJECT_NAME)

        self.COMMAND_PREFIX = getattr(settings, 'CRONTAB_COMMAND_PREFIX', '')
        self.COMMAND_SUFFIX = getattr(settings, 'CRONTAB_COMMAND_SUFFIX', '')

        self.LOCK_JOBS = getattr(settings, 'CRONTAB_LOCK_JOBS', False)
