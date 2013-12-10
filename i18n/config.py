import os
import json
from path import path

# BASE_DIR is the working directory to execute django-admin commands from.
# Typically this should be the 'edx-platform' directory.
BASE_DIR = path(__file__).abspath().dirname().joinpath('..').normpath()

# LOCALE_DIR contains the locale files.
# Typically this should be 'edx-platform/conf/locale'
LOCALE_DIR = BASE_DIR.joinpath('conf', 'locale')


class Configuration:
    """
    # Reads localization configuration in json format

    """
    _source_locale = 'en'

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
            return json.load(stream)

    @property
    def locales(self):
        """
        Returns a list of locales declared in the configuration file,
        e.g. ['en', 'fr', 'es']
        Each locale is a string.
        """
        return self._config['locales']

    @property
    def source_locale(self):
        """
        Returns source language.
        Source language is English.
        """
        return self._source_locale

    @property
    def dummy_locale(self):
        """
        Returns a locale to use for the dummy text, e.g. 'eo'.
        Throws exception if no dummy-locale is declared. 
        The locale is a string.
        """
        dummy = self._config.get('dummy-locale', None)
        if not dummy:
            raise Exception('Could not read dummy-locale from configuration file.')
        return dummy

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


CONFIGURATION = Configuration(LOCALE_DIR.joinpath('config').normpath())
