"""
Run and manage servers for local development.
"""
from __future__ import print_function
import argparse
import sys

from paver.easy import call_task, cmdopts, consume_args, needs, sh, task

from .assets import collect_assets
from .utils.cmd import django_cmd
from .utils.process import run_process, run_multi_processes


DEFAULT_PORT = {"lms": 8000, "studio": 8001}
DEFAULT_SETTINGS = 'devstack'
OPTIMIZED_SETTINGS = "devstack_optimized"
OPTIMIZED_ASSETS_SETTINGS = "test_static_optimized"

ASSET_SETTINGS_HELP = (
    "Settings file used for updating assets. Defaults to the value of the settings variable if not provided."
)


def run_server(
        system, fast=False, settings=None, asset_settings=None, port=None, contracts=False
):
    """Start the server for LMS or Studio.

    Args:
        system (str): The system to be run (lms or studio).
        fast (bool): If true, then start the server immediately without updating assets (defaults to False).
        settings (str): The Django settings module to use; if not provided, use the default.
        asset_settings (str) The settings to use when generating assets. If not provided, assets are not generated.
        port (str): The port number to run the server on. If not provided, uses the default port for the system.
        contracts (bool) If true then PyContracts is enabled (defaults to False).
    """
    if system not in ['lms', 'studio']:
        print("System must be either lms or studio", file=sys.stderr)
        exit(1)

    if not settings:
        settings = DEFAULT_SETTINGS

    if not fast and asset_settings:
        args = [system, '--settings={}'.format(asset_settings), '--watch']
        # The default settings use DEBUG mode for running the server which means that
        # the optimized assets are ignored, so we skip collectstatic in that case
        # to save time.
        if settings == DEFAULT_SETTINGS:
            args.append('--skip-collect')
        call_task('pavelib.assets.update_assets', args=args)

    if port is None:
        port = DEFAULT_PORT[system]

    args = [settings, 'runserver', '--traceback', '--pythonpath=.', '0.0.0.0:{}'.format(port)]

    if contracts:
        args.append("--contracts")

    run_process(django_cmd(system, *args))


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
    ("asset-settings=", "a", ASSET_SETTINGS_HELP),
    ("port=", "p", "Port"),
    ("fast", "f", "Skip updating assets"),
])
def lms(options):
    """
    Run the LMS server.
    """
    settings = getattr(options, 'settings', DEFAULT_SETTINGS)
    asset_settings = getattr(options, 'asset-settings', settings)
    port = getattr(options, 'port', None)
    fast = getattr(options, 'fast', False)
    run_server(
        'lms',
        fast=fast,
        settings=settings,
        asset_settings=asset_settings,
        port=port,
    )


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
    ("asset-settings=", "a", ASSET_SETTINGS_HELP),
    ("port=", "p", "Port"),
    ("fast", "f", "Skip updating assets"),
])
def studio(options):
    """
    Run the Studio server.
    """
    settings = getattr(options, 'settings', DEFAULT_SETTINGS)
    asset_settings = getattr(options, 'asset-settings', settings)
    port = getattr(options, 'port', None)
    fast = getattr(options, 'fast', False)
    run_server(
        'studio',
        fast=fast,
        settings=settings,
        asset_settings=asset_settings,
        port=port,
    )


@task
@needs('pavelib.prereqs.install_prereqs')
@consume_args
def devstack(args):
    """
    Start the devstack lms or studio server
    """
    parser = argparse.ArgumentParser(prog='paver devstack')
    parser.add_argument('system', type=str, nargs=1, help="lms or studio")
    parser.add_argument('--fast', action='store_true', default=False, help="Skip updating assets")
    parser.add_argument('--optimized', action='store_true', default=False, help="Run with optimized assets")
    parser.add_argument('--settings', type=str, default=DEFAULT_SETTINGS, help="Settings file")
    parser.add_argument('--asset-settings', type=str, default=None, help=ASSET_SETTINGS_HELP)
    parser.add_argument(
        '--no-contracts',
        action='store_true',
        default=False,
        help="Disable contracts. By default, they're enabled in devstack."
    )
    args = parser.parse_args(args)
    settings = args.settings
    asset_settings = args.asset_settings if args.asset_settings else settings
    if args.optimized:
        settings = OPTIMIZED_SETTINGS
        asset_settings = OPTIMIZED_ASSETS_SETTINGS
    sh(django_cmd('cms', settings, 'reindex_course', '--setup'))
    run_server(
        args.system[0],
        fast=args.fast,
        settings=settings,
        asset_settings=asset_settings,
        contracts=not args.no_contracts,
    )

