#!/usr/bin/env python

"""
See https://edx-wiki.atlassian.net/wiki/display/ENG/PO+File+workflow

This task extracts all English strings from all source code
and produces three human-readable files:
   conf/locale/en/LC_MESSAGES/django-partial.po
   conf/locale/en/LC_MESSAGES/djangojs-partial.po
   conf/locale/en/LC_MESSAGES/mako.po

This task will clobber any existing django.po file.
This is because django-admin.py makemessages hardcodes this filename
and it cannot be overridden.

"""

from datetime import datetime
import importlib
import os
import os.path
import logging
import sys
import argparse

from path import path
from polib import pofile

from i18n.config import BASE_DIR, LOCALE_DIR, CONFIGURATION
from i18n.execute import execute, remove_file
from i18n.segment import segment_pofiles


EDX_MARKER = "edX translation file"
LOG = logging.getLogger(__name__)
DEVNULL = open(os.devnull, 'wb')


def base(path1, *paths):
    """Return a relative path from BASE_DIR to path1 / paths[0] / ... """
    return BASE_DIR.relpathto(path1.joinpath(*paths))


def main(verbosity=1):
    """
    Main entry point of script
    """
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    LOCALE_DIR.parent.makedirs_p()
    source_msgs_dir = CONFIGURATION.source_messages_dir
    remove_file(source_msgs_dir.joinpath('django.po'))

    # Extract strings from mako templates.
    verbosity_map = {
        0: "-q",
        1: "",
        2: "-v",
    }
    babel_verbosity = verbosity_map.get(verbosity, "")

    if verbosity:
        stderr = None
    else:
        stderr = DEVNULL

    babel_mako_cmd = 'pybabel {verbosity} extract -F {config} -c "Translators:" . -o {output}'
    babel_mako_cmd = babel_mako_cmd.format(
        verbosity=babel_verbosity,
        config=base(LOCALE_DIR, 'babel_mako.cfg'),
        output=base(CONFIGURATION.source_messages_dir, 'mako.po'),
    )
    execute(babel_mako_cmd, working_directory=BASE_DIR, stderr=stderr)

    babel_underscore_cmd = 'pybabel {verbosity} extract -F {config} -c "Translators:" . -o {output}'
    babel_underscore_cmd = babel_underscore_cmd.format(
        verbosity=babel_verbosity,
        config=base(LOCALE_DIR, 'babel_underscore.cfg'),
        output=base(CONFIGURATION.source_messages_dir, 'underscore.po'),
    )
    execute(babel_underscore_cmd, working_directory=BASE_DIR, stderr=stderr)

    makemessages = "django-admin.py makemessages -l en -v{}".format(verbosity)
    ignores = " ".join('--ignore="{}/*"'.format(d) for d in CONFIGURATION.ignore_dirs)
    if ignores:
        makemessages += " " + ignores

    # Extract strings from django source files, including .py files.
    make_django_cmd = makemessages + ' --extension html'
    execute(make_django_cmd, working_directory=BASE_DIR, stderr=stderr)

    # Extract strings from Javascript source files.
    make_djangojs_cmd = makemessages + ' -d djangojs --extension js'
    execute(make_djangojs_cmd, working_directory=BASE_DIR, stderr=stderr)

    # makemessages creates 'django.po'. This filename is hardcoded.
    # Rename it to django-partial.po to enable merging into django.po later.
    os.rename(
        source_msgs_dir.joinpath('django.po'),
        source_msgs_dir.joinpath('django-partial.po')
    )

    # makemessages creates 'djangojs.po'. This filename is hardcoded.
    # Rename it to djangojs-partial.po to enable merging into djangojs.po later.
    os.rename(
        source_msgs_dir.joinpath('djangojs.po'),
        source_msgs_dir.joinpath('djangojs-partial.po')
    )

    files_to_clean = set()

    files_to_clean.add(source_msgs_dir / "underscore.po")

    # Extract strings from third-party applications.
    for app_name in CONFIGURATION.third_party:
        # Import the app to find out where it is.  Then use pybabel to extract
        # from that directory.
        app_module = importlib.import_module(app_name)
        app_dir = path(app_module.__file__).dirname().dirname()
        output_file = source_msgs_dir / (app_name + ".po")
        files_to_clean.add(output_file)

        babel_cmd = 'pybabel {verbosity} extract -F {config} -c "Translators:" {app} -o {output}'
        babel_cmd = babel_cmd.format(
            verbosity=babel_verbosity,
            config=LOCALE_DIR / 'babel_third_party.cfg',
            app=app_name,
            output=output_file,
        )
        execute(babel_cmd, working_directory=app_dir, stderr=stderr)

    # Segment the generated files.
    segmented_files = segment_pofiles("en")
    files_to_clean.update(segmented_files)

    # Finish each file.
    for filename in files_to_clean:
        LOG.info('Cleaning %s' % filename)
        po = pofile(source_msgs_dir.joinpath(filename))
        # replace default headers with edX headers
        fix_header(po)
        # replace default metadata with edX metadata
        fix_metadata(po)
        # remove key strings which belong in messages.po
        strip_key_strings(po)
        po.save()


