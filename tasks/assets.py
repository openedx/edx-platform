"""
Asset compilation and collection.
"""
from __future__ import print_function
from invoke import task
from invoke import run as sh
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import glob
import traceback
from path import path
from .utils.envs import Env
from .utils.cmd import cmd, django_cmd

COFFEE_DIRS = ['lms', 'cms', 'common']
SASS_LOAD_PATHS = ['./common/static/sass']
SASS_UPDATE_DIRS = ['*/static']
SASS_CACHE_PATH = '/tmp/sass-cache'


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
        for filename in sh(coffeescript_files(), hide='stdout').stdout.splitlines():
            dirnames.add(path(filename).abspath().dirname())
        for dirname in dirnames:
            observer.schedule(self, dirname)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_coffeescript(event.src_path)
        except Exception:  # pylint: disable=W0703
            traceback.print_exc()


class SassWatcher(PatternMatchingEventHandler):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    patterns = ['*.scss']
    ignore_patterns = ['common/static/xmodule/*']

    def register(self, observer):
        """
        register files with observer
        """
        for dirname in SASS_LOAD_PATHS + SASS_UPDATE_DIRS + theme_sass_paths():
            paths = []
            if '*' in dirname:
                paths.extend(glob.glob(dirname))
            else:
                paths.append(dirname)
            for dirname in paths:
                observer.schedule(self, dirname, recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            compile_sass()
        except Exception:  # pylint: disable=W0703
            traceback.print_exc()


class XModuleSassWatcher(SassWatcher):
    """
    Watches for sass file changes
    """
    ignore_directories = True
    ignore_patterns = []

    def register(self, observer):
        """
        register files with observer
        """
        observer.schedule(self, 'common/lib/xmodule/', recursive=True)

    def on_modified(self, event):
        print('\tCHANGED:', event.src_path)
        try:
            process_xmodule_assets()
        except Exception:  # pylint: disable=W0703
            traceback.print_exc()


def theme_sass_paths():
    """
    Return the a list of paths to the theme's sass assets,
    or an empty list if no theme is configured.
    """
    edxapp_env = Env()

    if edxapp_env.feature_flags.get('USE_CUSTOM_THEME', False):
        theme_name = edxapp_env.env_tokens.get('THEME_NAME', '')
        parent_dir = path(edxapp_env.REPO_ROOT).abspath().parent
        theme_root = parent_dir / "themes" / theme_name
        return [theme_root / "static" / "sass"]
    else:
        return []


def coffeescript_files():
    """
    return find command for paths containing coffee files
    """
    dirs = " ".join([Env.REPO_ROOT / coffee_dir for coffee_dir in COFFEE_DIRS])
    return cmd('find', dirs, '-type f', '-name \"*.coffee\"')


def compile_coffeescript(*files):
    """
    Compile CoffeeScript to JavaScript.
    """
    if not files:
        files = ["`{}`".format(coffeescript_files())]
    sh(cmd(
        "node_modules/.bin/coffee", "--compile", *files
    ))


def compile_sass(debug=False):
    """
    Compile Sass to CSS.
    """
    theme_paths = theme_sass_paths()
    sh(cmd(
        'sass', '' if debug else '--style compressed',
        "--cache-location {cache}".format(cache=SASS_CACHE_PATH),
        "--load-path", " ".join(SASS_LOAD_PATHS + theme_paths),
        "--update", "-E", "utf-8", " ".join(SASS_UPDATE_DIRS + theme_paths)
    ))


def compile_templated_sass(systems, settings):
    """
    Render Mako templates for Sass files.
    `systems` is a list of systems (e.g. 'lms' or 'cms' or both)
    `settings` is the Django settings module to use.
    """
    for sys in systems:
        sh(django_cmd(sys, settings, 'preprocess_assets'))


def process_xmodule_assets():
    """
    Process XModule static assets.
    """
    sh('xmodule_assets common/static/xmodule')


def collect_assets(systems, settings):
    """
    Collect static assets, including Django pipeline processing.
    `systems` is a list of systems (e.g. 'lms' or 'cms' or both)
    `settings` is the Django settings module to use.
    """
    for sys in systems:
        sh(django_cmd(sys, settings, "collectstatic --noinput > /dev/null"))


@task
def watch(background=False, **kwargs):
    """
    Watch for changes to asset files, and regenerate js/css
    """
    observer = Observer()

    CoffeeScriptWatcher().register(observer)
    SassWatcher().register(observer)
    XModuleSassWatcher().register(observer)

    print("Starting asset watcher...")
    observer.start()
    if not background:
        # when running as a separate process, the main thread needs to loop
        # in order to allow for shutdown by contrl-c
        try:
            while True:
                observer.join(2)
        except KeyboardInterrupt:
            observer.stop()
        print("\nStopped asset watcher.")



@task('prereqs.install', help={
    "system":       "lms or cms",
    "settings":     "Django settings module",
    "debug":        "Disable Sass compression",
    "skip-collect": "Skip collection of static assets",
    "watch":        "Watch files for changes",
})
def update(system=None, watch=False, settings="dev", debug=False, skip_collect=True, **kwargs):
    """
    Compile CoffeeScript and Sass, then collect static assets.
    """

    if system is None:
        system = ['lms', 'cms']
    else:
        system = [system]

    compile_templated_sass(system, settings)
    process_xmodule_assets()
    compile_coffeescript()
    compile_sass(debug)

    if not skip_collect:
        collect_assets(system, settings)
        print(Fore.WHITE + "Done collecting assets...")

    if watch:
        print(Fore.WHITE + "Starting to watch assets")
        run('invoke assets.watch --background {}'.format(not debug))
