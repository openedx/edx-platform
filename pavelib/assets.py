"""
Asset compilation and collection.
"""


import argparse
import glob
import json
import os
import traceback
from datetime import datetime
from functools import wraps
from threading import Timer

from paver import tasks
from paver.easy import call_task, cmdopts, consume_args, needs, no_help, path, sh, task
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.api import DEFAULT_OBSERVER_TIMEOUT

from openedx.core.djangoapps.theming.paver_helpers import get_theme_paths

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

# Common lookup paths that are added to the lookup paths for all sass compilations
COMMON_LOOKUP_PATHS = [
    path("common/static"),
    path("common/static/sass"),
    path('node_modules/@edx'),
    path('node_modules'),
]

# A list of NPM installed libraries that should be copied into the common
# static directory.
# If string ends with '/' then all file in the directory will be copied.
NPM_INSTALLED_LIBRARIES = [
    'backbone.paginator/lib/backbone.paginator.js',
    'backbone/backbone.js',
    'bootstrap/dist/js/bootstrap.bundle.js',
    'hls.js/dist/hls.js',
    'jquery-migrate/dist/jquery-migrate.js',
    'jquery.scrollto/jquery.scrollTo.js',
    'jquery/dist/jquery.js',
    'moment-timezone/builds/moment-timezone-with-data.js',
    'moment/min/moment-with-locales.js',
    'picturefill/dist/picturefill.js',
    'requirejs/require.js',
    'underscore.string/dist/underscore.string.js',
    'underscore/underscore.js',
    '@edx/studio-frontend/dist/',
    'which-country/index.js'
]

# A list of NPM installed developer libraries that should be copied into the common
# static directory only in development mode.
NPM_INSTALLED_DEVELOPER_LIBRARIES = [
    'sinon/pkg/sinon.js',
    'squirejs/src/Squire.js',
]

# Directory to install static vendor files
NPM_JS_VENDOR_DIRECTORY = path('common/static/common/js/vendor')
NPM_CSS_VENDOR_DIRECTORY = path("common/static/common/css/vendor")
NPM_CSS_DIRECTORY = path("common/static/common/css")

# system specific lookup path additions, add sass dirs if one system depends on the sass files for other systems
SASS_LOOKUP_DEPENDENCIES = {
    'cms': [path('lms') / 'static' / 'sass' / 'partials', ],
}

# Collectstatic log directory setting
COLLECTSTATIC_LOG_DIR_ARG = 'collect_log_dir'

# Webpack command
WEBPACK_COMMAND = 'STATIC_ROOT_LMS={static_root_lms} STATIC_ROOT_CMS={static_root_cms} $(npm bin)/webpack {options}'


def get_sass_directories(system, theme_dir=None):
    """
    Determine the set of SASS directories to be compiled for the specified list of system and theme
    and return a list of those directories.

    Each item in the list is dict object containing the following key-value pairs.
    {
        "sass_source_dir": "",  # directory where source sass files are present
        "css_destination_dir": "",  # destination where css files would be placed
        "lookup_paths": [],  # list of directories to be passed as lookup paths for @import resolution.
    }

    if theme_dir is empty or None then return sass directories for the given system only. (i.e. lms or cms)

    :param system: name if the system for which to compile sass e.g. 'lms', 'cms'
    :param theme_dir: absolute path of theme for which to compile sass files.
    """
    if system not in SYSTEMS:
        raise ValueError("'system' must be one of ({allowed_values})".format(
            allowed_values=', '.join(list(SYSTEMS.keys())))
        )
    system = SYSTEMS[system]

    applicable_directories = []

    if theme_dir:
        # Add theme sass directories
        applicable_directories.extend(
            get_theme_sass_dirs(system, theme_dir)
        )
    else:
        # add system sass directories
        applicable_directories.extend(
            get_system_sass_dirs(system)
        )

    return applicable_directories


def get_common_sass_directories():
    """
    Determine the set of common SASS directories to be compiled for all the systems and themes.

    Each item in the returned list is dict object containing the following key-value pairs.
    {
        "sass_source_dir": "",  # directory where source sass files are present
        "css_destination_dir": "",  # destination where css files would be placed
        "lookup_paths": [],  # list of directories to be passed as lookup paths for @import resolution.
    }
    """
    applicable_directories = []

    # add common sass directories
    applicable_directories.append({
        "sass_source_dir": path("common/static/sass"),
        "css_destination_dir": path("common/static/css"),
        "lookup_paths": COMMON_LOOKUP_PATHS,
    })

    return applicable_directories