@task
@needs('pavelib.prereqs.install_prereqs')
@consume_args
def devstack_appsembler(args):
    """
    Start the devstack lms or studio server
    """
    parser = argparse.ArgumentParser(prog='paver devstack_appsembler')
    parser.add_argument('system', type=str, nargs=1, help="lms or studio")
    parser.add_argument('--fast', action='store_true', default=False, help="Skip updating assets")
    args = parser.parse_args(args)
    run_server(args.system[0], settings='devstack_appsembler', skip_assets=args.fast)

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
    run_process(django_cmd('lms', settings, 'celery', 'worker', '--beat', '--loglevel=INFO', '--pythonpath=.'))


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings for both LMS and Studio"),
    ("asset_settings=", "a", "Django settings for updating assets for both LMS and Studio (defaults to settings)"),
    ("worker_settings=", "w", "Celery worker Django settings"),
    ("fast", "f", "Skip updating assets"),
    ("optimized", "o", "Run with optimized assets"),
    ("settings_lms=", "l", "Set LMS only, overriding the value from --settings (if provided)"),
    ("asset_settings_lms=", None, "Set LMS only, overriding the value from --asset_settings (if provided)"),
    ("settings_cms=", "c", "Set Studio only, overriding the value from --settings (if provided)"),
    ("asset_settings_cms=", None, "Set Studio only, overriding the value from --asset_settings (if provided)"),
])
def run_all_servers(options):
    """
    Runs Celery workers, Studio, and LMS.
    """
    settings = getattr(options, 'settings', DEFAULT_SETTINGS)
    asset_settings = getattr(options, 'asset_settings', settings)
    worker_settings = getattr(options, 'worker_settings', 'dev_with_worker')
    fast = getattr(options, 'fast', False)
    optimized = getattr(options, 'optimized', False)

    if optimized:
        settings = OPTIMIZED_SETTINGS
        asset_settings = OPTIMIZED_ASSETS_SETTINGS

    settings_lms = getattr(options, 'settings_lms', settings)
    settings_cms = getattr(options, 'settings_cms', settings)
    asset_settings_lms = getattr(options, 'asset_settings_lms', asset_settings)
    asset_settings_cms = getattr(options, 'asset_settings_cms', asset_settings)

    if not fast:
        # First update assets for both LMS and Studio but don't collect static yet
        args = [
            'lms', 'studio',
            '--settings={}'.format(asset_settings),
            '--skip-collect'
        ]
        call_task('pavelib.assets.update_assets', args=args)

        # Now collect static for each system separately with the appropriate settings.
        # Note that the default settings use DEBUG mode for running the server which
        # means that the optimized assets are ignored, so we skip collectstatic in that
        # case to save time.
        if settings != DEFAULT_SETTINGS:
            collect_assets(['lms'], asset_settings_lms)
            collect_assets(['studio'], asset_settings_cms)

        # Install an asset watcher to regenerate files that change
        call_task('pavelib.assets.watch_assets', options={'background': True})

    # Start up LMS, CMS and Celery
    lms_port = DEFAULT_PORT['lms']
    cms_port = DEFAULT_PORT['studio']
    lms_runserver_args = ["0.0.0.0:{}".format(lms_port)]
    cms_runserver_args = ["0.0.0.0:{}".format(cms_port)]

    run_multi_processes([
        django_cmd(
            'lms', settings_lms, 'runserver', '--traceback', '--pythonpath=.', *lms_runserver_args
        ),
        django_cmd(
            'studio', settings_cms, 'runserver', '--traceback', '--pythonpath=.', *cms_runserver_args
        ),
        django_cmd(
            'lms', worker_settings, 'celery', 'worker', '--beat', '--loglevel=INFO', '--pythonpath=.'
        )
    ])


@task
@needs('pavelib.prereqs.install_prereqs')
@cmdopts([
    ("settings=", "s", "Django settings"),
    ("fake-initial", None, "Fake the initial migrations"),
])
def update_db(options):
    """
    Runs syncdb and then migrate.
    """
    settings = getattr(options, 'settings', DEFAULT_SETTINGS)
    fake = "--fake-initial" if getattr(options, 'fake_initial', False) else ""
    for system in ('lms', 'cms'):
        sh(django_cmd(system, settings, 'migrate', fake, '--traceback', '--pythonpath=.'))


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

    except:  # pylint: disable=bare-except
        print("Failed to import settings", file=sys.stderr)
