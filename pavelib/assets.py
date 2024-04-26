"""
Asset compilation and collection.
"""

import argparse
import glob
import json
import shlex
import traceback
from functools import wraps
from threading import Timer

from paver import tasks
from paver.easy import call_task, cmdopts, consume_args, needs, no_help, sh, task
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer  # pylint disable=unused-import  # Used by Tutor. Remove after Sumac cut.

from .utils.cmd import cmd, django_cmd
from .utils.envs import Env
from .utils.process import run_background_process
from .utils.timer import timed

# setup baseline paths

ALL_SYSTEMS = ['lms', 'studio']

LMS = 'lms'
CMS = 'cms'

SYSTEMS = {
    'lms': LMS,
    'cms': CMS,
    'studio': CMS
}

# Collectstatic log directory setting
COLLECTSTATIC_LOG_DIR_ARG = 'collect_log_dir'

# Webpack command
WEBPACK_COMMAND = 'STATIC_ROOT_LMS={static_root_lms} STATIC_ROOT_CMS={static_root_cms} webpack {options}'


def debounce(seconds=1):
    """
    Prevents the decorated function from being called more than every `seconds`
    seconds. Waits until calls stop coming in before calling the decorated
    function.
    """
    def decorator(func):
        func.timer = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            def call():
                func(*args, **kwargs)
                func.timer = None
            if func.timer:
                func.timer.cancel()
            func.timer = Timer(seconds, call)
            func.timer.start()

        return wrapper
    return decorator


