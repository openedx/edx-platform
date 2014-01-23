from paver.easy import *
from pavelib import prereqs, proc_utils, paver_utils, assets


# devstack aimed at vagrant environment studio = cms
default_port = {"lms": 8000, "studio": 8001}


# Abort if system is not one we recognize
def assert_devstack_sys(sys_name):
    if not sys_name in ('lms', 'studio'):
        paver_utils.print_red("Devstack system must be either 'lms' or 'studio'")
        exit(1)


# Convert "studio" to "cms"
def old_system(sys_name):
    return "cms" if sys_name == "studio" else sys_name


@task
@cmdopts([
    ("system=", "s", "System to act on"),
])
def devstack_start(options):
    """
    Start the server
    """
    system = getattr(options, 'system', 'lms')
    assert_devstack_sys(system)
    port = default_port[system]
    system = old_system(system)

    proc_utils.run_process(
        ['python manage.py {system} runserver --settings=devstack 0.0.0.0:{port}'.format(
            system=system, port=port)
         ], True)


@task
@cmdopts([
    ("system=", "s", "System to act on"),
])
def devstack_assets(options):
    """
    Update static assets
    """
    system = getattr(options, 'system', 'lms')
    assert_devstack_sys(system)
    system = old_system(system)

    setattr(options, 'system', system)
    setattr(options, 'env', 'devstack')
    assets.compile_assets(options)


@task
def devstack_install():
    """
    Update Python, Ruby, and Node requirements
    """

    prereqs.install_prereqs()


@task
@cmdopts([
    ("system=", "s", "System to act on"),
])
def devstack(options):
    """
    Start the devstack lms or studio server
    """
    devstack_install(options)
    devstack_assets(options)
    devstack_start(options)
