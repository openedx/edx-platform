"""
Asset compilation and collection.

This entire module is DEPRECATED. In Redwood, it exists just as a collection of temporary compatibility wrappers.
In Sumac, this module will be deleted. To migrate, follow the advice in the printed warnings and/or read the
instructions on the DEPR ticket: https://github.com/openedx/edx-platform/issues/31895
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
from watchdog.observers import Observer  # pylint: disable=unused-import  # Used by Tutor. Remove after Sumac cut.

from .utils.cmd import django_cmd
from .utils.envs import Env
from .utils.timer import timed


SYSTEMS = {
    'lms': 'lms',
    'cms': 'cms',
    'studio': 'cms',
}

WARNING_SYMBOLS = "⚠️ " * 50  # A row of 'warning' emoji to catch CLI users' attention


def run_deprecated_command_wrapper(*, old_command, ignored_old_flags, new_command):
    """
    Run the new version of shell command, plus a warning that the old version is deprecated.
    """
    depr_warning = (
        "\n" +
        f"{WARNING_SYMBOLS}\n" +
        "\n" +
        f"WARNING: '{old_command}' is DEPRECATED! It will be removed before Sumac.\n" +
        "The command you ran is now just a temporary wrapper around a new,\n" +
        "supported command, which you should use instead:\n" +
        "\n" +
        f"\t{new_command}\n" +
        "\n" +
        "Details: https://github.com/openedx/edx-platform/issues/31895\n" +
        "".join(
            f" WARNING: ignored deprecated paver flag '{flag}'\n"
            for flag in ignored_old_flags
        ) +
        f"{WARNING_SYMBOLS}\n" +
        "\n"
    )
    # Print deprecation warning twice so that it's more likely to be seen in the logs.
    print(depr_warning)
    sh(new_command)
    print(depr_warning)


def debounce(seconds=1):
    """
    Prevents the decorated function from being called more than every `seconds`
    seconds. Waits until calls stop coming in before calling the decorated
    function.

    This is DEPRECATED. It exists in Redwood just to ease the transition for Tutor.
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

    This is DEPRECATED. It exists in Redwood just to ease the transition for Tutor.
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
    ('debug', 'd', 'Whether to use development settings'),
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
    systems = [SYSTEMS[sys] for sys in get_parsed_option(options, 'system', ['lms', 'cms'])]  # normalize studio->cms
    run_deprecated_command_wrapper(
        old_command="paver compile_sass",
        ignored_old_flags=(set(["--force"]) & set(options)),
        new_command=shlex.join([
            "npm",
            "run",
            ("compile-sass-dev" if options.get("debug") else "compile-sass"),
            "--",
            *(["--dry"] if tasks.environment.dry_run else []),
            *(["--skip-lms"] if "lms" not in systems else []),
            *(["--skip-cms"] if "cms" not in systems else []),
            *(
                arg
                for theme_dir in get_parsed_option(options, 'theme_dirs', [])
                for arg in ["--theme-dir", str(theme_dir)]
            ),
            *(
                arg
                for theme in get_parsed_option(options, "themes", [])
                for arg in ["--theme", theme]
            ),
        ]),
    )


def _compile_sass(system, theme, debug, force, _timing_info):
    """
    This is a DEPRECATED COMPATIBILITY WRAPPER

    It exists to ease the transition for Tutor in Redwood, which directly imported and used this function.
    """
    run_deprecated_command_wrapper(
        old_command="pavelib.assets:_compile_sass",
        ignored_old_flags=(set(["--force"]) if force else set()),
        new_command=[
            "npm",
            "run",
            ("compile-sass-dev" if debug else "compile-sass"),
            "--",
            *(["--dry"] if tasks.environment.dry_run else []),
            *(
                ["--skip-default", "--theme-dir", str(theme.parent), "--theme", str(theme.name)]
                if theme
                else []
            ),
            ("--skip-cms" if system == "lms" else "--skip-lms"),
        ]
    )


def process_npm_assets():
    """
    Process vendor libraries installed via NPM.

    This is a DEPRECATED COMPATIBILITY WRAPPER. It is now handled as part of `npm clean-install`.
    If you need to invoke it explicitly, you can run `npm run postinstall`.
    """
    run_deprecated_command_wrapper(
        old_command="pavelib.assets:process_npm_assets",
        ignored_old_flags=[],
        new_command=shlex.join(["npm", "run", "postinstall"]),
    )


@task
@no_help
def process_xmodule_assets():
    """
    Process XModule static assets.

    This is a DEPRECATED COMPATIBILITY STUB. Refrences to it should be deleted.
    """
    print(
        "\n" +
        f"{WARNING_SYMBOLS}",
        "\n" +
        "WARNING: 'paver process_xmodule_assets' is DEPRECATED! It will be removed before Sumac.\n" +
        "\n" +
        "Starting with Quince, it is no longer necessary to post-process XModule assets, so \n" +
        "'paver process_xmodule_assets' is a no-op. Please simply remove it from your build scripts.\n" +
        "\n" +
        "Details: https://github.com/openedx/edx-platform/issues/31895\n" +
        f"{WARNING_SYMBOLS}",
    )