def fix_header(po):
    """
    Replace default headers with edX headers
    """

    # By default, django-admin.py makemessages creates this header:
    #
    #   SOME DESCRIPTIVE TITLE.
    #   Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
    #   This file is distributed under the same license as the PACKAGE package.
    #   FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.

    po.metadata_is_fuzzy = []   # remove [u'fuzzy']
    header = po.header
    fixes = (
        ('SOME DESCRIPTIVE TITLE', EDX_MARKER),
        ('Translations template for PROJECT.', EDX_MARKER),
        ('YEAR', str(datetime.utcnow().year)),
        ('ORGANIZATION', 'edX'),
        ("THE PACKAGE'S COPYRIGHT HOLDER", "EdX"),
        (
            'This file is distributed under the same license as the PROJECT project.',
            'This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.'
        ),
        (
            'This file is distributed under the same license as the PACKAGE package.',
            'This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.'
        ),
        ('FIRST AUTHOR <EMAIL@ADDRESS>', 'EdX Team <info@edx.org>'),
    )
    for src, dest in fixes:
        header = header.replace(src, dest)
    po.header = header


def fix_metadata(po):
    """
    Replace default metadata with edX metadata
    """

    # By default, django-admin.py makemessages creates this metadata:
    #
    #   {u'PO-Revision-Date': u'YEAR-MO-DA HO:MI+ZONE',
    #   u'Language': u'',
    #   u'Content-Transfer-Encoding': u'8bit',
    #   u'Project-Id-Version': u'PACKAGE VERSION',
    #   u'Report-Msgid-Bugs-To': u'',
    #   u'Last-Translator': u'FULL NAME <EMAIL@ADDRESS>',
    #   u'Language-Team': u'LANGUAGE <LL@li.org>',
    #   u'POT-Creation-Date': u'2013-04-25 14:14-0400',
    #   u'Content-Type': u'text/plain; charset=UTF-8',
    #   u'MIME-Version': u'1.0'}

    fixes = {
        'PO-Revision-Date': datetime.utcnow(),
        'Report-Msgid-Bugs-To': 'openedx-translation@googlegroups.com',
        'Project-Id-Version': '0.1a',
        'Language': 'en',
        'Last-Translator': '',
        'Language-Team': 'openedx-translation <openedx-translation@googlegroups.com>',
    }
    po.metadata.update(fixes)


def strip_key_strings(po):
    """
    Removes all entries in PO which are key strings.
    These entries should appear only in messages.po, not in any other po files.
    """
    newlist = [entry for entry in po if not is_key_string(entry.msgid)]
    del po[:]
    po += newlist


def is_key_string(string):
    """
    returns True if string is a key string.
    Key strings begin with underscore.
    """
    return len(string) > 1 and string[0] == '_'


if __name__ == '__main__':
    # pylint: disable=invalid-name
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', '-v', action='count', default=0)
    args = parser.parse_args()
    main(verbosity=args.verbose)
