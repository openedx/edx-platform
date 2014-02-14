"""
Asset compilation and collection.
"""
import argparse
from paver.easy import *
from .utils.envs import Env
from .utils.cmd import cmd, django_cmd


COFFEE_DIRS = ['lms', 'cms', 'common']
SASS_LOAD_PATHS = ['./common/static/sass']
SASS_UPDATE_DIRS = ['*/static']
SASS_CACHE_PATH = '/tmp/sass-cache'


def theme_sass_paths():
    """
    Return the a list of paths to the theme's sass assets,
    or an empty list if no theme is configured.
    """
    edxapp_env = Env()

    if edxapp_env.feature_flags.get('USE_CUSTOM_THEME', False):
        theme_name = edxapp_env.env_tokens.get('THEME_NAME', '')
        theme_root = path(edxapp_env.REPO_ROOT).dirname() / "themes" / theme_name
        return [theme_root / "static" / "sass"]

    else:
        return []


def compile_coffeescript():
    """
    Compile CoffeeScript to JavaScript.
    """
    dirs = " ".join([Env.REPO_ROOT / coffee_dir for coffee_dir in COFFEE_DIRS])
    sh(cmd(
        "node_modules/.bin/coffee", "--compile",
        " `find {dirs} -type f -name \"*.coffee\"`".format(dirs=dirs)
    ))


def compile_sass(debug):
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
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
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
    `systems` is a list of systems (e.g. 'lms' or 'studio' or both)
    `settings` is the Django settings module to use.
    """
    for sys in systems:
        sh(django_cmd(sys, settings, "collectstatic --noinput > /dev/null"))


@task
@needs('pavelib.prereqs.install_prereqs')
@consume_args
def update_assets(args):
    """
    Compile CoffeeScript and Sass, then collect static assets.
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument('system', type=str, nargs='*', default=['lms', 'studio'], help="lms or studio")
    parser.add_argument('--settings', type=str, default="dev", help="Django settings module")
    parser.add_argument('--debug', action='store_true', default=False, help="Disable Sass compression")
    parser.add_argument('--skip-collect', action='store_true', default=False, help="Skip collection of static assets")
    args = parser.parse_args(args)

    compile_templated_sass(args.system, args.settings)
    process_xmodule_assets()
    compile_coffeescript()
    compile_sass(args.debug)

    if not args.skip_collect:
        collect_assets(args.system, args.settings)
