#!/usr/bin/env python

# Generate test translation files from human-readable po files.
# 
# Dummy language is specified in configuration file (see config.py)
# two letter language codes reference:
# see http://www.loc.gov/standards/iso639-2/php/code_list.php
#
# Django will not localize in languages that django itself has not been
# localized for. So we are using a well-known language (default='fr').
#
# po files can be generated with this:
# django-admin.py makemessages --all --extension html -l en

# Usage:
#
# $ ./make_dummy.py <sourcefile>
#
# $ ./make_dummy.py ../conf/locale/en/LC_MESSAGES/django.po
#
# generates output to
#    mitx/conf/locale/fr/LC_MESSAGES/django.po

import os, sys
import polib
from dummy import Dummy
from config import CONFIGURATION
from execute import create_dir_if_necessary

def main(file, locale):
    """
    Takes a source po file, reads it, and writes out a new po file
    in :param locale: containing a dummy translation.
    """
    if not os.path.exists(file):
        raise IOError('File does not exist: %s' % file)
    pofile = polib.pofile(file)
    converter = Dummy()
    converter.init_msgs(pofile.translated_entries())
    for msg in pofile:
        converter.convert_msg(msg)
    new_file = new_filename(file, locale)
    create_dir_if_necessary(new_file)
    pofile.save(new_file)

def new_filename(original_filename, new_locale):
    """Returns a filename derived from original_filename, using new_locale as the locale"""
    orig_dir = os.path.dirname(original_filename)
    msgs_dir = os.path.basename(orig_dir)
    orig_file = os.path.basename(original_filename)
    return os.path.abspath(os.path.join(orig_dir,
                                        '../..',
                                        new_locale,
                                        msgs_dir,
                                        orig_file))

if __name__ == '__main__':
    # required arg: file
    if len(sys.argv)<2:
        raise Exception("missing file argument")
    # optional arg: locale
    if len(sys.argv)<3:
        locale = CONFIGURATION.get_dummy_locale()
    else:
        locale = sys.argv[2]
    main(sys.argv[1], locale)
