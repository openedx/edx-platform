#!/usr/bin/env python
from __future__ import print_function
import sys
from polib import pofile
import argparse

from i18n.config import CONFIGURATION
from i18n.execute import execute
from i18n.extract import EDX_MARKER

TRANSIFEX_HEADER = u'edX community translations have been downloaded from {}'
TRANSIFEX_URL = 'https://www.transifex.com/projects/p/edx-platform/'


def push():
    execute('tx push -s')


def pull():
    print("Pulling languages from transifex...")
    execute('tx pull --mode=reviewed --all')
    clean_translated_locales()


def clean_translated_locales():
    """
    Strips out the warning from all translated po files
    about being an English source file.
    """
    for locale in CONFIGURATION.translated_locales:
        clean_locale(locale)


def clean_locale(locale):
    """
    Strips out the warning from all of a locale's translated po files
    about being an English source file.
    Iterates over machine-generated files.
    """
    dirname = CONFIGURATION.get_messages_dir(locale)
    for filename in ('django-partial.po', 'djangojs-partial.po', 'mako.po'):
        clean_file(dirname.joinpath(filename))


def clean_file(filename):
    """
    Strips out the warning from a translated po file about being an English source file.
    Replaces warning with a note about coming from Transifex.
    """
    po = pofile(filename)
    if po.header.find(EDX_MARKER) != -1:
        new_header = get_new_header(po)
        new = po.header.replace(EDX_MARKER, new_header)
        po.header = new
        po.save()


def get_new_header(po):
    team = po.metadata.get('Language-Team', None)
    if not team:
        return TRANSIFEX_HEADER.format(TRANSIFEX_URL)
    else:
        return TRANSIFEX_HEADER.format(team)


if __name__ == '__main__':
    # pylint: disable=invalid-name
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="push or pull")
    parser.add_argument("--verbose", "-v")
    args = parser.parse_args()
    # pylint: enable=invalid-name

    if args.command == "push":
        push()
    elif args.command == "pull":
        pull()
    else:
        raise Exception("unknown command ({cmd})".format(cmd=args.command))
