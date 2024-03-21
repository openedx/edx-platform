"""
Internationalization tasks
"""

import subprocess
import sys

from paver.easy import cmdopts, needs, sh, task

from .utils.envs import Env
from .utils.timer import timed

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

DEFAULT_SETTINGS = Env.DEVSTACK_SETTINGS


@task
@needs(
    "pavelib.prereqs.install_prereqs",
    "pavelib.i18n.i18n_validate_gettext",
)
@cmdopts([
    ("verbose", "v", "Sets 'verbose' to True"),
])
@timed
def i18n_extract(options):
    """
    Extract localizable strings from sources
    """
    verbose = getattr(options, "verbose", None)
    cmd = "i18n_tool extract"

    if verbose:
        cmd += " -v"

    sh(cmd)


@task
@needs("pavelib.i18n.i18n_extract")
@timed
def i18n_generate():
    """
    Compile localizable strings from sources, extracting strings first.
    """
    sh("i18n_tool generate")


@task
@needs("pavelib.i18n.i18n_extract")
@timed
def i18n_generate_strict():
    """
    Compile localizable strings from sources, extracting strings first.
    Complains if files are missing.
    """
    sh("i18n_tool generate --strict")


@task
@needs("pavelib.i18n.i18n_extract")
@timed
def i18n_dummy():
    """
    Simulate international translation by generating dummy strings
    corresponding to source strings.
    """
    sh("i18n_tool dummy")
    # Need to then compile the new dummy strings
    sh("i18n_tool generate")


@task
@timed
def i18n_validate_gettext():
    """
    Make sure GNU gettext utilities are available
    """

    returncode = subprocess.call(['which', 'xgettext'])

    if returncode != 0:
        msg = colorize(
            'red',
            "Cannot locate GNU gettext utilities, which are "
            "required by django for internationalization.\n (see "
            "https://docs.djangoproject.com/en/dev/topics/i18n/"
            "translation/#message-files)\nTry downloading them from "
            "http://www.gnu.org/software/gettext/ \n"
        )

        sys.stderr.write(msg)
        sys.exit(1)


@task
@timed
def i18n_clean():
    """
    Clean the i18n directory of artifacts
    """
    sh('git clean -fdX conf/locale')
