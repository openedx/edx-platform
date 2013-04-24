#!/usr/bin/python

import os, subprocess, logging, json
from make_dummy import create_dir_if_necessary, main as dummy_main

'''
Generate or update all translation files
 Usage:
    $ update.py


 1. extracts files from mako templates
 2. extracts files from django templates and python source files
 3. extracts files from django javascript files
 4. generates dummy text translations
 5. compiles po files to mo files

 Configuration (e.g. known languages) declared in mitx/conf/locale/config
'''

# -----------------------------------
# BASE_DIR is the working directory to execute django-admin commands from.
# Typically this should be the 'mitx' directory.
BASE_DIR = os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/..')

# LOCALE_DIR contains the locale files.
# Typically this should be 'mitx/conf/locale'
LOCALE_DIR = BASE_DIR + '/conf/locale'

# MSGS_DIR contains the English po files
MSGS_DIR = LOCALE_DIR + '/en/LC_MESSAGES'

# CONFIG_FILENAME contains localization configuration in json format
CONFIG_FILENAME = LOCALE_DIR + '/config'

# BABEL_CONFIG contains declarations for Babel to extract strings from mako template files
BABEL_CONFIG = LOCALE_DIR + '/babel.cfg'

# Strings from mako template files are written to BABEL_OUT
BABEL_OUT = MSGS_DIR + '/mako.po'

# These are the shell commands invoked by main()
COMMANDS = {
    'babel_mako': 'pybabel extract -F %s -c "TRANSLATORS:" . -o %s' % (BABEL_CONFIG, BABEL_OUT),
    'make_django': 'django-admin.py makemessages --all --ignore=src/* --extension html -l en',
    'make_djangojs': 'django-admin.py makemessages --all -d djangojs --ignore=src/* --extension js -l en',
    'msgcat' : 'msgcat -o merged.po django.po %s' % BABEL_OUT,
    'rename_django' : 'mv django.po django_old.po',
    'rename_merged' : 'mv merged.po django.po',
    'compile': 'django-admin.py compilemessages'
    
    }

def execute (command_kwd, log, working_directory=BASE_DIR):
    '''
    Executes command_kwd, which references a shell command in COMMANDS.
    '''
    full_cmd = COMMANDS[command_kwd]
    log.info('%s' % full_cmd)
    subprocess.call(full_cmd.split(' '), cwd=working_directory)
    
def make_log ():
    '''returns a logger'''
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    log.addHandler(log_handler)
    return log

def get_config ():
    '''Returns data found in config file, or returns None if file not found'''
    config_path = os.path.abspath(CONFIG_FILENAME)
    if not os.path.exists(config_path):
        return None
    with open(config_path) as stream:
        return json.load(stream)

def main ():
    log = make_log()
    create_dir_if_necessary(LOCALE_DIR)
    log.info('Executing all commands from %s' % BASE_DIR)

    remove_files = ['django.po', 'djangojs.po', 'nonesuch']
    for filename in remove_files:
        path = MSGS_DIR + '/' + filename
        log.info('Deleting file %s' % path)
        if not os.path.exists(path):
            log.warn("File does not exist: %s" % path)
        else:
            os.remove(path)

    # Generate or update human-readable .po files from all source code.
    execute('babel_mako', log=log)
    execute('make_django', log=log)
    execute('make_djangojs', log=log)
    execute('msgcat', log=log, working_directory=MSGS_DIR)
    execute('rename_django', log=log, working_directory=MSGS_DIR)
    execute('rename_merged', log=log, working_directory=MSGS_DIR)

    # Generate dummy text files from the English .po files
    log.info('Generating dummy text.')
    dummy_main(LOCALE_DIR + '/en/LC_MESSAGES/django.po')
    dummy_main(LOCALE_DIR + '/en/LC_MESSAGES/djangojs.po')

    # Generate machine-readable .mo files
    execute('compile', log)

if __name__ == '__main__':
    main()