def get_theme_sass_dirs(system, theme_dir):
    """
    Return list of sass dirs that need to be compiled for the given theme.

    :param system: name if the system for which to compile sass e.g. 'lms', 'cms'
    :param theme_dir: absolute path of theme for which to compile sass files.
    """
    if system not in ('lms', 'cms'):
        raise ValueError('"system" must either be "lms" or "cms"')

    dirs = []

    system_sass_dir = path(system) / "static" / "sass"
    sass_dir = theme_dir / system / "static" / "sass"
    css_dir = theme_dir / system / "static" / "css"
    certs_sass_dir = theme_dir / system / "static" / "certificates" / "sass"
    certs_css_dir = theme_dir / system / "static" / "certificates" / "css"

    dependencies = SASS_LOOKUP_DEPENDENCIES.get(system, [])
    if sass_dir.isdir():
        css_dir.mkdir_p()

        # first compile lms sass files and place css in theme dir
        dirs.append({
            "sass_source_dir": system_sass_dir,
            "css_destination_dir": css_dir,
            "lookup_paths": dependencies + [
                sass_dir / "partials",
                system_sass_dir / "partials",
                system_sass_dir,
            ],
        })

        # now compile theme sass files and override css files generated from lms
        dirs.append({
            "sass_source_dir": sass_dir,
            "css_destination_dir": css_dir,
            "lookup_paths": dependencies + [
                sass_dir / "partials",
                system_sass_dir / "partials",
                system_sass_dir,
            ],
        })

        # now compile theme sass files for certificate
        if system == 'lms':
            dirs.append({
                "sass_source_dir": certs_sass_dir,
                "css_destination_dir": certs_css_dir,
                "lookup_paths": [
                    sass_dir / "partials",
                    sass_dir
                ],
            })

    return dirs


def get_system_sass_dirs(system):
    """
    Return list of sass dirs that need to be compiled for the given system.

    :param system: name if the system for which to compile sass e.g. 'lms', 'cms'
    """
    if system not in ('lms', 'cms'):
        raise ValueError('"system" must either be "lms" or "cms"')

    dirs = []
    sass_dir = path(system) / "static" / "sass"
    css_dir = path(system) / "static" / "css"

    dependencies = SASS_LOOKUP_DEPENDENCIES.get(system, [])
    dirs.append({
        "sass_source_dir": sass_dir,
        "css_destination_dir": css_dir,
        "lookup_paths": dependencies + [
            sass_dir / "partials",
            sass_dir,
        ],
    })

    if system == 'lms':
        dirs.append({
            "sass_source_dir": path(system) / "static" / "certificates" / "sass",
            "css_destination_dir": path(system) / "static" / "certificates" / "css",
            "lookup_paths": [
                sass_dir / "partials",
                sass_dir
            ],
        })

    return dirs


def get_watcher_dirs(theme_dirs=None, themes=None):
    """
    Return sass directories that need to be added to sass watcher.

    Example:
        >> get_watcher_dirs('/edx/app/edx-platform/themes', ['red-theme'])
        [
            'common/static',
            'common/static/sass',
            'lms/static/sass',
            'lms/static/sass/partials',
            '/edx/app/edxapp/edx-platform/themes/red-theme/lms/static/sass',
            '/edx/app/edxapp/edx-platform/themes/red-theme/lms/static/sass/partials',
            'cms/static/sass',
            'cms/static/sass/partials',
            '/edx/app/edxapp/edx-platform/themes/red-theme/cms/static/sass/partials',
        ]

    Parameters:
        theme_dirs (list): list of theme base directories.
        themes (list): list containing names of themes
    Returns:
        (list): dirs that need to be added to sass watchers.
    """
    dirs = []
    dirs.extend(COMMON_LOOKUP_PATHS)
    if theme_dirs and themes:
        # Register sass watchers for all the given themes
        themes = get_theme_paths(themes=themes, theme_dirs=theme_dirs)
        for theme in themes:
            for _dir in get_sass_directories('lms', theme) + get_sass_directories('cms', theme):
                dirs.append(_dir['sass_source_dir'])
                dirs.extend(_dir['lookup_paths'])

    # Register sass watchers for lms and cms
    for _dir in get_sass_directories('lms') + get_sass_directories('cms') + get_common_sass_directories():
        dirs.append(_dir['sass_source_dir'])
        dirs.extend(_dir['lookup_paths'])

    # remove duplicates
    dirs = list(set(dirs))
    return dirs


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
    ignore_patterns = ['common/static/xmodule/*']

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


