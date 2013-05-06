#!/usr/bin/python

"""
 See https://edx-wiki.atlassian.net/wiki/display/ENG/PO+File+workflow


 This task merges and compiles the human-readable .pofiles on the 
 local filesystem into machine-readable .mofiles. This is typically
 necessary as part of the build process since these .mofiles are
 needed by Django when serving the web app.

 The configuration file (in mitx/conf/locale/config) specifies which
 languages to generate.
"""

import os
from polib import pofile

from config import BASE_DIR, CONFIGURATION
from execute import execute, remove_file, LOG

def merge(locale, target='django.po'):
    """
    For the given locale, merge django-partial.po, messages.po, mako.po -> django.po
    """
    LOG.info('Merging locale={0}'.format(locale))
    locale_directory = CONFIGURATION.get_messages_dir(locale)
    files_to_merge = ('django-partial.po', 'messages.po', 'mako.po')
    validate_files(locale_directory, files_to_merge)

    # merged file is merged.po
    merge_cmd = 'msgcat -o merged.po ' + ' '.join(files_to_merge)
    execute(merge_cmd, working_directory=locale_directory)

    # clean up redunancies in the metadata
    merged_filename = os.path.join(locale_directory, 'merged.po')
    clean_metadata(merged_filename)

    # rename merged.po -> django.po (default)
    django_filename = os.path.join(locale_directory, target)
    os.rename(merged_filename, django_filename) # can't overwrite file on Windows

def clean_metadata(file):
    """
    Clean up redundancies in the metadata caused by merging.
    This reads in a PO file and simply saves it back out again.
    """
    po = pofile(file)
    po.save()
    

def validate_files(dir, files_to_merge):
    """
    Asserts that the given files exist.
    files_to_merge is a list of file names (no directories).
    dir is the directory in which the files should appear.
    raises an Exception if any of the files are not in dir.
    """
    for path in files_to_merge:
        pathname = os.path.join(dir, path)
        if not os.path.exists(pathname):
            raise Exception("File not found: {0}".format(pathname))

def main ():
    for locale in CONFIGURATION.get_locales():
        merge(locale)
    compile_cmd = 'django-admin.py compilemessages'
    execute(compile_cmd, working_directory=BASE_DIR)

if __name__ == '__main__':
    main()
