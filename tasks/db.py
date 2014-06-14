from __future__ import print_function
from invoke import task
from invoke import run as sh
try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text
from .utils.cmd import django_cmd


@task('prereqs.install', name="update", help={
    "settings": "Django settings",
    "verbose": "Display verbose output"
})
def update_db(settings='dev', verbose=False):
    """
    Runs syncdb and then migrate.
    """
    hide = None
    if not verbose:
        hide = 'both'

    sh(django_cmd('lms', settings, 'syncdb', '--traceback', '--pythonpath=.'), hide=hide, echo=True)
    sh(django_cmd('lms', settings, 'migrate', '--traceback', '--pythonpath=.'), hide=hide, echo=True)
    print(colorize("green", "DB sucessufully updated"))