def collect_assets(systems, settings, **kwargs):
    """
    Collect static assets, including Django pipeline processing.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    `**kwargs` include arguments for using a log directory for collectstatic output. Defaults to /dev/null.

    This is a DEPRECATED COMPATIBILITY WRAPPER

    It exists to ease the transition for Tutor in Redwood, which directly imported and used this function.
    """
    run_deprecated_command_wrapper(
        old_command="pavelib.asset:collect_assets",
        ignored_old_flags=[],
        new_command=" && ".join(
            "( " +
            shlex.join(
                ["./manage.py", SYSTEMS[sys], f"--settings={settings}", "collectstatic", "--noinput"]
            ) + (
                ""
                if "collect_log_dir" not in kwargs else
                " > /dev/null"
                if kwargs["collect_log_dir"] is None else
                f"> {kwargs['collect_log_dir']}/{SYSTEMS[sys]}-collectstatic.out"
            ) +
            " )"
            for sys in systems
        ),
    )


def execute_compile_sass(args):
    """
    Construct django management command compile_sass (defined in theming app) and execute it.
    Args:
        args: command line argument passed via update_assets command

    This is a DEPRECATED COMPATIBILITY WRAPPER. Use `npm run compile-sass` instead.
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
    ('watch', 'w', "DEPRECATED. This flag never did anything anyway."),
])
@timed
def webpack(options):
    """
    Run a Webpack build.

    This is a DEPRECATED COMPATIBILITY WRAPPER. Use `npm run webpack` instead.
    """
    settings = getattr(options, 'settings', Env.DEVSTACK_SETTINGS)
    result = Env.get_django_settings(['STATIC_ROOT', 'WEBPACK_CONFIG_PATH'], "lms", settings=settings)
    static_root_lms, config_path = result
    static_root_cms, = Env.get_django_settings(["STATIC_ROOT"], "cms", settings=settings)
    js_env_extra_config_setting, = Env.get_django_json_settings(["JS_ENV_EXTRA_CONFIG"], "cms", settings=settings)
    js_env_extra_config = json.dumps(js_env_extra_config_setting or "{}")
    node_env = "development" if config_path == 'webpack.dev.config.js' else "production"
    run_deprecated_command_wrapper(
        old_command="paver webpack",
        ignored_old_flags=(set(["watch"]) & set(options)),
        new_command=' '.join([
            f"WEBPACK_CONFIG_PATH={config_path}",
            f"NODE_ENV={node_env}",
            f"STATIC_ROOT_LMS={static_root_lms}",
            f"STATIC_ROOT_CMS={static_root_cms}",
            f"JS_ENV_EXTRA_CONFIG={js_env_extra_config}",
            "npm",
            "run",
            "webpack",
        ]),
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
    run_deprecated_command_wrapper(
        old_command="paver watch_assets",
        ignored_old_flags=(set(["debug", "themes", "settings", "background"]) & set(options)),
        new_command=shlex.join([
            *(
                ["env", f"COMPREHENSIVE_THEME_DIRS={theme_dirs}"]
                if theme_dirs else []
            ),
            "npm",
            "run",
            "watch",
        ]),
    )


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

    This is a DEPRECATED COMPATIBILITY WRAPPER around other DEPRECATED COMPATIBILITY WRAPPERS.
    The aggregate affect of this command can be achieved with this sequence of commands instead:

    * pip install -r requirements/edx/assets.txt   # replaces install_python_prereqs
    * npm clean-install                            # replaces install_node_prereqs
    * npm run build                                # replaces execute_compile_sass and webpack
    * ./manage.py lms collectstatic --noinput      # replaces collect_assets (for LMS)
    * ./manage.py cms collectstatic --noinput      # replaces collect_assets (for CMS)
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument(
        'system', type=str, nargs='*', default=["lms", "studio"],
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
        help="list of themes to compile sass for. ignored when --watch is used; all themes are watched.",
    )
    parser.add_argument(
        '--collect-log', dest="collect_log_dir", default=None,
        help="When running collectstatic, direct output to specified log directory",
    )
    parser.add_argument(
        '--wait', type=float, default=0.0,
        help="DEPRECATED. Watchdog's default wait time is now used.",
    )
    args = parser.parse_args(args)

    # Build Webpack
    call_task('pavelib.assets.webpack', options={'settings': args.settings})

    # Compile sass for themes and system
    execute_compile_sass(args)

    if args.collect:
        if args.collect_log_dir:
            collect_log_args = {"collect_log_dir": args.collect_log_dir}
        elif args.debug or args.debug_collect:
            collect_log_args = {"collect_log_dir": None}
        else:
            collect_log_args = {}

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
