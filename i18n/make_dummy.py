#!/usr/bin/python

# Generate test translation files from human-readable po files.
# 
#
# po files can be generated with this:
# django-admin.py makemessages --all --extension html -l en

# Usage:
#
# $ ./make_dummy.py <sourcefile>
#
# $ ./make_dummy.py mitx/conf/locale/en/LC_MESSAGES/django.po
#
# generates output to
#    mitx/conf/locale/vr/LC_MESSAGES/django.po

import os, sys
import polib
from dummy import Dummy

# Dummy language 
# two letter language codes reference:
# see http://www.loc.gov/standards/iso639-2/php/code_list.php
#
# Django will not localize in languages that django itself has not been
# localized for. So we are using a well-known language: 'fr'.

OUT_LANG = 'fr'

def main(file):
    """
    Takes a source po file, reads it, and writes out a new po file
    containing a dummy translation.
    """
    if not os.path.exists(file):
        raise IOError('File does not exist: %s' % file)
    pofile = polib.pofile(file)
    converter = Dummy()
    converter.init_msgs(pofile.translated_entries())
    for msg in pofile:
        converter.convert_msg(msg)
    new_file = new_filename(file, OUT_LANG)
    create_dir_if_necessary(new_file)
    pofile.save(new_file)
    


def new_filename(original_filename, new_lang):
    """Returns a filename derived from original_filename, using new_lang as the locale"""
    orig_dir = os.path.dirname(original_filename)
    msgs_dir = os.path.basename(orig_dir)
    orig_file = os.path.basename(original_filename)
    return '%s/%s/%s/%s' % (os.path.abspath(orig_dir + '/../..'),
                            new_lang,
                            msgs_dir,
                            orig_file)


def create_dir_if_necessary(pathname):
    dirname = os.path.dirname(pathname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

if __name__ == '__main__':
    if len(sys.argv)<2:
        raise Exception("missing file argument")
    main(sys.argv[1])
