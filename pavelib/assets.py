from paver.easy import *
from pavelib import prereqs, proc_utils
from proc_utils import write_stderr

import json
import glob
import os
import platform

# Build Constants
REPO_ROOT = path(__file__).abspath().dirname().dirname()  # /project_dir/edx-platform/
PROJECT_ROOT = REPO_ROOT.dirname()      # /project_dir
REPORT_DIR = REPO_ROOT / "reports"   # /project_dir/edx-platform/reports
TEST_DIR = REPO_ROOT / ".testids"    # /project_dir/edx-platform/.testdir
COMMON_ROOT = PROJECT_ROOT / "common"   # /project_dir/common
COURSES_ROOT = PROJECT_ROOT / "data"    # /project_dir/data


# Environment constants
if 'SERVICE_VARIANT' in os.environ:
    CONFIG_PREFIX = os.environ['SERVICE_VARIANT'] + '.'
else:
    CONFIG_PREFIX = ''

ENV_FILE = os.path.join(PROJECT_ROOT, CONFIG_PREFIX + "env.json")

env_data = None

try:
    with open(ENV_FILE) as env_file:
        env_data = json.load(env_file)
except IOError:
    write_stderr("Warning: File env.json not found - some configuration requires this\n")

USE_CUSTOM_THEME = False

if env_data:
    if 'FEATURES' in env_data and 'USE_CUSTOM_THEME' in env_data['FEATURES']:
        USE_CUSTOM_THEME = env_data['FEATURES']['USE_CUSTOM_THEME']

    if USE_CUSTOM_THEME:
        THEME_NAME = env_data['THEME_NAME']
        THEME_ROOT = PROJECT_ROOT / "themes" / THEME_NAME
        THEME_SASS = THEME_ROOT / "static" / "sass"

MINIMAL_DARWIN_NOFILE_LIMIT = 8000


def xmodule_cmd(watch=False, debug=False):
    xmodule = 'xmodule_assets common/static/xmodule'

    if watch:
        xmodule = ("watchmedo shell-command "
                   " --patterns='*.js;*.coffee;*.sass;*.scss;*.css' "
                   " --recursive --command=\'xmodule_assets common/static/xmodule\'"
                   " --wait common/lib/xmodule"
                   )

    return xmodule


def coffee_clean():
    files = glob.glob('*/static/coffee/**/*.js')

    for f in files:
        os.remove(f)


def coffee_cmd(watch=False):

    if watch:
        cmd = "node_modules/.bin/coffee --compile --watch lms/ cms/ common/"
    else:
        cmd = "node_modules/.bin/coffee --compile `find lms/ cms/ common/ -type f -name *.coffee` "

    if platform.system() == "Darwin":
        precmd = "ulimit -n 8000;"
    else:
        precmd = ""

    return "{precmd} {cmd}".format(precmd=precmd, cmd=cmd)


def sass_cmd(watch=False, debug=False):
    load_paths = ["./common/static/sass"]
    watch_paths = ["*/static"]

    if USE_CUSTOM_THEME:
        load_paths.append(THEME_SASS)
        watch_paths.append(THEME_SASS)

    load_paths = ' '.join(load_paths)
    watch_paths = ' '.join(watch_paths)

    debug_info = '--debug-info' if debug else '--style=compressed '
    watch_or_update = '--watch' if watch else '--update'

    cmd = ('sass {debug_info} --load-path={load_paths} {watch_or_update} -E utf-8 {watch_paths}'.format(
           debug_info=debug_info, load_paths=load_paths, watch_or_update=watch_or_update, watch_paths=watch_paths)
           )

    return cmd


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
    ("watch", "w", "Run with watch"),
    ("debug", "d", "Run with debug"),
    ("clobber", "c", "Remove compiled Coffeescript files"),
])
def compile_coffeescript(options):
    """
    Runs coffeescript
    """

    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')
    run_watch = getattr(options, 'watch', False)
    clobber = getattr(options, 'clobber', False)

    print ("Compile Coffeescript")

    coffee_clean()

    if clobber:
        print("Coffeescript files removed")
        return

    try:
        sh('python manage.py %s preprocess_assets --settings=%s --traceback ' % (system, env))
    except:
        write_stderr("asset preprocessing failed")
        return

    sh(coffee_cmd(False))

    if run_watch:
        proc_utils.run_process([coffee_cmd(run_watch)], True)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
    ("watch", "w", "Run with watch"),
    ("debug", "d", "Run with debug"),
])
def compile_xmodule(options):
    """
    Runs xmodule_cmd
    """

    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')
    run_watch = getattr(options, 'watch', False)
    run_debug = getattr(options, 'debug', False)

    print ("Compile xmodule assets")

    try:
        sh('python manage.py %s preprocess_assets --settings=%s --traceback ' % (system, env))
    except:
        write_stderr("asset preprocessing failed")
        return

    sh(xmodule_cmd(False, run_debug))

    if run_watch:
        proc_utils.run_process([xmodule_cmd(run_watch, run_debug)], True)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
    ("watch", "w", "Run with watch"),
    ("debug", "d", "Run with debug"),
])
def compile_sass(options):
    """
    Runs sass
    """

    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')
    run_watch = getattr(options, 'watch', False)
    run_debug = getattr(options, 'debug', False)

    print ("Compile sass")

    try:
        sh('python manage.py %s preprocess_assets --settings=%s --traceback ' % (system, env))
    except:
        write_stderr("asset preprocessing failed")
        return

    sh(sass_cmd(False, run_debug))

    if run_watch:
        proc_utils.run_process([sass_cmd(run_watch, run_debug)], True)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
])
def collectstatic(options):
    """
    Runs collectstatic
    """

    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')

    print ("Run collectstatic")

    try:
        sh('python manage.py %s preprocess_assets --settings=%s --traceback ' % (system, env))
    except:
        write_stderr("asset preprocessing failed")
        return

    try:
        sh('python manage.py %s collectstatic --traceback --settings=%s' % (system, env) + ' --noinput > /dev/null')
    except:
        pass


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
    ("watch", "w", "Run with watch"),
    ("debug", "d", "Run with debug"),
    ("collectstatic", "c", "Collect Static"),
])
def compile_assets(options):
    """
    Runs coffeescript, sass and xmodule_cmd and then optionally collectstatic
    """

    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')
    run_watch = getattr(options, 'watch', False)
    run_debug = getattr(options, 'debug', False)
    collectstatic = getattr(options, 'collectstatic', False)

    print ("Compile all assets")

    try:
        sh('python manage.py %s preprocess_assets --settings=%s --traceback ' % (system, env))
    except:
        write_stderr("asset preprocessing failed")
        return

    prereqs.install_prereqs()

    coffee_clean()

    if collectstatic:
        print("collecting static")
        sh('python manage.py {system} collectstatic --traceback --settings={env} --noinput > /dev/null'.format(system=system, env=env))

    if run_watch:
        proc_utils.run_process([coffee_cmd(run_watch),
                                xmodule_cmd(run_watch, run_debug),
                                sass_cmd(run_watch, run_debug)], True)
    else:
        sh(coffee_cmd(False))
        sh(xmodule_cmd(False, run_debug))
        sh(sass_cmd(False, run_debug))
