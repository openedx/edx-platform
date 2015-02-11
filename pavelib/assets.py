"""
Asset compilation and collection.
"""
from __future__ import print_function
import argparse
from paver.easy import sh, path, task, cmdopts, needs, consume_args
from .utils.envs import Env
from .utils.cmd import cmd, django_cmd
from .utils.process import run_background_process

# setup baseline paths

edxapp_env = Env()
theme_enabled = edxapp_env.feature_flags.get('USE_CUSTOM_THEME', False)
if theme_enabled:
    theme_name = edxapp_env.env_tokens.get('THEME_NAME', '')
    parent_dir = path(edxapp_env.REPO_ROOT).abspath().parent
    theme_root = parent_dir / "themes" / theme_name


def compile_assets(systems, production):
    """
    Compile all assets.
    """
    for sys in systems:
        command = [
            # grunt should be installed globally
            # for now here as we don't want to
            # break tests & people's devstacks.
            './node_modules/grunt-cli/bin/grunt',
            sys + ':dist' if production else sys
        ]

        if theme_enabled:
            command += [u'--theme={}'.format(theme_root)]

        sh(cmd(*command))


def compile_coffeescript(systems):
    """
    Compile js.
    """
    for sys in systems:
        command = [
            # grunt should be installed globally
            # for now here as we don't want to
            # break tests & people's devstacks.
            './node_modules/grunt-cli/bin/grunt',
            sys + ':js'
        ]

        sh(cmd(*command))


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
@cmdopts([
    ('background', 'b', 'Background mode'),
    ('systems=', 's', 'Systems to run on')
])
def watch_assets(options):
    """
    Watch for changes to asset files, and regenerate js/css
    """
    systems = getattr(options, 'systems', ['lms', 'studio'])
    background = getattr(options, 'background', True)

    for sys in systems:
        command = [
            # grunt should be installed globally
            # for now here as we don't want to
            # break tests & people's devstacks.
            './node_modules/grunt-cli/bin/grunt',
            sys + ':watch'
        ]

        if theme_enabled:
            command += [u'--theme={}'.format(theme_root)]

        if background:
            run_background_process(cmd(*command))
        else:
            sh(cmd(*command))


@task
@needs(
    'pavelib.prereqs.install_node_prereqs'
)
@consume_args
def update_assets(args):
    """
    Compile CoffeeScript and Sass, then collect static assets.
    """
    parser = argparse.ArgumentParser(prog='paver update_assets')
    parser.add_argument(
        'system', type=str, nargs='*', default=['lms', 'studio'],
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
        '--production', action='store_true', default=False,
        help="Minify and optimize assets for production environment",
    )
    parser.add_argument(
        '--skip-collect', dest='collect', action='store_false', default=True,
        help="Skip collection of static assets",
    )
    args = parser.parse_args(args)

    compile_templated_sass(args.system, args.settings)
    process_xmodule_assets()
    compile_assets(args.system, args.production)

    if args.collect:
        collect_assets(args.system, args.settings)
