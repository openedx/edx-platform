#!/usr/bin/env python

import os, sys
from polib import pofile
from config import CONFIGURATION
from extract import SOURCE_WARN
from execute import execute

TRANSIFEX_HEADER = 'Translations in this file have been downloaded from %s'
TRANSIFEX_URL = 'https://www.transifex.com/projects/p/edx-studio/'

def push():
    execute('tx push -s')

def pull():
    for locale in CONFIGURATION.locales:
        if locale != CONFIGURATION.source_locale:
            execute('tx pull -l %s' % locale)
    clean_translated_locales()


def clean_translated_locales():
    """
    Strips out the warning from all translated po files
    about being an English source file.
    """
    for locale in CONFIGURATION.locales:
        if locale != CONFIGURATION.source_locale:
            clean_locale(locale)
        
def clean_locale(locale):
    """
    Strips out the warning from all of a locale's translated po files
    about being an English source file.
    Iterates over machine-generated files.
    """
    dirname = CONFIGURATION.get_messages_dir(locale)
    for filename in ('django-partial.po', 'djangojs.po', 'mako.po'):
        clean_file(dirname.joinpath(filename))

def clean_file(file):
    """
    Strips out the warning from a translated po file about being an English source file.
    Replaces warning with a note about coming from Transifex.
    """
    po = pofile(file)
    if po.header.find(SOURCE_WARN) != -1:
        new_header = get_new_header(po)
        new = po.header.replace(SOURCE_WARN, new_header)
        po.header = new
        po.save()

def get_new_header(po):
    team = po.metadata.get('Language-Team', None)
    if not team:
        return TRANSIFEX_HEADER % TRANSIFEX_URL
    else:
        return TRANSIFEX_HEADER % team

if __name__ == '__main__':
    if len(sys.argv)<2:
        raise Exception("missing argument: push or pull")
    arg = sys.argv[1]
    if arg == 'push':
        push()
    elif arg == 'pull':
        pull()
    else:
        raise Exception("unknown argument: (%s)" % arg)
        
