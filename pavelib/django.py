from paver.easy import *
from paver.setuputils import setup

import os
import psutil
from pavelib import prereqs

default_options = {"lms": '8000', "cms": '8001'}

setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)


def kill_process(proc):
    p1_group = psutil.Process(proc.pid)

    child_pids = p1_group.get_children(recursive=True)

    for child_pid in child_pids:
        os.kill(child_pid.pid, signal.SIGKILL)


@task
def pre_django():
    """
    Installs requirements and cleans previous python compiled files
    """
    prereqs.install_python_prereqs()
    sh("find . -type f -name *.pyc -delete")
    sh('pip install -q --no-index -r requirements/edx/local.txt')


@task
def fast_lms():
    """
      runs lms without running prereqs
    """
    sh("python manage.py lms runserver --traceback --settings=dev --pythonpath=. %s" % default_options['lms'])


@task
@cmdopts([
    ("env=", "e", "Environment settings"),
])
def cms(options):

    setattr(options,'system','cms')
    run_server(options)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
])
def run_server(options):
    """
      runs server specified by system using a supplied environment
    """
    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')

    try:
        sh('python manage.py %s runserver --traceback --settings=%s' % (system, env) + ' --pythonpath=. ' + default_options[system])
    except:
        print("Failed to runserver")
        return


@task
@cmdopts([
    ("env=", "e", "Environment settings"),
])
def resetdb():
    """
      runs syncdb and then migrate
    """
    env = getattr(options, 'env', 'dev')

    sh('python manage.py lms syncdb --traceback --settings=%s' % (env) + ' --pythonpath=. ')
    sh('python manage.py lms migrate --traceback --settings=%s' % (env) + ' --pythonpath=. ')


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
])
def check_settings():
    """
       checks settings files
    """
    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')

    try:
        sh(("echo 'import %s.envs.%s'" % (system, env)) + ' | python manage.py %s shell --plain --settings=%s' % (system, env) + ' --pythonpath=. ')
    except:
        print("Failed to import settings")
        return


@task
@cmdopts([
    ("system=", "s", "System to act on"),
])
def run_celery():
    """
      runs celery for the specified system
    """
    system = getattr(options, 'system', 'lms')

    kwargs = {'shell': True, 'cwd': None}

    p1 = 0

    try:
        p1 = subprocess.Popen('python manage.py %s celery worker --loglevel=INFO --settings=dev_with_worker --pythonpath=. ' % (system), **kwargs)

        input("Enter CTL-C to end")
    except KeyboardInterrupt:
        print("\nrun_celery ending")
    except:
        print("Failed to run celery")
        pass
    finally:
        try:
            kill_process(p1)
        except KeyboardInterrupt:
            pass


@task
@cmdopts([
    ("env=", "e", "Environment settings"),
])
def run_all_servers():
    """
      runs cms, lms and celery workers
    """
    env = getattr(options, 'env', 'dev')

    kwargs = {'shell': True, 'cwd': None}

    p1 = 0
    p2 = 0
    p3 = 0
    p4 = 0

    try:
        p1 = subprocess.Popen('python manage.py lms runserver --traceback --settings=%s' % (env) + ' --pythonpath=. ' + default_options['lms'], **kwargs)
        p2 = subprocess.Popen('python manage.py cms runserver --traceback --settings=%s' % (env) + ' --pythonpath=. ' + default_options['cms'], **kwargs)
        p3 = subprocess.Popen('python manage.py lms celery worker --loglevel=INFO --settings=%s_with_worker --pythonpath=. ' % (env), **kwargs)
        p4 = subprocess.Popen('python manage.py cms celery worker --loglevel=INFO --settings=%s_with_worker --pythonpath=. ' % (env), **kwargs)

        input("Enter to end")
    except:
        print("Failed to runserver")
        return
    finally:
        kill_process(p1)
        kill_process(p2)
        kill_process(p3)
        kill_process(p4)
