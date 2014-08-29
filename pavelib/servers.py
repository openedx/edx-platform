"""
Run and manage servers for local development.
"""
from __future__ import print_function
import sys
import argparse
from paver.easy import *
from .utils.cmd import django_cmd
from .utils.process import run_process, run_multi_processes


DEFAULT_PORT = {"lms": 8000, "studio": 8001}
DEFAULT_SETTINGS = 'devstack'


def run_server(system, settings=None, port=None, skip_assets=False):
    """
    Start the server for the specified `system` (lms or studio).
    `settings` is the Django settings module to use; if not provided, use the default.
    `port` is the port to run the server on; if not provided, use the default port for the system.

    If `skip_assets` is True, skip the asset compilation step.
    """
    if system not in ['lms', 'studio']:
        print("System must be either lms or studio", file=sys.stderr)
        exit(1)

    if not settings:
        settings = DEFAULT_SETTINGS

    if not skip_assets:
        # Local dev settings use staticfiles to serve assets, so we can skip the collecstatic step
        args = [system, '--settings={}'.format(settings), '--skip-collect', '--watch']
        call_task('pavelib.assets.update_assets', args=args)

    if port is None:
        port = DEFAULT_PORT[system]

    run_process(django_cmd(
        system, settings, 'runserver', '--traceback',
        '--pythonpath=.', '0.0.0.0:{}'.format(port)))


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
    ("port=", "p", "Port"),
    ("fast", "f", "Skip updating assets")
])
def lms(options):
    """
    Run the LMS server.
    """
    settings = getattr(options, 'settings', None)
    port = getattr(options, 'port', None)
    fast = getattr(options, 'fast', False)
    run_server('lms', settings=settings, port=port, skip_assets=fast)


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
    ("port=", "p", "Port"),
    ("fast", "f", "Skip updating assets")
])
def studio(options):
    """
    Run the Studio server.
    """
    settings = getattr(options, 'settings', None)
    port = getattr(options, 'port', None)
    fast = getattr(options, 'fast', False)
    run_server('studio', settings=settings, port=port, skip_assets=fast)


@task
@needs('pavelib.prereqs.install_prereqs')
@consume_args
@no_help
def devstack(args):
    """
    Start the devstack lms or studio server
    """
    parser = argparse.ArgumentParser(prog='paver devstack')
    parser.add_argument('system', type=str, nargs=1, help="lms or studio")
    parser.add_argument('--fast', action='store_true', default=False, help="Skip updating assets")
    args = parser.parse_args(args)
    run_server(args.system[0], settings='devstack', skip_assets=args.fast)


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
])
def celery(options):
    """
    Runs Celery workers.
    """
    settings = getattr(options, 'settings', 'dev_with_worker')
    run_process(django_cmd('lms', settings, 'celery', 'worker', '--loglevel=INFO', '--pythonpath=.'))


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings for both LMS and Studio"),
    ("worker_settings=", "w", "Celery worker Django settings"),
    ("fast", "f", "Skip updating assets"),
    ("settings_lms=", "l", "Set LMS only, overriding the value from --settings (if provided)"),
    ("settings_cms=", "c", "Set Studio only, overriding the value from --settings (if provided)"),
])
def run_all_servers(options):
    """
    Runs Celery workers, Studio, and LMS.
    """
    settings = getattr(options, 'settings', DEFAULT_SETTINGS)
    settings_lms = getattr(options, 'settings_lms', settings)
    settings_cms = getattr(options, 'settings_cms', settings)
    worker_settings = getattr(options, 'worker_settings', 'dev_with_worker')
    fast = getattr(options, 'fast', False)

    if not fast:
        args = ['lms', '--settings={}'.format(settings_lms), '--skip-collect']
        call_task('pavelib.assets.update_assets', args=args)

        args = ['studio', '--settings={}'.format(settings_cms), '--skip-collect']
        call_task('pavelib.assets.update_assets', args=args)

        call_task('pavelib.assets.watch_assets', options={'background': True})
    run_multi_processes([
        django_cmd('lms', settings_lms, 'runserver', '--traceback', '--pythonpath=.', "0.0.0.0:{}".format(DEFAULT_PORT['lms'])),
        django_cmd('studio', settings_cms, 'runserver', '--traceback', '--pythonpath=.', "0.0.0.0:{}".format(DEFAULT_PORT['studio'])),
        django_cmd('lms', worker_settings, 'celery', 'worker', '--loglevel=INFO', '--pythonpath=.')
    ])


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
])
def update_db():
    """
    Runs syncdb and then migrate.
    """
    settings = getattr(options, 'settings', DEFAULT_SETTINGS)
    sh(django_cmd('lms', settings, 'syncdb', '--traceback', '--pythonpath=.'))
    sh(django_cmd('lms', settings, 'migrate', '--traceback', '--pythonpath=.'))


@task
@needs('pavelib.prereqs.install_prereqs')
@consume_args
def check_settings(args):
    """
    Checks settings files.
    """
    parser = argparse.ArgumentParser(prog='paver check_settings')
    parser.add_argument('system', type=str, nargs=1, help="lms or studio")
    parser.add_argument('settings', type=str, nargs=1, help='Django settings')
    args = parser.parse_args(args)

    system = args.system[0]
    settings = args.settings[0]

    try:
        import_cmd = "echo 'import {system}.envs.{settings}'".format(system=system, settings=settings)
        django_shell_cmd = django_cmd(system, settings, 'shell', '--plain', '--pythonpath=.')
        sh("{import_cmd} | {shell_cmd}".format(import_cmd=import_cmd, shell_cmd=django_shell_cmd))

    except:
        print("Failed to import settings", file=sys.stderr)
