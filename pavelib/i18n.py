# --- Internationalization tasks

from paver.easy import *
from pavelib import paver_utils, test_utils, assets
import os


@task
def i18n_extract():
    """
    Extract localizable strings from sources
    """
    i18n_validate_gettext()
    sh(os.path.join(assets.REPO_ROOT, "i18n", "extract.py"))


@task
def i18n_validate_gettext():
    """
    Make sure GNU gettext utilities are available
    """
    if not test_utils.is_exe('xgettext'):
        msg = ("Cannot locate GNU gettext utilities, which are required by django for internationalization.\n"
               "(see https://docs.djangoproject.com/en/dev/topics/i18n/translation/#message-files)\n"
               "Try downloading them from http://www.gnu.org/software/gettext/")
        raise Exception(paver_utils.colorize_red(msg))


@task
@cmdopts([
    ("extract", "e", "Extract first"),
])
def i18n_generate(options):
    """
    Compile localizable strings from sources. With optional flag 'extract', will extract strings first.
    """
    i18n_validate_gettext()

    extract = getattr(options, 'extract', False)

    if extract:
        i18n_extract()
    else:
        sh(os.path.join(assets.REPO_ROOT, "i18n", "generate.py"))


@task
def i18n_dummy():
    """
    Simulate international translation by generating dummy strings corresponding to source strings.
    """
    source_files = []

    for subdir, dirs, files in os.walk(os.path.join(assets.REPO_ROOT, 'conf', 'locale', 'en', 'LC_MESSAGES')):
        for file in files:
            if file.endswith('.po'):
                source_files.append(os.path.join(subdir, file))

    dummy_locale = 'eo'
    cmd = os.path.join(assets.REPO_ROOT, "i18n", "make_dummy.py")

    for file in source_files:
        sh("{cmd} {file} {dummy_locale}".format(cmd=cmd, file=file, dummy_locale=dummy_locale))


@task
def i18n_validate_transifex_config():
    """
    Make sure config file with username/password exists
    """
    home = os.path.expanduser("~")
    config_file = "{home}/.transifexrc".format(home=home)

    if not os.path.isfile(config_file) or os.path.getsize(config_file) == 0:
        msg = "Cannot connect to Transifex, config file is missing or empty: {config_file}\n".format(
            config_file=config_file)
        msg += "See http://help.transifex.com/features/client/#transifexrc"
        raise Exception(paver_utils.colorize_red(msg))


@task
def i18n_transifex_push():
    """
    Push source strings to Transifex for translation
    """
    i18n_validate_transifex_config()
    cmd = os.path.join(assets.REPO_ROOT, "i18n", "transifex.py")
    sh("{cmd} push".format(cmd=cmd))


@task
def i18n_transifex_pull():
    """
    Pull translated strings from Transifex
    """
    i18n_validate_transifex_config()
    cmd = os.path.join(assets.REPO_ROOT, "i18n", "transifex.py")
    sh("{cmd} pull".format(cmd=cmd))


@task
def i18n_transifex_test():
    """
    Test translation
    """
    i18n_validate_transifex_config()
    test = os.path.join(assets.REPO_ROOT, "i18n", "tests")
    pythonpath_prefix = "PYTHONPATH={REPO_ROOT}/i18n:$PYTHONPATH".format(REPO_ROOT=assets.REPO_ROOT)
    sh("{pythonpath_prefix} nosetests {test}".format(pythonpath_prefix=pythonpath_prefix, test=test))
