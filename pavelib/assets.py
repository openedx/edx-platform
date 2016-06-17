"""
Asset compilation and collection.
"""

from __future__ import print_function
from datetime import datetime
from functools import wraps
from threading import Timer
import argparse
import glob
import traceback

from paver import tasks
from paver.easy import sh, path, task, cmdopts, needs, consume_args, call_task, no_help
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler

from .utils.envs import Env
from .utils.cmd import cmd, django_cmd

from openedx.core.djangoapps.theming.paver_helpers import get_theme_paths

# setup baseline paths

ALL_SYSTEMS = ['lms', 'studio']
COFFEE_DIRS = ['lms', 'cms', 'common']

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
    path('node_modules'),
    path('node_modules/edx-pattern-library/node_modules'),
]

# A list of NPM installed libraries that should be copied into the common
# static directory.
NPM_INSTALLED_LIBRARIES = [
    'jquery/dist/jquery.js',
    'jquery-migrate/dist/jquery-migrate.js',
    'jquery.scrollto/jquery.scrollTo.js',
    'underscore/underscore.js',
    'underscore.string/dist/underscore.string.js',
    'picturefill/dist/picturefill.js',
    'backbone/backbone.js',
    'edx-ui-toolkit/node_modules/backbone.paginator/lib/backbone.paginator.js',
]

# Directory to install static vendor files
NPM_VENDOR_DIRECTORY = path("common/static/common/js/vendor")

# system specific lookup path additions, add sass dirs if one system depends on the sass files for other systems
SASS_LOOKUP_DEPENDENCIES = {
    'cms': [path('lms') / 'static' / 'sass' / 'partials', ],
}

# Collectstatic log directory setting
COLLECTSTATIC_LOG_DIR_ARG = "collect_log_dir"


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
        raise ValueError("'system' must be one of ({allowed_values})".format(allowed_values=', '.join(SYSTEMS.keys())))
    system = SYSTEMS[system]

    applicable_directories = list()

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
    applicable_directories = list()

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
    def decorator(func):  # pylint: disable=missing-docstring
        func.timer = None

        @wraps(func)
        def wrapper(*args, **kwargs):  # pylint: disable=missing-docstring
            def call():  # pylint: disable=missing-docstring
                func(*args, **kwargs)
                func.timer = None
            if func.timer:
                func.timer.cancel()
            func.timer = Timer(seconds, call)
            func.timer.start()

        return wrapper
    return decorator


class CoffeeScriptWatcher(PatternMatchingEventHandler):
    """
    Watches for coffeescript changes
    """
    ignore_directories = True
    patterns = ['*.coffee']

    def register(self, observer):
        """
        register files with observer
        """
        dirnames = set()
        for filename in sh(coffeescript_files(), capture=True).splitlines():
            dirnames.add(path(filename).dirname())
        for dirname in dirnames:
            observer.schedule(self, dirname)

    @debounce()
    def on_any_event(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_coffeescript(event.src_path)
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()


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
            for dirname in paths:
                observer.schedule(self, dirname, recursive=True)

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
        observer.schedule(self, 'common/lib/xmodule/', recursive=True)

    @debounce()
    def on_any_event(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()

        # To refresh the hash values of static xmodule content
        restart_django_servers()


def coffeescript_files():
    """
    return find command for paths containing coffee files
    """
    dirs = " ".join(Env.REPO_ROOT / coffee_dir for coffee_dir in COFFEE_DIRS)
    return cmd('find', dirs, '-type f', '-name \"*.coffee\"')


@task
@no_help
def compile_coffeescript(*files):
    """
    Compile CoffeeScript to JavaScript.
    """
    if not files:
        files = ["`{}`".format(coffeescript_files())]
    sh(cmd(
        "node_modules/.bin/coffee", "--compile", *files
    ))


@task
@no_help
@cmdopts([
    ('system=', 's', 'The system to compile sass for (defaults to all)'),
    ('theme-dirs=', '-td', 'Theme dirs containing all themes (defaults to None)'),
    ('themes=', '-t', 'The theme to compile sass for (defaults to None)'),
    ('debug', 'd', 'Debug mode'),
    ('force', '', 'Force full compilation'),
])
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
    systems = getattr(options, 'system', ALL_SYSTEMS)
    themes = getattr(options, 'themes', [])
    theme_dirs = getattr(options, 'theme-dirs', [])

    if not theme_dirs and themes:
        # We can not compile a theme sass without knowing the directory that contains the theme.
        raise ValueError('theme-dirs must be provided for compiling theme sass.')

    if isinstance(systems, basestring):
        systems = systems.split(',')
    else:
        systems = systems if isinstance(systems, list) else [systems]

    if isinstance(themes, basestring):
        themes = themes.split(',')
    else:
        themes = themes if isinstance(themes, list) else [themes]

    if isinstance(theme_dirs, basestring):
        theme_dirs = theme_dirs.split(',')
    else:
        theme_dirs = theme_dirs if isinstance(theme_dirs, list) else [theme_dirs]

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
            print(">> {} -> {} in {}s".format(sass_dir, css_dir, duration))

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
                dir=sass_dirs, theme=theme or system,
            ))
            # theme doesn't override sass directory, so skip it
            continue

        if force:
            if dry_run:
                tasks.environment.info("rm -rf {css_dir}/*.css".format(
                    css_dir=css_dir,
                ))
            else:
                sh("rm -rf {css_dir}/*.css".format(css_dir=css_dir))

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
            duration = datetime.now() - start
            timing_info.append((sass_source_dir, css_dir, duration))
    return True


