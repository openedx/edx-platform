#!/usr/bin/python
  
"""
See https://edx-wiki.atlassian.net/wiki/display/ENG/PO+File+workflow

 This task extracts all English strings from all source code
 and produces three human-readable files:
   conf/locale/en/LC_MESSAGES/django-partial.po
   conf/locale/en/LC_MESSAGES/djangojs.po
   conf/locale/en/LC_MESSAGES/mako.po

 This task will clobber any existing django.po file.
 This is because django-admin.py makemessages hardcodes this filename
 and it cannot be overridden.
 
"""

import os
from datetime import datetime
from polib import pofile
from execute import execute, create_dir_if_necessary, remove_file, \
     BASE_DIR, LOCALE_DIR, SOURCE_MSGS_DIR, LOG


# BABEL_CONFIG contains declarations for Babel to extract strings from mako template files
# Use relpath to reduce noise in logs
BABEL_CONFIG = os.path.relpath(LOCALE_DIR + '/babel.cfg', BASE_DIR)

# Strings from mako template files are written to BABEL_OUT
# Use relpath to reduce noise in logs
BABEL_OUT = os.path.relpath(SOURCE_MSGS_DIR + '/mako.po', BASE_DIR)


def main ():
    create_dir_if_necessary(LOCALE_DIR)
    generated_files = ('django-partial.po', 'djangojs.po', 'mako.po')

    for filename in generated_files:
        remove_file(os.path.join(SOURCE_MSGS_DIR, filename))

    # Extract strings from mako templates
    babel_mako_cmd = 'pybabel extract -F %s -c "TRANSLATORS:" . -o %s' % (BABEL_CONFIG, BABEL_OUT)

    # Extract strings from django source files
    make_django_cmd = 'django-admin.py makemessages -l en --ignore=src/* --ignore=i18n/* ' \
                      + '--extension html'

    # Extract strings from javascript source files
    make_djangojs_cmd = 'django-admin.py makemessages -l en -d djangojs --ignore=src/* ' \
                        + '--ignore=i18n/* --extension js'
    execute(babel_mako_cmd, working_directory=BASE_DIR)
    execute(make_django_cmd, working_directory=BASE_DIR)
    # makemessages creates 'django.po'. This filename is hardcoded.
    # Rename it to django-partial.po to enable merging into django.po later.
    os.rename(os.path.join(SOURCE_MSGS_DIR, 'django.po'), 
              os.path.join(SOURCE_MSGS_DIR, 'django-partial.po'))
    execute(make_djangojs_cmd, working_directory=BASE_DIR)

    for filename in generated_files:
        LOG.info('Cleaning %s' % filename)
        po = pofile(os.path.join(SOURCE_MSGS_DIR, filename))
        # replace default headers with edX headers
        fix_header(po)
        # replace default metadata with edX metadata
        fix_metadata(po)
        # remove key strings which belong in messages.po
        strip_key_strings(po)
        po.save()

# By default, django-admin.py makemessages creates this header:
"""
SOME DESCRIPTIVE TITLE.
Copyright (C) YEAR THE PACKAGE'S COPYRIGHT HOLDER
This file is distributed under the same license as the PACKAGE package.
FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
"""

def fix_header(po):
    """
    Replace default headers with edX headers
    """
    po.metadata_is_fuzzy = []   # remove [u'fuzzy']
    header = po.header
    fixes = (
        ('SOME DESCRIPTIVE TITLE', 'edX translation file'),
        ('Translations template for PROJECT.', 'edX translation file'),
        ('YEAR', '%s' % datetime.utcnow().year),
        ('ORGANIZATION', 'edX'),
        ("THE PACKAGE'S COPYRIGHT HOLDER", "EdX"),
        ('This file is distributed under the same license as the PROJECT project.',
         'This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.'),
        ('This file is distributed under the same license as the PACKAGE package.',
         'This file is distributed under the GNU AFFERO GENERAL PUBLIC LICENSE.'),
        ('FIRST AUTHOR <EMAIL@ADDRESS>',
         'EdX Team <info@edx.org>')
        )
    for (src, dest) in fixes:
        header = header.replace(src, dest)
    po.header = header

# By default, django-admin.py makemessages creates this metadata:
"""
{u'PO-Revision-Date': u'YEAR-MO-DA HO:MI+ZONE',
 u'Language': u'',
 u'Content-Transfer-Encoding': u'8bit',
 u'Project-Id-Version': u'PACKAGE VERSION',
 u'Report-Msgid-Bugs-To': u'',
 u'Last-Translator': u'FULL NAME <EMAIL@ADDRESS>', 
 u'Language-Team': u'LANGUAGE <LL@li.org>',
 u'POT-Creation-Date': u'2013-04-25 14:14-0400',
 u'Content-Type': u'text/plain; charset=UTF-8',
 u'MIME-Version': u'1.0'}
""" 

def fix_metadata(po):
    """
    Replace default metadata with edX metadata
    """
    fixes = {'PO-Revision-Date': datetime.utcnow(),
             'Report-Msgid-Bugs-To': 'translation_team@edx.org',
             'Project-Id-Version': '0.1a',
             'Language' : 'en',
             'Last-Translator' : '',
             'Language-Team': 'translation team <translation_team@edx.org>',
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
    return len(string)>1 and string[0]=='_'

if __name__ == '__main__':
    main()
