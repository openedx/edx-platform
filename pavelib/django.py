from paver.easy import *
from paver.setuputils import setup

import os
import psutil
from pavelib import prereqs

default_options = {"lms": '8000', "cms": '8001'}

"""

desc "Set the staff bit for a user"
task :set_staff, [:user, :system, :env] do |t, args|
    args.with_defaults(:env => 'dev', :system => 'lms', :options => '')
    sh(django_admin(args.system, args.env, 'set_staff', args.user))
end

"""


setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)


def kill_process(pid):
    p1_group = psutil.Process(p1.pid)

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
    sh("django-admin.py runserver --traceback --settings=lms.envs.dev --pythonpath=.")


@task
@cmdopts([
    ("system=", "s", "System to act on"),
    ("env=", "e", "Environment settings"),
])
def run_server():
    """
      runs server specified by system using a supplied environment
    """
    system = getattr(options, 'system', 'lms')
    env = getattr(options, 'env', 'dev')

    prereqs.install_prereqs()
    pre_django()

    try:
        sh('django-admin.py runserver --traceback ' + ('--settings=%s.envs.%s' % (system, env)) + '--pythonpath=. ' + default_options[system])
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
    pre_django()

    try:
        sh('django-admin.py syncdb --traceback ' + ('--settings=lms.envs.%s' % (env)) + '--pythonpath=. ')
        sh('django-admin.py migrate --traceback ' + ('--settings=lms.envs.%s' % (env)) + '--pythonpath=. ')
    except:
        print("Failed to import settings")
        return


@task
@cmdopts([
    ("env=", "e", "Environment settings"),
])
def check_settings():
    """
       checks settings files
    """
    env = getattr(options, 'env', 'dev')
    pre_django()

    try:
        sh(("echo 'import cms.envs.%s'" % env) + " | django-admin.py shell " + (' --settings=cms.envs.%s' % (env)) + ' --pythonpath=. ')
        sh(("echo 'import lms.envs.%s'" % env) + " | django-admin.py shell " + (' --settings=lms.envs.%s' % (env)) + ' --pythonpath=. ')
    except:
        print("Failed to import settings")
        return


@task
@cmdopts([
    ("env=", "e", "Environment settings"),
])
def run_all_servers():
    """
      runs cms, lms and celery workers
    """
    env = getattr(options, 'env', 'dev')

    # prereqs.install_prereqs()
    # pre_django()

    kwargs = {'shell': True, 'cwd': None}

    p1 = 0
    p2 = 0
    p3 = 0
    p4 = 0

    try:
        p1 = subprocess.Popen('django-admin.py runserver --traceback ' + ('--settings=lms.envs.%s' % (env)) + ' --pythonpath=. ' + default_options['lms'], **kwargs)
        p2 = subprocess.Popen('django-admin.py runserver --traceback ' + ('--settings=cms.envs.%s' % (env)) + ' --pythonpath=. ' + default_options['cms'], **kwargs)
        p3 = subprocess.Popen("django-admin.py celery worker --loglevel=INFO --settings=lms.envs.dev_with_worker --pythonpath=. ", **kwargs)
        p4 = subprocess.Popen("django-admin.py celery worker --loglevel=INFO --settings=lms.envs.dev_with_worker --pythonpath=. ", **kwargs)

        input("Enter to end")
    except:
        print("Failed to runserver")
        return
    finally:
        kill_process(p1)
        kill_process(p2)
        kill_process(p3)
        kill_process(p4)
