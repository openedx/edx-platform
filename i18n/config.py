import os, json

# BASE_DIR is the working directory to execute django-admin commands from.
# Typically this should be the 'mitx' directory.
BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__))+'/..')

# LOCALE_DIR contains the locale files.
# Typically this should be 'mitx/conf/locale'
LOCALE_DIR =  os.path.join(BASE_DIR, 'conf', 'locale')

class Configuration:
    """
    # Reads localization configuration in json format

    """
    _source_locale = 'en'

    def __init__(self, filename):
        self.filename = filename
        self.config = self.get_config(self.filename)

    def get_config(self, filename):
        """
        Returns data found in config file (as dict), or raises exception if file not found
        """
        if not os.path.exists(filename):
            raise Exception("Configuration file cannot be found: %s" % filename)
        with open(filename) as stream:
            return json.load(stream)

    def get_locales(self):
        """
        Returns a list of locales declared in the configuration file,
        e.g. ['en', 'fr', 'es']
        Each locale is a string.
        """
        return self.config['locales']

    def get_source_locale(self):
        """
        Returns source language.
        Source language is English.
        """
        return self._source_locale

    def get_dummy_locale(self):
        """
        Returns a locale to use for the dummy text, e.g. 'fr'.
        Throws exception if no dummy-locale is declared. 
        The locale is a string.
        """
        dummy = self.config.get('dummy-locale', None)
        if not dummy:
            raise Exception('Could not read dummy-locale from configuration file.')
        return dummy

    def get_messages_dir(self, locale):
        """
        Returns the name of the directory holding the po files for locale.
        Example: mitx/conf/locale/fr/LC_MESSAGES
        """
        return os.path.join(LOCALE_DIR, locale, 'LC_MESSAGES')

    def get_source_messages_dir(self):
        """
        Returns the name of the directory holding the source-language po files (English).
        Example: mitx/conf/locale/en/LC_MESSAGES
        """
        return self.get_messages_dir(self.get_source_locale())


CONFIGURATION = Configuration(os.path.normpath(os.path.join(LOCALE_DIR, 'config')))