def compile_templated_sass(systems, settings):
    """
    Render Mako templates for Sass files.
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    """
    for system in systems:
        if system == "studio":
            system = "cms"
        sh(django_cmd(
            system, settings, 'preprocess_assets',
            '{system}/static/sass/*.scss'.format(system=system),
            '{system}/static/themed_sass'.format(system=system)
        ))
        print("\t\tFinished preprocessing {} assets.".format(system))


def process_npm_assets():
    """
    Process vendor libraries installed via NPM.
    """
    # Skip processing of the libraries if this is just a dry run
    if tasks.environment.dry_run:
        tasks.environment.info("install npm_assets")
        return

    # Ensure that the vendor directory exists
    NPM_VENDOR_DIRECTORY.mkdir_p()

    # Copy each file to the vendor directory, overwriting any existing file.
    for library in NPM_INSTALLED_LIBRARIES:
        sh('/bin/cp -rf node_modules/{library} {vendor_dir}'.format(
            library=library,
            vendor_dir=NPM_VENDOR_DIRECTORY,
        ))


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

    for sys in systems:
        collectstatic_stdout_str = _collect_assets_cmd(sys, **kwargs)
        sh(django_cmd(sys, settings, "collectstatic --noinput {logfile_str}".format(
            logfile_str=collectstatic_stdout_str
        )))
        print("\t\tFinished collecting {} assets.".format(sys))


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
    ('background', 'b', 'Background mode'),
    ('theme-dirs=', '-td', 'The themes dir containing all themes (defaults to None)'),
    ('themes=', '-t', 'The themes to add sass watchers for (defaults to None)'),
])
def watch_assets(options):
    """
    Watch for changes to asset files, and regenerate js/css
    """
    # Don't watch assets when performing a dry run
    if tasks.environment.dry_run:
        return

    themes = getattr(options, 'themes', None)
    theme_dirs = getattr(options, 'theme-dirs', [])

    if not theme_dirs and themes:
        # We can not add theme sass watchers without knowing the directory that contains the themes.
        raise ValueError('theme-dirs must be provided for watching theme sass.')
    else:
        theme_dirs = [path(_dir) for _dir in theme_dirs]

    if isinstance(themes, basestring):
        themes = themes.split(',')
    else:
        themes = themes if isinstance(themes, list) else [themes]

    sass_directories = get_watcher_dirs(theme_dirs, themes)
    observer = PollingObserver()

    CoffeeScriptWatcher().register(observer)
    SassWatcher().register(observer, sass_directories)
    XModuleSassWatcher().register(observer, ['common/lib/xmodule/'])
    XModuleAssetsWatcher().register(observer)

    print("Starting asset watcher...")
    observer.start()
    if not getattr(options, 'background', False):
        # when running as a separate process, the main thread needs to loop
        # in order to allow for shutdown by contrl-c
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
def update_assets(args):
    """
    Compile CoffeeScript and Sass, then collect static assets.
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument(
        'system', type=str, nargs='*', default=ALL_SYSTEMS,
        help="lms or studio",
    )
    parser.add_argument(
        '--settings', type=str, default="devstack",
        help="Django settings module",
    )
    parser.add_argument(
        '--debug', action='store_true', default=False,
        help="Disable Sass compression",
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
    args = parser.parse_args(args)
    collect_log_args = {}

    compile_templated_sass(args.system, args.settings)
    process_xmodule_assets()
    process_npm_assets()
    compile_coffeescript()

    # Compile sass for themes and system
    execute_compile_sass(args)

    if args.collect:
        if args.debug:
            collect_log_args.update({COLLECTSTATIC_LOG_DIR_ARG: None})

        if args.collect_log_dir:
            collect_log_args.update({COLLECTSTATIC_LOG_DIR_ARG: args.collect_log_dir})

        collect_assets(args.system, args.settings, **collect_log_args)

    if args.watch:
        call_task(
            'pavelib.assets.watch_assets',
            options={'background': not args.debug, 'theme-dirs': args.theme_dirs, 'themes': args.themes},
        )
