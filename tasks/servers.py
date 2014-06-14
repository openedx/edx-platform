"""
Run and manage servers for local development.
"""
from __future__ import print_function
import sys
import traceback
from invoke import task, Collection
from invoke import run as sh
try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

from .utils.cmd import django_cmd
from .utils.process import run_process, run_multi_processes

DEFAULT_PORT = {"lms": 8000, "studio": 8001}


def run_server(system, settings="dev", port=0, skip_assets=False):
    """
    Start the server for the specified `system` (lms or cms).
    `settings` is the Django settings module to use; if not provided, use the default.
    `port` is the port to run the server on; if not provided, use the default port for the system.

    If `skip_assets` is True, skip the asset compilation step.
    """
    if system not in ['lms', 'cms']:
        print(colorize("darkred", "System must be either lms or cms", file=sys.stderr))
        exit(1)

    if not skip_assets:
        # Local dev settings use staticfiles to serve assets, so we can skip the collecstatic step
        sh('invoke assets.update --system={system} --settings={settings}'.format(system=system, settings=settings), echo=True)

    if not port:
        port = DEFAULT_PORT[system]

    run_process(django_cmd(
        system, settings, 'runserver', '--traceback',
        '--pythonpath=.', '0.0.0.0:{}'.format(port)))


@task('prereqs.install', help={
    "settings": "Django settings",
    "port": "Port",
    "fast": "Skip updating assets",
})
def lms(settings="dev", port=8000, fast=False):
    """
    Run the LMS server.
    """
    run_server('lms', settings=settings, port=port, skip_assets=fast)


@task('prereqs.install', help={
    "settings": "Django settings",
    "port": "Port",
    "fast": "Skip updating assets",
})
def cms(settings="dev", port=8001, fast=False):
    """
    Run the cms server.
    """
    run_server('cms', settings=settings, port=port, skip_assets=fast)


@task('prereqs.install', positional=("system"), help={
    "system": "lms or cms",
    "fast": "Skip updating assets",
})
def devstack(system, fast=False):
    """
    Start the devstack LMS or CMS server
    """
    if system is None:
        print(colorize("lightgray", "Usage: invoke servers.devstack --system (lms|cms) [--fast]"))
        sys.exit(2)
    run_server(system, settings='devstack', skip_assets=fast)


@task('prereqs.install', help={
    "settings": "Django settings"
})
def celery(settings="dev_with_worker"):
    """
    Runs Celery workers.
    """
    run_process(django_cmd('lms', settings, 'celery', 'worker', '--loglevel=INFO', '--pythonpath=.'))


@task('prereqs.install', default=True, help={
    "settings":        "Django settings",
    "worker_settings": "Celery worker Django settings",
    "fast":            "Skip updating assets",
})
def run(settings="dev", worker_settings='dev_with_worker', fast=False):
    """
    Runs Celery workers, CMS and LMS.
    """
    if not fast:
        # This is annoying: invoke does not support calling
        # tasks within tasks...

        sh('invoke assets.update --settings={settings} --skip-collect'.format(settings=settings), hide='both', echo=True)
        sh('invoke assets.watch --background', hide='both', echo=True)
    run_multi_processes([
        django_cmd('lms', settings, 'runserver', '--traceback', '--pythonpath=.', "0.0.0.0:{}".format(DEFAULT_PORT['lms'])),
        django_cmd('studio', settings, 'runserver', '--traceback', '--pythonpath=.', "0.0.0.0:{}".format(DEFAULT_PORT['studio'])),
        django_cmd('lms', worker_settings, 'celery', 'worker', '--loglevel=INFO', '--pythonpath=.')
    ])


@task('prereqs.install', help={
    'system': "lms or cms",
    'settings': "Django settings",
})
def check_settings(system=None, settings=None):
    """
    Checks settings files.
    """
    if system is None or settings is None:
        print(colorize("lightgray",
'''Usage:
    invoke servers.check_settings --system (lms|cms) --settings <settings>
'''))
        print("Too few arguments")
        sys.exit(2)

    try:
        import_cmd = "echo 'import {system}.envs.{settings}'".format(system=system, settings=settings)
        django_shell_cmd = django_cmd(system, settings, 'shell', '--plain', '--pythonpath=.')
        sh("{import_cmd} | {shell_cmd}".format(import_cmd=import_cmd, shell_cmd=django_shell_cmd), hide='both')
        print(colorize("green", "{system} settings for {settings} are ok.".format(system=system, settings=settings)))
    except Exception as exc:
        traceback.print_exc()
        print(colorize("darkred", "Failed to import settings", file=sys.stderr))