class XModuleSassWatcher(SassWatcher):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    ignore_patterns = []

    @debounce()
    def on_any_event(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()


class XModuleAssetsWatcher(PatternMatchingEventHandler):
    """
    Watches for css and js file changes
    """
    ignore_directories = True
    patterns = ['*.css', '*.js']

    def register(self, observer):
        """
        Register files with observer
        """
        observer.schedule(self, 'xmodule/', recursive=True)

    @debounce()
    def on_any_event(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()

        # To refresh the hash values of static xmodule content
        restart_django_servers()


@task
@no_help
@cmdopts([
    ('system=', 's', 'The system to compile sass for (defaults to all)'),
    ('theme-dirs=', '-td', 'Theme dirs containing all themes (defaults to None)'),
    ('themes=', '-t', 'The theme to compile sass for (defaults to None)'),
    ('debug', 'd', 'Debug mode'),
    ('force', '', 'Force full compilation'),
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

    """
    debug = options.get('debug')
    force = options.get('force')
    systems = get_parsed_option(options, 'system', ALL_SYSTEMS)
    themes = get_parsed_option(options, 'themes', [])
    theme_dirs = get_parsed_option(options, 'theme_dirs', [])

    if not theme_dirs and themes:
        # We can not compile a theme sass without knowing the directory that contains the theme.
        raise ValueError('theme-dirs must be provided for compiling theme sass.')

    if themes and theme_dirs:
        themes = get_theme_paths(themes=themes, theme_dirs=theme_dirs)

    # Compile sass for OpenEdx theme after comprehensive themes
    if None not in themes:
        themes.append(None)

    timing_info = []
    dry_run = tasks.environment.dry_run
    compilation_results = {'success': [], 'failure': []}

    print("\t\tStarted compiling Sass:")

    # compile common sass files
    is_successful = _compile_sass('common', None, debug, force, timing_info)
    if is_successful:
        print("Finished compiling 'common' sass.")
    compilation_results['success' if is_successful else 'failure'].append('"common" sass files.')

    for system in systems:
        for theme in themes:
            print("Started compiling '{system}' Sass for '{theme}'.".format(system=system, theme=theme or 'system'))

            # Compile sass files
            is_successful = _compile_sass(
                system=system,
                theme=path(theme) if theme else None,
                debug=debug,
                force=force,
                timing_info=timing_info
            )

            if is_successful:
                print("Finished compiling '{system}' Sass for '{theme}'.".format(
                    system=system, theme=theme or 'system'
                ))

            compilation_results['success' if is_successful else 'failure'].append('{system} sass for {theme}.'.format(
                system=system, theme=theme or 'system',
            ))

    print("\t\tFinished compiling Sass:")
    if not dry_run:
        for sass_dir, css_dir, duration in timing_info:
            print(f">> {sass_dir} -> {css_dir} in {duration}s")

    if compilation_results['success']:
        print("\033[92m\nSuccessful compilations:\n--- " + "\n--- ".join(compilation_results['success']) + "\n\033[00m")
    if compilation_results['failure']:
        print("\033[91m\nFailed compilations:\n--- " + "\n--- ".join(compilation_results['failure']) + "\n\033[00m")


def _compile_sass(system, theme, debug, force, timing_info):
    """
    Compile sass files for the given system and theme.

    :param system: system to compile sass for e.g. 'lms', 'cms', 'common'
    :param theme: absolute path of the theme to compile sass for.
    :param debug: boolean showing whether to display source comments in resulted css
    :param force: boolean showing whether to remove existing css files before generating new files
    :param timing_info: list variable to keep track of timing for sass compilation
    """

    # Note: import sass only when it is needed and not at the top of the file.
    # This allows other paver commands to operate even without libsass being
    # installed. In particular, this allows the install_prereqs command to be
    # used to install the dependency.
    import sass
    if system == "common":
        sass_dirs = get_common_sass_directories()
    else:
        sass_dirs = get_sass_directories(system, theme)

    dry_run = tasks.environment.dry_run

    # determine css out put style and source comments enabling
    if debug:
        source_comments = True
        output_style = 'nested'
    else:
        source_comments = False
        output_style = 'compressed'

    for dirs in sass_dirs:
        start = datetime.now()
        css_dir = dirs['css_destination_dir']
        sass_source_dir = dirs['sass_source_dir']
        lookup_paths = dirs['lookup_paths']

        if not sass_source_dir.isdir():
            print("\033[91m Sass dir '{dir}' does not exists, skipping sass compilation for '{theme}' \033[00m".format(
                dir=sass_source_dir, theme=theme or system,
            ))
            # theme doesn't override sass directory, so skip it
            continue

        if force:
            if dry_run:
                tasks.environment.info("rm -rf {css_dir}/*.css".format(
                    css_dir=css_dir,
                ))
            else:
                sh(f"rm -rf {css_dir}/*.css")

        if dry_run:
            tasks.environment.info("libsass {sass_dir}".format(
                sass_dir=sass_source_dir,
            ))
        else:
            sass.compile(
                dirname=(sass_source_dir, css_dir),
                include_paths=COMMON_LOOKUP_PATHS + lookup_paths,
                source_comments=source_comments,
                output_style=output_style,
            )

        # For Sass files without explicit RTL versions, generate
        # an RTL version of the CSS using the rtlcss library.
        for sass_file in glob.glob(sass_source_dir + '/**/*.scss'):
            if should_generate_rtl_css_file(sass_file):
                source_css_file = sass_file.replace(sass_source_dir, css_dir).replace('.scss', '.css')
                target_css_file = source_css_file.replace('.css', '-rtl.css')
                sh("rtlcss {source_file} {target_file}".format(
                    source_file=source_css_file,
                    target_file=target_css_file,
                ))

        # Capture the time taken
        if not dry_run:
            duration = datetime.now() - start
            timing_info.append((sass_source_dir, css_dir, duration))
    return True


def should_generate_rtl_css_file(sass_file):
    """
    Returns true if a Sass file should have an RTL version generated.
    """
    # Don't generate RTL CSS for partials
    if path(sass_file).name.startswith('_'):
        return False

    # Don't generate RTL CSS if the file is itself an RTL version
    if sass_file.endswith('-rtl.scss'):
        return False

    # Don't generate RTL CSS if there is an explicit Sass version for RTL
    rtl_sass_file = path(sass_file.replace('.scss', '-rtl.scss'))
    if rtl_sass_file.exists():
        return False

    return True


def process_npm_assets():
    """
    Process vendor libraries installed via NPM.
    """
    def copy_vendor_library(library, skip_if_missing=False):
        """
        Copies a vendor library to the shared vendor directory.
        """
        if library.startswith('node_modules/'):
            library_path = library
        else:
            library_path = f'node_modules/{library}'

        if library.endswith('.css') or library.endswith('.css.map'):
            vendor_dir = NPM_CSS_VENDOR_DIRECTORY
        else:
            vendor_dir = NPM_JS_VENDOR_DIRECTORY
        if os.path.exists(library_path):
            sh('/bin/cp -rf {library_path} {vendor_dir}'.format(
                library_path=library_path,
                vendor_dir=vendor_dir,
            ))
        elif not skip_if_missing:
            raise Exception(f'Missing vendor file {library_path}')

    def copy_vendor_library_dir(library_dir, skip_if_missing=False):
        """
        Copies all vendor libraries in directory to the shared vendor directory.
        """
        library_dir_path = f'node_modules/{library_dir}'
        print(f'Copying vendor library dir: {library_dir_path}')
        if os.path.exists(library_dir_path):
            for dirpath, _, filenames in os.walk(library_dir_path):
                for filename in filenames:
                    copy_vendor_library(os.path.join(dirpath, filename), skip_if_missing=skip_if_missing)

    # Skip processing of the libraries if this is just a dry run
    if tasks.environment.dry_run:
        tasks.environment.info("install npm_assets")
        return

    # Ensure that the vendor directory exists
    NPM_JS_VENDOR_DIRECTORY.mkdir_p()
    NPM_CSS_DIRECTORY.mkdir_p()
    NPM_CSS_VENDOR_DIRECTORY.mkdir_p()

    # Copy each file to the vendor directory, overwriting any existing file.
    print("Copying vendor files into static directory")
    for library in NPM_INSTALLED_LIBRARIES:
        if library.endswith('/'):
            copy_vendor_library_dir(library)
        else:
            copy_vendor_library(library)

    # Copy over each developer library too if they have been installed
    print("Copying developer vendor files into static directory")
    for library in NPM_INSTALLED_DEVELOPER_LIBRARIES:
        copy_vendor_library(library, skip_if_missing=True)


@task
@needs(
    'pavelib.prereqs.install_python_prereqs',
)
@no_help
def process_xmodule_assets():
    """
    Process XModule static assets.
    """
    sh('xmodule_assets common/static/xmodule')
    print("\t\tFinished processing xmodule assets.")


def restart_django_servers():
    """
    Restart the django server.

    `$ touch` makes the Django file watcher thinks that something has changed, therefore
    it restarts the server.
    """
    sh(cmd(
        "touch", 'lms/urls.py', 'cms/urls.py',
    ))


def collect_assets(systems, settings, **kwargs):
    """
    Collect static assets, including Django pipeline processing.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    `**kwargs` include arguments for using a log directory for collectstatic output. Defaults to /dev/null.
    """
    ignore_patterns = [
        # Karma test related files...
        "fixtures",
        "karma_*.js",
        "spec",
        "spec_helpers",
        "spec-helpers",
        "xmodule_js",  # symlink for tests

        # Geo-IP data, only accessed in Python
        "geoip",

        # We compile these out, don't need the source files in staticfiles
        "sass",
    ]

    ignore_args = " ".join(
        f'--ignore "{pattern}"' for pattern in ignore_patterns
    )

    for sys in systems:
        collectstatic_stdout_str = _collect_assets_cmd(sys, **kwargs)
        sh(django_cmd(sys, settings, "collectstatic {ignore_args} --noinput {logfile_str}".format(
            ignore_args=ignore_args,
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
            '{environment} $(npm bin)/webpack --config={config_path}'.format(
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
        'STATIC_ROOT_LMS={static_root_lms} STATIC_ROOT_CMS={static_root_cms} $(npm bin)/webpack {options}'.format(
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
    ('background', 'b', 'Background mode'),
    ('settings=', 's', "Django settings (defaults to devstack)"),
    ('theme-dirs=', '-td', 'The themes dir containing all themes (defaults to None)'),
    ('themes=', '-t', 'The themes to add sass watchers for (defaults to None)'),
    ('wait=', '-w', 'How long to pause between filesystem scans.')
])
@timed
def watch_assets(options):
    """
    Watch for changes to asset files, and regenerate js/css
    """
    # Don't watch assets when performing a dry run
    if tasks.environment.dry_run:
        return

    settings = getattr(options, 'settings', Env.DEVSTACK_SETTINGS)

    themes = get_parsed_option(options, 'themes')
    theme_dirs = get_parsed_option(options, 'theme_dirs', [])

    default_wait = [str(DEFAULT_OBSERVER_TIMEOUT)]
    wait = float(get_parsed_option(options, 'wait', default_wait)[0])

    if not theme_dirs and themes:  # lint-amnesty, pylint: disable=no-else-raise
        # We can not add theme sass watchers without knowing the directory that contains the themes.
        raise ValueError('theme-dirs must be provided for watching theme sass.')
    else:
        theme_dirs = [path(_dir) for _dir in theme_dirs]

    sass_directories = get_watcher_dirs(theme_dirs, themes)
    observer = Observer(timeout=wait)

    SassWatcher().register(observer, sass_directories)
    XModuleSassWatcher().register(observer, ['xmodule/'])
    XModuleAssetsWatcher().register(observer)

    print("Starting asset watcher...")
    observer.start()

    # Run the Webpack file system watcher too
    execute_webpack_watch(settings=settings)

    if not getattr(options, 'background', False):
        # when running as a separate process, the main thread needs to loop
        # in order to allow for shutdown by control-c
        try:
            while True:
                observer.join(2)
        except KeyboardInterrupt:
            observer.stop()
        print("\nStopped asset watcher.")


@task
@needs(
    'pavelib.prereqs.install_node_prereqs',
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

    process_xmodule_assets()
    process_npm_assets()

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
