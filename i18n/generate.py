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
from execute import execute, get_config, messages_dir, remove_file, \
     BASE_DIR, LOG, SOURCE_LOCALE

def merge(locale, target='django.po'):
    """
    For the given locale, merge django-partial.po, messages.po, mako.po -> django.po
    """
    LOG.info('Merging locale=%s' % locale)
    locale_directory = messages_dir(locale)
    files_to_merge = ('django-partial.po', 'messages.po', 'mako.po')
    validate_files(locale_directory, files_to_merge)

    # merged file is merged.po
    merge_cmd = 'msgcat -o merged.po ' + ' '.join(files_to_merge)
    execute(merge_cmd, working_directory=locale_directory)

    # rename merged.po -> django.po (default)
    merged_filename = os.path.join(locale_directory, 'merged.po')
    django_filename = os.path.join(locale_directory, target)
    os.rename(merged_filename, django_filename) # can't overwrite file on Windows

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
            raise Exception("File not found: %s" % pathname)

def main ():
    configuration = get_config()
    if configuration == None:
        LOG.warn('Configuration file not found, using only English.')
        locales = (SOURCE_LOCALE,)
    else:
        locales = configuration['locales']
    for locale in locales:
        merge(locale)

    compile_cmd = 'django-admin.py compilemessages'
    execute(compile_cmd, working_directory=BASE_DIR)

if __name__ == '__main__':
    main()
