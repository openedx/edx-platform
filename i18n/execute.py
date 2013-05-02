import os, subprocess, logging, json

def init_module():
    """
    Initializes module parameters
    """
    global BASE_DIR, LOCALE_DIR, CONFIG_FILENAME, SOURCE_MSGS_DIR, SOURCE_LOCALE, LOG

    # BASE_DIR is the working directory to execute django-admin commands from.
    # Typically this should be the 'mitx' directory.
    BASE_DIR = os.path.normpath(os.path.dirname(os.path.abspath(__file__))+'/..')

    # Source language is English
    SOURCE_LOCALE = 'en'

    # LOCALE_DIR contains the locale files.
    # Typically this should be 'mitx/conf/locale'
    LOCALE_DIR = BASE_DIR + '/conf/locale'

    # CONFIG_FILENAME contains localization configuration in json format
    CONFIG_FILENAME = LOCALE_DIR + '/config'

    # SOURCE_MSGS_DIR contains the English po files.
    SOURCE_MSGS_DIR = messages_dir(SOURCE_LOCALE)

    # Default logger.
    LOG = get_logger()
    

def messages_dir(locale):
    """
    Returns the name of the directory holding the po files for locale.
    Example: mitx/conf/locale/en/LC_MESSAGES
    """
    return os.path.join(LOCALE_DIR, locale, 'LC_MESSAGES')

def get_logger():
    """Returns a default logger"""
    log = logging.getLogger(__name__)
    log.setLevel(logging.INFO)
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    log.addHandler(log_handler)
    return log

# Run this after defining messages_dir and get_logger, because it depends on these.
init_module()    

def execute (command, working_directory=BASE_DIR, log=LOG):
    """
    Executes shell command in a given working_directory.
    Command is a string to pass to the shell.
    Output is logged to log.
    """
    log.info(command)
    subprocess.call(command.split(' '), cwd=working_directory)
    
def get_config():
    """Returns data found in config file, or returns None if file not found"""
    config_path = os.path.abspath(CONFIG_FILENAME)
    if not os.path.exists(config_path):
        log.warn("Configuration file cannot be found: %s" % \
                 os.path.relpath(config_path, BASE_DIR))
        return None
    with open(config_path) as stream:
        return json.load(stream)
    
def create_dir_if_necessary(pathname):
    dirname = os.path.dirname(pathname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def remove_file(filename, log=LOG, verbose=True):
    """
    Attempt to delete filename.
    Log a warning if file does not exist.
    Logging filenames are releative to BASE_DIR to cut down on noise in output.
    """
    if verbose:
        log.info('Deleting file %s' % os.path.relpath(filename, BASE_DIR))
    if not os.path.exists(filename):
        log.warn("File does not exist: %s" % os.path.relpath(filename, BASE_DIR))
    else:
        os.remove(filename)

