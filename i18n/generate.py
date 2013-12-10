#!/usr/bin/env python

"""
 See https://edx-wiki.atlassian.net/wiki/display/ENG/PO+File+workflow


 This task merges and compiles the human-readable .pofiles on the 
 local filesystem into machine-readable .mofiles. This is typically
 necessary as part of the build process since these .mofiles are
 needed by Django when serving the web app.

 The configuration file (in edx-platform/conf/locale/config) specifies which
 languages to generate.
"""

import os, sys, logging
from polib import pofile

from config import BASE_DIR, CONFIGURATION
from execute import execute

LOG = logging.getLogger(__name__)

def merge(locale, target='django.po', fail_if_missing=True):
    """
    For the given locale, merge django-partial.po, messages.po, mako.po -> django.po
    target is the resulting filename
    If fail_if_missing is True, and the files to be merged are missing,
    throw an Exception.
    If fail_if_missing is False, and the files to be merged are missing,
    just return silently.
    """
    LOG.info('Merging locale={0}'.format(locale))
    locale_directory = CONFIGURATION.get_messages_dir(locale)
    files_to_merge = ('django-partial.po', 'messages.po', 'mako.po')
    try:
        validate_files(locale_directory, files_to_merge)
    except Exception, e:
        if not fail_if_missing:
            return
        raise e

    # merged file is merged.po
    merge_cmd = 'msgcat -o merged.po ' + ' '.join(files_to_merge)
    execute(merge_cmd, working_directory=locale_directory)

    # clean up redunancies in the metadata
    merged_filename = locale_directory.joinpath('merged.po')
    clean_metadata(merged_filename)

    # rename merged.po -> django.po (default)
    django_filename = locale_directory.joinpath(target)
    os.rename(merged_filename, django_filename) # can't overwrite file on Windows

def clean_metadata(file):
    """
    Clean up redundancies in the metadata caused by merging.
    This reads in a PO file and simply saves it back out again.
    """
    pofile(file).save()

def validate_files(dir, files_to_merge):
    """
    Asserts that the given files exist.
    files_to_merge is a list of file names (no directories).
    dir is the directory (a path object from path.py) in which the files should appear.
    raises an Exception if any of the files are not in dir.
    """
    for path in files_to_merge:
        pathname = dir.joinpath(path)
        if not pathname.exists():
            raise Exception("I18N: Cannot generate because file not found: {0}".format(pathname))

def main ():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)

    for locale in CONFIGURATION.locales:
        merge(locale)
    # Dummy text is not required. Don't raise exception if files are missing.
    merge(CONFIGURATION.dummy_locale, fail_if_missing=False)
    compile_cmd = 'django-admin.py compilemessages'
    execute(compile_cmd, working_directory=BASE_DIR)

if __name__ == '__main__':
    main()
