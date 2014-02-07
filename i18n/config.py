import os

import yaml
from path import path

# BASE_DIR is the working directory to execute django-admin commands from.
# Typically this should be the 'edx-platform' directory.
BASE_DIR = path(__file__).abspath().dirname().dirname()

# LOCALE_DIR contains the locale files.
# Typically this should be 'edx-platform/conf/locale'
LOCALE_DIR = BASE_DIR.joinpath('conf', 'locale')


class Configuration(object):
    """
    Reads localization configuration in json format.
    """
    DEFAULTS = {
        'dummy_locales': [],
        'generate_merge': {},
        'ignore_dirs': [],
        'locales': ['en'],
        'segment': {},
        'source_locale': 'en',
    }

    def __init__(self, filename):
        self._filename = filename
        self._config = self.read_config(filename)

    def read_config(self, filename):
        """
        Returns data found in config file (as dict), or raises exception if file not found
        """
        if not os.path.exists(filename):
            raise Exception("Configuration file cannot be found: %s" % filename)
        with open(filename) as stream:
            return yaml.safe_load(stream)

    def __getattr__(self, name):
        if name in self.DEFAULTS:
            return self._config.get(name, self.DEFAULTS[name])
        raise AttributeError("Configuration has no such setting: {!r}".format(name))

    def get_messages_dir(self, locale):
        """
        Returns the name of the directory holding the po files for locale.
        Example: edx-platform/conf/locale/fr/LC_MESSAGES
        """
        return LOCALE_DIR.joinpath(locale, 'LC_MESSAGES')

    @property
    def source_messages_dir(self):
        """
        Returns the name of the directory holding the source-language po files (English).
        Example: edx-platform/conf/locale/en/LC_MESSAGES
        """
        return self.get_messages_dir(self.source_locale)

    @property
    def translated_locales(self):
        """
        Returns the set of locales to be translated (ignoring the source_locale).
        """
        return sorted(set(self.locales) - set([self.source_locale]))

CONFIGURATION = Configuration(LOCALE_DIR.joinpath('config.yaml').normpath())