class SassWatcher(PatternMatchingEventHandler):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    patterns = ['*.scss']

    def register(self, observer, directories):
        """
        register files with observer
        Arguments:
            observer (watchdog.observers.Observer): sass file observer
            directories (list): list of directories to be register for sass watcher.
        """
        for dirname in directories:
            paths = []
            if '*' in dirname:
                paths.extend(glob.glob(dirname))
            else:
                paths.append(dirname)

            for obs_dirname in paths:
                observer.schedule(self, obs_dirname, recursive=True)

    @debounce()
    def on_any_event(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_sass()      # pylint: disable=no-value-for-parameter
        except Exception:       # pylint: disable=broad-except
            traceback.print_exc()


@task
@no_help
@cmdopts([
    ('system=', 's', 'The system to compile sass for (defaults to all)'),
    ('theme-dirs=', '-td', 'Theme dirs containing all themes (defaults to None)'),
    ('themes=', '-t', 'The theme to compile sass for (defaults to None)'),
    ('debug', 'd', 'DEPRECATED. Debug mode is now determined by NODE_ENV.'),
    ('force', '', 'DEPRECATED. Full recompilation is now always forced.'),
])
@timed
def compile_sass(options):
    """
    Compile Sass to CSS. If command is called without any arguments, it will
    only compile lms, cms sass for the open source theme. And none of the comprehensive theme's sass would be compiled.

    If you want to compile sass for all comprehensive themes you will have to run compile_sass
    specifying all the themes that need to be compiled..

    The following is a list of some possible ways to use this command.

    Command:
        paver compile_sass
    Description:
        compile sass files for both lms and cms. If command is called like above (i.e. without any arguments) it will
        only compile lms, cms sass for the open source theme. None of the theme's sass will be compiled.

    Command:
        paver compile_sass --theme-dirs /edx/app/edxapp/edx-platform/themes --themes=red-theme
    Description:
        compile sass files for both lms and cms for 'red-theme' present in '/edx/app/edxapp/edx-platform/themes'

    Command:
        paver compile_sass --theme-dirs=/edx/app/edxapp/edx-platform/themes --themes red-theme stanford-style
    Description:
        compile sass files for both lms and cms for 'red-theme' and 'stanford-style' present in
        '/edx/app/edxapp/edx-platform/themes'.

    Command:
        paver compile_sass --system=cms
            --theme-dirs /edx/app/edxapp/edx-platform/themes /edx/app/edxapp/edx-platform/common/test/
            --themes red-theme stanford-style test-theme
    Description:
        compile sass files for cms only for 'red-theme', 'stanford-style' and 'test-theme' present in
        '/edx/app/edxapp/edx-platform/themes' and '/edx/app/edxapp/edx-platform/common/test/'.

    This is a DEPRECATED COMPATIBILITY WRAPPER. Use `npm run compile-sass` instead.
    """
    systems = set(get_parsed_option(options, 'system', ALL_SYSTEMS))
    command = shlex.join(
        [
            "npm",
            "run",
            "compile-sass",
            "--",
            *(["--dry"] if tasks.environment.dry_run else []),
            *(["--skip-lms"] if not systems & {"lms"} else []),
            *(["--skip-cms"] if not systems & {"cms", "studio"} else []),
            *(
                arg
                for theme_dir in get_parsed_option(options, 'theme_dirs', [])
                for arg in ["--theme-dir", str(theme_dir)]
            ),
            *(
                arg
                for theme in get_parsed_option(options, "theme", [])
                for arg in ["--theme", theme]
            ),
        ]
    )
    depr_warning = (
        "\n" +
        "⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ \n" +
        "\n" +
        "WARNING: 'paver compile_sass' is DEPRECATED! It will be removed before Sumac.\n" +
        "The command you ran is now just a temporary wrapper around a new,\n" +
        "supported command, which you should use instead:\n" +
        "\n" +
        f"\t{command}\n" +
        "\n" +
        "Details: https://github.com/openedx/edx-platform/issues/31895\n" +
        "\n" +
        ("WARNING: ignoring deprecated flag '--debug'\n" if options.get("debug") else "") +
        ("WARNING: ignoring deprecated flag '--force'\n" if options.get("force") else "") +
        "⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ \n" +
        "\n"
    )
    # Print deprecation warning twice so that it's more likely to be seen in the logs.
    print(depr_warning)
    sh(command)
    print(depr_warning)


def _compile_sass(system, theme, _debug, _force, _timing_info):
    """
    This is a DEPRECATED COMPATIBILITY WRAPPER

    It exists to ease the transition for Tutor in Redwood, which directly imported and used this function.
    """
    command = shlex.join(
        [
            "npm",
            "run",
            "compile-sass",
            "--",
            *(["--dry"] if tasks.environment.dry_run else []),
            *(["--skip-default", "--theme-dir", str(theme.parent), "--theme", str(theme.name)] if theme else []),
            ("--skip-cms" if system == "lms" else "--skip-lms"),
        ]
    )
    depr_warning = (
        "\n" +
        "⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ \n" +
        "\n" +
        "WARNING: 'pavelib/assets.py' is DEPRECATED! It will be removed before Sumac.\n" +
        "The function you called is just a temporary wrapper around a new, supported command,\n" +
        "which you should use instead:\n" +
        "\n" +
        f"\t{command}\n" +
        "\n" +
        "Details: https://github.com/openedx/edx-platform/issues/31895\n" +
        "\n" +
        "⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ \n" +
        "\n"
    )
    # Print deprecation warning twice so that it's more likely to be seen in the logs.
    print(depr_warning)
    sh(command)
    print(depr_warning)


def process_npm_assets():
    """
    Process vendor libraries installed via NPM.
    """
    sh('scripts/copy-node-modules.sh')


@task
@no_help
def process_xmodule_assets():
    """
    Process XModule static assets.
    """
    print("\t\tProcessing xmodule assets is no longer needed. This task is now a no-op.")
    print("\t\tWhen paver is removed from edx-platform, this step will not replaced.")


def collect_assets(systems, settings, **kwargs):
    """
    Collect static assets, including Django pipeline processing.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    `**kwargs` include arguments for using a log directory for collectstatic output. Defaults to /dev/null.
    """
    for sys in systems:
        collectstatic_stdout_str = _collect_assets_cmd(sys, **kwargs)
        sh(django_cmd(sys, settings, "collectstatic --noinput {logfile_str}".format(
            logfile_str=collectstatic_stdout_str
        )))
        print(f"\t\tFinished collecting {sys} assets.")


def _collect_assets_cmd(system, **kwargs):
    """
    Returns the collecstatic command to be used for the given system

    Unless specified, collectstatic (which can be verbose) pipes to /dev/null
    """
    try:
        if kwargs[COLLECTSTATIC_LOG_DIR_ARG] is None:
            collectstatic_stdout_str = ""
        else:
            collectstatic_stdout_str = "> {output_dir}/{sys}-collectstatic.log".format(
                output_dir=kwargs[COLLECTSTATIC_LOG_DIR_ARG],
                sys=system
            )
    except KeyError:
        collectstatic_stdout_str = "> /dev/null"

    return collectstatic_stdout_str


def execute_compile_sass(args):
    """
    Construct django management command compile_sass (defined in theming app) and execute it.
    Args:
        args: command line argument passed via update_assets command
    """
    for sys in args.system:
        options = ""
        options += " --theme-dirs " + " ".join(args.theme_dirs) if args.theme_dirs else ""
        options += " --themes " + " ".join(args.themes) if args.themes else ""
        options += " --debug" if args.debug else ""

        sh(
            django_cmd(
                sys,
                args.settings,
                "compile_sass {system} {options}".format(
                    system='cms' if sys == 'studio' else sys,
                    options=options,
                ),
            ),
        )


@task
@cmdopts([
    ('settings=', 's', "Django settings (defaults to devstack)"),
    ('watch', 'w', "Watch file system and rebuild on change (defaults to off)"),
])
@timed
def webpack(options):
    """
    Run a Webpack build.
    """
    settings = getattr(options, 'settings', Env.DEVSTACK_SETTINGS)
    result = Env.get_django_settings(['STATIC_ROOT', 'WEBPACK_CONFIG_PATH'], "lms", settings=settings)
    static_root_lms, config_path = result
    static_root_cms, = Env.get_django_settings(["STATIC_ROOT"], "cms", settings=settings)
    js_env_extra_config_setting, = Env.get_django_json_settings(["JS_ENV_EXTRA_CONFIG"], "cms", settings=settings)
    js_env_extra_config = json.dumps(js_env_extra_config_setting or "{}")
    environment = (
        "NODE_ENV={node_env} STATIC_ROOT_LMS={static_root_lms} STATIC_ROOT_CMS={static_root_cms} "
        "JS_ENV_EXTRA_CONFIG={js_env_extra_config}"
    ).format(
        node_env="development" if config_path == 'webpack.dev.config.js' else "production",
        static_root_lms=static_root_lms,
        static_root_cms=static_root_cms,
        js_env_extra_config=js_env_extra_config,
    )
    sh(
        cmd(
            '{environment} webpack --config={config_path}'.format(
                environment=environment,
                config_path=config_path
            )
        )
    )


def execute_webpack_watch(settings=None):
    """
    Run the Webpack file system watcher.
    """
    # We only want Webpack to re-run on changes to its own entry points,
    # not all JS files, so we use its own watcher instead of subclassing
    # from Watchdog like the other watchers do.

    result = Env.get_django_settings(["STATIC_ROOT", "WEBPACK_CONFIG_PATH"], "lms", settings=settings)
    static_root_lms, config_path = result
    static_root_cms, = Env.get_django_settings(["STATIC_ROOT"], "cms", settings=settings)
    run_background_process(
        'STATIC_ROOT_LMS={static_root_lms} STATIC_ROOT_CMS={static_root_cms} webpack {options}'.format(
            options='--watch --config={config_path}'.format(
                config_path=config_path
            ),
            static_root_lms=static_root_lms,
            static_root_cms=static_root_cms,
        )
    )


def get_parsed_option(command_opts, opt_key, default=None):
    """
    Extract user command option and parse it.
    Arguments:
        command_opts: Command line arguments passed via paver command.
        opt_key: name of option to get and parse
        default: if `command_opt_value` not in `command_opts`, `command_opt_value` will be set to default.
    Returns:
         list or None
    """
    command_opt_value = getattr(command_opts, opt_key, default)
    if command_opt_value:
        command_opt_value = listfy(command_opt_value)

    return command_opt_value


def listfy(data):
    """
    Check and convert data to list.
    Arguments:
        data: data structure to be converted.
    """

    if isinstance(data, str):
        data = data.split(',')
    elif not isinstance(data, list):
        data = [data]

    return data


@task
@cmdopts([
    ('background', 'b', 'DEPRECATED. Use shell tools like & to run in background if needed.'),
    ('settings=', 's', "DEPRECATED. Django is not longer invoked to compile JS/Sass."),
    ('theme-dirs=', '-td', 'The themes dir containing all themes (defaults to None)'),
    ('themes=', '-t', 'DEPRECATED. All themes in --theme-dirs are now watched.'),
    ('wait=', '-w', 'DEPRECATED. Watchdog\'s default wait time is now used.'),
])
@timed
def watch_assets(options):
    """
    Watch for changes to asset files, and regenerate js/css

    This is a DEPRECATED COMPATIBILITY WRAPPER. Use `npm run watch` instead.
    """
    # Don't watch assets when performing a dry run
    if tasks.environment.dry_run:
        return

    theme_dirs = ':'.join(get_parsed_option(options, 'theme_dirs', []))
    command = shlex.join(
        [
            *(
                ["env", f"EDX_PLATFORM_THEME_DIRS={theme_dirs}"] if theme_dirs else []
            ),
            "npm",
            "run",
            "watch",
        ]
    )
    depr_warning = (
        "\n" +
        "⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ \n" +
        "\n" +
        "WARNING: 'paver watch_assets' is DEPRECATED! It will be removed before Sumac.\n" +
        "The command you ran is now just a temporary wrapper around a new,\n" +
        "supported command, which you should use instead:\n" +
        "\n" +
        f"\t{command}\n" +
        "\n" +
        "Details: https://github.com/openedx/edx-platform/issues/31895\n" +
        "\n" +
        ("WARNING: ignoring deprecated flag '--debug'\n" if options.get("debug") else "") +
        ("WARNING: ignoring deprecated flag '--themes'\n" if options.get("themes") else "") +
        ("WARNING: ignoring deprecated flag '--settings'\n" if options.get("settings") else "") +
        ("WARNING: ignoring deprecated flag '--background'\n" if options.get("background") else "") +
        "⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ \n" +
        "\n"
    )
    # Print deprecation warning twice so that it's more likely to be seen in the logs.
    print(depr_warning)
    sh(command)
    print(depr_warning)


@task
@needs(
    'pavelib.prereqs.install_node_prereqs',
    'pavelib.prereqs.install_python_prereqs',
)
@consume_args
@timed
def update_assets(args):
    """
    Compile Sass, then collect static assets.
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument(
        'system', type=str, nargs='*', default=ALL_SYSTEMS,
        help="lms or studio",
    )
    parser.add_argument(
        '--settings', type=str, default=Env.DEVSTACK_SETTINGS,
        help="Django settings module",
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Enable all debugging",
    )
    parser.add_argument(
        '--debug-collect', action='store_true', default=False,
        help="Disable collect static",
    )
    parser.add_argument(
        '--skip-collect', dest='collect', action='store_false', default=True,
        help="Skip collection of static assets",
    )
    parser.add_argument(
        '--watch', action='store_true', default=False,
        help="Watch files for changes",
    )
    parser.add_argument(
        '--theme-dirs', dest='theme_dirs', type=str, nargs='+', default=None,
        help="base directories where themes are placed",
    )
    parser.add_argument(
        '--themes', type=str, nargs='+', default=None,
        help="list of themes to compile sass for",
    )
    parser.add_argument(
        '--collect-log', dest=COLLECTSTATIC_LOG_DIR_ARG, default=None,
        help="When running collectstatic, direct output to specified log directory",
    )
    parser.add_argument(
        '--wait', type=float, default=0.0,
        help="How long to pause between filesystem scans"
    )
    args = parser.parse_args(args)
    collect_log_args = {}

    # Build Webpack
    call_task('pavelib.assets.webpack', options={'settings': args.settings})

    # Compile sass for themes and system
    execute_compile_sass(args)

    if args.collect:
        if args.debug or args.debug_collect:
            collect_log_args.update({COLLECTSTATIC_LOG_DIR_ARG: None})

        if args.collect_log_dir:
            collect_log_args.update({COLLECTSTATIC_LOG_DIR_ARG: args.collect_log_dir})

        collect_assets(args.system, args.settings, **collect_log_args)

    if args.watch:
        call_task(
            'pavelib.assets.watch_assets',
            options={
                'background': not args.debug,
                'settings': args.settings,
                'theme_dirs': args.theme_dirs,
                'themes': args.themes,
                'wait': [float(args.wait)]
            },
        )
