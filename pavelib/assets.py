from paver.easy import *
from paver.setuputils import setup
from pavelib import prereqs

import sys
import json
import glob
import os
import platform
import subprocess
import signal
import psutil


setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)

# Build Constants
REPO_ROOT = path(__file__).abspath().dirname().dirname()  # /project_dir/edx-platform/
PROJECT_ROOT = REPO_ROOT.dirname()      # /project_dir
REPORT_DIR = PROJECT_ROOT / "reports"   # /project_dir/reports
COMMON_ROOT = PROJECT_ROOT / "common"   # /project_dir/common
COURSES_ROOT = PROJECT_ROOT / "data"    # /project_dir/data

# Environment constants
try:
    CONFIG_PREFIX = os.environ['SERVICE_VARIANT'] + '.'
except KeyError:
    CONFIG_PREFIX = ''

ENV_FILE = os.path.join(PROJECT_ROOT, CONFIG_PREFIX + "env.json")

env_data = None

try:
    with open(ENV_FILE) as env_file:
        env_data = json.load(env_file)
except IOError:
    sys.stderr.write("Warning: File env.json not found - some configuration requires this\n")
    sys.stderr.flush()

USE_CUSTOM_THEME = False

if env_data:
    USE_CUSTOM_THEME = 'THEME_NAME' in env_data and env_data['THEME_NAME'] != ''

    if USE_CUSTOM_THEME:
        THEME_NAME = env_data['THEME_NAME']
        THEME_ROOT = PROJECT_ROOT / "themes" / THEME_NAME
        THEME_SASS = THEME_ROOT / "static" / "sass"

MINIMAL_DARWIN_NOFILE_LIMIT = 8000


def signal_handler(signal, frame):
    print("Ending...")


def kill_process(proc):
    p1_group = psutil.Process(proc.pid)

    child_pids = p1_group.get_children(recursive=True)

    for child_pid in child_pids:
        os.kill(child_pid.pid, signal.SIGKILL)


def xmodule_cmd(watch=False, debug=False):
    xmodule = 'xmodule_assets common/static/xmodule'
    if watch:

        xmodule = "watchmedo shell-command " + \
                  " --patterns='*.js;*.coffee;*.sass;*.scss;*.css' " + \
                  " --recursive " + \
                  " --command=\'xmodule_assets common/static/xmodule\'" + \
                  " --wait " + \
                  " common/lib/xmodule"

    return xmodule


def coffee_clean():
    files = glob.glob('*/static/coffee/**/*.js')

    for f in files:
        os.remove(f)


def coffee_cmd(watch=False, debug=False):
    cmd = ''

    if platform.system() == 'Darwin':
        cmd = 'ulimit -n 8000; '

    return ('%s node_modules/.bin/coffee --compile ' % cmd) + ('--watch' if watch else '') + ' .'


def sass_cmd(watch=False, debug=False):
    sass_load_paths = ["./common/static/sass"]
    sass_watch_paths = ["*/static"]
    if USE_CUSTOM_THEME:
        sass_load_paths.append(THEME_SASS)
        sass_watch_paths.append(THEME_SASS)

    return 'sass ' + ('--debug-info' if debug else '--style=compressed ') + \
           ' --load-path=' + ' '.join(sass_load_paths) + \
           (' --watch' if watch else ' --update') + ' -E utf-8 ' + ' '.join(sass_watch_paths)


 # This task takes arguments purely to pass them via dependencies to the preprocess task
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
    run_debug = getattr(options, 'debug', False)
    clobber = getattr(options, 'clobber', False)

    print ("Compile Coffeescript")

    coffee_clean()

    if clobber:
        print("Coffeescript files removed")
        return

    try:
        sh('python manage.py %s preprocess_assets --settings=%s --traceback ' % (system, env))
    except:
        sys.stderr.write("asset preprocessing failed")
        sys.stderr.flush()
        return

    kwargs = {'shell': True, 'cwd': None}

    sh(coffee_cmd(False, run_debug))

    p1 = 0

    try:
        if run_watch:
            p1 = subprocess.Popen(coffee_cmd(run_watch, run_debug), **kwargs)

            signal.signal(signal.SIGINT, signal_handler)
            print("Enter CTL-C to end")
            signal.pause()
            print("Compile Coffescript ending")
    except:
        sys.stderr.write("Error running watch Coffeescript")
        sys.stderr.flush()
    finally:
        if run_watch:
            try:
                kill_process(p1)
            except KeyboardInterrupt:
                pass
            except:
                pass


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
        sys.stderr.write("asset preprocessing failed")
        sys.stderr.flush()
        return

    kwargs = {'shell': True, 'cwd': None}

    sh(xmodule_cmd(False, run_debug))

    p1 = 0

    try:
        if run_watch:
            p1 = subprocess.Popen(xmodule_cmd(run_watch, run_debug), **kwargs)

            signal.signal(signal.SIGINT, signal_handler)
            print("Enter CTL-C to end")
            signal.pause()
            print("Compile Xmodule ending")
    except:
        sys.stderr.write("Error running watch Xmodule")
        sys.stderr.flush()
    finally:
        if run_watch:
            try:
                p1.terminate()
            except KeyboardInterrupt:
                pass
            except:
                pass


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
        sys.stderr.write("asset preprocessing failed")
        sys.stderr.flush()
        return

    kwargs = {'shell': True, 'cwd': None}

    sh(sass_cmd(False, run_debug))

    p1 = 0

    try:
        if run_watch:
            p1 = subprocess.Popen(sass_cmd(run_watch, run_debug), **kwargs)

            signal.signal(signal.SIGINT, signal_handler)
            print("Enter CTL-C to end")
            signal.pause()
            print("Compile Sass ending")
    except:
        sys.stderr.write("Error running compile Sass")
        sys.stderr.flush()
    finally:
        if run_watch:
            try:
                kill_process(p1)
            except KeyboardInterrupt:
                pass
            except:
                pass


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
        sys.stderr.write("asset preprocessing failed")
        sys.stderr.flush()
        return

    try:
        sh('python manage.py %s collectstatic --traceback --settings=%s' % (system, env) + ' --noinput > /dev/null')
    except:
        pass


# This task takes arguments purely to pass them via dependencies to the preprocess task
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
        sys.stderr.write("asset preprocessing failed")
        sys.stderr.flush()
        return

    prereqs.install_prereqs()

    coffee_clean()
    kwargs = {'shell': True, 'cwd': None}

    sh(coffee_cmd(False, run_debug))
    sh(xmodule_cmd(False, run_debug))
    sh(sass_cmd(False, run_debug))

    p1 = 0
    p2 = 0
    p3 = 0

    try:
        if collectstatic:
            print("collecting static")
            sh('python manage.py %s collectstatic --traceback --settings=%s' % (system, env) + ' --noinput > /dev/null')

        if run_watch:
            p1 = subprocess.Popen(coffee_cmd(run_watch, run_debug), **kwargs)
            p2 = subprocess.Popen(xmodule_cmd(run_watch, run_debug), **kwargs)
            p3 = subprocess.Popen(sass_cmd(run_watch, run_debug), **kwargs)

            signal.signal(signal.SIGINT, signal_handler)
            print("Enter CTL-C to end")
            signal.pause()
            print("compile_assets ending")
    except:
        sys.stderr.write("Error running compile_assets")
        sys.stderr.flush()
    finally:
        if run_watch:
            try:
                p2.terminate()
            except KeyboardInterrupt:
                pass

            try:
                kill_process(p3)
                kill_process(p1)
            except KeyboardInterrupt:
                pass
            except:
                pass
