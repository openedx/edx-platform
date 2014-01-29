#!/usr/bin/env python

# Generate test translation files from human-readable po files.
#
# Dummy language is specified in configuration file (see config.py)
# two letter language codes reference:
# see http://www.loc.gov/standards/iso639-2/php/code_list.php
#
# Django will not localize in languages that django itself has not been
# localized for. So we are using a well-known language (default='eo').
# Django languages are listed in django.conf.global_settings.LANGUAGES
#
# po files can be generated with this:
# django-admin.py makemessages --all --extension html -l en
#
# Usage:
#
# $ ./make_dummy.py
#
# generates output conf/locale/$DUMMY_LOCALE/LC_MESSAGES,
# where $DUMMY_LOCALE is the dummy_locale value set in the i18n config

import os, sys
import polib

from i18n.dummy import Dummy
from i18n.config import CONFIGURATION
from i18n.execute import create_dir_if_necessary


def main(file, locale):
    """
    Takes a source po file, reads it, and writes out a new po file
    in :param locale: containing a dummy translation.
    """
    if not os.path.exists(file):
        raise IOError('File does not exist: %s' % file)
    pofile = polib.pofile(file)
    converter = Dummy()
    for msg in pofile:
        converter.convert_msg(msg)

    # Apply declaration for English pluralization rules so that ngettext will
    # do something reasonable.
    pofile.metadata['Plural-Forms'] = 'nplurals=2; plural=(n != 1);'

    new_file = new_filename(file, locale)
    create_dir_if_necessary(new_file)
    pofile.save(new_file)


def new_filename(original_filename, new_locale):
    """Returns a filename derived from original_filename, using new_locale as the locale"""
    orig_dir = os.path.dirname(original_filename)
    msgs_dir = os.path.basename(orig_dir)
    orig_file = os.path.basename(original_filename)
    return os.path.abspath(os.path.join(orig_dir, '../..', new_locale, msgs_dir, orig_file))

if __name__ == '__main__':
    LOCALE = CONFIGURATION.dummy_locale
    SOURCE_MSGS_DIR = CONFIGURATION.source_messages_dir
    print "Processing source language files into dummy strings:"
    for source_file in CONFIGURATION.source_messages_dir.walkfiles('*.po'):
        print '   ', source_file.relpath()
        main(SOURCE_MSGS_DIR.joinpath(source_file), LOCALE)
    print
